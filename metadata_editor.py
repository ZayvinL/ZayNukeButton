
"""
元数据编辑器 - 负责工具名称、标签、匹配类的编辑和同步
"""

import sqlite3
import json
import os
# from PySide6.QtWidgets import QMessageBox
# from PySide6.QtCore import Qt
from qt_imports import QMessageBox, Qt


class MetadataEditor:
    """元数据编辑器"""

    def __init__(self, db_path, current_tool_data, widgets, all_tools):
        self.db_path = db_path
        self.current_tool_data = current_tool_data
        self.widgets = widgets
        self.all_tools = all_tools

    def rename_tool(self):
        """修改工具名称并同步到所有位置"""
        if not self.current_tool_data:
            QMessageBox.warning(None, "警告", "请先选择一个工具")
            return False

        new_name = self.widgets['edit_tool_name'].text().strip()
        if not new_name:
            QMessageBox.warning(None, "警告", "请输入新的工具名称")
            return False

        import paths_setup as psp

        tool_id = self.current_tool_data.get('id')
        old_name = self.current_tool_data.get('name', '')
        main_file = self.current_tool_data.get('main_file', '')

        if not main_file:
            QMessageBox.critical(None, "错误", "工具没有主文件路径")
            return False

        tools_root = psp.tools_path_get()
        old_full_path = os.path.join(tools_root, main_file.replace('/', os.sep))

        if not os.path.exists(old_full_path):
            QMessageBox.critical(None, "错误", f"原文件不存在:\n{old_full_path}")
            return False

        base_name, ext = os.path.splitext(old_full_path)
        new_file_name = new_name + ext
        new_full_path = os.path.join(os.path.dirname(old_full_path), new_file_name)

        if old_full_path == new_full_path:
            QMessageBox.information(None, "提示", "文件名没有变化")
            return False

        try:
            # 1. 重命名主文件
            os.rename(old_full_path, new_full_path)
            print(f"重命名主文件: {old_full_path} -> {new_full_path}")

            # 2. 重命名关联文件
            associated_files = []
            new_icon_rel = None
            for suffix in ['.json', '.png', '.md', '.markdown']:
                old_assoc = base_name + suffix
                if os.path.exists(old_assoc):
                    new_assoc = os.path.join(os.path.dirname(old_full_path), new_name + suffix)
                    try:
                        os.rename(old_assoc, new_assoc)
                        associated_files.append(new_assoc)
                        if suffix == '.png':
                            new_icon_rel = os.path.relpath(new_assoc, tools_root).replace(os.sep, '/')
                        print(f"重命名关联文件: {old_assoc} -> {new_assoc}")
                    except Exception as e:
                        print(f"重命名关联文件失败 {old_assoc}: {e}")

            # 3. 更新数据库
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
                SET name = ?, main_file = ?, icon_file = ?
                WHERE id = ?
            ''', (new_name, new_main_rel, new_icon_rel, tool_id))
            conn.commit()
            conn.close()

            # 4. 更新 JSON 文件
            if new_json_rel:
                json_path = os.path.join(tools_root, new_json_rel.replace('/', os.sep))
                if os.path.exists(json_path):
                    with open(json_path, 'r', encoding='utf-8') as f:
                        metadata = json.load(f)

                    metadata['name'] = new_name
                    metadata['files']['main'] = new_main_rel
                    if new_icon_rel:
                        metadata['files']['icon'] = new_icon_rel

                    with open(json_path, 'w', encoding='utf-8') as f:
                        json.dump(metadata, f, indent=2, ensure_ascii=False)

            # 5. 更新内存中的数据
            self.current_tool_data['name'] = new_name
            self.current_tool_data['main_file'] = new_main_rel
            if new_icon_rel:
                self.current_tool_data['icon_file'] = new_icon_rel

            # 6. 更新 all_tools 列表中的对应项
            for tool in self.all_tools:
                if tool.get('id') == tool_id:
                    tool['name'] = new_name
                    tool['main_file'] = new_main_rel
                    if new_icon_rel:
                        tool['icon_file'] = new_icon_rel
                    break

            QMessageBox.information(None, "成功", f"工具已重命名为:\n{new_name}")
            return True

        except Exception as e:
            QMessageBox.critical(None, "错误", f"更新元数据失败:\n{str(e)}")
            return False

    def save_tag(self, on_refresh_callback):
        """保存标签并同步更新"""
        if not self.current_tool_data:
            QMessageBox.warning(None, "警告", "请先选择一个工具")
            return False

        new_tag = self.widgets['edit_tag'].text().strip()
        tool_id = self.current_tool_data.get('id')

        try:
            import paths_setup as psp

            # 1. 更新数据库
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE tools_index
                SET tag = ?
                WHERE id = ?
            ''', (new_tag, tool_id))
            conn.commit()
            conn.close()

            # 2. 更新 JSON 文件
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

            # 3. 更新内存中的数据
            self.current_tool_data['tag'] = new_tag

            # 4. 更新 all_tools 列表中的对应项
            for tool in self.all_tools:
                if tool.get('id') == tool_id:
                    tool['tag'] = new_tag
                    break

            # 5. 刷新列表和显示
            if on_refresh_callback:
                on_refresh_callback()

            QMessageBox.information(None, "成功", f"标签已保存:\n{new_tag if new_tag else '无'}")
            return True

        except Exception as e:
            QMessageBox.critical(None, "错误", f"保存标签失败:\n{str(e)}")
            return False

    def save_matchclass(self, on_refresh_callback):
        """保存匹配类并同步更新"""
        if not self.current_tool_data:
            QMessageBox.warning(None, "警告", "请先选择一个工具")
            return False

        matchclass_text = self.widgets['edit_matchclass'].text().strip()
        tool_id = self.current_tool_data.get('id')

        matchclass_list = [item.strip() for item in matchclass_text.split(',') if item.strip()] if matchclass_text else []

        try:
            import paths_setup as psp

            # 1. 更新数据库
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

            # 2. 更新 JSON 文件
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

            # 3. 更新内存中的数据
            self.current_tool_data['matchClass'] = matchclass_list

            # 4. 更新 all_tools 列表中的对应项
            for tool in self.all_tools:
                if tool.get('id') == tool_id:
                    tool['matchClass'] = matchclass_list
                    break

            # 5. 刷新列表和显示
            if on_refresh_callback:
                on_refresh_callback()

            display_text = ', '.join(matchclass_list) if matchclass_list else '无'
            QMessageBox.information(None, "成功", f"匹配类已保存:\n{display_text}")
            return True

        except Exception as e:
            QMessageBox.critical(None, "错误", f"保存匹配类失败:\n{str(e)}")
            return False
