# -*- coding: UTF-8 -*-
"""
搜索型工具窗口 - 智能缓存 + 虚拟列表
支持多条件组合搜索，动态加载显示
"""

import os
import sys
import json
import sqlite3

import paths_setup as psp

from PySide6.QtGui import *
from PySide6.QtCore import *
from PySide6.QtWidgets import *


# ============================================================================
# 🔧 内部辅助函数
# ============================================================================

def _get_user_db_path():
    """获取当前用户的数据库路径"""
    db_path = psp.user_db_path_get()
    config_path = psp.get_user_dbjson_path()
    
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"用户配置文件不存在: {config_path}")
    
    with open(config_path, 'r', encoding='utf-8') as f:
        config = json.load(f)
        db_uuid = config.get('current_db_uuid')
        
        if not db_uuid:
            raise ValueError("配置文件中未找到 current_db_uuid")
    
    db_path = os.path.join(db_path, f"tools_{db_uuid}.db")
    
    if not os.path.exists(db_path):
        raise FileNotFoundError(f"数据库文件不存在: {db_path}")
    
    return db_path


def _get_toolbox_path():
    """获取工具箱根目录路径"""
    return os.path.join(os.path.dirname(__file__), 'tools')


# ============================================================================
# 🚀 核心实现区
# ============================================================================

class FastDBQuery:
    """快速数据库查询器"""
    
    def __init__(self, db_path):
        self.db_path = db_path
        self._connection = None
    
    def _get_connection(self):
        if self._connection is None and self.db_path:
            if os.path.exists(self.db_path):
                self._connection = sqlite3.connect(self.db_path)
                self._connection.row_factory = sqlite3.Row
            else:
                raise FileNotFoundError(f"数据库文件不存在: {self.db_path}")
        return self._connection
    
    def search_tools(self, search_params, limit=10, offset=0):
        """
        搜索工具
        
        search_params: {
            'classes': ['Read', 'Write'],  # C=: 类别
            'labels': ['Python'],          # L=: 标签
            'paths': ['C:\\Tools'],        # P=: 路径
            'names': ['Notepad'],          # N=: 名称
            'keywords': ['test']           # 普通关键词（模糊搜索所有字段）
        }
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # 构建查询条件
        conditions = []
        params = []
        
        # 类别搜索
        if search_params.get('classes'):
            class_conditions = []
            for cls in search_params['classes']:
                class_conditions.append("t.matchClass LIKE ?")
                params.append(f'%"{cls}"%')
            conditions.append(f"({' OR '.join(class_conditions)})")
        
        # 标签搜索
        if search_params.get('labels'):
            label_conditions = []
            for label in search_params['labels']:
                label_conditions.append("t.tag LIKE ?")
                params.append(f'%{label}%')
            conditions.append(f"({' OR '.join(label_conditions)})")
        
        # 路径搜索
        if search_params.get('paths'):
            path_conditions = []
            for path in search_params['paths']:
                path_conditions.append("t.main_file LIKE ?")
                params.append(f'%{path}%')
            conditions.append(f"({' OR '.join(path_conditions)})")
        
        # 名称搜索
        if search_params.get('names'):
            name_conditions = []
            for name in search_params['names']:
                name_conditions.append("t.name LIKE ?")
                params.append(f'%{name}%')
            conditions.append(f"({' OR '.join(name_conditions)})")
        
        # 普通关键词（模糊搜索所有字段）
        if search_params.get('keywords'):
            keyword_conditions = []
            for keyword in search_params['keywords']:
                keyword_conditions.append(
                    "(t.name LIKE ? OR t.tag LIKE ? OR t.main_file LIKE ?)"
                )
                params.extend([f'%{keyword}%', f'%{keyword}%', f'%{keyword}%'])
            conditions.append(f"({' OR '.join(keyword_conditions)})")
        
        # 构建完整查询
        where_clause = " AND ".join(conditions) if conditions else "1=1"
        
        query = f'''
            SELECT 
                t.id as tuuid,
                t.name as tname,
                t.matchClass as tclass,
                t.main_file as tpath,
                t.icon_file as tpng,
                t.help_file as ttxt,
                t.tag as ttip,
                u.is_installed,
                u.is_favorite,
                u.usage_count
            FROM tools_index t
            INNER JOIN user_tools u ON t.id = u.tool_id
            WHERE {where_clause}
            ORDER BY u.is_favorite DESC, t.name
            LIMIT ? OFFSET ?
        '''
        
        params.extend([limit, offset])
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        result = []
        for row in rows:
            result.append({
                'tuuid': row['tuuid'],
                'tname': row['tname'],
                'tclass': row['tclass'],
                'tpath': row['tpath'],
                'tpng': row['tpng'] if row['tpng'] else '',
                'ttxt': row['ttxt'] if row['ttxt'] else '',
                'ttip': row['ttip'] if row['ttip'] else '',
                'is_installed': row['is_installed'],
                'is_favorite': row['is_favorite'],
                'usage_count': row['usage_count']
            })
        
        return result
    
    def get_total_count(self, search_params):
        """获取搜索结果总数"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        conditions = []
        params = []
        
        if search_params.get('classes'):
            class_conditions = []
            for cls in search_params['classes']:
                class_conditions.append("t.matchClass LIKE ?")
                params.append(f'%"{cls}"%')
            conditions.append(f"({' OR '.join(class_conditions)})")
        
        if search_params.get('labels'):
            label_conditions = []
            for label in search_params['labels']:
                label_conditions.append("t.tag LIKE ?")
                params.append(f'%{label}%')
            conditions.append(f"({' OR '.join(label_conditions)})")
        
        if search_params.get('paths'):
            path_conditions = []
            for path in search_params['paths']:
                path_conditions.append("t.main_file LIKE ?")
                params.append(f'%{path}%')
            conditions.append(f"({' OR '.join(path_conditions)})")
        
        if search_params.get('names'):
            name_conditions = []
            for name in search_params['names']:
                name_conditions.append("t.name LIKE ?")
                params.append(f'%{name}%')
            conditions.append(f"({' OR '.join(name_conditions)})")
        
        if search_params.get('keywords'):
            keyword_conditions = []
            for keyword in search_params['keywords']:
                keyword_conditions.append(
                    "(t.name LIKE ? OR t.tag LIKE ? OR t.main_file LIKE ?)"
                )
                params.extend([f'%{keyword}%', f'%{keyword}%', f'%{keyword}%'])
            conditions.append(f"({' OR '.join(keyword_conditions)})")
        
        where_clause = " AND ".join(conditions) if conditions else "1=1"
        
        query = f'''
            SELECT COUNT(*) as count
            FROM tools_index t
            INNER JOIN user_tools u ON t.id = u.tool_id
            WHERE {where_clause}
        '''
        
        cursor.execute(query, params)
        return cursor.fetchone()['count']
    
    def close(self):
        if self._connection:
            self._connection.close()
            self._connection = None


