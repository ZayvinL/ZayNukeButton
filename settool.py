import sqlite3
import json
import os
import sys

# 添加本地 libs 到 Python 路径
libs_path = os.path.join(os.path.dirname(__file__), 'libs')
if os.path.exists(libs_path):
    sys.path.insert(0, libs_path)

from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                               QHBoxLayout, QListWidget, QListWidgetItem, 
                               QTextBrowser, QLabel, QPushButton, QLineEdit, 
                               QSplitter, QMessageBox, QCheckBox,
                               QGroupBox, QFormLayout, QTabWidget,
                               QTextEdit, QFileDialog, QScrollArea, QSizePolicy)
from PySide6.QtCore import Qt, QUrl, QSize
from PySide6.QtGui import QFont, QClipboard, QImage, QPixmap
from PySide6 import QtWidgets

import paths_setup as psp
import sqlite_file_setup as sfs
import toolsfile_json as tfj

# 导入拆分后的模块
from widgets import ToolItemWidget
from help_editor import HelpEditorMixin

# 尝试导入 markdown
try:
    import markdown
    HAS_MARKDOWN = True
    print("成功加载 markdown 库")
except ImportError:
    HAS_MARKDOWN = False
    print("警告: 未安装 markdown 库，Markdown 预览功能受限")
    print("运行以下命令安装: pip install markdown --target=./libs")


