# c:/Users/liucx/.nuke/MyButton/window_01/search_window.py
# -*- coding: UTF-8 -*-
"""搜索型工具窗口主类"""

import os
import json
import sys
import nuke


# from PySide6.QtCore import Qt, QTimer, QEvent, Signal
# from PySide6.QtWidgets import (
#     QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
#     QGridLayout, QScrollArea, QLineEdit, QPushButton, 
#     QLabel, QMessageBox, QSlider, QCheckBox
# )
# from PySide6.QtGui import QKeySequence, QShortcut, QCursor

from qt_imports import (Qt, QTimer, QEvent, Signal,
                        QMainWindow, QWidget, QVBoxLayout,
                        QHBoxLayout, QGridLayout, QScrollArea,
                        QLineEdit, QPushButton, QLabel, QMessageBox,
                        QSlider, QCheckBox, QKeySequence, QShortcut, QCursor,
                        QApplication)

from window_01.config import _get_user_db_path, _get_toolbox_path
from window_01.db import FastDBQuery, IconCache, SmartCache
from window_01.widgets import ToolButton
import nukendoesget
# ShowMyFun = True

class SearchToolWindow(QMainWindow):
    """搜索型工具窗口"""
    
    # 定义窗口隐藏信号
    window_hidden = Signal()
    
    @staticmethod
    def _scale_factor():
        """获取当前主屏幕的 DPI 缩放系数（以 96 DPI 为基准 1.0，上限 1.2）"""
        screen = QApplication.primaryScreen()
        if screen is None:
            return 1.0
        raw = screen.logicalDotsPerInch() / 96.0
        return min(raw, 1.2)

    def __init__(self, toolbox_path, parent=None, initial_search_text=""):
        super().__init__(parent)
        self.setWindowTitle(" 工具搜索")

        self.toolbox_path = toolbox_path
        self.initial_search_text = initial_search_text
        self.is_visible = False  # 使用实例属性存储状态
        self.ShowP = True  # 控制是否在显示时重新定位到鼠标位置

        s = self._scale_factor() * 0.8

        # 布局参数配置（可调整）
        self.tools_per_row = 5  # 每行显示数量
        self.beishu = 3  # 倍数
        self.page_size = self.tools_per_row * self.beishu  # 每次加载数量（3的倍数）
        self.button_width = int(150 * s)  # 按钮固定宽度（按 DPI 缩放）
        self.button_height = int(80 * s)  # 按钮固定高度（按 DPI 缩放）
        self.grid_spacing = max(1, int(1 * s))  # 按钮间距
        self.grid_margins = max(1, int(1 * s))  # 网格边距

        # 透明度参数（0-255，0=完全透明，255=完全不透明）
        self.button_bg_alpha = 10  # 按钮区域背景透明度
        self.search_bg_alpha = 30  # 搜索框背景透明度（与按钮区域一致）

        # 虚拟列表参数
        self.visible_rows = 3  # 可见行数
        self.buffer_rows = 2  # 缓冲行数（上下各留）
        self.total_button_slots = (self.visible_rows + self.buffer_rows * 2) * self.tools_per_row  # 总按钮槽位

        # 计算窗口尺寸（固定偏移量也跟随缩放）
        pad_x = int(30 * s)
        search_h = int(70 * s)  # 搜索框区域高度
        bottom_pad = int(20 * s)

        window_width = self.tools_per_row * self.button_width + (self.tools_per_row + 1) * self.grid_spacing + pad_x
        button_area_height = self.visible_rows * self.button_height + (self.visible_rows + 1) * self.grid_spacing
        window_height = search_h + button_area_height + bottom_pad

        self.setFixedSize(window_width, window_height)
        
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
        self.nodesnames_list = []  # 由 window_panel 设置，避免点击时焦点丢失导致查询错误
        
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
    
    def set_show_at_mouse(self, show_p: bool):
        """设置是否在显示时重新定位到鼠标位置
        
        Args:
            show_p: True=每次显示时定位到鼠标位置，False=保持上次位置
        """
        self.ShowP = show_p

    def _move_near_cursor(self, cursor_pos):
        """将窗口移动到鼠标附近，同时确保窗口不超出屏幕边界"""
        win_w = self.width()
        win_h = self.height()

        # 默认偏移：窗口中心偏左上，让鼠标大致在窗口右下方
        offset_x = -150
        offset_y = -100

        preferred_x = cursor_pos.x() + offset_x
        preferred_y = cursor_pos.y() + offset_y

        # 获取鼠标所在屏幕的可用区域
        screen = QApplication.screenAt(cursor_pos)
        if screen is None:
            screen = QApplication.primaryScreen()
        geom = screen.availableGeometry()

        # 在屏幕范围内 clamp
        x = max(geom.left(), min(preferred_x, geom.right() - win_w))
        y = max(geom.top(), min(preferred_y, geom.bottom() - win_h))

        self.move(x, y)

    def _apply_initial_search(self):
        """应用初始搜索文本（已合并到 _load_initial_data，此方法保留但不执行）"""
        pass
    
    def _setup_shortcuts(self):
        """设置快捷键"""
        esc_shortcut = QShortcut(QKeySequence("Esc"), self)
        esc_shortcut2 = QShortcut(QKeySequence("ALT+W"), self)
        esc_shortcut.activated.connect(self.refresh_status)
        esc_shortcut2.activated.connect(self.refresh_status)
    
    def showEvent(self, event):
        """窗口显示时设置状态"""
        self.is_visible = True
        print(f"窗口显示，is_visible={self.is_visible}")
        
        # 如果 ShowP 为 True，重新定位到鼠标位置
        if self.ShowP:
            cursor_pos = QCursor.pos()
            # 将窗口移动到鼠标附近，但确保窗口在屏幕范围内
            self._move_near_cursor(cursor_pos)
        
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
        
        # 创建四个拖拽标签（低调深灰色）
        drag_alpha = 128
        dragcolor1 = 20
        dragcolor2 = 23
        dragcolor3 = 20
        
        # 上边框
        self.drag_top = QLabel()
        self.drag_top.setMinimumHeight(2)
        self.drag_top.setStyleSheet(f"""
            QLabel {{
                background-color: rgba({dragcolor1}, {dragcolor2}, {dragcolor3}, {drag_alpha});
                border-radius: 30px;
            }}
        """)
        self.drag_top.installEventFilter(self)
        
        # 下边框
        self.drag_bottom = QLabel()
        self.drag_bottom.setMinimumHeight(2)
        self.drag_bottom.setStyleSheet(f"""
            QLabel {{
                background-color: rgba({dragcolor1}, {dragcolor2}, {dragcolor3}, {drag_alpha});
                border-radius: 5px;
            }}
        """)
        self.drag_bottom.installEventFilter(self)
        
        # 左边框
        self.drag_left = QLabel()
        self.drag_left.setMinimumWidth(5)
        self.drag_left.setStyleSheet(f"""
            QLabel {{
                background-color: rgba({dragcolor1}, {dragcolor2}, {dragcolor3}, {drag_alpha});
                border-radius: 5px;
            }}
        """)
        self.drag_left.installEventFilter(self)
        
        # 右边框
        self.drag_right = QLabel()
        self.drag_right.setMinimumWidth(5)
        self.drag_right.setStyleSheet(f"""
            QLabel {{
                background-color: rgba({dragcolor1}, {dragcolor2}, {dragcolor3}, {drag_alpha});
                border-radius: 5px;
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
        
        # 设置内容区域圆角
        content_widget.setStyleSheet("""
            QWidget {
                background-color: transparent;
                border-radius: 30px;
            }
        """)
        
        # 搜索框 + 关闭按钮（横向布局）
        search_layout = QHBoxLayout()
        search_layout.setSpacing(5)
        
        # 已安装过滤复选框
        self.check_installed_only = QCheckBox("仅已安装")
        self.check_installed_only.setChecked(True)
        self.check_installed_only.setStyleSheet("""
            QCheckBox {
                color: rgba(255, 230, 200, 220);
                font-size: 11px;
                spacing: 5px;
            }
            QCheckBox::indicator {
                width: 16px;
                height: 16px;
                border: 2px solid rgba(255, 140, 50, 180);
                border-radius: 3px;
                background-color: rgba(30, 30, 30, 150);
            }
            QCheckBox::indicator:checked {
                background-color: rgba(255, 140, 50, 200);
                border-color: rgba(255, 160, 80, 220);
            }
            QCheckBox::indicator:hover {
                border-color: rgba(255, 180, 100, 220);
            }
        """)
        self.check_installed_only.stateChanged.connect(self._on_installed_filter_changed)
        search_layout.addWidget(self.check_installed_only)

        # 显示图标复选框
        self.check_show_icons = QCheckBox("图标")
        self.check_show_icons.setChecked(True)
        self.check_show_icons.setStyleSheet("""
            QCheckBox {
                color: rgba(255, 230, 200, 220);
                font-size: 11px;
                spacing: 5px;
            }
            QCheckBox::indicator {
                width: 16px;
                height: 16px;
                border: 2px solid rgba(255, 140, 50, 180);
                border-radius: 3px;
                background-color: rgba(30, 30, 30, 150);
            }
            QCheckBox::indicator:checked {
                background-color: rgba(255, 140, 50, 200);
                border-color: rgba(255, 160, 80, 220);
            }
            QCheckBox::indicator:hover {
                border-color: rgba(255, 180, 100, 220);
            }
        """)
        self.check_show_icons.stateChanged.connect(self._on_show_icons_changed)
        search_layout.addWidget(self.check_show_icons)
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("双击或Alt+E输入 | C=:类 L=:标签 P=:路径 N=:名称")
        self.search_input.setStyleSheet(f"""
            QLineEdit {{
                padding: 8px 12px;
                font-size: 12px;
                background-color: rgba(30, 30, 30, {self.search_bg_alpha});
                color: rgba(255, 230, 200, 255);
                border: 1px solid rgba(255, 140, 50, 100);
                border-radius: 3px;
            }}
            QLineEdit:focus {{
                border-color: rgba(255, 160, 80, 220);
                background-color: rgba(35, 35, 35, {self.search_bg_alpha});
            }}
            QLineEdit::placeholder {{
                color: rgba(180, 170, 160, 150);
            }}
        """)
        self.search_input.textChanged.connect(self._on_search_changed)
        search_layout.addWidget(self.search_input)

        # 默认只读：防止打开面板后快捷键误入搜索框，Tab 或双击激活
        self.search_input.setReadOnly(True)
        self.search_input.installEventFilter(self)
        self._search_active = False
        
        
        
        # 刷新按钮（清空缓存）
        refresh_btn = QPushButton("⟳")
        refresh_btn.setFixedSize(24, 30)
        refresh_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: rgba(255, 140, 50, {self.search_bg_alpha});
                color: rgba(255, 255, 255, 255);
                border: none;
                border-radius: 3px;
                font-size: 16px;
                font-weight: bold;
                padding: 0px;
            }}
            QPushButton:hover {{
                background-color: rgba(255, 160, 80, {min(255, int(self.search_bg_alpha * 1.5))});
            }}
        """)
        refresh_btn.clicked.connect(self._refresh_cache)
        refresh_btn.setToolTip("清空缓存并重新搜索")
        search_layout.addWidget(refresh_btn)
        
        # 关闭按钮
        close_btn = QPushButton("×")
        close_btn.setFixedSize(18, 30)
        close_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: rgba(255, 80, 50, {self.search_bg_alpha});
                color: rgba(255, 255, 255, 255);
                border: none;
                border-radius: 3px;
                font-size: 18px;
                font-weight: bold;
                padding: 0px;
            }}
            QPushButton:hover {{
                background-color: rgba(255, 100, 70, {self.search_bg_alpha});
            }}
        """)
        close_btn.clicked.connect(self.refresh_status)
        search_layout.addWidget(close_btn)
        
        content_layout.addLayout(search_layout)
        
        # 创建主内容区域（横向布局：按钮区 + 滑块）
        content_hlayout = QHBoxLayout()
        content_hlayout.setContentsMargins(0, 0, 0, 0)
        content_hlayout.setSpacing(5)
        
        # 左侧：按钮网格区域
        self.grid_container = QWidget()
        self.grid_layout = QGridLayout(self.grid_container)
        self.grid_layout.setContentsMargins(self.grid_margins, self.grid_margins, self.grid_margins, self.grid_margins)
        self.grid_layout.setSpacing(self.grid_spacing)
        
        # 设置按钮区域背景
        self.grid_container.setStyleSheet(f"""
            QWidget {{
                background-color: rgba(30, 30, 30, {self.button_bg_alpha});
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
                background-color: rgba(30, 30, 30, {self.search_bg_alpha});
                border: none;
                border-radius: 5px;
                width: 18px;
            }}
            QSlider::groove:vertical {{
                background: rgba(30, 30, 30, {self.search_bg_alpha});
                width: 18px;
                border-radius: 5px;
            }}
            QSlider::handle:vertical {{
                background: rgba(255, 140, 50, {min(255, int(self.search_bg_alpha * 2.5))});
                height: 30px;
                border-radius: 5px;
                margin: 0px -1px;
            }}
            QSlider::handle:vertical:hover {{
                background: rgba(255, 160, 80, {min(255, int(self.search_bg_alpha * 3))});
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
                border-radius: 5px;
            }
        """)
    
    def eventFilter(self, obj, event):
        """事件过滤器 - 处理滚轮、拖拽、搜索框激活"""
        # Alt+E 激活搜索框
        if event.type() == QEvent.KeyPress and \
           event.key() == Qt.Key_E and \
           event.modifiers() == Qt.AltModifier:
            if not self._search_active:
                self._activate_search_input()
                return True

        # 搜索框事件（search_input 尚未创建时跳过）
        if hasattr(self, 'search_input') and obj == self.search_input:
            if event.type() == QEvent.MouseButtonDblClick:
                if not self._search_active:
                    self._activate_search_input()
                    return True
            if event.type() == QEvent.FocusOut:
                self._deactivate_search_input()

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
    
    def _activate_search_input(self):
        """激活搜索框：允许输入"""
        self.search_input.setReadOnly(False)
        self.search_input.setFocus()
        self.search_input.selectAll()
        self._search_active = True
        # 激活后边框变亮
        self.search_input.setStyleSheet(self.search_input.styleSheet().replace(
            'border: 1px solid rgba(255, 140, 50, 100);',
            'border: 1px solid rgba(255, 160, 80, 220);'))

    def _deactivate_search_input(self):
        """停用搜索框：恢复只读"""
        self.search_input.setReadOnly(True)
        self.search_input.clearFocus()
        self._search_active = False
        # 停用后边框变暗
        self.search_input.setStyleSheet(self.search_input.styleSheet().replace(
            'border: 1px solid rgba(255, 160, 80, 220);',
            'border: 1px solid rgba(255, 140, 50, 100);'))

    def _on_search_changed(self, text):
        """搜索框内容变化 - 使用 debounce 避免频繁搜索"""
        # 停止之前的定时器
        self.search_timer.stop()

        # 300ms 后执行搜索
        self.search_timer.start(300)
    
    def _on_installed_filter_changed(self, state):
        """已安装过滤复选框状态改变"""
        # 重新执行搜索
        self._perform_search()

    def _on_show_icons_changed(self, state):
        """显示图标复选框状态改变"""
        self._update_visible_buttons()
    
    def _refresh_cache(self):
        """清空缓存并重新搜索"""
        # 清空智能缓存
        self.smart_cache.clear()
        print(f"[缓存刷新] 已清空 {len(self.smart_cache._cache)} 个缓存项")
        
        # 重新执行当前搜索
        self._perform_search()
    
    def _perform_search(self):
        """执行搜索"""
        search_text = self.search_input.text()
        search_params = self._parse_search_text(search_text)
        cache_key = self._search_params_to_key(search_params)
        
        # 获取是否只搜索已安装工具
        is_installed_only = self.check_installed_only.isChecked()
        
        # 更新缓存键（包含安装过滤状态）
        cache_key = json.dumps({
            'search_params': search_params,
            'is_installed_only': is_installed_only
        }, sort_keys=True)
        
        # print(f"\n{'='*60}")
        # print(f"[搜索调试]")
        # print(f"  输入文本: '{search_text}'")
        # print(f"  解析参数: {search_params}")
        # print(f"  仅已安装: {is_installed_only}")
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
        self.total_count = self.db_query.get_total_count(search_params, is_installed_only)
        print(f"  [数据库查询] 总数: {self.total_count} (仅已安装: {is_installed_only})")
        
        # 查询初始工具（所有工具）
        self.all_tools = self.db_query.search_tools(
            search_params,
            is_installed_only=is_installed_only,
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
                show_icons = self.check_show_icons.isChecked()
                btn.update_content(tool_copy, show_icon_mode=show_icons)
                btn.setVisible(True)
            else:
                btn.setVisible(False)
                btn.tool_data = None  # 清空工具数据
    
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
        
        # 设置 grid_layout 的对齐方式为左上角对齐，不居中
        self.grid_layout.setAlignment(Qt.AlignTop | Qt.AlignLeft)
    
    def _update_stats(self):
        """更新统计信息"""
        loaded_count = min(self.current_offset + self.page_size, self.total_count)
        # self.stats_label.setText(f"共 {self.total_count} 个工具，已加载 {loaded_count} 个")
    
    def _on_tool_clicked(self, btn):
        """工具按钮点击"""
        tool_data = btn.tool_data
        # 优先使用 show_search_window 时保存的选中节点信息（此时 DAG 上下文正确），
        # 避免因点击搜索窗口导致焦点离开 Nuke DAG 后 selectedNodes() 丢失 Group 上下文
        if getattr(self, 'nodesnames_list', None):
            self.nodesclasslsit = nukendoesget.getcurnodes()[1]
        else:
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
            # print("ccc")
            # print(self.nodesnames_list)
            # print("ccc")
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