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

"""
帮助文档查看器 - 负责 Markdown 帮助文档的加载和显示
"""

import os
import re
import urllib.parse


class HelpViewer:
    """帮助文档查看器"""
    
    def __init__(self, widgets):
        self.widgets = widgets
    
    def load_help_document(self, help_file):
        """加载 Markdown 帮助文档"""
        if not help_file:
            self.widgets['md_preview'].setHtml("<h3>此工具没有帮助文档</h3>")
            self.widgets['lbl_md_status'].setText("无帮助文档")
            return
        
        try:
            import paths_setup as psp
            
            tools_root = psp.tools_path_get()
            help_full = os.path.join(tools_root, help_file.replace('/', os.sep))
            
            if not os.path.exists(help_full):
                self.widgets['md_preview'].setHtml("<h3>未找到帮助文档</h3>")
                self.widgets['lbl_md_status'].setText("帮助文档不存在")
                return
            
            # 读取 Markdown 文件内容
            with open(help_full, 'r', encoding='utf-8') as f:
                md_content = f.read()
            
            # 获取 pnghelp 文件夹路径作为图片资源目录
            pnghelp_dir = os.path.join(os.path.dirname(__file__), 'pnghelp')
            
            if not os.path.exists(pnghelp_dir):
                print(f"警告: pnghelp 目录不存在: {pnghelp_dir}")
                pnghelp_dir = os.path.dirname(__file__)
            
            # Markdown 转换为 HTML
            try:
                import markdown
                html_content = markdown.markdown(
                    md_content,
                    extensions=['tables', 'fenced_code', 'toc']
                )
            except ImportError:
                html_content = self._simple_markdown_to_html(md_content)
            
            # 将 HTML 中的图片路径转换为 pnghelp 的绝对路径
            def replace_image_path(match):
                src = match.group(1)
                if not src:
                    return match.group(0)
                
                if src.startswith(('http://', 'https://', 'data:')):
                    return match.group(0)
                
                elif src.startswith('file://'):
                    return match.group(0)
                
                elif os.path.isabs(src):
                    if not os.path.exists(src):
                        print(f"警告: 图片文件不存在: {src}")
                        return f'<img src="" alt="图片不存在">'
                    img_url = urllib.parse.quote(src.replace('\\', '/'), safe=':/')
                    return f'<img src="file:///{img_url}" alt="{os.path.basename(src)}">'
                
                else:
                    img_full_path = os.path.join(pnghelp_dir, src)
                    
                    if not os.path.exists(img_full_path):
                        print(f"警告: 图片文件不存在: {img_full_path}")
                        return f'<img src="" alt="图片不存在: {src}">'
                    
                    img_url = urllib.parse.quote(img_full_path.replace('\\', '/'), safe=':/')
                    return f'<img src="file:///{img_url}" alt="{src}">'
            
            html_content = re.sub(
                r'<img\s+[^>]*src=["\']([^"\']*)["\'][^>]*>',
                replace_image_path,
                html_content
            )
            
            self.widgets['md_preview'].setHtml(html_content)
            self.widgets['lbl_md_status'].setText(f"已加载: {os.path.basename(help_full)}")
            
        except Exception as e:
            print(f"加载帮助文档失败: {e}")
            import traceback
            traceback.print_exc()
            self.widgets['md_preview'].setHtml("<h3>帮助文档加载失败</h3>")
    
    def _simple_markdown_to_html(self, markdown_text):
        """简单的 Markdown 转 HTML 转换"""
        import re
        
        html = re.sub(r'!\[([^\]]*)\]\(([^)]+)\)', r'<img src="\2" alt="\1" style="max-width:100%; height:auto;">', markdown_text)
        html = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'<a href="\2">\1</a>', html)
        html = re.sub(r'^### (.+)$', r'<h3>\1</h3>', html, flags=re.MULTILINE)
        html = re.sub(r'^## (.+)$', r'<h2>\1</h2>', html, flags=re.MULTILINE)
        html = re.sub(r'^# (.+)$', r'<h1>\1</h1>', html, flags=re.MULTILINE)
        html = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', html)
        html = re.sub(r'\*(.+?)\*', r'<em>\1</em>', html)
        html = re.sub(r'`([^`]+)`', r'<code>\1</code>', html)
        html = re.sub(r'^[-*+] (.+)$', r'<li>\1</li>', html, flags=re.MULTILINE)
        html = re.sub(r'((?:<li>.*</li>\n?)+)', r'<ul>\1</ul>', html)
        html = re.sub(r'^\d+\. (.+)$', r'<li>\1</li>', html, flags=re.MULTILINE)
        
        paragraphs = re.split(r'\n\n+', html)
        processed_paragraphs = []
        for p in paragraphs:
            p = p.strip()
            if p and not p.startswith('<'):
                p = f'<p>{p}</p>'
            processed_paragraphs.append(p)
        html = '\n'.join(processed_paragraphs)
        
        return html