class ToolManagerApp(QMainWindow, HelpEditorMixin):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Nuke Tools Manager")
        self.setGeometry(100, 100, 1400, 900)
        
        self.current_tool_data = None
        self.all_tools = []
        self.db_path = None
        self.pending_changes = []
        
        self.init_ui()
        self.ensure_database_exists()
        self.load_tools_from_db()

    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(8, 8, 8, 8)
        main_layout.setSpacing(8)
        
        # 顶部栏
        top_bar = QHBoxLayout()
        
        self.lbl_db = QLabel("")
        top_bar.addWidget(self.lbl_db)
        
        top_bar.addStretch()
        
        self.btn_sync = QPushButton("同步工具")
        self.btn_sync.clicked.connect(self.sync_tools)
        top_bar.addWidget(self.btn_sync)
        
        self.btn_save = QPushButton("保存更改")
        self.btn_save.clicked.connect(self.save_changes)
        self.btn_save.setStyleSheet("""
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
        top_bar.addWidget(self.btn_save)
        
        self.btn_refresh = QPushButton("刷新")
        self.btn_refresh.clicked.connect(self.refresh_tools_list)
        top_bar.addWidget(self.btn_refresh)
        
        main_layout.addLayout(top_bar)
        
        # 主分割器
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # 左侧面板
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(6)
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("搜索工具名称、标签...")
        self.search_input.textChanged.connect(self.filter_list)
        left_layout.addWidget(self.search_input)
        
        filter_layout = QHBoxLayout()
        filter_layout.setSpacing(5)
        
        self.btn_all = QPushButton("全部")
        self.btn_installed = QPushButton("已安装")
        self.btn_favorite = QPushButton("已收藏")
        
        for btn in [self.btn_all, self.btn_installed, self.btn_favorite]:
            btn.setCheckable(True)
            filter_layout.addWidget(btn)
        
        self.btn_all.setChecked(True)
        self.btn_all.clicked.connect(lambda: self.set_filter("all"))
        self.btn_installed.clicked.connect(lambda: self.set_filter("installed"))
        self.btn_favorite.clicked.connect(lambda: self.set_filter("favorite"))
        
        left_layout.addLayout(filter_layout)
        
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(5, 0, 5, 0)
        
        # 全选安装复选框
        self.check_select_all = QCheckBox()
        self.check_select_all.setFixedWidth(40)
        self.check_select_all.stateChanged.connect(self.on_select_all_changed)
        header_layout.addWidget(self.check_select_all)
        
        lbl_install = QLabel("安装")
        lbl_install.setFixedWidth(40)
        header_layout.addWidget(lbl_install)
        
        lbl_favorite = QLabel("收藏")
        lbl_favorite.setFixedWidth(40)
        header_layout.addWidget(lbl_favorite)
        
        lbl_name = QLabel("工具名称")
        header_layout.addWidget(lbl_name, 1)
        
        left_layout.addLayout(header_layout)
        
        self.tool_list = QListWidget()
        self.tool_list.currentItemChanged.connect(self.on_selection_changed)
        left_layout.addWidget(self.tool_list, 1)
        
        # 实时统计栏
        self.lbl_stats = QLabel("")
        self.lbl_stats.setStyleSheet("font-size: 12px; color: #aaa; padding: 5px;")
        left_layout.addWidget(self.lbl_stats)
        
        # 右侧面板
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)
        
        tabs = QTabWidget()
        
        # 详情标签页
        detail_widget = QWidget()
        detail_layout = QVBoxLayout(detail_widget)
        detail_layout.setContentsMargins(0, 0, 0, 0)
        detail_layout.setSpacing(0)
        
        # 使用 QSplitter 实现可调节的分区
        detail_splitter = QSplitter(Qt.Vertical)
        
        # 工具信息区域
        info_group = QGroupBox("工具信息")
        info_layout = QFormLayout()
        info_layout.setSpacing(8)
        
        self.lbl_id = QLabel("")
        self.lbl_id.setWordWrap(True)
        info_layout.addRow("UUID:", self.lbl_id)
        
        self.lbl_name = QLabel("")
        info_layout.addRow("名称:", self.lbl_name)
        
        self.lbl_tag = QLabel("")
        info_layout.addRow("标签:", self.lbl_tag)
        
        self.lbl_matchClass = QLabel("")
        info_layout.addRow("匹配类:", self.lbl_matchClass)
        
        self.lbl_category = QLabel("")
        info_layout.addRow("分类:", self.lbl_category)
        
        self.lbl_file = QLabel("")
        self.lbl_file.setWordWrap(True)
        info_layout.addRow("主文件:", self.lbl_file)
        
        info_group.setLayout(info_layout)
        detail_splitter.addWidget(info_group)
        
        # 图标预览区域 - 占满剩余空间
        icon_preview_group = QGroupBox("工具图标预览")
        icon_preview_layout = QVBoxLayout()
        icon_preview_layout.setContentsMargins(0, 0, 0, 0)
        
        self.icon_preview_label = QLabel()
        self.icon_preview_label.setAlignment(Qt.AlignCenter)
        self.icon_preview_label.setStyleSheet("""
            background-color: #1e1e1e;
            border: none;
        """)
        self.icon_preview_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.icon_preview_label.setText("无图标")
        icon_preview_layout.addWidget(self.icon_preview_label)
        
        icon_preview_group.setLayout(icon_preview_layout)
        detail_splitter.addWidget(icon_preview_group)
        
        # 设置图标预览区域为拉伸因子
        detail_splitter.setStretchFactor(0, 0)  # 工具信息不拉伸
        detail_splitter.setStretchFactor(1, 1)  # 图标预览自动拉伸
        
        detail_layout.addWidget(detail_splitter)
        
        tabs.addTab(detail_widget, "详情")
        
        # JSON 标签页
        json_widget = QWidget()
        json_layout = QVBoxLayout(json_widget)
        self.json_view = QTextBrowser()
        self.json_view.setFont(QFont("Consolas", 10))
        json_layout.addWidget(self.json_view)
        tabs.addTab(json_widget, "JSON")
        
        # 帮助标签页
        help_widget = QWidget()
        help_layout = QVBoxLayout(help_widget)
        help_layout.setContentsMargins(10, 10, 10, 10)
        help_layout.setSpacing(10)
        
        # 顶部工具栏
        help_toolbar = QHBoxLayout()
        
        self.btn_load_md = QPushButton("📂 加载文档")
        self.btn_load_md.clicked.connect(self.load_help_md)
        self.btn_load_md.setToolTip("从文件加载 HTML 帮助文档")
        help_toolbar.addWidget(self.btn_load_md)
        
        self.btn_save_md = QPushButton("💾 更换文档")
        self.btn_save_md.clicked.connect(self.save_help_md)
        self.btn_save_md.setToolTip("更换 HTML 帮助文档文件")
        help_toolbar.addWidget(self.btn_save_md)
        
        self.btn_export_html = QPushButton("🌐 导出HTML")
        self.btn_export_html.clicked.connect(self.export_md_to_html)
        self.btn_export_html.setToolTip("将预览内容导出为 HTML 文件")
        help_toolbar.addWidget(self.btn_export_html)
        
        help_toolbar.addStretch()
        
        self.lbl_md_status = QLabel("就绪")
        self.lbl_md_status.setStyleSheet("color: #666; font-size: 12px;")
        help_toolbar.addWidget(self.lbl_md_status)
        
        help_layout.addLayout(help_toolbar)
        
        md_splitter = QSplitter(Qt.Horizontal)
        
        # Markdown 预览器
        self.md_preview = QTextBrowser()
        self.md_preview.setOpenExternalLinks(True)
        md_splitter.addWidget(self.md_preview)
        
        help_layout.addWidget(md_splitter, 1)
        
        tabs.addTab(help_widget, "帮助")
        
        # 编辑标签页（新增）
        edit_widget = QWidget()
        edit_layout = QVBoxLayout(edit_widget)
        edit_layout.setContentsMargins(10, 10, 10, 10)
        edit_layout.setSpacing(10)
        
        # 编辑工具名称
        name_edit_group = QGroupBox("修改工具名称")
        name_edit_layout = QVBoxLayout(name_edit_group)
        
        name_input_layout = QHBoxLayout()
        self.edit_tool_name = QLineEdit()
        self.edit_tool_name.setPlaceholderText("输入新的工具名称")
        name_input_layout.addWidget(self.edit_tool_name)
        
        self.btn_rename = QPushButton("重命名工具")
        self.btn_rename.clicked.connect(self.rename_tool)
        name_input_layout.addWidget(self.btn_rename)
        
        name_edit_layout.addLayout(name_input_layout)
        edit_layout.addWidget(name_edit_group)
        
        # 编辑标签和匹配类
        meta_edit_group = QGroupBox("编辑元数据")
        meta_edit_layout = QVBoxLayout(meta_edit_group)
        
        # 标签编辑
        tag_layout = QHBoxLayout()
        self.edit_tag = QLineEdit()
        self.edit_tag.setPlaceholderText("输入工具标签（如：合成、抠像、调色）")
        tag_layout.addWidget(self.edit_tag)
        
        self.btn_save_tag = QPushButton("保存标签")
        self.btn_save_tag.clicked.connect(self.save_tag)
        tag_layout.addWidget(self.btn_save_tag)
        
        meta_edit_layout.addLayout(tag_layout)
        
        # 匹配类编辑
        matchclass_layout = QHBoxLayout()
        self.edit_matchclass = QLineEdit()
        self.edit_matchclass.setPlaceholderText("输入匹配类（多个用逗号分隔，如：Read,Write,Transform）")
        matchclass_layout.addWidget(self.edit_matchclass)
        
        self.btn_save_matchclass = QPushButton("保存匹配类")
        self.btn_save_matchclass.clicked.connect(self.save_matchclass)
        matchclass_layout.addWidget(self.btn_save_matchclass)
        
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
        self.btn_get_clipboard = QPushButton("从剪贴板获取图标")
        self.btn_get_clipboard.clicked.connect(self.get_icon_from_clipboard)
        icon_btn_layout.addWidget(self.btn_get_clipboard)
        
        self.btn_save_icon = QPushButton("保存图标")
        self.btn_save_icon.clicked.connect(self.save_icon)
        self.btn_save_icon.setEnabled(False)
        icon_btn_layout.addWidget(self.btn_save_icon)
        
        icon_layout.addLayout(icon_btn_layout)
        
        self.lbl_icon_preview = QLabel("图标预览")
        self.lbl_icon_preview.setAlignment(Qt.AlignCenter)
        self.lbl_icon_preview.setMinimumSize(100, 100)
        self.lbl_icon_preview.setStyleSheet("border: 1px solid #555; background: #2a2a2a;")
        icon_layout.addWidget(self.lbl_icon_preview)
        
        edit_layout.addWidget(icon_group)
        
        edit_layout.addStretch()
        
        tabs.addTab(edit_widget, "编辑")
        
        right_layout.addWidget(tabs)
        
        splitter.addWidget(left_panel)
        splitter.addWidget(right_panel)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 2)
        
        main_layout.addWidget(splitter)
        
        self.update_db_info()
        self.update_stats()
        
        # 剪贴板图片缓存
        self.clipboard_image = None

    def ensure_database_exists(self):
        """确保数据库存在，如果不存在则自动创建"""
        if not os.path.exists(self.db_path):
            print(f"数据库不存在，正在创建: {self.db_path}")
            sfs.sync_tools_to_database(self.db_path)
            QMessageBox.information(self, "提示", "已自动创建数据库并同步工具")

    def update_db_info(self):
        self.db_path = sfs.get_user_db_path()
        username = sfs.get_current_user()
        db_uuid = sfs.get_current_user_db_uuid()
        self.lbl_db.setText(f"用户: {username} | 数据库: {db_uuid}")
    
    def load_icon_preview(self):
        """加载工具图标到大预览区域"""
        icon_file = self.current_tool_data.get('icon_file')
        
        if not icon_file:
            self.icon_preview_label.setText("无图标")
            self.icon_preview_label.setPixmap(QPixmap())
            return
        
        try:
            tools_root = psp.tools_path_get()
            icon_full_path = os.path.join(tools_root, icon_file.replace('/', os.sep))
            
            if not os.path.exists(icon_full_path):
                self.icon_preview_label.setText("图标文件不存在")
                self.icon_preview_label.setPixmap(QPixmap())
                return
            
            # 加载图片
            pixmap = QPixmap(icon_full_path)
            
            if pixmap.isNull():
                self.icon_preview_label.setText("无法加载图标")
                self.icon_preview_label.setPixmap(QPixmap())
                return
            
            # 缩放图片以适应预览区域（保持宽高比）
            scaled_pixmap = pixmap.scaled(
                self.icon_preview_label.size(),
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )
            
            self.icon_preview_label.setPixmap(scaled_pixmap)
            self.icon_preview_label.setText("")
            
        except Exception as e:
            self.icon_preview_label.setText(f"加载失败: {str(e)}")
            self.icon_preview_label.setPixmap(QPixmap())
            print(f"加载图标预览失败: {e}")

    def set_filter(self, filter_type):
        if filter_type == "all":
            self.btn_all.setChecked(True)
            self.btn_installed.setChecked(False)
            self.btn_favorite.setChecked(False)
        elif filter_type == "installed":
            self.btn_all.setChecked(False)
            self.btn_installed.setChecked(True)
            self.btn_favorite.setChecked(False)
        elif filter_type == "favorite":
            self.btn_all.setChecked(False)
            self.btn_installed.setChecked(False)
            self.btn_favorite.setChecked(True)
        
        self.filter_list()

    def load_tools_from_db(self):
        try:
            self.all_tools = sfs.get_all_tools_from_db(self.db_path)
            self.refresh_list()
        except Exception as e:
            QMessageBox.critical(self, "错误", f"加载失败:\n{str(e)}")

    def sync_tools(self):
        reply = QMessageBox.question(self, "同步", "重新扫描并同步所有工具？", 
                                    QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            try:
                count = sfs.sync_tools_to_database(self.db_path)
                QMessageBox.information(self, "成功", f"已同步 {count} 个工具")
                self.load_tools_from_db()
            except Exception as e:
                QMessageBox.critical(self, "错误", f"同步失败:\n{str(e)}")

    def save_changes(self):
        """保存所有更改到数据库"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            saved_count = 0
            installed_count = 0
            favorite_count = 0
            
            print("开始保存工具状态到数据库...")
            
            for i in range(self.tool_list.count()):
                item = self.tool_list.item(i)
                widget = self.tool_list.itemWidget(item)
                
                if widget is None:
                    continue
                
                tool_data = widget.tool_data
                tool_id = tool_data.get('id')
                if not tool_id:
                    continue
                
                is_installed = 1 if widget.check_install.isChecked() else 0
                is_favorite = 1 if widget.check_favorite.isChecked() else 0
                
                tool_data['is_installed'] = is_installed
                tool_data['is_favorite'] = is_favorite
                
                usage_count = tool_data.get('usage_count', 0)
                last_used = tool_data.get('last_used', None)
                
                if is_installed:
                    installed_count += 1
                if is_favorite:
                    favorite_count += 1
                
                if saved_count < 3:
                    print(f"  保存工具: {tool_data.get('name')} - 安装:{is_installed} 收藏:{is_favorite}")
                
                cursor.execute('''
                    INSERT OR REPLACE INTO user_tools 
                    (tool_id, is_installed, is_favorite, usage_count, last_used) 
                    VALUES (?, ?, ?, ?, ?)
                ''', (tool_id, is_installed, is_favorite, usage_count, last_used))
                
                saved_count += 1
            
            conn.commit()
            conn.close()
            
            print(f"保存完成：总计 {saved_count} 个工具，已安装 {installed_count} 个，已收藏 {favorite_count} 个")
            
            self.pending_changes = []
            self.update_stats()
            
            QMessageBox.information(self, "成功", f"已保存 {saved_count} 个工具的状态\n已安装: {installed_count}\n已收藏: {favorite_count}")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"保存失败:\n{str(e)}")

    def refresh_tools_list(self):
        self.load_tools_from_db()

    def refresh_list(self):
        """刷新工具列表"""
        self.tool_list.clear()
        
        for i in range(self.tool_list.count()):
            item = self.tool_list.item(i)
            widget = self.tool_list.itemWidget(item)
            if widget:
                widget.deleteLater()
        
        self.tool_list.clear()
        
        print(f"加载 {len(self.all_tools)} 个工具到列表")
        for i, tool in enumerate(self.all_tools):
            if i < 3:
                print(f"  工具 {i}: {tool.get('name')} - 安装:{tool.get('is_installed')} 收藏:{tool.get('is_favorite')}")
            
            widget = ToolItemWidget(tool)
            widget.stateChanged.connect(self.on_tool_state_changed)
            
            item = QListWidgetItem()
            item.setSizeHint(widget.sizeHint())
            item.setData(Qt.ItemDataRole.UserRole, tool)
            
            self.tool_list.addItem(item)
            self.tool_list.setItemWidget(item, widget)
        
        self.update_stats()

    def on_tool_state_changed(self):
        """状态改变时实时更新统计"""
        sender = self.sender()
        if isinstance(sender, ToolItemWidget):
            self.update_stats()
    
    def on_select_all_changed(self, state):
        """全选复选框状态改变时，同步到所有工具"""
        is_checked = self.check_select_all.isChecked()
        
        print(f"全选状态变为: {'勾选' if is_checked else '取消'}")
        
        for i in range(self.tool_list.count()):
            item = self.tool_list.item(i)
            widget = self.tool_list.itemWidget(item)
            
            if widget is None:
                continue
            
            widget.check_install.blockSignals(True)
            widget.check_install.setChecked(is_checked)
            widget.check_install.blockSignals(False)
            
            widget.tool_data['is_installed'] = 1 if is_checked else 0
        
        self.update_stats()

    def update_stats(self):
        """实时更新安装和收藏统计"""
        total = len(self.all_tools)
        installed = sum(1 for t in self.all_tools if t.get('is_installed', 0))
        favorite = sum(1 for t in self.all_tools if t.get('is_favorite', 0))
        showing = 0
        
        for i in range(self.tool_list.count()):
            item = self.tool_list.item(i)
            if not item.isHidden():
                showing += 1
        
        self.lbl_stats.setText(
            f"总计: {total}  |  已安装: {installed}  |  已收藏: {favorite}  |  "
            f"当前显示: {showing}"
        )

    def filter_list(self):
        search_text = self.search_input.text().lower()
        
        if self.btn_installed.isChecked():
            filter_type = "installed"
        elif self.btn_favorite.isChecked():
            filter_type = "favorite"
        else:
            filter_type = "all"
        
        for i in range(self.tool_list.count()):
            item = self.tool_list.item(i)
            tool = item.data(Qt.ItemDataRole.UserRole)
            
            match_text = (
                search_text in tool.get('name', '').lower() or
                search_text in tool.get('tag', '').lower()
            )
            
            if filter_type == "installed":
                match_filter = tool.get('is_installed', 0) == 1
            elif filter_type == "favorite":
                match_filter = tool.get('is_favorite', 0) == 1
            else:
                match_filter = True
            
            item.setHidden(not (match_text and match_filter))
        
        self.update_stats()

    def on_selection_changed(self, current, previous):
        if not current:
            return
        
        self.current_tool_data = current.data(Qt.ItemDataRole.UserRole)
        name = self.current_tool_data.get('name', '')
        
        self.lbl_id.setText(self.current_tool_data.get('id', 'N/A'))
        self.lbl_name.setText(self.current_tool_data.get('name', 'N/A'))
        self.lbl_tag.setText(self.current_tool_data.get('tag', '无') or '无')
        
        matchClass = self.current_tool_data.get('matchClass', '[]')
        try:
            if isinstance(matchClass, str):
                matchClass = json.loads(matchClass)
            self.lbl_matchClass.setText(', '.join(matchClass) if matchClass else '无')
        except:
            self.lbl_matchClass.setText(str(matchClass))
        
        self.lbl_category.setText(self.current_tool_data.get('category', 'N/A'))
        
        main_file = self.current_tool_data.get('main_file', 'N/A')
        tools_root = psp.tools_path_get()
        full_path = os.path.join(tools_root, main_file.replace('/', os.sep))
        self.lbl_file.setText(full_path)
        
        # 加载图标预览
        self.load_icon_preview()
        
        self.json_view.setPlainText(json.dumps(self.current_tool_data, indent=2, ensure_ascii=False))
        
        # 更新编辑框的值
        self.edit_tool_name.clear()
        self.edit_tag.setText(self.current_tool_data.get('tag', ''))
        
        matchClass = self.current_tool_data.get('matchClass', [])
        if isinstance(matchClass, str):
            try:
                matchClass = json.loads(matchClass)
            except:
                matchClass = []
        self.edit_matchclass.setText(', '.join(matchClass) if matchClass else '')
        
        # 加载 HTML 帮助文档
        help_file = self.current_tool_data.get('help_file')
        if help_file:
            help_full = os.path.join(tools_root, help_file.replace('/', os.sep))
            if os.path.exists(help_full):
                try:
                    from PySide6.QtCore import QUrl
                    self.md_preview.setSource(QUrl.fromLocalFile(help_full))
                    self.lbl_md_status.setText(f"已加载: {os.path.basename(help_full)}")
                except Exception as e:
                    print(f"加载帮助文档失败: {e}")
                    self.md_preview.setHtml("<h3>帮助文档加载失败</h3>")
            else:
                self.md_preview.setHtml("<h3>未找到帮助文档</h3>")
                self.lbl_md_status.setText("帮助文档不存在")
        else:
            self.md_preview.setHtml("<h3>此工具没有帮助文档</h3>")
            self.lbl_md_status.setText("无帮助文档")

    def rename_tool(self):
        """修改工具名称并同步到实际文件"""
        if not self.current_tool_data:
            QMessageBox.warning(self, "警告", "请先选择一个工具")
            return
        
        new_name = self.edit_tool_name.text().strip()
        if not new_name:
            QMessageBox.warning(self, "警告", "请输入新的工具名称")
            return
        
        tool_id = self.current_tool_data.get('id')
        old_name = self.current_tool_data.get('name', '')
        main_file = self.current_tool_data.get('main_file', '')
        
        if not main_file:
            QMessageBox.critical(self, "错误", "工具没有主文件路径")
            return
        
        tools_root = psp.tools_path_get()
        old_full_path = os.path.join(tools_root, main_file.replace('/', os.sep))
        
        if not os.path.exists(old_full_path):
            QMessageBox.critical(self, "错误", f"原文件不存在:\n{old_full_path}")
            return
        
        base_name, ext = os.path.splitext(old_full_path)
        new_file_name = new_name + ext
        
        new_full_path = os.path.join(os.path.dirname(old_full_path), new_file_name)
        
        if old_full_path == new_full_path:
            QMessageBox.information(self, "提示", "文件名没有变化")
            return
        
        try:
            os.rename(old_full_path, new_full_path)
            print(f"重命名主文件: {old_full_path} -> {new_full_path}")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"重命名主文件失败:\n{str(e)}")
            return
        
        associated_files = []
        for suffix in ['.json', '.png', '.html']:
            old_assoc = base_name + suffix
            if os.path.exists(old_assoc):
                new_assoc = os.path.join(os.path.dirname(old_full_path), new_name + suffix)
                try:
                    os.rename(old_assoc, new_assoc)
                    associated_files.append(new_assoc)
                    print(f"重命名关联文件: {old_assoc} -> {new_assoc}")
                except Exception as e:
                    print(f"重命名关联文件失败 {old_assoc}: {e}")
        
        try:
            new_main_rel = os.path.relpath(new_full_path, tools_root).replace(os.sep, '/')
            new_json_rel = None
            
            if associated_files:
                for f in associated_files:
                    if f.endswith('.json'):
                        new_json_rel = os.path.relpath(f, tools_root).replace(os.sep, '/')
                        break
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE tools_index 
                SET name = ?, main_file = ?
                WHERE id = ?
            ''', (new_name, new_main_rel, tool_id))
            conn.commit()
            conn.close()
            
            if new_json_rel:
                json_path = os.path.join(tools_root, new_json_rel.replace('/', os.sep))
                if os.path.exists(json_path):
                    with open(json_path, 'r', encoding='utf-8') as f:
                        metadata = json.load(f)
                    
                    metadata['name'] = new_name
                    metadata['files']['main'] = new_main_rel
                    
                    with open(json_path, 'w', encoding='utf-8') as f:
                        json.dump(metadata, f, indent=2, ensure_ascii=False)
            
            self.current_tool_data['name'] = new_name
            self.current_tool_data['main_file'] = new_main_rel
            
            self.on_selection_changed(self.tool_list.currentItem(), None)
            self.load_tools_from_db()
            
            QMessageBox.information(self, "成功", f"工具已重命名为:\n{new_name}")
            self.edit_tool_name.clear()
            
        except Exception as e:
            QMessageBox.critical(self, "错误", f"更新元数据失败:\n{str(e)}")

    def get_icon_from_clipboard(self):
        """从剪贴板获取图片"""
        clipboard = QApplication.clipboard()
        mime_data = clipboard.mimeData()
        
        if mime_data.hasImage():
            image = clipboard.image()
            if not image.isNull():
                self.clipboard_image = image
                
                pixmap = QPixmap.fromImage(image)
                scaled_pixmap = pixmap.scaled(100, 100, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                self.lbl_icon_preview.setPixmap(scaled_pixmap)
                
                self.btn_save_icon.setEnabled(True)
                QMessageBox.information(self, "成功", '已从剪贴板获取图标，点击"保存图标"按钮保存')
            else:
                QMessageBox.warning(self, "警告", "剪贴板中的图片数据无效")
        elif mime_data.hasUrls():
            urls = mime_data.urls()
            if urls:
                file_path = urls[0].toLocalFile()
                if file_path.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp')):
                    image = QImage(file_path)
                    if not image.isNull():
                        self.clipboard_image = image
                        
                        pixmap = QPixmap.fromImage(image)
                        scaled_pixmap = pixmap.scaled(100, 100, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                        self.lbl_icon_preview.setPixmap(scaled_pixmap)
                        
                        self.btn_save_icon.setEnabled(True)
                        QMessageBox.information(self, "成功", f"已加载图标文件:\n{file_path}")
                    else:
                        QMessageBox.warning(self, "警告", "无法加载图片文件")
                else:
                    QMessageBox.warning(self, "警告", "剪贴板中的文件不是图片格式")
        else:
            QMessageBox.warning(self, "警告", "剪贴板中没有图片数据\n请先复制图片到剪贴板")

    def save_icon(self):
        """保存图标到工具目录"""
        if not self.current_tool_data:
            QMessageBox.warning(self, "警告", "请先选择一个工具")
            return
        
        if not self.clipboard_image:
            QMessageBox.warning(self, "警告", "没有可保存的图标")
            return
        
        tool_id = self.current_tool_data.get('id')
        main_file = self.current_tool_data.get('main_file', '')
        
        if not main_file:
            QMessageBox.critical(self, "错误", "工具没有主文件路径")
            return
        
        tools_root = psp.tools_path_get()
        main_full_path = os.path.join(tools_root, main_file.replace('/', os.sep))
        
        base_name = os.path.splitext(main_full_path)[0]
        icon_path = base_name + '.png'
        
        try:
            self.clipboard_image.save(icon_path, 'PNG')
            print(f"保存图标: {icon_path}")
            
            icon_rel_path = os.path.relpath(icon_path, tools_root).replace(os.sep, '/')
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE tools_index 
                SET icon_file = ?, has_icon = 1
                WHERE id = ?
            ''', (icon_rel_path, tool_id))
            conn.commit()
            conn.close()
            
            for suffix in ['.json']:
                json_path = base_name + suffix
                if os.path.exists(json_path):
                    with open(json_path, 'r', encoding='utf-8') as f:
                        metadata = json.load(f)
                    
                    metadata['files']['icon'] = icon_rel_path
                    
                    with open(json_path, 'w', encoding='utf-8') as f:
                        json.dump(metadata, f, indent=2, ensure_ascii=False)
                    break
            
            self.current_tool_data['icon_file'] = icon_rel_path
            self.current_tool_data['has_icon'] = 1
            
            self.on_selection_changed(self.tool_list.currentItem(), None)
            
            self.clipboard_image = None
            self.lbl_icon_preview.setText("图标预览")
            self.lbl_icon_preview.setPixmap(QPixmap())
            self.btn_save_icon.setEnabled(False)
            
            QMessageBox.information(self, "成功", "图标已保存")
            
        except Exception as e:
            QMessageBox.critical(self, "错误", f"保存图标失败:\n{str(e)}")

    def save_tag(self):
        """保存标签到数据库和 JSON"""
        if not self.current_tool_data:
            QMessageBox.warning(self, "警告", "请先选择一个工具")
            return
        
        new_tag = self.edit_tag.text().strip()
        tool_id = self.current_tool_data.get('id')
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE tools_index 
                SET tag = ?
                WHERE id = ?
            ''', (new_tag, tool_id))
            conn.commit()
            conn.close()
            
            main_file = self.current_tool_data.get('main_file', '')
            if main_file:
                tools_root = psp.tools_path_get()
                main_full_path = os.path.join(tools_root, main_file.replace('/', os.sep))
                base_name = os.path.splitext(main_full_path)[0]
                
                for suffix in ['.json']:
                    json_path = base_name + suffix
                    if os.path.exists(json_path):
                        with open(json_path, 'r', encoding='utf-8') as f:
                            metadata = json.load(f)
                        
                        metadata['tag'] = new_tag
                        
                        with open(json_path, 'w', encoding='utf-8') as f:
                            json.dump(metadata, f, indent=2, ensure_ascii=False)
                        break
            
            self.current_tool_data['tag'] = new_tag
            
            self.on_selection_changed(self.tool_list.currentItem(), None)
            self.load_tools_from_db()
            
            QMessageBox.information(self, "成功", f"标签已保存:\n{new_tag if new_tag else '无'}")
            
        except Exception as e:
            QMessageBox.critical(self, "错误", f"保存标签失败:\n{str(e)}")
    
    def save_matchclass(self):
        """保存匹配类到数据库和 JSON"""
        if not self.current_tool_data:
            QMessageBox.warning(self, "警告", "请先选择一个工具")
            return
        
        matchclass_text = self.edit_matchclass.text().strip()
        tool_id = self.current_tool_data.get('id')
        
        matchclass_list = [item.strip() for item in matchclass_text.split(',') if item.strip()] if matchclass_text else []
        
        try:
            matchclass_json = json.dumps(matchclass_list, ensure_ascii=False)
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE tools_index 
                SET matchClass = ?
                WHERE id = ?
            ''', (matchclass_json, tool_id))
            conn.commit()
            conn.close()
            
            main_file = self.current_tool_data.get('main_file', '')
            if main_file:
                tools_root = psp.tools_path_get()
                main_full_path = os.path.join(tools_root, main_file.replace('/', os.sep))
                base_name = os.path.splitext(main_full_path)[0]
                
                for suffix in ['.json']:
                    json_path = base_name + suffix
                    if os.path.exists(json_path):
                        with open(json_path, 'r', encoding='utf-8') as f:
                            metadata = json.load(f)
                        
                        metadata['matchClass'] = matchclass_list
                        
                        with open(json_path, 'w', encoding='utf-8') as f:
                            json.dump(metadata, f, indent=2, ensure_ascii=False)
                        break
            
            self.current_tool_data['matchClass'] = matchclass_list
            
            self.on_selection_changed(self.tool_list.currentItem(), None)
            self.load_tools_from_db()
            
            display_text = ', '.join(matchclass_list) if matchclass_list else '无'
            QMessageBox.information(self, "成功", f"匹配类已保存:\n{display_text}")
            
        except Exception as e:
            QMessageBox.critical(self, "错误", f"保存匹配类失败:\n{str(e)}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ToolManagerApp()
    window.show()
    sys.exit(app.exec())