class IconCache:
    """图标缓存管理器"""
    
    def __init__(self, toolbox_path):
        self._cache = {}
        self._base_path = toolbox_path
    
    def get_icon(self, icon_relative_path, size=QSize(20, 20)):
        if not icon_relative_path:
            return QIcon()
        
        if icon_relative_path in self._cache:
            return self._cache[icon_relative_path]
        
        full_path = os.path.join(self._base_path, icon_relative_path)
        
        if os.path.exists(full_path):
            pixmap = QPixmap(full_path)
            if not pixmap.isNull():
                scaled_pixmap = pixmap.scaled(
                    size,
                    Qt.KeepAspectRatio,
                    Qt.SmoothTransformation
                )
                icon = QIcon(scaled_pixmap)
                self._cache[icon_relative_path] = icon
                return icon
        
        return QIcon()


class SmartCache:
    """智能缓存管理器"""
    
    def __init__(self, max_size=100):
        self._cache = {}  # {search_key: [tools]}
        self._max_size = max_size
        self._access_order = []  # 记录访问顺序（用于 LRU）
    
    def get(self, search_key):
        """获取缓存数据"""
        if search_key in self._cache:
            # 更新访问顺序
            if search_key in self._access_order:
                self._access_order.remove(search_key)
            self._access_order.append(search_key)
            return self._cache[search_key]
        return None
    
    def set(self, search_key, data):
        """设置缓存数据"""
        # 如果缓存满了，清理最久未使用的
        if len(self._cache) >= self._max_size and search_key not in self._cache:
            oldest_key = self._access_order.pop(0)
            if oldest_key in self._cache:
                del self._cache[oldest_key]
        
        self._cache[search_key] = data
        
        # 更新访问顺序
        if search_key in self._access_order:
            self._access_order.remove(search_key)
        self._access_order.append(search_key)
    
    def clear(self):
        """清空缓存"""
        self._cache.clear()
        self._access_order.clear()


