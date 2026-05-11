import os
import sqlite3
import json
import re
import shutil
import traceback
from PySide6.QtWidgets import QMessageBox, QFileDialog
from PySide6.QtCore import QUrl

import paths_setup as psp


class HelpEditorMixin:
    """HTML 帮助文档查看器混入类"""
    
    def load_help_md(self):
        """加载 HTML 帮助文档"""
        if not self.current_tool_data:
            QMessageBox.warning(self, "警告", "请先选择一个工具")
            return
        
        help_file = self.current_tool_data.get('help_file')
        
        if not help_file:
            reply = QMessageBox.question(self, "提示", 
                                        "此工具没有帮助文档，是否设置一个？",
                                        QMessageBox.Yes | QMessageBox.No)
            if reply == QMessageBox.Yes:
                self._select_help_file()
            return

        tools_root = psp.tools_path_get()
        help_full_path = os.path.join(tools_root, help_file.replace('/', os.sep))
        
        if not os.path.exists(help_full_path):
            QMessageBox.warning(self, "警告", f"帮助文档不存在:\n{help_full_path}")
            return
        
        try:
            self.md_preview.setSource(QUrl.fromLocalFile(help_full_path))
            self.lbl_md_status.setText(f"已加载: {os.path.basename(help_full_path)}")
            print(f"已加载帮助文档: {help_full_path}")
            
        except Exception as e:
            QMessageBox.critical(self, "错误", f"加载帮助文档失败:\n{str(e)}")
    
    def _select_help_file(self):
        """选择 HTML 文件并复制到工具目录"""
        if not self.current_tool_data:
            QMessageBox.warning(self, "警告", "请先选择一个工具")
            return
        
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择 HTML 帮助文档", "", "HTML Files (*.html *.htm)"
        )
        
        if not file_path:
            return
        
        try:
            tools_root = psp.tools_path_get()
            main_file = self.current_tool_data.get('main_file', '')
            tool_name = self.current_tool_data.get('name', '')
            
            if not main_file:
                QMessageBox.warning(self, "警告", "工具主文件路径不存在")
                return
            
            main_full_path = os.path.join(tools_root, main_file.replace('/', os.sep))
            tool_dir = os.path.dirname(main_full_path)
            
            # 使用工具名作为 HTML 文件名
            if not tool_name:
                html_dest_name = "help.html"
            else:
                safe_name = re.sub(r'[<>:"/\\|?*]', '_', tool_name)
                html_dest_name = f"{safe_name}.html"
            
            html_dest_path = os.path.join(tool_dir, html_dest_name)
            
            # 如果已存在，先删除
            if os.path.exists(html_dest_path):
                reply = QMessageBox.question(self, "确认", 
                                            "工具目录已存在帮助文档，是否覆盖？",
                                            QMessageBox.Yes | QMessageBox.No)
                if reply == QMessageBox.No:
                    return
                os.remove(html_dest_path)
            
            # 复制 HTML 文件
            shutil.copy2(file_path, html_dest_path)
            
            # 处理 HTML 中的图片引用 - 使用 pngfiles_path_get() 获取路径
            source_dir = os.path.dirname(file_path)
            pnghelp_dir = psp.pngfiles_path_get()
            
            if not os.path.exists(pnghelp_dir):
                os.makedirs(pnghelp_dir)
            
            # 读取 HTML 内容并处理图片
            with open(html_dest_path, 'r', encoding='utf-8') as f:
                html_content = f.read()
            
            # 查找所有图片引用
            img_pattern = re.compile(r'<img[^>]+src=["\']([^"\']+)["\']', re.IGNORECASE)
            
            images_to_copy = []
            for match in img_pattern.finditer(html_content):
                img_src = match.group(1)
                
                if img_src.startswith('data:'):
                    continue
                
                if img_src.startswith(('http://', 'https://')):
                    continue
                
                if os.path.isabs(img_src):
                    img_full_path = img_src
                else:
                    img_full_path = os.path.join(source_dir, img_src)
                
                if os.path.exists(img_full_path):
                    images_to_copy.append((img_src, img_full_path))
            
            # 复制图片并更新 HTML
            if images_to_copy:
                for old_src, img_full_path in images_to_copy:
                    img_name = os.path.basename(img_full_path)
                    img_dest_path = os.path.join(pnghelp_dir, img_name)
                    
                    if not os.path.exists(img_dest_path):
                        shutil.copy2(img_full_path, img_dest_path)
                    
                    new_src = f"../../pnghelp/{img_name}"
                    html_content = html_content.replace(old_src, new_src, 1)
                
                with open(html_dest_path, 'w', encoding='utf-8') as f:
                    f.write(html_content)
                
                msg = f"已设置帮助文档\n\n文件: {html_dest_name}\n复制了 {len(images_to_copy)} 张图片到 pnghelp 文件夹"
            else:
                msg = f"已设置帮助文档\n\n文件: {html_dest_name}\n（未检测到需要复制的图片）"
            
            # 计算相对路径
            help_rel_path = os.path.relpath(html_dest_path, tools_root).replace(os.sep, '/')
            tool_id = self.current_tool_data.get('id')
            
            # 更新数据库
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE tools_index 
                SET help_file = ?, has_help = 1
                WHERE id = ?
            ''', (help_rel_path, tool_id))
            conn.commit()
            conn.close()
            
            # 更新 JSON 文件
            for suffix in ['.json']:
                json_path = os.path.splitext(main_full_path)[0] + suffix
                if os.path.exists(json_path):
                    with open(json_path, 'r', encoding='utf-8') as f:
                        metadata = json.load(f)
                    
                    metadata['files']['help'] = help_rel_path
                    metadata['has_help'] = True
                    
                    with open(json_path, 'w', encoding='utf-8') as f:
                        json.dump(metadata, f, indent=2, ensure_ascii=False)
                    break
            
            # 更新当前工具数据
            self.current_tool_data['help_file'] = help_rel_path
            self.current_tool_data['has_help'] = 1
            
            # 加载文档
            self.md_preview.setSource(QUrl.fromLocalFile(html_dest_path))
            self.lbl_md_status.setText(f"已设置: {html_dest_name}")
            
            QMessageBox.information(self, "成功", msg)
            
        except Exception as e:
            QMessageBox.critical(self, "错误", f"设置帮助文档失败:\n{str(e)}\n\n{traceback.format_exc()}")

    def save_help_md(self):
        """设置/更新 HTML 帮助文档"""
        if not self.current_tool_data:
            QMessageBox.warning(self, "警告", "请先选择一个工具")
            return
        
        current_help = self.current_tool_data.get('help_file')
        
        if current_help:
            reply = QMessageBox.question(self, "提示", 
                                        "是否要更换帮助文档？\n\n新文档将复制到工具目录并自动处理图片依赖。",
                                        QMessageBox.Yes | QMessageBox.No)
            if reply == QMessageBox.Yes:
                self._select_help_file()
        else:
            self._select_help_file()

    def insert_image_to_md(self):
        """此功能已禁用"""
        QMessageBox.information(self, "提示", "HTML 文档编辑功能已移除\n请使用外部编辑器修改 HTML 文件")

    def refresh_md_preview(self):
        """刷新 HTML 预览"""
        if self.current_tool_data:
            help_file = self.current_tool_data.get('help_file')
            if help_file:
                tools_root = psp.tools_path_get()
                help_full_path = os.path.join(tools_root, help_file.replace('/', os.sep))
                if os.path.exists(help_full_path):
                    self.md_preview.setSource(QUrl.fromLocalFile(help_full_path))
                    return
        
        self.md_preview.setHtml("<h3>无帮助文档</h3>")

    def copy_md_to_clipboard(self):
        """此功能已禁用"""
        QMessageBox.information(self, "提示", "HTML 文档复制功能已移除")

    def export_md_to_html(self):
        """导出当前 HTML 到文件"""
        if not self.current_tool_data:
            QMessageBox.warning(self, "警告", "请先选择一个工具")
            return
        
        help_file = self.current_tool_data.get('help_file')
        if not help_file:
            QMessageBox.warning(self, "警告", "此工具没有 HTML 帮助文档")
            return
        
        tools_root = psp.tools_path_get()
        help_full_path = os.path.join(tools_root, help_file.replace('/', os.sep))
        
        if not os.path.exists(help_full_path):
            QMessageBox.warning(self, "警告", f"帮助文档不存在:\n{help_full_path}")
            return
        
        save_path, _ = QFileDialog.getSaveFileName(
            self, "导出 HTML", help_full_path, "HTML Files (*.html)"
        )
        
        if not save_path:
            return
        
        try:
            shutil.copy2(help_full_path, save_path)
            QMessageBox.information(self, "成功", f"HTML 已导出到:\n{save_path}")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"导出失败:\n{str(e)}")