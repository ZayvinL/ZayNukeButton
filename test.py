# -*- coding: UTF-8 -*-
"""
浮动工具按钮 - 快速切换版
类似 360 悬浮球的设计，快捷键切换显示/隐藏
"""

from PySide6.QtGui import *
from PySide6.QtCore import *
from PySide6.QtWidgets import *

import os
import sys
import json
import sqlite3

import paths_setup as psp


# ============================================================================
# 📌 接口定义区 - 使用者需要实现这些函数
# ============================================================================

def get_database_path():
    """【接口1】获取数据库路径"""
    return _get_user_db_path()


def get_selected_node_classes():
    """【接口2】获取当前选中的节点类列表"""
    # TODO: 在这里实现你的节点类获取逻辑
    return ["testclass"]


def get_hotkey_sequence():
    """【接口3】获取快捷键序列"""
    # TODO: 在这里实现你的快捷键设置
    return "Ctrl+1"


def execute_tool(tool_path, node_names):
    """【接口4】执行工具"""
    # TODO: 在这里实现你的工具执行逻辑
    print(f"[执行工具] 路径: {tool_path}")
    print(f"[执行工具] 节点: {node_names}")


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
        """获取数据库连接（单例复用）"""
        if self._connection is None and self.db_path:
            if os.path.exists(self.db_path):
                self._connection = sqlite3.connect(self.db_path)
                self._connection.row_factory = sqlite3.Row
            else:
                raise FileNotFoundError(f"数据库文件不存在: {self.db_path}")
        return self._connection
    
    def get_tools_by_class(self, tool_class):
        """根据工具类获取已安装的工具"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        query = '''
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
            WHERE u.is_installed = 1
              AND t.matchClass LIKE ?
            ORDER BY t.name
        '''
        
        pattern = f'%"{tool_class}"%'
        cursor.execute(query, (pattern,))
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
    
    def close(self):
        """关闭数据库连接"""
        if self._connection:
            self._connection.close()
            self._connection = None


class IconCache:
    """图标缓存管理器"""
    
    def __init__(self, toolbox_path):
        self._cache = {}
        self._base_path = toolbox_path
    
    def get_icon(self, icon_relative_path, size=QSize(20, 20)):
        """获取图标（带缓存和预缩放）"""
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


class FloatingButton(QWidget):
    """浮动小按钮（悬浮球）"""
    
    toggle_window = Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_NoSystemBackground)
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        self.dragging = False
        self.offset = None
        
        self._setup_ui()
        self.installEventFilter(self)
    
    def _setup_ui(self):
        """设置UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        self.button = QPushButton("")
        self.button.setFixedSize(50, 50)
        self.button.setStyleSheet("""
            QPushButton {
                background-color: rgba(60, 140, 200, 200);
                color: white;
                border: 2px solid rgba(100, 180, 240, 220);
                border-radius: 25px;
                font-size: 24px;
            }
            QPushButton:hover {
                background-color: rgba(80, 160, 220, 220);
                border-color: rgba(120, 200, 255, 240);
            }
            QPushButton:pressed {
                background-color: rgba(40, 120, 180, 200);
            }
        """)
        
        self.button.clicked.connect(self.toggle_window.emit)
        layout.addWidget(self.button)
        
        self.resize(50, 50)
    
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


class ToolButton(QPushButton):
    """工具按钮"""
    
    def __init__(self, tool_data, parent=None):
        super().__init__(parent)
        self.tool_data = tool_data
        self._setup_ui()
    
    def _setup_ui(self):
        """设置UI"""
        name = self.tool_data['tname']
        if '.' in name:
            name = name[:name.rindex('.')]
        
        self.setText(name)
        
        tooltip_parts = [f"<b>{name}</b>"]
        if self.tool_data['ttip']:
            tooltip_parts.append(f"说明: {self.tool_data['ttip']}")
        if self.tool_data['tclass']:
            tooltip_parts.append(f"类: {self.tool_data['tclass']}")
        
        self.setToolTip("<br>".join(tooltip_parts))
        
        self.setStyleSheet("""
            QPushButton {
                text-align: left;
                padding: 6px 12px 6px 35px;
                font-size: 12px;
                background-color: transparent;
                color: rgba(200, 210, 220, 255);
                border: none;
                border-radius: 2px;
            }
            QPushButton:hover {
                background-color: rgba(80, 100, 120, 180);
                color: rgba(255, 200, 100, 255);
            }
            QPushButton:pressed {
                background-color: rgba(60, 80, 100, 200);
            }
        """)
        
        self.setMinimumHeight(30)
    
    def set_icon(self, icon):
        """设置图标"""
        if not icon.isNull():
            self.setIcon(icon)
            self.setIconSize(QSize(18, 18))


