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

def init_search_window(initial_search_text=""):
    """初始化搜索窗口
    
    Args:
        initial_search_text: 初始搜索文本
    """
    global _search_window_instance
    
    # 如果实例已存在，重新创建（确保代码更改生效）
    if _search_window_instance is not None:
        _search_window_instance = None
    
    toolbox_path = _get_toolbox_path()
    _search_window_instance = SearchToolWindow(toolbox_path, initial_search_text=initial_search_text)
    
    return _search_window_instance

def show_search_window(initial_search_text=""):
    """显示搜索窗口
    
    Args:
        initial_search_text: 初始搜索文本，例如：
            - "Read" - 搜索名称包含 Read 的工具
            - "C=Read" - 搜索类名等于 Read 的工具
            - "L=blur" - 搜索标签包含 blur 的工具
            - "P=color" - 搜索路径包含 color 的工具
    """
    window = init_search_window(initial_search_text)
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