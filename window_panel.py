import sys
from PySide6.QtWidgets import QApplication

from window_01 import show_search_window, hide_search_window
import nukendoesget


# 必须先创建 QApplication
# app = QApplication(sys.argv)

# 示例：传入初始搜索参数
# show_search_window("Read")              # 搜索名称包含 Read
# show_search_window("C=:Read")            # 搜索类名等于 Read
# show_search_window("L=:blur,color")      # 搜索标签包含 blur 和 color
# show_search_window("N=:Write,P=01")     # 搜索名称和路径

# show_search_window("C=:001")  # 不传参数，正常显示

# 运行事件循环
# sys.exit(app.exec())


ShowMyFun = True

# 运行显示
def run_show():
    global ShowMyFun
    if ShowMyFun == True:
        nodesnameslsit,nodesclasslsit = nukendoesget.getcurnodes()
        if nodesclasslsit == []:
            show_search_window()
        else:
            classlist = "C=:" + ",".join(nodesclasslsit)
            show_search_window(classlist)
        ShowMyFun = False

    else:
        hide_search_window()
        ShowMyFun = True        
