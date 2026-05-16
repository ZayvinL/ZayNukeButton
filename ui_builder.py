"""
UI 构建器 - 负责创建和配置所有 UI 组件
"""

# from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QListWidget, 
#                                QLabel, QPushButton, QLineEdit, QSplitter, 
#                                QCheckBox, QGroupBox, QFormLayout, QTabWidget,
#                                QTextEdit, QTextBrowser, QScrollArea, QSizePolicy, QComboBox)
# from PySide6.QtCore import Qt
# from PySide6 import QtWidgets
# from PySide6.QtGui import QFont
# from PySide6.QtWidgets import QTextBrowser
# from PySide6.QtGui import QFont

from qt_imports import (QWidget, QVBoxLayout, QHBoxLayout,
                        QListWidget, QLabel, QPushButton, 
                        QLineEdit, QSplitter, QCheckBox, 
                        QGroupBox, QFormLayout, QTabWidget,
                        QTextEdit, QTextBrowser, QScrollArea, 
                        QSizePolicy, QComboBox, Qt, QtWidgets, QFont)

class UIBuilder:
    """UI 组件构建器"""
    
    def __init__(self, main_window):
        self.main_window = main_window
        self.widgets = {}
    
    def create_main_layout(self, central_widget):
        """创建主布局"""
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(8, 8, 8, 8)
        main_layout.setSpacing(8)
        return main_layout
    
    def create_top_bar(self):
        """创建顶部工具栏"""
        top_bar = QHBoxLayout()
        
        self.widgets['lbl_db'] = QLabel("")
        top_bar.addWidget(self.widgets['lbl_db'])
        
        top_bar.addStretch()
        
        self.widgets['btn_sync'] = QPushButton("同步工具")
        top_bar.addWidget(self.widgets['btn_sync'])
        
        self.widgets['btn_save'] = QPushButton("保存更改")
        self.widgets['btn_save'].setStyleSheet("""
            QPushButton {
                background: #27ae60;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 6px 15px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: #229954;
            }
        """)
        top_bar.addWidget(self.widgets['btn_save'])
        
        self.widgets['btn_refresh'] = QPushButton("刷新")
        top_bar.addWidget(self.widgets['btn_refresh'])
        
        return top_bar
    
    def create_left_panel(self):
        """创建左侧面板"""
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(6)
        
        # 搜索框
        self.widgets['search_input'] = QLineEdit()
        self.widgets['search_input'].setPlaceholderText("搜索工具名称、标签...")
        left_layout.addWidget(self.widgets['search_input'])
        
        # 过滤器
        filter_layout = QHBoxLayout()
        filter_layout.setSpacing(5)
        
        self.widgets['btn_all'] = QPushButton("全部")
        self.widgets['btn_installed'] = QPushButton("已安装")
        self.widgets['btn_favorite'] = QPushButton("已收藏")
        
        for btn in [self.widgets['btn_all'], self.widgets['btn_installed'], self.widgets['btn_favorite']]:
            btn.setCheckable(True)
            filter_layout.addWidget(btn)
        
        self.widgets['btn_all'].setChecked(True)
        left_layout.addLayout(filter_layout)
        
        # 列表头
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(5, 0, 5, 0)
        
        self.widgets['check_select_all'] = QCheckBox()
        self.widgets['check_select_all'].setFixedWidth(40)
        header_layout.addWidget(self.widgets['check_select_all'])
        
        header_layout.addWidget(self._create_fixed_label("安装", 40))
        header_layout.addWidget(self._create_fixed_label("收藏", 40))
        header_layout.addWidget(QLabel("工具名称"), 1)
        
        left_layout.addLayout(header_layout)
        
        # 工具列表
        self.widgets['tool_list'] = QListWidget()
        left_layout.addWidget(self.widgets['tool_list'], 1)
        
        # 统计栏
        self.widgets['lbl_stats'] = QLabel("")
        self.widgets['lbl_stats'].setStyleSheet("font-size: 12px; color: #aaa; padding: 5px;")
        left_layout.addWidget(self.widgets['lbl_stats'])
        
        return left_panel
    
    def create_right_panel(self, custom_suggestions=None):
        """创建右侧面板"""
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)
        
        tabs = QTabWidget()
        
        # 详情标签页
        tabs.addTab(self._create_detail_tab(), "详情")
        
        # JSON 标签页
        tabs.addTab(self._create_json_tab(), "JSON")
        
        # 帮助标签页
        tabs.addTab(self._create_help_tab(), "帮助")
        
        # 编辑标签页
        tabs.addTab(self._create_edit_tab(custom_suggestions or []), "编辑")
        
        right_layout.addWidget(tabs)
        
        return right_panel
    
    def _create_detail_tab(self):
        """创建详情标签页"""
        detail_widget = QWidget()
        detail_layout = QVBoxLayout(detail_widget)
        detail_layout.setContentsMargins(0, 0, 0, 0)
        detail_layout.setSpacing(0)
        
        detail_splitter = QSplitter(Qt.Vertical)
        
        # 工具信息区域
        info_group = QGroupBox("工具信息")
        info_layout = QFormLayout()
        info_layout.setSpacing(10)
        info_layout.setContentsMargins(10, 10, 10, 10)
        info_layout.setFieldGrowthPolicy(QFormLayout.AllNonFixedFieldsGrow)
        info_layout.setRowWrapPolicy(QFormLayout.DontWrapRows)
        info_layout.setLabelAlignment(Qt.AlignRight | Qt.AlignVCenter)
        
        self.widgets['lbl_id'] = self._create_wrappable_label()
        info_layout.addRow("UUID:", self.widgets['lbl_id'])
        
        self.widgets['lbl_name'] = self._create_simple_label()
        info_layout.addRow("名称:", self.widgets['lbl_name'])
        
        self.widgets['lbl_tag'] = self._create_simple_label()
        info_layout.addRow("标签:", self.widgets['lbl_tag'])
        
        self.widgets['lbl_matchClass'] = self._create_simple_label()
        info_layout.addRow("匹配类:", self.widgets['lbl_matchClass'])
        
        self.widgets['lbl_category'] = self._create_simple_label()
        info_layout.addRow("分类:", self.widgets['lbl_category'])
        
        self.widgets['lbl_file'] = self._create_wrappable_label()
        info_layout.addRow("主文件:", self.widgets['lbl_file'])
        
        info_group.setLayout(info_layout)
        detail_splitter.addWidget(info_group)
        
        # 图标预览区域
        icon_preview_group = QGroupBox("工具图标预览")
        icon_preview_layout = QVBoxLayout()
        icon_preview_layout.setContentsMargins(0, 0, 0, 0)
        
        self.widgets['icon_preview_label'] = QLabel()
        self.widgets['icon_preview_label'].setAlignment(Qt.AlignCenter)
        self.widgets['icon_preview_label'].setStyleSheet("background-color: #1e1e1e; border: none;")
        self.widgets['icon_preview_label'].setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.widgets['icon_preview_label'].setText("无图标")
        icon_preview_layout.addWidget(self.widgets['icon_preview_label'])
        
        icon_preview_group.setLayout(icon_preview_layout)
        detail_splitter.addWidget(icon_preview_group)
        
        detail_splitter.setStretchFactor(0, 0)
        detail_splitter.setStretchFactor(1, 1)
        
        detail_layout.addWidget(detail_splitter)
        
        return detail_widget
    
    def _create_json_tab(self):
        """创建 JSON 标签页"""
        
        
        json_widget = QWidget()
        json_layout = QVBoxLayout(json_widget)
        
        self.widgets['json_view'] = QTextBrowser()
        self.widgets['json_view'].setFont(QFont("Consolas", 10))
        json_layout.addWidget(self.widgets['json_view'])
        
        return json_widget
    
    def _create_help_tab(self):
        """创建帮助标签页"""
        help_widget = QWidget()
        help_layout = QVBoxLayout(help_widget)
        help_layout.setContentsMargins(10, 10, 10, 10)
        help_layout.setSpacing(10)
        
        # 工具栏
        help_toolbar = QHBoxLayout()
        
        self.widgets['btn_load_md'] = QPushButton("📂 加载文档")
        self.widgets['btn_load_md'].setToolTip("从文件加载 HTML 帮助文档")
        help_toolbar.addWidget(self.widgets['btn_load_md'])
        
        self.widgets['btn_save_md'] = QPushButton(" 更换文档")
        self.widgets['btn_save_md'].setToolTip("更换 HTML 帮助文档文件")
        help_toolbar.addWidget(self.widgets['btn_save_md'])
        
        self.widgets['btn_export_html'] = QPushButton("📦 导出MD")
        self.widgets['btn_export_html'].setToolTip("导出 Markdown 文档及图片依赖")
        help_toolbar.addWidget(self.widgets['btn_export_html'])
        
        help_toolbar.addStretch()
        
        self.widgets['lbl_md_status'] = QLabel("就绪")
        self.widgets['lbl_md_status'].setStyleSheet("color: #666; font-size: 12px;")
        help_toolbar.addWidget(self.widgets['lbl_md_status'])
        
        help_layout.addLayout(help_toolbar)
        
        md_splitter = QSplitter(Qt.Horizontal)
        
        self.widgets['md_preview'] = QTextBrowser()
        self.widgets['md_preview'].setOpenExternalLinks(True)
        md_splitter.addWidget(self.widgets['md_preview'])
        
        help_layout.addWidget(md_splitter, 1)
        
        return help_widget
    
    def _create_edit_tab(self, custom_suggestions):
        """创建编辑标签页"""
        edit_widget = QWidget()
        edit_layout = QVBoxLayout(edit_widget)
        edit_layout.setContentsMargins(10, 10, 10, 10)
        edit_layout.setSpacing(10)
        
        # 修改工具名称
        name_edit_group = QGroupBox("修改工具名称")
        name_edit_layout = QVBoxLayout(name_edit_group)
        
        name_input_layout = QHBoxLayout()
        self.widgets['edit_tool_name'] = QLineEdit()
        self.widgets['edit_tool_name'].setPlaceholderText("输入新的工具名称")
        name_input_layout.addWidget(self.widgets['edit_tool_name'])
        
        self.widgets['btn_rename'] = QPushButton("重命名工具")
        name_input_layout.addWidget(self.widgets['btn_rename'])
        
        name_edit_layout.addLayout(name_input_layout)
        edit_layout.addWidget(name_edit_group)
        
        # 编辑元数据
        meta_edit_group = QGroupBox("编辑元数据")
        meta_edit_layout = QVBoxLayout(meta_edit_group)
        
        # 标签编辑
        tag_layout = QHBoxLayout()
        self.widgets['edit_tag'] = QLineEdit()
        self.widgets['edit_tag'].setPlaceholderText("输入工具标签（如：合成、抠像、调色）")
        tag_layout.addWidget(self.widgets['edit_tag'])
        
        self.widgets['btn_save_tag'] = QPushButton("保存标签")
        tag_layout.addWidget(self.widgets['btn_save_tag'])
        
        meta_edit_layout.addLayout(tag_layout)
        
        # 匹配类编辑 - 带联想功能
        matchclass_layout = QHBoxLayout()
        matchclass_layout.setSpacing(5)
        
        self.widgets['edit_matchclass'] = QLineEdit()
        self.widgets['edit_matchclass'].setPlaceholderText("输入匹配类（多个用逗号分隔，如：Read,Write,Transform）")
        matchclass_layout.addWidget(self.widgets['edit_matchclass'])
        
        # 联想词条选择器
        self.widgets['matchclass_combo'] = QtWidgets.QComboBox()
        self.widgets['matchclass_combo'].addItems(sorted(custom_suggestions))
        self.widgets['matchclass_combo'].setMinimumWidth(120)
        self.widgets['matchclass_combo'].setStyleSheet("""
            QComboBox {
                padding: 5px 10px;
                background-color: #2a2a2a;
                color: #ddd;
                border: 1px solid #555;
                border-radius: 3px;
            }
            QComboBox::drop-down {
                border: none;
                width: 20px;
            }
            QComboBox QAbstractItemView {
                background-color: #2a2a2a;
                color: #ddd;
                selection-background-color: #0078d7;
            }
        """)
        matchclass_layout.addWidget(self.widgets['matchclass_combo'])
        
        self.widgets['btn_add_matchclass'] = QPushButton("+")
        self.widgets['btn_add_matchclass'].setFixedSize(30, 28)
        self.widgets['btn_add_matchclass'].setStyleSheet("""
            QPushButton {
                background-color: #0078d7;
                color: white;
                border: none;
                border-radius: 3px;
                font-weight: bold;
                font-size: 16px;
            }
            QPushButton:hover {
                background-color: #1084d9;
            }
            QPushButton:pressed {
                background-color: #006cbd;
            }
        """)
        self.widgets['btn_add_matchclass'].setToolTip("将选中的词条添加到匹配类输入框")
        matchclass_layout.addWidget(self.widgets['btn_add_matchclass'])
        
        self.widgets['btn_save_matchclass'] = QPushButton("保存匹配类")
        matchclass_layout.addWidget(self.widgets['btn_save_matchclass'])
        
        meta_edit_layout.addLayout(matchclass_layout)
        
        edit_layout.addWidget(meta_edit_group)
        
        # 添加图标
        icon_group = QGroupBox("添加工具图标")
        icon_layout = QVBoxLayout(icon_group)
        
        icon_info = QLabel('提示：将图标图片复制到剪贴板，然后点击"从剪贴板获取"按钮')
        icon_info.setWordWrap(True)
        icon_info.setStyleSheet("color: #aaa; font-size: 11px;")
        icon_layout.addWidget(icon_info)
        
        icon_btn_layout = QHBoxLayout()
        self.widgets['btn_get_clipboard'] = QPushButton("从剪贴板获取图标")
        icon_btn_layout.addWidget(self.widgets['btn_get_clipboard'])
        
        self.widgets['btn_save_icon'] = QPushButton("保存图标")
        self.widgets['btn_save_icon'].setEnabled(False)
        icon_btn_layout.addWidget(self.widgets['btn_save_icon'])
        
        icon_layout.addLayout(icon_btn_layout)
        
        self.widgets['lbl_icon_preview'] = QLabel("图标预览")
        self.widgets['lbl_icon_preview'].setAlignment(Qt.AlignCenter)
        self.widgets['lbl_icon_preview'].setMinimumSize(100, 100)
        self.widgets['lbl_icon_preview'].setStyleSheet("border: 1px solid #555; background: #2a2a2a;")
        icon_layout.addWidget(self.widgets['lbl_icon_preview'])
        
        edit_layout.addWidget(icon_group)
        edit_layout.addStretch()
        
        return edit_widget
    
    def _create_wrappable_label(self):
        """创建可换行的标签"""
        label = QLabel("")
        label.setWordWrap(True)
        label.setMinimumHeight(20)
        label.setStyleSheet("padding: 2px 0;")
        return label
    
    def _create_simple_label(self):
        """创建简单标签"""
        label = QLabel("")
        label.setMinimumHeight(20)
        label.setStyleSheet("padding: 2px 0;")
        return label
    
    def _create_fixed_label(self, text, width):
        """创建固定宽度标签"""
        label = QLabel(text)
        label.setFixedWidth(width)
        return label
    
    def get_widget(self, name):
        """获取指定名称的组件"""
        return self.widgets.get(name)
    
    def get_all_widgets(self):
        """获取所有组件"""
        return self.widgets