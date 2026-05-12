# c:/Users/liucx/.nuke/MyButton/window_01/search_window.py
# -*- coding: UTF-8 -*-
"""搜索型工具窗口主类"""

import os
import json

from PySide6.QtCore import Qt, QTimer, QEvent
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QGridLayout, QScrollArea, QLineEdit, QPushButton, 
    QLabel, QMessageBox
)
from PySide6.QtGui import QKeySequence, QShortcut

from window_01.config import _get_user_db_path, _get_toolbox_path
from window_01.db import FastDBQuery, IconCache, SmartCache
from window_01.widgets import ToolButton


class SearchToolWindow(QMainWindow):
    """搜索型工具窗口"""
    
    def __init__(self, toolbox_path, parent=None):
        super().__init__(parent)
        self.setWindowTitle(" 工具搜索")
        self.setGeometry(100, 100, 100, 100)
        self.setMinimumSize(800, 400)
        self.setMaximumSize(800, 400)
        
        
        
        self.toolbox_path = toolbox_path
        
        # 布局参数配置（可调整）
        self.tools_per_row = 5  # 每行显示数量
        self.page_size = self.tools_per_row * 5  # 每次加载数量（3的倍数）
        self.button_width = 250  # 按钮固定宽度（可调整）
        self.button_height = 80  # 按钮固定高度（可调整）
        self.grid_spacing = 10  # 按钮间距（可调整）
        self.grid_margins = 10  # 网格边距（可调整）
        
        try:
            db_path = _get_user_db_path()
            self.db_query = FastDBQuery(db_path)
        except Exception as e:
            QMessageBox.critical(None, "错误", f"数据库初始化失败:\n{str(e)}")
            raise
        
        self.icon_cache = IconCache(toolbox_path)
        self.smart_cache = SmartCache(max_size=100)
        

        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_NoSystemBackground)
        self.setAttribute(Qt.WA_TranslucentBackground)

        # self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.Tool)
        
        # self.setAttribute(Qt.WA_NoSystemBackground, False)
        # self.setAttribute(Qt.WA_TranslucentBackground, False)
        
        self.dragging = False
        self.offset = None
        self.current_search_params = {}
        self.current_offset = 0
        self.total_count = 0
        
        self._setup_ui()
        self.installEventFilter(self)
        # 绑定 ESC 快捷键关闭窗口
        self._setup_shortcuts()
        
        QTimer.singleShot(100, self._load_initial_data)

    def _setup_shortcuts(self):
        """设置快捷键"""
        esc_shortcut = QShortcut(QKeySequence("Esc"), self)
        esc_shortcut.activated.connect(self.hide)
    
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
        title_label.setVisible(False)
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
        # self.stats_label = QLabel("加载中...")
        # self.stats_label.setStyleSheet("""
        #     QLabel {
        #         padding: 5px;
        #         font-size: 11px;
        #         color: rgba(180, 190, 200, 255);
        #     }
        # """)
        # main_layout.addWidget(self.stats_label)
        
        # 结果显示区（滚动区域）
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.scroll_area.setFrameShape(QScrollArea.NoFrame)
        
        self.content_widget = QWidget()
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setContentsMargins(5, 5, 5, 5)
        self.content_layout.setSpacing(5)
        
        # 设置固定宽度，确保水平方向不会拉伸
        self.content_widget.setMinimumWidth(400)
        self.content_widget.setMaximumWidth(600)
        
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
        
        print(f"\n{'='*60}")
        print(f"[搜索调试]")
        print(f"  输入文本: '{search_text}'")
        print(f"  解析参数: {search_params}")
        print(f"  缓存键: {cache_key}")
        
        self.current_search_params = search_params
        
        # 检查缓存
        cached_data = self.smart_cache.get(cache_key)
        if cached_data:
            print(f"  [缓存命中] 总数: {cached_data['total_count']}, 工具数: {len(cached_data['tools'])}")
            self.total_count = cached_data['total_count']
            tools = cached_data['tools']
            self._display_tools(tools)
            self._update_stats()
            return
        
        # 从数据库查询
        print(f"  [数据库查询] 开始查询...")
        tools = self.db_query.search_tools(
            search_params,
            limit=self.page_size,
            offset=self.current_offset
        )
        
        print(f"  [数据库查询] 找到 {len(tools)} 个工具")
        
        self.total_count = self.db_query.get_total_count(search_params)
        print(f"  [数据库查询] 总数: {self.total_count}")
        
        # 缓存结果
        self.smart_cache.set(cache_key, {
            'tools': tools,
            'total_count': self.total_count
        })
        
        self._display_tools(tools)
        self._update_stats()
        print(f"{'='*60}\n")
    
    def _display_tools(self, tools):
        """显示工具列表（网格布局）"""
        self._clear_results()
        
        if not tools:
            empty_label = QLabel("没有找到工具")
            empty_label.setAlignment(Qt.AlignCenter)
            empty_label.setStyleSheet("""
                QLabel {
                    color: rgba(150, 160, 170, 200);
                    font-size: 12px;
                    padding: 20px;
                }
            """)
            self.content_layout.insertWidget(
                self.content_layout.count() - 1,
                empty_label
            )
            return
        
        # 创建网格容器
        grid_widget = QWidget()
        grid_layout = QGridLayout(grid_widget)
        grid_layout.setContentsMargins(self.grid_margins, self.grid_margins, self.grid_margins, self.grid_margins)
        grid_layout.setSpacing(self.grid_spacing)
        
        row = 0
        col = 0
        
        for tool_data in tools:
            # 创建数据副本，避免修改原始数据
            tool_copy = dict(tool_data)
            
            # 拼接图标的完整路径
            if tool_copy['tpng']:
                original_path = tool_copy['tpng']
                tool_copy['tpng'] = os.path.join(self.toolbox_path, tool_copy['tpng'])
            
            tool_btn = ToolButton(tool_copy)
            tool_btn.setProperty('button_width', self.button_width)
            tool_btn.setProperty('button_height', self.button_height)
            
            tool_btn.clicked.connect(lambda checked, btn=tool_btn: self._on_tool_clicked(btn))
            
            grid_layout.addWidget(tool_btn, row, col)
            
            col += 1
            if col >= self.tools_per_row:
                col = 0
                row += 1
        
        self.content_layout.insertWidget(
            self.content_layout.count() - 1,
            grid_widget
        )
    
    def _clear_results(self):
        """清空结果显示"""
        for i in reversed(range(self.content_layout.count())):
            widget = self.content_layout.itemAt(i).widget()
            if widget and isinstance(widget, QWidget):
                if widget.layout() and isinstance(widget.layout(), QGridLayout):
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
            return
        
        self.current_offset += self.page_size
        
        cache_key = self._search_params_to_key(self.current_search_params)
        cached_data = self.smart_cache.get(cache_key)
        
        if cached_data and len(cached_data['tools']) >= self.current_offset + self.page_size:
            tools = cached_data['tools'][self.current_offset:self.current_offset + self.page_size]
        else:
            tools = self.db_query.search_tools(
                self.current_search_params,
                limit=self.page_size,
                offset=self.current_offset
            )
            
            if cached_data:
                cached_data['tools'].extend(tools)
            else:
                self.smart_cache.set(cache_key, {
                    'tools': tools,
                    'total_count': self.total_count
                })
        
        # 获取现有的网格布局
        grid_widget = None
        for i in range(self.content_layout.count()):
            widget = self.content_layout.itemAt(i).widget()
            if widget and isinstance(widget, QWidget):
                layout = widget.layout()
                if isinstance(layout, QGridLayout):
                    grid_widget = widget
                    grid_layout = layout
                    break
        
        if grid_widget and grid_layout:
            row_count = grid_layout.rowCount()
            
            start_row = row_count - 1
            last_row_items = 0
            for c in range(self.tools_per_row):
                item = grid_layout.itemAtPosition(start_row, c)
                if item:
                    last_row_items += 1
            
            if last_row_items >= self.tools_per_row:
                start_row += 1
            
            row = start_row
            col = last_row_items if last_row_items < self.tools_per_row else 0
            
            for tool_data in tools:
                tool_btn = ToolButton(tool_data)
                
                tool_btn.clicked.connect(lambda checked, btn=tool_btn: self._on_tool_clicked(btn))
                
                grid_layout.addWidget(tool_btn, row, col)
                
                col += 1
                if col >= self.tools_per_row:
                    col = 0
                    row += 1
    
    def _update_stats(self):
        """更新统计信息"""
        loaded_count = min(self.current_offset + self.page_size, self.total_count)
        # self.stats_label.setText(f"共 {self.total_count} 个工具，已加载 {loaded_count} 个")
    
    def _on_tool_clicked(self, btn):
        """工具按钮点击"""
        tool_data = btn.tool_data
        
        print(f"[执行工具] {tool_data['tname']}")
        print(f"   工具路径: {tool_data['tpath']}")
        print(f"   图标路径: {tool_data['tpng']}")
        if tool_data['tpng']:
            print(f"   图标完整路径: {os.path.join(self.toolbox_path, tool_data['tpng'])}")
            print(f"   图标存在: {os.path.exists(os.path.join(self.toolbox_path, tool_data['tpng']))}")
        else:
            print(f"   无图标")
        
        # TODO: 在这里实现工具执行逻辑
        
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