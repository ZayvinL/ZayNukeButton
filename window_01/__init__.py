# c:/Users/liucx/.nuke/MyButton/window_01/__init__.py
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

def init_search_window():
    """初始化搜索窗口"""
    global _search_window_instance
    
    if _search_window_instance is None:
        toolbox_path = _get_toolbox_path()
        _search_window_instance = SearchToolWindow(toolbox_path)
    
    return _search_window_instance

def show_search_window():
    """显示搜索窗口"""
    window = init_search_window()
    window.show()

def hide_search_window():
    """隐藏搜索窗口"""
    global _search_window_instance
    if _search_window_instance:
        _search_window_instance.hide()

# 测试入口
if __name__ == "__main__":
    import sys
    from PySide6.QtWidgets import QApplication
    
    app = QApplication(sys.argv)
    show_search_window()
    sys.exit(app.exec())