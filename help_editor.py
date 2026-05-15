import shutil
import os
import re
from PySide6.QtWidgets import (QFileDialog, QMessageBox)
from PySide6.QtCore import QUrl
import paths_setup as psp

class HelpEditorMixin:
    """Markdown 帮助文档查看器混入类"""
    
    def load_help_md(self):
        """加载 Markdown 帮助文档"""
        if not self.current_tool_data:
            QMessageBox.warning(self, "警告", "请先选择一个工具")
            return
        
        help_file = self.current_tool_data.get('help_file')
        if not help_file:
            QMessageBox.warning(self, "警告", "当前工具没有帮助文档")
            return
        
        tools_root = psp.tools_path_get()
        help_full_path = os.path.join(tools_root, help_file.replace('/', os.sep))
        
        if not os.path.exists(help_full_path):
            QMessageBox.warning(self, "警告", f"帮助文档不存在:\n{help_full_path}")
            return
        
        try:
            from settool import ToolManagerApp
            if isinstance(self, ToolManagerApp):
                self.on_selection_changed(self.tool_list.currentItem(), None)
            self.lbl_md_status.setText(f"已加载: {os.path.basename(help_full_path)}")
            print(f"已加载帮助文档: {help_full_path}")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"加载失败:\n{str(e)}")

    def _select_help_file(self):
        """选择 Markdown 文件并处理图片"""
        if not self.current_tool_data:
            QMessageBox.warning(self, "警告", "请先选择一个工具")
            return
        
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择 Markdown 帮助文档", "", "Markdown Files (*.md *.markdown)"
        )
        
        if not file_path:
            return
        
        try:
            tools_root = psp.tools_path_get()
            tool_name = self.current_tool_data.get('name', 'unknown')
            
            # 读取 Markdown 文件内容
            with open(file_path, 'r', encoding='utf-8') as f:
                md_content = f.read()
            
            # 获取 pnghelp 目录
            pnghelp_dir = os.path.join(os.path.dirname(__file__), 'pnghelp')
            os.makedirs(pnghelp_dir, exist_ok=True)
            
            # 提取所有图片引用
            image_refs = self._extract_images_from_markdown(md_content)
            
            if image_refs:
                # 处理图片文件
                processed_images = self._process_images(image_refs, file_path, pnghelp_dir, tool_name)
                
                # 更新 Markdown 内容中的图片路径
                md_content = self._update_markdown_images(md_content, processed_images)
            
            # 保存处理后的 Markdown 文件到工具目录
            tool_dir = os.path.dirname(os.path.join(tools_root, self.current_tool_data.get('main_file', '').replace('/', os.sep)))
            os.makedirs(tool_dir, exist_ok=True)
            
            safe_name = self._sanitize_filename(tool_name)
            md_dest_path = os.path.join(tool_dir, f"{safe_name}.md")
            
            with open(md_dest_path, 'w', encoding='utf-8') as f:
                f.write(md_content)
            
            # 更新数据库和 JSON
            md_rel_path = os.path.relpath(md_dest_path, tools_root).replace(os.sep, '/')
            self.current_tool_data['help_file'] = md_rel_path
            
            # 更新数据库
            import sqlite3
            db_path = self.db_path if hasattr(self, 'db_path') else None
            if db_path:
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE tools_index 
                    SET help_file = ?
                    WHERE id = ?
                ''', (md_rel_path, self.current_tool_data.get('id')))
                conn.commit()
                conn.close()
            
            # 更新 JSON 文件
            json_path = os.path.splitext(md_dest_path)[0] + '.json'
            if os.path.exists(json_path):
                import json
                with open(json_path, 'r', encoding='utf-8') as f:
                    metadata = json.load(f)
                metadata['files']['help'] = md_rel_path
                with open(json_path, 'w', encoding='utf-8') as f:
                    json.dump(metadata, f, indent=2, ensure_ascii=False)
            
            QMessageBox.information(self, "成功", 
                f"帮助文档已更新:\n{md_dest_path}\n\n"
                f"处理了 {len(processed_images)} 张图片到 pnghelp 目录")
            
            # 刷新预览
            if hasattr(self, 'on_selection_changed'):
                self.on_selection_changed(self.tool_list.currentItem(), None)
                
        except Exception as e:
            import traceback
            QMessageBox.critical(self, "错误", f"处理失败:\n{str(e)}\n\n{traceback.format_exc()}")
    
    def _extract_images_from_markdown(self, md_content):
        """从 Markdown 中提取所有图片引用"""
        # 匹配 ![alt](path) 和 <img src="path">
        pattern = r'!\[([^\]]*)\]\(([^)]+)\)|<img\s+[^>]*src=["\']([^"\']*)["\'][^>]*>'
        matches = re.findall(pattern, md_content)
        
        images = []
        for match in matches:
            img_path = match[1] if match[1] else match[2]
            if img_path and not img_path.startswith(('http://', 'https://', 'data:')):
                images.append(img_path)
        
        return images
    
    def _process_images(self, image_refs, source_file, pnghelp_dir, tool_name):
        """处理图片文件：复制、重命名、版本控制"""
        processed_images = {}  # 原路径 -> 新文件名映射
        source_dir = os.path.dirname(source_file)
        
        for img_path in image_refs:
            # 构建完整源路径
            if os.path.isabs(img_path):
                src_img_path = img_path
            else:
                src_img_path = os.path.join(source_dir, img_path)
            
            if not os.path.exists(src_img_path):
                print(f"警告：图片文件不存在: {src_img_path}")
                continue
            
            # 获取文件名和扩展名
            filename = os.path.basename(img_path)
            name, ext = os.path.splitext(filename)
            
            # 检查是否有重名文件
            dest_filename = filename
            dest_path = os.path.join(pnghelp_dir, dest_filename)
            
            if os.path.exists(dest_path):
                # 有重名文件，生成新版本号
                version = 1
                while os.path.exists(dest_path):
                    dest_filename = f"{name}_v{version}{ext}"
                    dest_path = os.path.join(pnghelp_dir, dest_filename)
                    version += 1
            
            # 复制图片到 pnghelp
            shutil.copy2(src_img_path, dest_path)
            
            # 记录映射关系
            processed_images[img_path] = dest_filename
            print(f"已处理图片: {filename} -> {dest_filename}")
        
        return processed_images
    
    def _update_markdown_images(self, md_content, processed_images):
        """更新 Markdown 中的图片路径为 pnghelp 中的文件名"""
        for old_path, new_filename in processed_images.items():
            # 替换 ![alt](path) 格式
            md_content = md_content.replace(f']({old_path})', f']({new_filename})')
            # 替换 <img src="path"> 格式
            md_content = md_content.replace(f'src="{old_path}"', f'src="{new_filename}"')
            md_content = md_content.replace(f"src='{old_path}'", f"src='{new_filename}'")
        
        return md_content
    
    def _sanitize_filename(self, name):
        """清理文件名，移除非法字符"""
        import re
        # 移除 Windows 文件名非法字符
        name = re.sub(r'[<>:"/\\|?*]', '_', name)
        # 移除前后空格
        name = name.strip()
        return name if name else 'help'

    def save_help_md(self):
        """选择 Markdown 文件并处理图片（与 _select_help_file 相同）"""
        self._select_help_file()

    def export_md_to_html(self):
        """导出 Markdown 帮助文档"""
        if not self.current_tool_data:
            QMessageBox.warning(self, "警告", "请先选择一个工具")
            return
        
        help_full_path = self.current_tool_data.get('help_file')
        if not help_full_path:
            QMessageBox.warning(self, "警告", "当前工具没有帮助文档")
            return
        
        # 设置导出路径
        export_path, _ = QFileDialog.getSaveFileName(
            self, "导出 Markdown 文档", "", "Markdown Files (*.md *.markdown)"
        )
        
        if not export_path:
            return
        
        try:
            shutil.copy2(help_full_path, export_path)
            QMessageBox.information(self, "成功", f"Markdown 文档已导出到:\n{export_path}")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"导出失败:\n{str(e)}")

    def copy_md_to_clipboard(self):
        """此功能已禁用"""
        QMessageBox.information(self, "提示", "Markdown 文档复制功能已移除")

    def refresh_help_preview(self):
        """刷新 Markdown 预览"""
        if self.current_tool_data:
            help_file = self.current_tool_data.get('help_file')
            if help_file:
                tools_root = psp.tools_path_get()
                help_full_path = os.path.join(tools_root, help_file.replace('/', os.sep))
                if os.path.exists(help_full_path):
                    from settool import ToolManagerApp
                    if isinstance(self, ToolManagerApp):
                        self.on_selection_changed(self.tool_list.currentItem(), None)
                    return
        
        self.md_preview.setHtml("<h3>无帮助文档</h3>")

    def copy_html_to_clipboard(self):
        """此功能已禁用"""
        QMessageBox.information(self, "提示", "Markdown 文档复制功能已移除")