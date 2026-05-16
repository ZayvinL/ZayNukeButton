
"""
工具列表管理器 - 负责工具列表的加载、过滤和显示
"""

import sqlite3
import json
from PySide6.QtWidgets import QListWidgetItem, QMessageBox
from PySide6.QtCore import Qt
from widgets import ToolItemWidget


class ToolListManager:
    """工具列表管理器"""
    
    def __init__(self, db_path, widgets):
        self.db_path = db_path
        self.widgets = widgets
        self.all_tools = []
        self.current_filter = "all"
    
    def load_tools_from_db(self):
        """从数据库加载工具"""
        try:
            import sqlite_file_setup as sfs
            self.all_tools = sfs.get_all_tools_from_db(self.db_path)
            self.refresh_list()
            return True
        except Exception as e:
            QMessageBox.critical(None, "错误", f"加载失败:\n{str(e)}")
            return False
    
    def sync_tools(self):
        """同步工具到数据库"""
        reply = QMessageBox.question(None, "同步", "重新扫描并同步所有工具？", 
                                    QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            try:
                import sqlite_file_setup as sfs
                count = sfs.sync_tools_to_database(self.db_path)
                QMessageBox.information(None, "成功", f"已同步 {count} 个工具")
                self.load_tools_from_db()
                return True
            except Exception as e:
                QMessageBox.critical(None, "错误", f"同步失败:\n{str(e)}")
                return False
        return False
    
    def refresh_list(self):
        """刷新工具列表"""
        self.widgets['tool_list'].clear()
        
        print(f"加载 {len(self.all_tools)} 个工具到列表")
        for i, tool in enumerate(self.all_tools):
            if i < 3:
                print(f"  工具 {i}: {tool.get('name')} - 安装:{tool.get('is_installed')} 收藏:{tool.get('is_favorite')}")
            
            widget = ToolItemWidget(tool)
            widget.stateChanged.connect(self._on_tool_state_changed)
            
            item = QListWidgetItem()
            item.setSizeHint(widget.sizeHint())
            item.setData(Qt.ItemDataRole.UserRole, tool)
            
            self.widgets['tool_list'].addItem(item)
            self.widgets['tool_list'].setItemWidget(item, widget)
        
        self.update_stats()
    
    def set_filter(self, filter_type):
        """设置过滤器"""
        self.current_filter = filter_type
        
        if filter_type == "all":
            self.widgets['btn_all'].setChecked(True)
            self.widgets['btn_installed'].setChecked(False)
            self.widgets['btn_favorite'].setChecked(False)
        elif filter_type == "installed":
            self.widgets['btn_all'].setChecked(False)
            self.widgets['btn_installed'].setChecked(True)
            self.widgets['btn_favorite'].setChecked(False)
        elif filter_type == "favorite":
            self.widgets['btn_all'].setChecked(False)
            self.widgets['btn_installed'].setChecked(False)
            self.widgets['btn_favorite'].setChecked(True)
        
        self.filter_list()
    
    def filter_list(self):
        """过滤工具列表"""
        search_text = self.widgets['search_input'].text().lower()
        
        for i in range(self.widgets['tool_list'].count()):
            item = self.widgets['tool_list'].item(i)
            tool = item.data(Qt.ItemDataRole.UserRole)
            
            match_text = (
                search_text in tool.get('name', '').lower() or
                search_text in tool.get('tag', '').lower()
            )
            
            if self.current_filter == "installed":
                match_filter = tool.get('is_installed', 0) == 1
            elif self.current_filter == "favorite":
                match_filter = tool.get('is_favorite', 0) == 1
            else:
                match_filter = True
            
            item.setHidden(not (match_text and match_filter))
        
        self.update_stats()
    
    def update_stats(self):
        """更新统计信息"""
        total = len(self.all_tools)
        installed = sum(1 for t in self.all_tools if t.get('is_installed', 0))
        favorite = sum(1 for t in self.all_tools if t.get('is_favorite', 0))
        showing = 0
        
        for i in range(self.widgets['tool_list'].count()):
            item = self.widgets['tool_list'].item(i)
            if not item.isHidden():
                showing += 1
        
        self.widgets['lbl_stats'].setText(
            f"总计: {total}  |  已安装: {installed}  |  已收藏: {favorite}  |  "
            f"当前显示: {showing}"
        )
    
    def on_select_all_changed(self, state):
        """全选复选框状态改变"""
        is_checked = self.widgets['check_select_all'].isChecked()
        
        print(f"全选状态变为: {'勾选' if is_checked else '取消'}")
        
        for i in range(self.widgets['tool_list'].count()):
            item = self.widgets['tool_list'].item(i)
            widget = self.widgets['tool_list'].itemWidget(item)
            
            if widget is None:
                continue
            
            widget.check_install.blockSignals(True)
            widget.check_install.setChecked(is_checked)
            widget.check_install.blockSignals(False)
            
            widget.tool_data['is_installed'] = 1 if is_checked else 0
        
        self.update_stats()
    
    def save_changes(self):
        """保存所有更改到数据库"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            saved_count = 0
            installed_count = 0
            favorite_count = 0
            
            print("开始保存工具状态到数据库...")
            
            for i in range(self.widgets['tool_list'].count()):
                item = self.widgets['tool_list'].item(i)
                widget = self.widgets['tool_list'].itemWidget(item)
                
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
            
            self.update_stats()
            
            QMessageBox.information(None, "成功", f"已保存 {saved_count} 个工具的状态\n已安装: {installed_count}\n已收藏: {favorite_count}")
            return True
        except Exception as e:
            QMessageBox.critical(None, "错误", f"保存失败:\n{str(e)}")
            return False
    
    def _on_tool_state_changed(self):
        """工具状态改变时更新统计"""
        self.update_stats()
    
    def get_all_tools(self):
        """获取所有工具数据"""
        return self.all_tools