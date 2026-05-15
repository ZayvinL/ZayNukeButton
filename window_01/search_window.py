# c:/Users/liucx/.nuke/MyButton/window_01/search_window.py
# -*- coding: UTF-8 -*-
"""搜索型工具窗口主类"""

import os
import json
import sys
import nuke

from PySide6.QtCore import Qt, QTimer, QEvent, Signal
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QGridLayout, QScrollArea, QLineEdit, QPushButton, 
    QLabel, QMessageBox, QSlider
)
from PySide6.QtGui import QKeySequence, QShortcut

from window_01.config import _get_user_db_path, _get_toolbox_path
from window_01.db import FastDBQuery, IconCache, SmartCache
from window_01.widgets import ToolButton
import nukendoesget
# ShowMyFun = True

class SearchToolWindow(QMainWindow):
    """搜索型工具窗口"""
    
    # 定义窗口隐藏信号
    window_hidden = Signal()
    
    def __init__(self, toolbox_path, parent=None, initial_search_text=""):
        super().__init__(parent)
        self.setWindowTitle(" 工具搜索")
        
        self.toolbox_path = toolbox_path
        self.initial_search_text = initial_search_text
        self.is_visible = False  # 使用实例属性存储状态
        
        # 布局参数配置（可调整）
        self.tools_per_row = 5  # 每行显示数量
        self.beishu = 3  # 倍数
        self.page_size = self.tools_per_row * self.beishu  # 每次加载数量（3的倍数）
        self.button_width = 150  # 按钮固定宽度（可调整）
        self.button_height = 80  # 按钮固定高度（可调整）
        self.grid_spacing = 1  # 按钮间距（可调整）
        self.grid_margins = 1 # 网格边距（可调整）
        
        # 透明度参数（0-255，0=完全透明，255=完全不透明）
        self.button_bg_alpha = 50  # 按钮区域背景透明度
        self.search_bg_alpha = 50  # 搜索框背景透明度（与按钮区域一致）
        
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
        
        # 全透明窗口
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        self.dragging = False
        self.offset = None
        self.current_search_params = {}
        self.current_offset = 0
        self.total_count = 0
        
        # 搜索 debounce 定时器
        self.search_timer = QTimer()
        self.search_timer.setSingleShot(True)
        self.search_timer.timeout.connect(self._perform_search)
        
        # 虚拟列表数据
        self.all_tools = []  # 所有工具数据（从数据库加载）
        self.tool_buttons = []  # 固定的按钮对象列表
        self.start_index = 0  # 当前显示的第一个工具索引
        
        self._setup_ui()
        self.installEventFilter(self)
        self._setup_shortcuts()
        
        QTimer.singleShot(100, self._load_initial_data)
        QTimer.singleShot(200, self._apply_initial_search)
    
    def _apply_initial_search(self):
        """应用初始搜索文本（已合并到 _load_initial_data，此方法保留但不执行）"""
        pass
    
    def _setup_shortcuts(self):
        """设置快捷键"""
        esc_shortcut = QShortcut(QKeySequence("Esc"), self)
        esc_shortcut2 = QShortcut(QKeySequence("A"), self)
        esc_shortcut.activated.connect(self.refresh_status)
        esc_shortcut2.activated.connect(self.refresh_status)
    
    def showEvent(self, event):
        """窗口显示时设置状态"""
        self.is_visible = True
        print(f"窗口显示，is_visible={self.is_visible}")
        super().showEvent(event)
    
    def hideEvent(self, event):
        """窗口隐藏时更新状态并发送信号"""
        self.is_visible = False
        print(f"窗口隐藏，is_visible={self.is_visible}")
        self.window_hidden.emit()
        super().hideEvent(event)
    
    def refresh_status(self):
        """刷新状态"""
        self.hide()
        print(f"refresh_status 调用，is_visible={self.is_visible}")
    
    def _setup_ui(self):
        """设置UI"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 主布局：使用 QGridLayout 来放置四个边框标签和中央内容
        main_layout = QGridLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # 创建四个拖拽标签（50% 透明度）
        drag_alpha = 128  # 50% 透明度
        
        # 上边框
        self.drag_top = QLabel()
        self.drag_top.setMinimumHeight(10)
        self.drag_top.setStyleSheet(f"""
            QLabel {{
                background-color: rgba(50, 60, 70, {drag_alpha});
            }}
        """)
        self.drag_top.installEventFilter(self)
        
        # 下边框
        self.drag_bottom = QLabel()
        self.drag_bottom.setMinimumHeight(10)
        self.drag_bottom.setStyleSheet(f"""
            QLabel {{
                background-color: rgba(50, 60, 70, {drag_alpha});
            }}
        """)
        self.drag_bottom.installEventFilter(self)
        
        # 左边框
        self.drag_left = QLabel()
        self.drag_left.setMinimumWidth(10)
        self.drag_left.setStyleSheet(f"""
            QLabel {{
                background-color: rgba(50, 60, 70, {drag_alpha});
            }}
        """)
        self.drag_left.installEventFilter(self)
        
        # 右边框
        self.drag_right = QLabel()
        self.drag_right.setMinimumWidth(10)
        self.drag_right.setStyleSheet(f"""
            QLabel {{
                background-color: rgba(50, 60, 70, {drag_alpha});
            }}
        """)
        self.drag_right.installEventFilter(self)
        
        # 将四个标签添加到网格布局的四个边
        main_layout.addWidget(self.drag_top, 0, 0, 1, 3)    # 第 0 行，跨 3 列
        main_layout.addWidget(self.drag_left, 1, 0, 1, 1)   # 第 1 行，第 0 列
        main_layout.addWidget(self.drag_right, 1, 2, 1, 1)  # 第 1 行，第 2 列
        main_layout.addWidget(self.drag_bottom, 2, 0, 1, 3) # 第 2 行，跨 3 列
        
        # 中央内容区域（第 1 行，第 1 列）
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(1, 1, 1, 1)
        content_layout.setSpacing(1)
        
        # 搜索框 + 关闭按钮（横向布局）- 不透明背景
        search_layout = QHBoxLayout()
        search_layout.setSpacing(5)
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("搜索工具... (C=:类, L=:标签, P=:路径, N=:名称)")
        self.search_input.setStyleSheet(f"""
            QLineEdit {{
                padding: 8px 12px;
                font-size: 12px;
                background-color: rgba(50, 60, 70, {self.search_bg_alpha});
                color: rgba(220, 230, 240, 255);
                border: 1px solid rgba(80, 100, 120, 150);
                border-radius: 3px;
            }}
            QLineEdit:focus {{
                border-color: rgba(100, 150, 200, 200);
            }}
        """)
        self.search_input.textChanged.connect(self._on_search_changed)
        search_layout.addWidget(self.search_input)
        
        # 关闭按钮（宽度与滑块一致，18px）
        close_btn = QPushButton("×")
        close_btn.setFixedSize(18, 30)
        close_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: rgba(200, 60, 60, {self.search_bg_alpha});
                color: white;
                border: none;
                border-radius: 3px;
                font-size: 18px;
                font-weight: bold;
                padding: 0px;
            }}
            QPushButton:hover {{
                background-color: rgba(220, 80, 80, {self.search_bg_alpha});
            }}
        """)
        close_btn.clicked.connect(self.refresh_status)
        search_layout.addWidget(close_btn)
        
        content_layout.addLayout(search_layout)
        
        # 创建主内容区域（横向布局：按钮区 + 滑块）
        content_hlayout = QHBoxLayout()
        content_hlayout.setContentsMargins(0, 0, 0, 0)
        content_hlayout.setSpacing(5)
        
        # 左侧：按钮网格区域 - 半透明背景
        self.grid_container = QWidget()
        self.grid_layout = QGridLayout(self.grid_container)
        self.grid_layout.setContentsMargins(self.grid_margins, self.grid_margins, self.grid_margins, self.grid_margins)
        self.grid_layout.setSpacing(self.grid_spacing)
        
        # 设置按钮区域背景透明度
        self.grid_container.setStyleSheet(f"""
            QWidget {{
                background-color: rgba(50, 60, 70, {self.button_bg_alpha});
                border-radius: 5px;
            }}
        """)
        
        # 预创建按钮槽位
        self._create_button_slots()
        
        # 给 grid_container 安装事件过滤器，支持滚轮控制滑块
        self.grid_container.installEventFilter(self)
        
        content_hlayout.addWidget(self.grid_container)
        
        # 右侧：自定义滑块（替代滚动条）- 加宽到 18px
        self.slider = QSlider(Qt.Vertical)
        self.slider.setMinimum(0)
        self.slider.setMaximum(0)  # 初始范围
        self.slider.setPageStep(1)
        self.slider.setSingleStep(1)
        self.slider.setTickPosition(QSlider.NoTicks)
        self.slider.setInvertedAppearance(True)  # 反转外观：0 在顶部，最大值在底部
        
        # 安装事件过滤器，支持鼠标滚轮
        self.slider.installEventFilter(self)
        
        self.slider.setStyleSheet(f"""
            QSlider {{
                background-color: rgba(50, 60, 70, {self.search_bg_alpha});
                border: none;
                border-radius: 5px;
                width: 18px;
            }}
            QSlider::groove:vertical {{
                background: rgba(50, 60, 70, {self.search_bg_alpha});
                width: 18px;
                border-radius: 5px;
            }}
            QSlider::handle:vertical {{
                background: rgba(100, 150, 200, {int(self.search_bg_alpha * 1.5)});
                height: 30px;
                border-radius: 5px;
                margin: 0px -1px;
            }}
            QSlider::handle:vertical:hover {{
                background: rgba(120, 170, 220, {min(255, int(self.search_bg_alpha * 1.8))});
            }}
            QSlider::add-page:vertical, QSlider::sub-page:vertical {{
                background: transparent;
            }}
        """)
        self.slider.valueChanged.connect(self._on_slider_changed)
        
        content_hlayout.addWidget(self.slider)
        
        content_layout.addLayout(content_hlayout)
        
        # 将中央内容区域添加到网格布局的中心位置（第 1 行，第 1 列）
        main_layout.addWidget(content_widget, 1, 1)
        
        # central_widget 全透明
        central_widget.setStyleSheet("""
            QWidget {
                background-color: transparent;
            }
        """)
    
    def eventFilter(self, obj, event):
        """事件过滤器 - 处理滚轮和拖拽事件"""
        # 处理滚轮事件（在按钮区域和滑块上都支持）
        if event.type() == QEvent.Wheel:
            if obj == self.grid_container or obj == self.slider or obj in self.tool_buttons:
                delta = event.angleDelta().y()
                if delta > 0:
                    self.slider.setValue(max(0, self.slider.value() - 1))
                else:
                    self.slider.setValue(min(self.slider.maximum(), self.slider.value() + 1))
                return True
        
        # 处理鼠标拖拽事件（只在四个边框标签上拖拽）
        if obj in [self.drag_top, self.drag_bottom, self.drag_left, self.drag_right]:
            if event.type() == QEvent.MouseButtonPress and event.button() == Qt.LeftButton:
                self.dragging = True
                self.offset = event.globalPos() - self.frameGeometry().topLeft()
                return True
            elif event.type() == QEvent.MouseMove and self.dragging:
                self.move(event.globalPos() - self.offset)
                return True
            elif event.type() == QEvent.MouseButtonRelease and event.button() == Qt.LeftButton:
                self.dragging = False
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
        """加载初始数据（优先使用传入的搜索文本）"""
        
        
        # 如果有初始搜索文本，直接使用；否则显示所有工具
        if self.initial_search_text:
            self.search_input.setText(self.initial_search_text)
        else:
            self.search_input.setText("")
        
        self._perform_search()

        # 设置焦点到滚动条（滑块）
        # self.search_input.setFocus()
        self.slider.setFocus()
    
    def _on_search_changed(self, text):
        """搜索框内容变化 - 使用 debounce 避免频繁搜索"""
        # 停止之前的定时器
        self.search_timer.stop()
        
        # 300ms 后执行搜索
        self.search_timer.start(300)
    
    def _perform_search(self):
        """执行搜索"""
        search_text = self.search_input.text()
        search_params = self._parse_search_text(search_text)
        cache_key = self._search_params_to_key(search_params)
        
        # print(f"\n{'='*60}")
        # print(f"[搜索调试]")
        # print(f"  输入文本: '{search_text}'")
        # print(f"  解析参数: {search_params}")
        # print(f"  缓存键: {cache_key}")
        
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
    
    def _clear_results(self):
        """清空结果显示"""
        self.all_tools.clear()
        self.total_count = 0
        self.start_index = 0
        
        # 清空所有按钮
        for btn in self.tool_buttons:
            btn.setVisible(False)
        
        # 重置滑块
        self.slider.setValue(0)
        self.slider.setMaximum(0)
    
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
        
        # print(f"[滑块调试] value={value}, start_index={self.start_index}")
        
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
        self.nodesnames_list, self.nodesclasslsit = nukendoesget.getcurnodes()
        
        print(f"[执行工具] {tool_data['tname']}")
        print(f"   工具路径: {tool_data['tpath']}")

        # 执行后隐藏窗口
        self.refresh_status()

        tool_path = os.path.join(self.toolbox_path, tool_data['tpath'])

        # 验证路径存在
        if not os.path.exists(tool_path):
            QMessageBox.information(
                None, 
                "提示",
                f"找不到工具文件:\n{tool_path}\n可能已被删除或移动"
            )
            return
        
        # 执行工具
        try:
            nuke.execute_tool(tool_path,self.nodesnames_list)
        except Exception as e:
            QMessageBox.critical(
                None,
                "执行错误",
                f"无法执行工具:\n{tool_path}\n错误: {str(e)}"
            )



        if tool_data['tpng']:
            print(f"   图标完整路径: {os.path.join(self.toolbox_path, tool_data['tpng'])}")
        else:
            print(f"   无图标")
        

        
        
    
    def closeEvent(self, event):
        self.db_query.close()
        super().closeEvent(event)
