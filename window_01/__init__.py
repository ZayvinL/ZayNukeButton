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
搜索型工具窗口模块
支持多条件组合搜索，动态加载显示
"""

from window_01.config import _get_user_db_path, _get_toolbox_path
from window_01.db import FastDBQuery, IconCache, SmartCache
from window_01.widgets import ToolButton
from window_01.search_window import SearchToolWindow

# ============================================================================
# 🎯 对外接口
# ============================================================================

_search_window_instance = None

def init_search_window(initial_search_text="", nodesnames_list=None):
    """初始化搜索窗口

    Args:
        initial_search_text: 初始搜索文本
        nodesnames_list: 当前选中节点名称列表
    """
    global _search_window_instance

    # 如果实例已存在，重新创建（确保代码更改生效）
    if _search_window_instance is not None:
        _search_window_instance = None

    toolbox_path = _get_toolbox_path()
    _search_window_instance = SearchToolWindow(toolbox_path, initial_search_text=initial_search_text)
    if nodesnames_list is not None:
        _search_window_instance.nodesnames_list = nodesnames_list

    return _search_window_instance

def is_window_visible():
    """检查窗口是否可见"""
    if _search_window_instance:
        return getattr(_search_window_instance, 'is_visible', False)
    return False

def set_show_at_mouse(show_p: bool):
    """设置是否在显示时重新定位到鼠标位置
    
    Args:
        show_p: True=每次显示时定位到鼠标位置，False=保持上次位置
    """
    if _search_window_instance:
        _search_window_instance.set_show_at_mouse(show_p)

def show_search_window(initial_search_text="", nodesnames_list=None):
    """显示搜索窗口"""
    if _search_window_instance is None:
        init_search_window(initial_search_text, nodesnames_list)
    else:
        # 每次显示时都更新搜索文本（用户可能已手动清空）
        _search_window_instance.initial_search_text = initial_search_text
        if initial_search_text:
            _search_window_instance.search_input.setText(initial_search_text)
        if nodesnames_list is not None:
            _search_window_instance.nodesnames_list = nodesnames_list
        _search_window_instance._perform_search()

    _search_window_instance.show()
    return _search_window_instance

def hide_search_window():
    """隐藏搜索窗口"""
    global _search_window_instance
    if _search_window_instance:
        _search_window_instance.hide()

def get_window_instance():
    """获取当前窗口实例（用于连接信号）"""
    return _search_window_instance

# 测试入口
if __name__ == "__main__":
    import sys
    # from PySide6.QtWidgets import QApplication
    from qt_imports import QApplication
    
    app = QApplication(sys.argv)
    show_search_window()
    sys.exit(app.exec())