class ToolButton(QPushButton):
    """自定义工具按钮"""
    
    def __init__(self, tool_data, parent=None):
        super().__init__(parent)
        self.tool_data = tool_data
        self._setup_ui()
    
    def _setup_ui(self):
        name = self.tool_data['tname']
        if '.' in name:
            name = name[:name.rindex('.')]
        
        self.setText(name)
        
        # 构建 tooltip
        tooltip_parts = [f"<b>{name}</b>"]
        if self.tool_data['ttip']:
            tooltip_parts.append(f"说明: {self.tool_data['ttip']}")
        if self.tool_data['tclass']:
            tooltip_parts.append(f"类: {self.tool_data['tclass']}")
        if self.tool_data['is_favorite']:
            tooltip_parts.append("⭐ 已收藏")
        
        self.setToolTip("<br>".join(tooltip_parts))
        
        self.setStyleSheet("""
            QPushButton {
                text-align: left;
                padding: 8px 12px 8px 40px;
                font-size: 12px;
                background-color: rgba(50, 60, 70, 200);
                color: rgba(200, 210, 220, 255);
                border: 1px solid rgba(80, 100, 120, 150);
                border-radius: 3px;
            }
            QPushButton:hover {
                background-color: rgba(70, 90, 110, 220);
                color: rgba(255, 200, 100, 255);
                border-color: rgba(100, 130, 160, 200);
            }
            QPushButton:pressed {
                background-color: rgba(60, 80, 100, 200);
            }
        """)
        
        self.setMinimumHeight(35)
    
    def set_icon(self, icon):
        if not icon.isNull():
            self.setIcon(icon)
            self.setIconSize(QSize(20, 20))


