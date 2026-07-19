# Copyright 2026 LIUXIAOBO (刘晓波)
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import sqlite3
import json
import os
import sys

# 添加本地 libs 到 Python 路径
libs_path = os.path.join(os.path.dirname(__file__), 'libs')
if os.path.exists(libs_path):
    sys.path.insert(0, libs_path)

# from PySide6.QtWidgets import QApplication, QMainWindow, QWidget, QMessageBox
# from PySide6.QtCore import Qt

import paths_setup as psp
from qt_imports import QApplication, QMainWindow, QWidget, QMessageBox, Qt, QSplitter
import sqlite_file_setup as sfs

# 导入拆分后的模块
from widgets import ToolItemWidget
from help_editor import HelpEditorMixin
from ui_builder import UIBuilder
from metadata_editor import MetadataEditor
from icon_manager import IconManager
from help_viewer import HelpViewer
from tool_list_manager import ToolListManager


class ToolManagerApp(QMainWindow, HelpEditorMixin):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Nuke Tools Manager")
        self.setGeometry(100, 100, 1400, 900)
        
        self.current_tool_data = None
        self.db_path = None
        self.pending_changes = []
        
        # 自定义联想词列表
        self.custom_suggestions = [
            "Read",
            "Write",
            "Blur",
            "FrameHold",
            "NoSelectedNode",
            "AnySelectedNode",
            "AnyTime",
        ]
        
        # 初始化 UI 构建器
        self.ui_builder = UIBuilder(self)
        
        # 先初始化 UI
        self.init_ui()
        
        # 再初始化数据库和管理器
        self.ensure_database_exists()
        
        # 初始化管理器
        self.list_manager = ToolListManager(self.db_path, self.ui_builder.get_all_widgets())
        self.metadata_editor = MetadataEditor(
            self.db_path, 
            self.current_tool_data, 
            self.ui_builder.get_all_widgets(),
            self.list_manager.get_all_tools()
        )
        self.icon_manager = IconManager(self.db_path, self.current_tool_data, self.ui_builder.get_all_widgets())
        self.help_viewer = HelpViewer(self.ui_builder.get_all_widgets())
        
        # 加载工具数据
        self.load_tools_from_db()
        
        # 设置信号连接
        self.setup_connections()
    
    def init_ui(self):
        """初始化 UI"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = self.ui_builder.create_main_layout(central_widget)
        
        # 顶部栏
        top_bar = self.ui_builder.create_top_bar()
        main_layout.addLayout(top_bar)
        
        # 主分割器
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # 左侧面板
        left_panel = self.ui_builder.create_left_panel()
        
        # 右侧面板
        right_panel = self.ui_builder.create_right_panel(self.custom_suggestions)
        
        splitter.addWidget(left_panel)
        splitter.addWidget(right_panel)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 2)
        
        main_layout.addWidget(splitter)
        
        # 为 help_editor.py 提供直接访问的组件引用（保持向后兼容）
        widgets = self.ui_builder.get_all_widgets()
        self.tool_list = widgets['tool_list']
        self.lbl_md_status = widgets['lbl_md_status']
        self.md_preview = widgets['md_preview']
        self.search_input = widgets['search_input']
        self.btn_all = widgets['btn_all']
        self.btn_installed = widgets['btn_installed']
        self.btn_favorite = widgets['btn_favorite']
        self.json_view = widgets['json_view']
        self.edit_tool_name = widgets['edit_tool_name']
        self.edit_tag = widgets['edit_tag']
        self.edit_matchclass = widgets['edit_matchclass']
        self.matchclass_combo = widgets['matchclass_combo']
        self.lbl_id = widgets['lbl_id']
        self.lbl_name = widgets['lbl_name']
        self.lbl_tag = widgets['lbl_tag']
        self.lbl_matchClass = widgets['lbl_matchClass']
        self.lbl_category = widgets['lbl_category']
        self.lbl_file = widgets['lbl_file']
        self.icon_preview_label = widgets['icon_preview_label']
        self.lbl_icon_preview = widgets['lbl_icon_preview']
        self.btn_save_icon = widgets['btn_save_icon']
        self.lbl_stats = widgets['lbl_stats']
        
        self.update_db_info()
    
    def setup_connections(self):
        """设置信号和槽连接"""
        widgets = self.ui_builder.get_all_widgets()
        
        # 顶部按钮
        widgets['btn_sync'].clicked.connect(self.sync_tools)
        widgets['btn_save'].clicked.connect(self.save_changes)
        widgets['btn_refresh'].clicked.connect(self.refresh_tools_list)
        
        # 搜索和过滤
        widgets['search_input'].textChanged.connect(self.filter_list)
        widgets['btn_all'].clicked.connect(lambda: self.set_filter("all"))
        widgets['btn_installed'].clicked.connect(lambda: self.set_filter("installed"))
        widgets['btn_favorite'].clicked.connect(lambda: self.set_filter("favorite"))
        widgets['check_select_all'].stateChanged.connect(self.on_select_all_changed)
        
        # 工具列表选择
        widgets['tool_list'].currentItemChanged.connect(self.on_selection_changed)
        
        # 编辑功能
        widgets['btn_rename'].clicked.connect(self.rename_tool)
        widgets['btn_move_tool'].clicked.connect(self.move_tool)
        widgets['btn_save_tag'].clicked.connect(self.save_tag)
        widgets['btn_save_matchclass'].clicked.connect(self.save_matchclass)
        widgets['btn_add_matchclass'].clicked.connect(self.add_suggestion_to_matchclass)
        
        # 图标功能
        widgets['btn_get_clipboard'].clicked.connect(self.get_icon_from_clipboard)
        widgets['btn_save_icon'].clicked.connect(self.save_icon)
        
        # 帮助文档
        widgets['btn_load_md'].clicked.connect(self.load_help_md)
        widgets['btn_save_md'].clicked.connect(self.save_help_md)
        widgets['btn_export_html'].clicked.connect(self.export_md_to_html)
    
    def ensure_database_exists(self):
        """确保数据库存在"""
        if not os.path.exists(self.db_path):
            print(f"数据库不存在，正在创建: {self.db_path}")
            sfs.sync_tools_to_database(self.db_path)
            QMessageBox.information(self, "提示", "已自动创建数据库并同步工具")
    
    def update_db_info(self):
        """更新数据库信息"""
        self.db_path = sfs.get_user_db_path()
        username = sfs.get_current_user()
        db_uuid = sfs.get_current_user_db_uuid()
        self.ui_builder.get_widget('lbl_db').setText(f"用户: {username} | 数据库: {db_uuid}")
    
    def load_tools_from_db(self):
        """从数据库加载工具"""
        success = self.list_manager.load_tools_from_db()
        if success:
            # 更新 metadata_editor 中的 all_tools 引用
            self.metadata_editor.all_tools = self.list_manager.get_all_tools()
    
    def sync_tools(self):
        """同步工具"""
        self.list_manager.sync_tools()
        self.metadata_editor.all_tools = self.list_manager.get_all_tools()
    
    def save_changes(self):
        """保存更改"""
        self.list_manager.save_changes()
    
    def refresh_tools_list(self):
        """刷新工具列表"""
        self.load_tools_from_db()
    
    def set_filter(self, filter_type):
        """设置过滤器"""
        self.list_manager.set_filter(filter_type)
    
    def filter_list(self):
        """过滤列表"""
        self.list_manager.filter_list()
    
    def on_selection_changed(self, current, previous):
        """选择改变时更新显示"""
        if not current:
            return
        
        self.current_tool_data = current.data(Qt.ItemDataRole.UserRole)
        
        # 更新 metadata_editor 的 current_tool_data
        self.metadata_editor.current_tool_data = self.current_tool_data
        self.icon_manager.current_tool_data = self.current_tool_data
        
        # 更新详情显示
        widgets = self.ui_builder.get_all_widgets()
        
        widgets['lbl_id'].setText(self.current_tool_data.get('id', 'N/A'))
        widgets['lbl_name'].setText(self.current_tool_data.get('name', 'N/A'))
        widgets['lbl_tag'].setText(self.current_tool_data.get('tag', '无') or '无')
        
        matchClass = self.current_tool_data.get('matchClass', '[]')
        try:
            if isinstance(matchClass, str):
                matchClass = json.loads(matchClass)
            widgets['lbl_matchClass'].setText(', '.join(matchClass) if matchClass else '无')
        except:
            widgets['lbl_matchClass'].setText(str(matchClass))
        
        widgets['lbl_category'].setText(self.current_tool_data.get('category', 'N/A'))

        # 移动工具：显示当前所在目录
        current_dir = os.path.dirname(self.current_tool_data.get('main_file', ''))
        widgets['lbl_move_current'].setText(f"当前位于: {current_dir if current_dir else 'tools/'}")

        main_file = self.current_tool_data.get('main_file', 'N/A')
        tools_root = psp.tools_path_get()
        full_path = os.path.join(tools_root, main_file.replace('/', os.sep))
        widgets['lbl_file'].setText(full_path)
        
        # 加载图标预览
        self.icon_manager.load_icon_preview()
        
        # 更新 JSON 显示
        widgets['json_view'].setPlainText(json.dumps(self.current_tool_data, indent=2, ensure_ascii=False))
        
        # 更新编辑框
        widgets['edit_tool_name'].clear()
        widgets['edit_tag'].setText(self.current_tool_data.get('tag', ''))
        
        matchClass = self.current_tool_data.get('matchClass', [])
        if isinstance(matchClass, str):
            try:
                matchClass = json.loads(matchClass)
            except:
                matchClass = []
        widgets['edit_matchclass'].setText(', '.join(matchClass) if matchClass else '')
        
        # 加载帮助文档
        help_file = self.current_tool_data.get('help_file')
        self.help_viewer.load_help_document(help_file)
    
    def on_select_all_changed(self, state):
        """全选状态改变"""
        self.list_manager.on_select_all_changed(state)
    
    def rename_tool(self):
        """重命名工具"""
        success = self.metadata_editor.rename_tool()
        if success:
            # 刷新显示
            self.on_selection_changed(self.ui_builder.get_widget('tool_list').currentItem(), None)
            self.load_tools_from_db()

    def move_tool(self):
        """移动工具到其他目录"""
        success = self.metadata_editor.move_tool()
        if success:
            # 刷新显示和列表
            self.on_selection_changed(self.ui_builder.get_widget('tool_list').currentItem(), None)
            self.load_tools_from_db()
    
    def save_tag(self):
        """保存标签"""
        def on_refresh():
            self.on_selection_changed(self.ui_builder.get_widget('tool_list').currentItem(), None)
            self.load_tools_from_db()
        
        self.metadata_editor.save_tag(on_refresh)
    
    def save_matchclass(self):
        """保存匹配类"""
        def on_refresh():
            self.on_selection_changed(self.ui_builder.get_widget('tool_list').currentItem(), None)
            self.load_tools_from_db()
        
        self.metadata_editor.save_matchclass(on_refresh)
    
    def add_suggestion_to_matchclass(self):
        """添加联想词条到匹配类"""
        selected_text = self.ui_builder.get_widget('matchclass_combo').currentText()
        if selected_text:
            current_text = self.ui_builder.get_widget('edit_matchclass').text()
            
            if not current_text:
                self.ui_builder.get_widget('edit_matchclass').setText(selected_text)
            else:
                if current_text.endswith(','):
                    self.ui_builder.get_widget('edit_matchclass').setText(current_text + selected_text)
                else:
                    self.ui_builder.get_widget('edit_matchclass').setText(current_text + ', ' + selected_text)
    
    def get_icon_from_clipboard(self):
        """从剪贴板获取图标"""
        self.icon_manager.get_icon_from_clipboard()
    
    def save_icon(self):
        """保存图标"""
        success = self.icon_manager.save_icon()
        if success:
            # 刷新显示
            self.on_selection_changed(self.ui_builder.get_widget('tool_list').currentItem(), None)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ToolManagerApp()
    window.show()
    sys.exit(app.exec())