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
元数据编辑器 - 负责工具名称、标签、匹配类的编辑和同步
"""

import sqlite3
import json
import os
# from PySide6.QtWidgets import QMessageBox
# from PySide6.QtCore import Qt
from qt_imports import QMessageBox, QVBoxLayout, QLabel, Qt, QtWidgets


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

    def move_tool(self):
        """移动工具到其他目录，同步更新所有路径引用"""
        if not self.current_tool_data:
            QMessageBox.warning(None, "警告", "请先选择一个工具")
            return False

        import paths_setup as psp

        tool_id = self.current_tool_data.get('id')
        tool_name = self.current_tool_data.get('name', '')
        main_file = self.current_tool_data.get('main_file', '')

        if not main_file:
            QMessageBox.critical(None, "错误", "工具没有主文件路径")
            return False

        tools_root = psp.tools_path_get()
        old_main_rel = main_file
        old_dir = os.path.dirname(old_main_rel)
        old_filename = os.path.basename(old_main_rel)
        base_name, ext = os.path.splitext(old_filename)

        old_full_path = os.path.join(tools_root, old_main_rel.replace('/', os.sep))
        if not os.path.exists(old_full_path):
            QMessageBox.critical(None, "错误", f"原文件不存在:\n{old_full_path}")
            return False

        # --- 弹出目录选择对话框 ---
        target_dir = self._show_directory_picker(tools_root, old_dir)
        if not target_dir:
            return False

        if target_dir == old_dir:
            QMessageBox.information(None, "提示", "目标目录与当前目录相同，无需移动")
            return False

        new_main_rel = os.path.join(target_dir, old_filename).replace(os.sep, '/')
        new_full_path = os.path.join(tools_root, target_dir, old_filename)

        if os.path.exists(new_full_path):
            reply = QMessageBox.question(None, "文件冲突",
                f"目标位置已存在同名文件:\n{new_full_path}\n\n是否覆盖？",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            if reply != QMessageBox.StandardButton.Yes:
                return False

        try:
            os.makedirs(os.path.dirname(new_full_path), exist_ok=True)

            # 1. 移动主文件
            os.rename(old_full_path, new_full_path)

            # 2. 移动关联文件 (.json, .png, .md)
            old_base = os.path.splitext(old_full_path)[0]
            new_base = os.path.splitext(new_full_path)[0]
            new_json_rel = None
            new_icon_rel = None

            for suffix in ['.json', '.png', '.md', '.markdown']:
                old_assoc = old_base + suffix
                if os.path.exists(old_assoc):
                    new_assoc = new_base + suffix
                    os.rename(old_assoc, new_assoc)
                    if suffix == '.json':
                        new_json_rel = os.path.relpath(new_assoc, tools_root).replace(os.sep, '/')
                    elif suffix == '.png':
                        new_icon_rel = os.path.relpath(new_assoc, tools_root).replace(os.sep, '/')

            # 3. 更新 JSON 文件内的路径
            if new_json_rel:
                json_full_path = os.path.join(tools_root, new_json_rel.replace('/', os.sep))
                if os.path.exists(json_full_path):
                    with open(json_full_path, 'r', encoding='utf-8') as f:
                        metadata = json.load(f)

                    metadata['files']['main'] = new_main_rel

                    # 修正 icon 路径（如果还在旧目录下）
                    old_icon = metadata.get('files', {}).get('icon')
                    if old_icon and old_icon.startswith(old_dir + '/'):
                        metadata['files']['icon'] = os.path.join(
                            target_dir, os.path.basename(old_icon)).replace(os.sep, '/')

                    # 修正 help 路径（如果还在旧目录下）
                    old_help = metadata.get('files', {}).get('help')
                    if old_help and old_help.startswith(old_dir + '/'):
                        metadata['files']['help'] = os.path.join(
                            target_dir, os.path.basename(old_help)).replace(os.sep, '/')

                    with open(json_full_path, 'w', encoding='utf-8') as f:
                        json.dump(metadata, f, indent=2, ensure_ascii=False)

            # 4. 更新 SQLite
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE tools_index
                SET main_file = ?, icon_file = ?, category = ?
                WHERE id = ?
            ''', (new_main_rel, new_icon_rel, target_dir, tool_id))
            conn.commit()
            conn.close()

            # 5. 更新内存数据
            self.current_tool_data['main_file'] = new_main_rel
            self.current_tool_data['category'] = target_dir
            if new_icon_rel:
                self.current_tool_data['icon_file'] = new_icon_rel

            for tool in self.all_tools:
                if tool.get('id') == tool_id:
                    tool['main_file'] = new_main_rel
                    tool['category'] = target_dir
                    if new_icon_rel:
                        tool['icon_file'] = new_icon_rel
                    break

            # 6. 设置共享权限
            import QuanXianSet as quanxian
            quanxian.set_file_permissions(new_full_path)
            if new_json_rel:
                quanxian.set_file_permissions(json_full_path)

            QMessageBox.information(None, "成功",
                f"工具已移动到:\n{target_dir}/\n\n路径引用已全部更新")
            return True

        except Exception as e:
            QMessageBox.critical(None, "错误", f"移动工具失败:\n{str(e)}")
            return False

    def _show_directory_picker(self, tools_root, current_dir):
        """弹出目录树选择对话框，返回相对于 tools_root 的路径"""

        def _populate_tree(parent_item, dir_path):
            """递归填充目录树，排除含 # 的目录"""
            try:
                entries = sorted(os.listdir(dir_path))
            except OSError:
                return
            for name in entries:
                if '#' in name:
                    continue
                full = os.path.join(dir_path, name)
                if os.path.isdir(full):
                    rel = os.path.relpath(full, tools_root).replace(os.sep, '/')
                    item = QtWidgets.QTreeWidgetItem(parent_item)
                    item.setText(0, name)
                    item.setData(0, Qt.ItemDataRole.UserRole, rel)
                    _populate_tree(item, full)

        dlg = QtWidgets.QDialog(None)
        dlg.setWindowTitle("选择目标目录")
        dlg.setMinimumSize(420, 500)
        dlg.resize(450, 550)

        layout = QVBoxLayout(dlg)

        info_lbl = QLabel(f"当前分类: <b>{current_dir if current_dir else '(根目录)'}</b>")
        layout.addWidget(info_lbl)

        tree = QtWidgets.QTreeWidget()
        tree.setHeaderHidden(True)
        tree.setIndentation(16)

        # 根节点 (tools/)
        root_item = QtWidgets.QTreeWidgetItem(tree)
        root_item.setText(0, "tools/")
        root_item.setData(0, Qt.ItemDataRole.UserRole, "")
        _populate_tree(root_item, tools_root)

        tree.expandAll()

        # 预选当前目录
        def _select_current(item):
            for i in range(item.childCount()):
                child = item.child(i)
                if child.data(0, Qt.ItemDataRole.UserRole) == current_dir:
                    tree.setCurrentItem(child)
                    return
                _select_current(child)

        _select_current(tree.invisibleRootItem())

        layout.addWidget(tree)

        # 预览标签
        preview_lbl = QLabel("")
        preview_lbl.setStyleSheet("color: #aaa; font-size: 11px; padding: 4px;")
        layout.addWidget(preview_lbl)

        def _on_selection():
            cur = tree.currentItem()
            if cur:
                sel = cur.data(0, Qt.ItemDataRole.UserRole)
                preview_lbl.setText(f"目标: {sel + '/' if sel else ''}{{工具名}}")
            else:
                preview_lbl.setText("")

        # 选中后才启用确认按钮，同时更新预览
        def _on_current_changed(cur, _prev):
            btn_ok.setEnabled(cur is not None)
            _on_selection()

        tree.currentItemChanged.connect(_on_current_changed)

        # 按钮
        btn_box = QtWidgets.QDialogButtonBox()
        btn_ok = btn_box.addButton(QtWidgets.QDialogButtonBox.StandardButton.Ok)
        btn_cancel = btn_box.addButton(QtWidgets.QDialogButtonBox.StandardButton.Cancel)
        btn_ok.setText("确认移动")
        btn_cancel.setText("取消")
        btn_ok.setEnabled(False)

        def _on_ok():
            cur = tree.currentItem()
            if cur:
                dlg._selected_dir = cur.data(0, Qt.ItemDataRole.UserRole)
                dlg.accept()

        btn_box.accepted.connect(_on_ok)
        btn_box.rejected.connect(dlg.reject)
        layout.addWidget(btn_box)

        dlg._selected_dir = None
        dlg.exec()

        return dlg._selected_dir

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