class SearchToolWindow(QMainWindow):
    """搜索型工具窗口"""
    
    def __init__(self, toolbox_path, parent=None):
        super().__init__(parent)
        self.setWindowTitle("🔧 工具搜索")
        self.setGeometry(200, 200, 500, 600)
        
        self.toolbox_path = toolbox_path
        self.page_size = 10  # 每页显示数量（可配置）
        
        # 初始化组件
        try:
            db_path = _get_user_db_path()
            self.db_query = FastDBQuery(db_path)
        except Exception as e:
            QMessageBox.critical(None, "错误", f"数据库初始化失败:\n{str(e)}")
            raise
        
        self.icon_cache = IconCache(toolbox_path)
        self.smart_cache = SmartCache(max_size=100)
        
        # 窗口设置
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_NoSystemBackground)
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        # 状态变量
        self.dragging = False
        self.offset = None
        self.current_search_params = {}
        self.current_offset = 0
        self.total_count = 0
        
        # UI
        self._setup_ui()
        self.installEventFilter(self)
        
        # 延迟加载初始数据
        QTimer.singleShot(100, self._load_initial_data)
    
    def _setup_ui(self):
        """设置UI"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(5, 5, 5, 5)
        main_layout.setSpacing(5)
        
        # 标题栏
        title_bar = QWidget()
        title_layout = QHBoxLayout(title_bar)
        title_layout.setContentsMargins(10, 5, 10, 5)
        
        title_label = QLabel(" 工具搜索")
        title_label.setStyleSheet("""
            QLabel {
                color: rgba(220, 230, 240, 255);
                font-size: 14px;
                font-weight: bold;
            }
        """)
        title_layout.addWidget(title_label)
        title_layout.addStretch()
        
        close_btn = QPushButton("×")
        close_btn.setFixedSize(25, 25)
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(200, 60, 60, 180);
                color: white;
                border: none;
                border-radius: 3px;
                font-size: 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: rgba(220, 80, 80, 220);
            }
        """)
        close_btn.clicked.connect(self.hide)
        title_layout.addWidget(close_btn)
        
        main_layout.addWidget(title_bar)
        
        # 搜索框
        search_layout = QHBoxLayout()
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("搜索工具... (C=:类, L=:标签, P=:路径, N=:名称)")
        self.search_input.setStyleSheet("""
            QLineEdit {
                padding: 8px 12px;
                font-size: 12px;
                background-color: rgba(50, 60, 70, 200);
                color: rgba(220, 230, 240, 255);
                border: 1px solid rgba(80, 100, 120, 150);
                border-radius: 3px;
            }
            QLineEdit:focus {
                border-color: rgba(100, 150, 200, 200);
            }
        """)
        self.search_input.textChanged.connect(self._on_search_changed)
        search_layout.addWidget(self.search_input)
        
        main_layout.addLayout(search_layout)
        
        # 统计信息
        self.stats_label = QLabel("加载中...")
        self.stats_label.setStyleSheet("""
            QLabel {
                padding: 5px;
                font-size: 11px;
                color: rgba(180, 190, 200, 255);
            }
        """)
        main_layout.addWidget(self.stats_label)
        
        # 结果显示区（虚拟列表）
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.scroll_area.setFrameShape(QScrollArea.NoFrame)
        
        self.content_widget = QWidget()
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        self.content_layout.setSpacing(3)
        self.content_layout.addStretch()
        
        self.scroll_area.setWidget(self.content_widget)
        main_layout.addWidget(self.scroll_area)
        
        # 监听滚动事件
        self.scroll_area.verticalScrollBar().valueChanged.connect(self._on_scroll)
        
        central_widget.setStyleSheet("""
            QWidget {
                background-color: rgba(40, 50, 60, 230);
                border-radius: 5px;
            }
        """)
    
    def _parse_search_text(self, text):
        """解析搜索文本"""
        search_params = {
            'classes': [],
            'labels': [],
            'paths': [],
            'names': [],
            'keywords': []
        }
        
        if not text.strip():
            return search_params
        
        # 分割关键词（逗号分隔）
        parts = [p.strip() for p in text.split(',') if p.strip()]
        
        for part in parts:
            if part.startswith('C=:'):
                search_params['classes'].append(part[3:])
            elif part.startswith('L=:'):
                search_params['labels'].append(part[3:])
            elif part.startswith('P=:'):
                search_params['paths'].append(part[3:])
            elif part.startswith('N=:'):
                search_params['names'].append(part[3:])
            else:
                search_params['keywords'].append(part)
        
        return search_params
    
    def _search_params_to_key(self, search_params):
        """将搜索参数转换为缓存键"""
        return json.dumps(search_params, sort_keys=True)
    
    def _load_initial_data(self):
        """加载初始数据（默认显示所有工具）"""
        # TODO: 这里可以根据其他数据生成默认搜索字符串
        # 例如：根据选中的节点类自动生成搜索条件
        default_search = ""  # 空搜索，显示所有工具
        
        self.search_input.setText(default_search)
        self._perform_search()
    
    def _on_search_changed(self, text):
        """搜索框内容变化"""
        self.current_offset = 0
        self._clear_results()
        self._perform_search()
    
    def _perform_search(self):
        """执行搜索"""
        search_text = self.search_input.text()
        search_params = self._parse_search_text(search_text)
        cache_key = self._search_params_to_key(search_params)
        
        self.current_search_params = search_params
        
        # 检查缓存
        cached_data = self.smart_cache.get(cache_key)
        if cached_data:
            self.total_count = cached_data['total_count']
            tools = cached_data['tools']
            self._display_tools(tools)
            self._update_stats()
            return
        
        # 从数据库查询
        tools = self.db_query.search_tools(
            search_params,
            limit=self.page_size,
            offset=self.current_offset
        )
        
        self.total_count = self.db_query.get_total_count(search_params)
        
        # 缓存结果
        self.smart_cache.set(cache_key, {
            'tools': tools,
            'total_count': self.total_count
        })
        
        self._display_tools(tools)
        self._update_stats()
    
    def _display_tools(self, tools):
        """显示工具列表"""
        self._clear_results()
        
        for tool_data in tools:
            tool_btn = ToolButton(tool_data)
            
            if tool_data['tpng']:
                icon = self.icon_cache.get_icon(tool_data['tpng'])
                tool_btn.set_icon(icon)
            
            tool_btn.clicked.connect(lambda checked, btn=tool_btn: self._on_tool_clicked(btn))
            
            # 插入到滚动区域之前
            self.content_layout.insertWidget(
                self.content_layout.count() - 1,
                tool_btn
            )
    
    def _clear_results(self):
        """清空结果显示"""
        for i in reversed(range(self.content_layout.count())):
            widget = self.content_layout.itemAt(i).widget()
            if widget and isinstance(widget, ToolButton):
                widget.setParent(None)
    
    def _on_scroll(self, value):
        """滚动事件 - 动态加载更多"""
        scrollbar = self.scroll_area.verticalScrollBar()
        max_value = scrollbar.maximum()
        
        # 当滚动到底部时加载更多
        if value >= max_value - 10:
            self._load_more()
    
    def _load_more(self):
        """加载更多工具"""
        if self.current_offset + self.page_size >= self.total_count:
            return  # 已经加载完所有数据
        
        self.current_offset += self.page_size
        
        # 查询更多数据
        cache_key = self._search_params_to_key(self.current_search_params)
        cached_data = self.smart_cache.get(cache_key)
        
        if cached_data and len(cached_data['tools']) >= self.current_offset + self.page_size:
            # 缓存中已有数据
            tools = cached_data['tools'][self.current_offset:self.current_offset + self.page_size]
        else:
            # 从数据库查询
            tools = self.db_query.search_tools(
                self.current_search_params,
                limit=self.page_size,
                offset=self.current_offset
            )
            
            # 更新缓存
            if cached_data:
                cached_data['tools'].extend(tools)
            else:
                self.smart_cache.set(cache_key, {
                    'tools': tools,
                    'total_count': self.total_count
                })
        
        # 显示新加载的工具
        for tool_data in tools:
            tool_btn = ToolButton(tool_data)
            
            if tool_data['tpng']:
                icon = self.icon_cache.get_icon(tool_data['tpng'])
                tool_btn.set_icon(icon)
            
            tool_btn.clicked.connect(lambda checked, btn=tool_btn: self._on_tool_clicked(btn))
            
            self.content_layout.insertWidget(
                self.content_layout.count() - 1,
                tool_btn
            )
    
    def _update_stats(self):
        """更新统计信息"""
        loaded_count = min(self.current_offset + self.page_size, self.total_count)
        self.stats_label.setText(f"共 {self.total_count} 个工具，已加载 {loaded_count} 个")
    
    def _on_tool_clicked(self, btn):
        """工具按钮点击"""
        tool_data = btn.tool_data
        
        # TODO: 在这里实现工具执行逻辑
        print(f"[执行工具] {tool_data['tname']}")
        print(f"   路径: {tool_data['tpath']}")
        
        # 执行后隐藏窗口
        self.hide()
    
    def eventFilter(self, obj, event):
        """窗口拖动"""
        if event.type() == QEvent.MouseButtonPress and event.button() == Qt.LeftButton:
            self.dragging = True
            self.offset = event.position().toPoint()
            return True
        elif event.type() == QEvent.MouseMove and self.dragging and self.offset:
            self.move(self.mapToGlobal(event.position().toPoint() - self.offset))
            return True
        elif event.type() == QEvent.MouseButtonRelease:
            self.dragging = False
            self.offset = None
            return True
        return super().eventFilter(obj, event)
    
    def closeEvent(self, event):
        self.db_query.close()
        super().closeEvent(event)


# ============================================================================
# 🎯 对外接口
# ============================================================================

_search_window_instance = None

def init_search_window():
    """初始化搜索窗口"""
    global _search_window_instance
    
    if _search_window_instance is None:
        toolbox_path = _get_toolbox_path()
        _search_window_instance = SearchToolWindow(toolbox_path)
    
    return _search_window_instance

def show_search_window():
    """显示搜索窗口"""
    window = init_search_window()
    window.show()

def hide_search_window():
    """隐藏搜索窗口"""
    global _search_window_instance
    if _search_window_instance:
        _search_window_instance.hide()


# ============================================================================
# 📝 测试入口
# ============================================================================

if __name__ == "__main__":
    app = QApplication(sys.argv)
    show_search_window()
    sys.exit(app.exec())