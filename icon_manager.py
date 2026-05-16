
"""
图标管理器 - 负责工具图标的获取、预览和保存
"""

import sqlite3
import json
import os
from PySide6.QtWidgets import QMessageBox
from PySide6.QtGui import QClipboard, QImage, QPixmap
from PySide6.QtCore import Qt


class IconManager:
    """图标管理器"""
    
    def __init__(self, db_path, current_tool_data, widgets):
        self.db_path = db_path
        self.current_tool_data = current_tool_data
        self.widgets = widgets
        self.clipboard_image = None
    
    def load_icon_preview(self):
        """加载工具图标到预览区域"""
        icon_file = self.current_tool_data.get('icon_file')
        
        if not icon_file:
            self.widgets['icon_preview_label'].setText("无图标")
            self.widgets['icon_preview_label'].setPixmap(QPixmap())
            return
        
        try:
            import paths_setup as psp
            
            tools_root = psp.tools_path_get()
            icon_full_path = os.path.join(tools_root, icon_file.replace('/', os.sep))
            
            if not os.path.exists(icon_full_path):
                self.widgets['icon_preview_label'].setText("图标文件不存在")
                self.widgets['icon_preview_label'].setPixmap(QPixmap())
                return
            
            pixmap = QPixmap(icon_full_path)
            
            if pixmap.isNull():
                self.widgets['icon_preview_label'].setText("无法加载图标")
                self.widgets['icon_preview_label'].setPixmap(QPixmap())
                return
            
            scaled_pixmap = pixmap.scaled(
                self.widgets['icon_preview_label'].size(),
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )
            
            self.widgets['icon_preview_label'].setPixmap(scaled_pixmap)
            self.widgets['icon_preview_label'].setText("")
            
        except Exception as e:
            self.widgets['icon_preview_label'].setText(f"加载失败: {str(e)}")
            self.widgets['icon_preview_label'].setPixmap(QPixmap())
            print(f"加载图标预览失败: {e}")
    
    def get_icon_from_clipboard(self):
        """从剪贴板获取图片"""
        from PySide6.QtWidgets import QApplication
        
        clipboard = QApplication.clipboard()
        mime_data = clipboard.mimeData()
        
        if mime_data.hasImage():
            image = clipboard.image()
            if not image.isNull():
                self.clipboard_image = image
                
                pixmap = QPixmap.fromImage(image)
                scaled_pixmap = pixmap.scaled(100, 100, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                self.widgets['lbl_icon_preview'].setPixmap(scaled_pixmap)
                
                self.widgets['btn_save_icon'].setEnabled(True)
                QMessageBox.information(None, "成功", '已从剪贴板获取图标，点击"保存图标"按钮保存')
            else:
                QMessageBox.warning(None, "警告", "剪贴板中的图片数据无效")
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
                        self.widgets['lbl_icon_preview'].setPixmap(scaled_pixmap)
                        
                        self.widgets['btn_save_icon'].setEnabled(True)
                        QMessageBox.information(None, "成功", f"已加载图标文件:\n{file_path}")
                    else:
                        QMessageBox.warning(None, "警告", "无法加载图片文件")
                else:
                    QMessageBox.warning(None, "警告", "剪贴板中的文件不是图片格式")
        else:
            QMessageBox.warning(None, "警告", "剪贴板中没有图片数据\n请先复制图片到剪贴板")
    
    def save_icon(self):
        """保存图标到工具目录"""
        if not self.current_tool_data:
            QMessageBox.warning(None, "警告", "请先选择一个工具")
            return False
        
        if not self.clipboard_image:
            QMessageBox.warning(None, "警告", "没有可保存的图标")
            return False
        
        tool_id = self.current_tool_data.get('id')
        main_file = self.current_tool_data.get('main_file', '')
        
        if not main_file:
            QMessageBox.critical(None, "错误", "工具没有主文件路径")
            return False
        
        try:
            import paths_setup as psp
            
            tools_root = psp.tools_path_get()
            main_full_path = os.path.join(tools_root, main_file.replace('/', os.sep))
            
            base_name = os.path.splitext(main_full_path)[0]
            icon_path = base_name + '.png'
            
            # 1. 保存图标文件
            self.clipboard_image.save(icon_path, 'PNG')
            print(f"保存图标: {icon_path}")
            
            icon_rel_path = os.path.relpath(icon_path, tools_root).replace(os.sep, '/')
            
            # 2. 更新数据库
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE tools_index 
                SET icon_file = ?, has_icon = 1
                WHERE id = ?
            ''', (icon_rel_path, tool_id))
            conn.commit()
            conn.close()
            
            # 3. 更新 JSON 文件
            for suffix in ['.json']:
                json_path = base_name + suffix
                if os.path.exists(json_path):
                    with open(json_path, 'r', encoding='utf-8') as f:
                        metadata = json.load(f)
                    
                    metadata['files']['icon'] = icon_rel_path
                    
                    with open(json_path, 'w', encoding='utf-8') as f:
                        json.dump(metadata, f, indent=2, ensure_ascii=False)
                    break
            
            # 4. 更新内存中的数据
            self.current_tool_data['icon_file'] = icon_rel_path
            self.current_tool_data['has_icon'] = 1
            
            # 5. 清理剪贴板缓存
            self.clipboard_image = None
            self.widgets['lbl_icon_preview'].setText("图标预览")
            self.widgets['lbl_icon_preview'].setPixmap(QPixmap())
            self.widgets['btn_save_icon'].setEnabled(False)
            
            QMessageBox.information(None, "成功", "图标已保存")
            return True
            
        except Exception as e:
            QMessageBox.critical(None, "错误", f"保存图标失败:\n{str(e)}")
            return False