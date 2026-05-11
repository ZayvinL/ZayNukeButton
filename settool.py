import os
import sys
import json
import sqlite3
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                               QHBoxLayout, QListWidget, QListWidgetItem, 
                               QTextBrowser, QLabel, QPushButton, QLineEdit, 
                               QSplitter, QMessageBox, QCheckBox,
                               QGroupBox, QFormLayout, QTabWidget)
from PySide6.QtCore import Qt, QUrl, QSize, Signal
from PySide6.QtGui import QFont

import paths_setup as psp
import sqlite_file_setup as sfs

class ToolItemWidget(QWidget):
    """自定义工具列表项"""
    stateChanged = Signal()
    
    def __init__(self, tool_data, parent=None):
        super().__init__(parent)
        self.tool_data = tool_data
        self.setup_ui()
    
    def setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(5, 2, 5, 2)
        layout.setSpacing(8)
        
        # 安装复选框
        self.check_install = QCheckBox()
        self.check_install.setChecked(self.tool_data.get('is_installed', 0) == 1)
        self.check_install.stateChanged.connect(self.on_install_changed)
        layout.addWidget(self.check_install)
        
        # 收藏复选框
        self.check_favorite = QCheckBox()
        self.check_favorite.setChecked(self.tool_data.get('is_favorite', 0) == 1)
        self.check_favorite.stateChanged.connect(self.on_favorite_changed)
        layout.addWidget(self.check_favorite)
        
        # 工具名称
        self.lbl_name = QLabel(self.tool_data.get('name', 'Unnamed'))
        layout.addWidget(self.lbl_name, 1)
    
    def on_install_changed(self, state):
        """安装状态改变时，直接更新 tool_data"""
        new_value = 1 if state == Qt.CheckState.Checked else 0
        self.tool_data['is_installed'] = new_value
        print(f"工具 {self.tool_data.get('name')} 安装状态变为: {new_value}")
        self.stateChanged.emit()
    
    def on_favorite_changed(self, state):
        """收藏状态改变时，直接更新 tool_data"""
        new_value = 1 if state == Qt.CheckState.Checked else 0
        self.tool_data['is_favorite'] = new_value
        print(f"工具 {self.tool_data.get('name')} 收藏状态变为: {new_value}")
        self.stateChanged.emit()


class ToolManagerApp(QMainWindow):
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
        
        detail_widget = QWidget()
        detail_layout = QVBoxLayout(detail_widget)
        detail_layout.setContentsMargins(10, 10, 10, 10)
        detail_layout.setSpacing(10)
        
        self.title_label = QLabel("选择工具查看详情")
        detail_layout.addWidget(self.title_label)
        
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
        detail_layout.addWidget(info_group)
        
        stats_group = QGroupBox("使用统计")
        stats_layout = QFormLayout()
        stats_layout.setSpacing(8)
        
        self.lbl_usage = QLabel("0")
        stats_layout.addRow("使用次数:", self.lbl_usage)
        
        self.lbl_last = QLabel("未使用")
        stats_layout.addRow("最后使用:", self.lbl_last)
        
        stats_group.setLayout(stats_layout)
        detail_layout.addWidget(stats_group)
        
        detail_layout.addStretch()
        
        tabs.addTab(detail_widget, "详情")
        
        json_widget = QWidget()
        json_layout = QVBoxLayout(json_widget)
        self.json_view = QTextBrowser()
        self.json_view.setFont(QFont("Consolas", 10))
        json_layout.addWidget(self.json_view)
        tabs.addTab(json_widget, "JSON")
        
        help_widget = QWidget()
        help_layout = QVBoxLayout(help_widget)
        self.html_view = QTextBrowser()
        self.html_view.setOpenExternalLinks(True)
        help_layout.addWidget(self.html_view)
        tabs.addTab(help_widget, "帮助")
        
        right_layout.addWidget(tabs)
        
        splitter.addWidget(left_panel)
        splitter.addWidget(right_panel)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 2)
        
        main_layout.addWidget(splitter)
        
        self.update_db_info()
        self.update_stats()

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
        self.lbl_db.setText(f"用户: {username} | 数据库: {db_uuid[:8]}...")

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
            
            # 从界面上的 widget 读取实际状态，而不是从 self.all_tools 读取
            for i in range(self.tool_list.count()):
                item = self.tool_list.item(i)
                widget = self.tool_list.itemWidget(item)
                
                if widget is None:
                    continue
                
                tool_data = widget.tool_data
                tool_id = tool_data.get('id')
                if not tool_id:
                    continue
                
                # 直接从 widget 的复选框读取当前状态
                is_installed = 1 if widget.check_install.isChecked() else 0
                is_favorite = 1 if widget.check_favorite.isChecked() else 0
                
                # 同步更新 tool_data（确保数据一致）
                tool_data['is_installed'] = is_installed
                tool_data['is_favorite'] = is_favorite
                
                usage_count = tool_data.get('usage_count', 0)
                last_used = tool_data.get('last_used', None)
                
                # 统计
                if is_installed:
                    installed_count += 1
                if is_favorite:
                    favorite_count += 1
                
                # 打印前几个工具的状态
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
        # 完全清空列表和 widget
        self.tool_list.clear()
        
        for i in range(self.tool_list.count()):
            item = self.tool_list.item(i)
            widget = self.tool_list.itemWidget(item)
            if widget:
                widget.deleteLater()
        
        self.tool_list.clear()
        
        # 重新加载所有工具（确保从数据库读取最新状态）
        print(f"加载 {len(self.all_tools)} 个工具到列表")
        for i, tool in enumerate(self.all_tools):
            # 打印前几个工具的状态用于调试
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
        # 直接使用 isChecked() 获取当前状态
        is_checked = self.check_select_all.isChecked()
        
        print(f"全选状态变为: {'勾选' if is_checked else '取消'}")
        
        for i in range(self.tool_list.count()):
            item = self.tool_list.item(i)
            widget = self.tool_list.itemWidget(item)
            
            if widget is None:
                continue
            
            # 批量设置所有工具的安装状态
            widget.check_install.blockSignals(True)
            widget.check_install.setChecked(is_checked)
            widget.check_install.blockSignals(False)
            
            # 同步更新数据
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
        self.title_label.setText(name)
        
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
        
        self.lbl_usage.setText(str(self.current_tool_data.get('usage_count', 0)))
        last_used = self.current_tool_data.get('last_used', '未使用')
        self.lbl_last.setText(str(last_used) if last_used else '未使用')
        
        self.json_view.setPlainText(json.dumps(self.current_tool_data, indent=2, ensure_ascii=False))
        
        help_file = self.current_tool_data.get('help_file')
        if help_file:
            help_full = os.path.join(tools_root, help_file.replace('/', os.sep))
            if os.path.exists(help_full):
                self.html_view.setSource(QUrl.fromLocalFile(help_full))
            else:
                self.html_view.setHtml("<h3>未找到帮助文档</h3>")
        else:
            self.html_view.setHtml("<h3>此工具没有帮助文档</h3>")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ToolManagerApp()
    window.show()
    sys.exit(app.exec())