class ExpandableMenuButton(QPushButton):
    """可展开/收起的菜单按钮"""
    
    def __init__(self, title, parent=None):
        super().__init__(title, parent)
        self.setCheckable(True)
        self.setChecked(False)
        
        self.setStyleSheet("""
            QPushButton {
                text-align: left;
                padding: 8px 15px;
                font-size: 13px;
                font-weight: bold;
                background-color: rgba(60, 70, 80, 220);
                color: rgba(220, 230, 240, 255);
                border: none;
                border-radius: 3px;
            }
            QPushButton:hover {
                background-color: rgba(70, 85, 100, 230);
            }
            QPushButton:checked {
                background-color: rgba(80, 100, 120, 240);
            }
        """)
        
        self.setMinimumHeight(35)


class MenuSection(QWidget):
    """菜单区域"""
    
    def __init__(self, class_name, tools_data, icon_cache, toolbox_path, parent=None):
        super().__init__(parent)
        self.class_name = class_name
        self.tools_data = tools_data
        self.icon_cache = icon_cache
        self.toolbox_path = toolbox_path
        self.is_expanded = False
        self.tool_buttons = []
        
        self._setup_ui()
    
    def _setup_ui(self):
        """设置UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)
        
        display_name = self.class_name
        if self.tools_data:
            display_name += f" ({len(self.tools_data)})"
        
        self.menu_button = ExpandableMenuButton(f"▼ {display_name}")
        self.menu_button.clicked.connect(self.toggle_expand)
        layout.addWidget(self.menu_button)
        
        self.tools_container = QWidget()
        tools_layout = QVBoxLayout(self.tools_container)
        tools_layout.setContentsMargins(10, 2, 0, 2)
        tools_layout.setSpacing(1)
        
        for tool_data in self.tools_data:
            tool_btn = ToolButton(tool_data)
            
            full_path = os.path.join(self.toolbox_path, tool_data['tpath'])
            tool_btn.setProperty('tool_path', full_path)
            tool_btn.setProperty('icon_path', tool_data['tpng'])
            
            tool_btn.clicked.connect(self.on_tool_clicked)
            
            tools_layout.addWidget(tool_btn)
            self.tool_buttons.append(tool_btn)
        
        self.tools_container.setVisible(False)
        layout.addWidget(self.tools_container)
    
    def toggle_expand(self):
        """切换展开/收起状态"""
        self.is_expanded = not self.is_expanded
        self.tools_container.setVisible(self.is_expanded)
        
        if self.is_expanded:
            self.menu_button.setText(f"▲ {self.class_name} ({len(self.tools_data)})")
            QTimer.singleShot(10, self._load_icons)
        else:
            self.menu_button.setText(f"▼ {self.class_name} ({len(self.tools_data)})")
    
    def _load_icons(self):
        """异步加载图标"""
        for tool_btn in self.tool_buttons:
            icon_path = tool_btn.property('icon_path')
            if icon_path and tool_btn.icon().isNull():
                icon = self.icon_cache.get_icon(icon_path)
                if not icon.isNull():
                    tool_btn.set_icon(icon)
    
    def on_tool_clicked(self):
        """工具按钮点击"""
        btn = self.sender()
        tool_path = btn.property('tool_path')
        
        if tool_path:
            parent_window = self.window()
            if hasattr(parent_window, 'execute_tool'):
                parent_window.execute_tool(tool_path)


class ToolPanelWindow(QMainWindow):
    """工具面板窗口（可停靠浮动）"""
    
    def __init__(self, toolbox_path, parent=None):
        super().__init__(parent)
        self.setWindowTitle("🔧 工具面板")
        self.setGeometry(200, 200, 400, 500)
        
        self.toolbox_path = toolbox_path
        self.tools_loaded = False
        
        # 初始化数据库查询器
        try:
            db_path = get_database_path()
            self.db_query = FastDBQuery(db_path)
        except Exception as e:
            QMessageBox.critical(None, "错误", f"数据库初始化失败:\n{str(e)}")
            raise
        
        # 初始化图标缓存
        self.icon_cache = IconCache(toolbox_path)
        
        # 窗口设置 - 可停靠浮动
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_NoSystemBackground)
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        # 状态变量
        self.dragging = False
        self.offset = None
        self.node_names = []
        
        # 创建UI
        self._setup_ui()
        self._setup_shortcuts()
        
        # 事件过滤器
        self.installEventFilter(self)
    
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
        
        title_label = QLabel(" 工具面板")
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
        close_btn.clicked.connect(self.hide)  # 隐藏而不是关闭
        title_layout.addWidget(close_btn)
        
        main_layout.addWidget(title_bar)
        
        # 滚动区域
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setFrameShape(QScrollArea.NoFrame)
        
        self.content_widget = QWidget()
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        self.content_layout.setSpacing(3)
        self.content_layout.addStretch()
        
        scroll_area.setWidget(self.content_widget)
        main_layout.addWidget(scroll_area)
        
        central_widget.setStyleSheet("""
            QWidget {
                background-color: rgba(40, 50, 60, 230);
                border-radius: 5px;
            }
        """)
    
    def _setup_shortcuts(self):
        """设置快捷键"""
        try:
            hotkey = get_hotkey_sequence()
            shortcut = QShortcut(QKeySequence(hotkey), self)
            shortcut.activated.connect(self.hide)
        except:
            pass
        
        esc = QShortcut(QKeySequence("Esc"), self)
        esc.activated.connect(self.hide)
    
    def load_tools(self):
        """加载工具（只加载一次）"""
        if self.tools_loaded:
            return True
        
        self._clear_content()
        
        try:
            nodesclass = get_selected_node_classes()
        except Exception as e:
            QMessageBox.critical(None, "错误", f"获取节点类失败:\n{str(e)}")
            return False
        
        self.node_names = []
        
        class_groups = {}
        
        if nodesclass:
            for tool_class in nodesclass:
                tools = self.db_query.get_tools_by_class(tool_class)
                if tools:
                    class_groups[tool_class] = tools
                    break
            
            if not class_groups:
                tools = self.db_query.get_tools_by_class("CBA")
                if tools:
                    class_groups["通用工具 (CBA)"] = tools
        else:
            for cls in ["CBB", "NoSelectedNode"]:
                tools = self.db_query.get_tools_by_class(cls)
                if tools:
                    class_groups[cls] = tools
        
        if class_groups:
            for class_name, tools_data in class_groups.items():
                section = MenuSection(
                    class_name, 
                    tools_data, 
                    self.icon_cache,
                    self.toolbox_path
                )
                self.content_layout.insertWidget(
                    self.content_layout.count() - 1,
                    section
                )
            
            first_section = self.content_layout.itemAt(0).widget()
            if isinstance(first_section, MenuSection):
                first_section.toggle_expand()
            
            self.tools_loaded = True
            return True
        
        return False
    
    def _clear_content(self):
        """清空内容"""
        for i in reversed(range(self.content_layout.count())):
            widget = self.content_layout.itemAt(i).widget()
            if widget and isinstance(widget, MenuSection):
                widget.setParent(None)
    
    def execute_tool(self, tool_path):
        """执行工具"""
        try:
            execute_tool(tool_path, self.node_names)
            self.hide()  # 执行后隐藏窗口，回到悬浮按钮
        except Exception as e:
            QMessageBox.critical(None, "错误", f"执行工具失败:\n{str(e)}")
    
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
        """关闭时清理资源"""
        self.db_query.close()
        super().closeEvent(event)


class FloatingToolApp:
    """浮动工具应用管理器"""
    
    def __init__(self):
        self.app = QApplication(sys.argv)
        self.toolbox_path = _get_toolbox_path()
        
        # 创建悬浮按钮
        self.floating_btn = FloatingButton()
        self.floating_btn.move(100, 100)
        
        # 创建工具面板
        self.tool_panel = ToolPanelWindow(self.toolbox_path)
        
        # 连接信号
        self.floating_btn.toggle_window.connect(self.toggle_panel)
        
        # 设置全局快捷键
        self._setup_global_shortcut()
    
    def _setup_global_shortcut(self):
        """设置全局快捷键"""
        hotkey = get_hotkey_sequence()
        self.global_shortcut = QShortcut(QKeySequence(hotkey), self.tool_panel)
        self.global_shortcut.activated.connect(self.toggle_panel)
    
    def toggle_panel(self):
        """切换面板显示/隐藏"""
        if self.tool_panel.isVisible():
            self.tool_panel.hide()
        else:
            if not self.tool_panel.tools_loaded:
                self.tool_panel.load_tools()
            
            # 将面板显示在悬浮按钮附近
            btn_pos = self.floating_btn.pos()
            panel_pos = QPoint(
                btn_pos.x() + 60,
                btn_pos.y()
            )
            self.tool_panel.move(panel_pos)
            self.tool_panel.show()
    
    def run(self):
        """运行应用"""
        self.floating_btn.show()
        sys.exit(self.app.exec())


def run_floating_tool():
    """启动浮动工具应用"""
    app_manager = FloatingToolApp()
    app_manager.run()


# ============================================================================
#  测试入口
# ============================================================================

if __name__ == "__main__":
    run_floating_tool()