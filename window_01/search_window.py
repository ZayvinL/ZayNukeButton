# c:/Users/liucx/.nuke/MyButton/window_01/search_window.py
# -*- coding: UTF-8 -*-
"""搜索型工具窗口主类"""

import os
import json

from PySide6.QtCore import Qt, QTimer, QEvent
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QGridLayout, QScrollArea, QLineEdit, QPushButton, 
    QLabel, QMessageBox, QSlider
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
        
        self.toolbox_path = toolbox_path
        
        # 布局参数配置（可调整）
        self.tools_per_row = 5  # 每行显示数量
        self.beishu = 3  # 倍数
        self.page_size = self.tools_per_row * self.beishu  # 每次加载数量（3的倍数）
        self.button_width = 150  # 按钮固定宽度（可调整）
        self.button_height = 80  # 按钮固定高度（可调整）
        self.grid_spacing = 1  # 按钮间距（可调整）
        self.grid_margins = 1 # 网格边距（可调整）
        
        # 虚拟列表参数
        self.visible_rows = 3  # 可见行数
        self.buffer_rows = 2  # 缓冲行数（上下各留）
        self.total_button_slots = (self.visible_rows + self.buffer_rows * 2) * self.tools_per_row  # 总按钮槽位
        
        # 计算窗口尺寸
        window_width = self.tools_per_row * self.button_width + (self.tools_per_row + 1) * self.grid_spacing + 30
        button_area_height = self.visible_rows * self.button_height + (self.visible_rows + 1) * self.grid_spacing
        window_height = 35 + 35 + button_area_height + 20
        
        self.setMinimumSize(window_width, window_height)
        self.setMaximumSize(window_width + 50, 700)
        
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
        
        self.dragging = False
        self.offset = None
        self.current_search_params = {}
        self.current_offset = 0
        self.total_count = 0
        
        # 虚拟列表数据
        self.all_tools = []  # 所有工具数据（从数据库加载）
        self.tool_buttons = []  # 固定的按钮对象列表
        self.start_index = 0  # 当前显示的第一个工具索引
        
        self._setup_ui()
        self.installEventFilter(self)
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
        
        # 创建主内容区域（横向布局：按钮区 + 滑块）
        content_hlayout = QHBoxLayout()
        content_hlayout.setContentsMargins(0, 0, 0, 0)
        content_hlayout.setSpacing(5)
        
        # 左侧：按钮网格区域
        self.grid_container = QWidget()
        self.grid_layout = QGridLayout(self.grid_container)
        self.grid_layout.setContentsMargins(self.grid_margins, self.grid_margins, self.grid_margins, self.grid_margins)
        self.grid_layout.setSpacing(self.grid_spacing)
        
        # 预创建按钮槽位
        self._create_button_slots()
        
        content_hlayout.addWidget(self.grid_container)
        
        # 右侧：自定义滑块（替代滚动条）
        self.slider = QSlider(Qt.Vertical)
        self.slider.setMinimum(0)
        self.slider.setMaximum(0)  # 初始范围
        self.slider.setPageStep(1)
        self.slider.setSingleStep(1)
        self.slider.setTickPosition(QSlider.NoTicks)
        self.slider.setInvertedAppearance(True)  # 反转外观：0 在顶部，最大值在底部
        
        # 安装事件过滤器，支持鼠标滚轮
        self.slider.installEventFilter(self)
        
        self.slider.setStyleSheet("""
            QSlider {
                background-color: rgba(50, 60, 70, 100);
                border: none;
                border-radius: 5px;
                width: 10px;
            }
            QSlider::groove:vertical {
                background: rgba(50, 60, 70, 150);
                width: 10px;
                border-radius: 5px;
            }
            QSlider::handle:vertical {
                background: rgba(100, 150, 200, 180);
                height: 30px;
                border-radius: 5px;
                margin: 0px -2px;
            }
            QSlider::handle:vertical:hover {
                background: rgba(120, 170, 220, 220);
            }
            QSlider::add-page:vertical, QSlider::sub-page:vertical {
                background: transparent;
            }
        """)
        self.slider.valueChanged.connect(self._on_slider_changed)
        
        content_hlayout.addWidget(self.slider)
        
        main_layout.addLayout(content_hlayout)
        
        central_widget.setStyleSheet("""
            QWidget {
                background-color: rgba(40, 50, 60, 230);
                border-radius: 5px;
            }
        """)
    
    def eventFilter(self, obj, event):
        """事件过滤器 - 处理滑块滚轮事件"""
        if obj == self.slider and event.type() == QEvent.Wheel:
            # 处理滚轮事件
            delta = event.angleDelta().y()
            if delta > 0:
                # 向上滚动：滑块向上移动，显示更早的工具
                self.slider.setValue(max(0, self.slider.value() - 1))
            else:
                # 向下滚动：滑块向下移动，显示更晚的工具
                self.slider.setValue(min(self.slider.maximum(), self.slider.value() + 1))
            
            # 阻止默认行为
            return True
        
        return super().eventFilter(obj, event)
    
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
            print(f"  [缓存命中] 总数: {cached_data['total_count']}")
            self.total_count = cached_data['total_count']
            self.all_tools = cached_data['tools']
            self.start_index = 0
            
            # 更新滑块范围
            self._update_slider_range()
            
            # 显示初始工具
            self._update_visible_buttons()
            self._update_stats()
            return
        
        # 从数据库查询总数量
        self.total_count = self.db_query.get_total_count(search_params)
        print(f"  [数据库查询] 总数: {self.total_count}")
        
        # 查询初始工具（所有工具）
        self.all_tools = self.db_query.search_tools(
            search_params,
            limit=-1,
            offset=0
        )
        
        # 缓存结果
        self.smart_cache.set(cache_key, {
            'tools': self.all_tools,
            'total_count': self.total_count
        })
        
        self.start_index = 0
        
        # 更新滑块范围
        self._update_slider_range()
        
        # 显示初始工具
        self._update_visible_buttons()
        self._update_stats()
        print(f"{'='*60}\n")
    
    def _display_tools(self, tools):
        """显示工具列表"""
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
            self.content_layout.addWidget(empty_label)
            return
        
        grid_widget = QWidget()
        grid_layout = QGridLayout(grid_widget)
        grid_layout.setContentsMargins(self.grid_margins, self.grid_margins, self.grid_margins, self.grid_spacing)
        grid_layout.setSpacing(self.grid_spacing)
        
        # 计算实际需要的行数
        total_rows = (len(tools) + self.tools_per_row - 1) // self.tools_per_row
        
        # 设置每列固定宽度，禁止拉伸
        for col in range(self.tools_per_row):
            grid_layout.setColumnMinimumWidth(col, self.button_width)
            grid_layout.setColumnStretch(col, 0)
        
        # 设置每行固定高度，禁止拉伸
        for row in range(total_rows):
            grid_layout.setRowMinimumHeight(row, self.button_height)
            grid_layout.setRowStretch(row, 0)
        
        # 计算容器固定尺寸（只根据当前加载的工具数量）
        total_width = self.tools_per_row * self.button_width + (self.tools_per_row + 1) * self.grid_spacing
        total_height = total_rows * self.button_height + (total_rows + 1) * self.grid_spacing
        grid_widget.setFixedSize(total_width, total_height)
        
        row = 0
        col = 0
        
        for tool_data in tools:
            tool_copy = dict(tool_data)
            
            if tool_copy['tpng']:
                tool_copy['tpng'] = os.path.join(self.toolbox_path, tool_copy['tpng'])
            
            tool_btn = ToolButton(tool_copy)
            tool_btn.setFixedSize(self.button_width, self.button_height)
            
            tool_btn.clicked.connect(lambda checked, btn=tool_btn: self._on_tool_clicked(btn))
            
            grid_layout.addWidget(tool_btn, row, col)
            
            col += 1
            if col >= self.tools_per_row:
                col = 0
                row += 1
        
        # 插入 grid_widget 到顶部
        self.content_layout.addWidget(grid_widget)
        
        # 关键：添加 stretch 填充底部空白，保持滚动范围
        self.content_layout.addStretch()
    
    def _clear_results(self):
        """清空结果显示"""
        self.all_tools.clear()
        self.total_count = 0
        self.start_index = 0
        self._update_content_height()
        self._update_visible_buttons()
    
    def _update_content_height(self):
        """设置滚动条范围（不改变 content_widget 高度）"""
        # content_widget 高度固定为可见区域（3行）
        visible_height = self.visible_rows * self.button_height + (self.visible_rows + 1) * self.grid_spacing
        self.content_widget.setFixedHeight(visible_height)
        
        if self.total_count == 0:
            # 没有工具时，设置滚动条范围很小
            scrollbar = self.scroll_area.verticalScrollBar()
            scrollbar.setRange(0, 1)
            return
        
        # 计算总行数
        total_rows = (self.total_count + self.tools_per_row - 1) // self.tools_per_row
        visible_rows = self.visible_rows
        scrollable_rows = max(0, total_rows - visible_rows)
        
        # 手动设置滚动条的范围（模拟总高度）
        scrollbar = self.scroll_area.verticalScrollBar()
        max_range = scrollable_rows * self.button_height
        scrollbar.setRange(0, max_range)
    
    def _update_slider_range(self):
        """根据数据库总工具数设置滑块范围"""
        if self.total_count == 0:
            self.slider.setMaximum(0)
            self.slider.setValue(0)
            return
        
        # 计算总行数
        total_rows = (self.total_count + self.tools_per_row - 1) // self.tools_per_row
        visible_rows = self.visible_rows
        scrollable_rows = max(0, total_rows - visible_rows)
        
        # 设置滑块范围（正向：0 到 scrollable_rows）
        self.slider.setMaximum(scrollable_rows)
        self.slider.setValue(0)  # 重置到顶部
        
        print(f"[滑块范围] total_count={self.total_count}, scrollable_rows={scrollable_rows}")
    
    def _on_slider_changed(self, value):
        """滑块值变化 - 虚拟列表核心"""
        if not self.all_tools or self.total_count == 0:
            return
        
        # 直接使用滑块值（不反转）
        # 滑块在顶部（value=0）→ 显示工具 0-14
        # 滑块在底部（value=max）→ 显示工具 15-29
        self.start_index = value * self.tools_per_row
        
        print(f"[滑块调试] value={value}, start_index={self.start_index}")
        
        # 更新按钮内容
        self._update_visible_buttons()
    
    def _update_visible_buttons(self):
        """更新可见区域的按钮内容（虚拟列表核心）"""
        if not self.all_tools:
            for btn in self.tool_buttons:
                btn.setVisible(False)
            return
        
        # 只更新可见区域的按钮（15 个）
        visible_count = self.visible_rows * self.tools_per_row
        
        for i in range(len(self.tool_buttons)):
            btn = self.tool_buttons[i]
            tool_index = self.start_index + i
            
            if tool_index < len(self.all_tools):
                tool_data = self.all_tools[tool_index]
                tool_copy = dict(tool_data)
                
                if tool_copy['tpng']:
                    tool_copy['tpng'] = os.path.join(self.toolbox_path, tool_copy['tpng'])
                
                btn.tool_data = tool_copy
                btn.button_index = tool_index  # 设置索引
                btn.update_content(tool_copy)
                btn.setVisible(True)
            else:
                btn.setVisible(False)
    
    def _create_button_slots(self):
        """创建固定的按钮槽位（虚拟列表）"""
        for btn in self.tool_buttons:
            btn.setParent(None)
            btn.deleteLater()
        self.tool_buttons.clear()
        
        # 只创建可见区域的按钮（15 个）
        total_slots = self.visible_rows * self.tools_per_row
        for i in range(total_slots):
            empty_data = {
                'tname': '',
                'ttip': '',
                'tclass': '',
                'tpath': '',
                'tpng': '',
                'is_favorite': False
            }
            btn = ToolButton(empty_data)
            btn.setFixedSize(self.button_width, self.button_height)
            btn.setVisible(False)
            
            btn.clicked.connect(lambda checked, b=btn: self._on_tool_clicked(b))
            
            self.tool_buttons.append(btn)
            
            row = i // self.tools_per_row
            col = i % self.tools_per_row
            self.grid_layout.addWidget(btn, row, col)
        
        # grid_container 固定大小（只容纳可见区域）
        grid_width = self.tools_per_row * self.button_width + (self.tools_per_row + 1) * self.grid_spacing
        grid_height = self.visible_rows * self.button_height + (self.visible_rows + 1) * self.grid_spacing
        self.grid_container.setFixedSize(grid_width, grid_height)
    
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
    
    def closeEvent(self, event):
        self.db_query.close()
        super().closeEvent(event)