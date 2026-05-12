import sys
from PySide6.QtWidgets import QApplication

from window_01 import show_search_window, hide_search_window

# 必须先创建 QApplication
app = QApplication(sys.argv)

# 然后显示窗口
show_search_window()

# 运行事件循环
sys.exit(app.exec())