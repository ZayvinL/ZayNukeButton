import sys
from PySide6.QtWidgets import QApplication

from window_01 import set_show_at_mouse,show_search_window, hide_search_window, get_window_instance, is_window_visible
import nukendoesget



# 全局状态
ShowMyFun = True
_window_signal_connected = False  # 标记信号是否已连接

def on_window_hidden():
    """窗口隐藏时的回调函数"""
    global ShowMyFun
    ShowMyFun = True
    print("窗口已隐藏，ShowMyFun 已更新为:", ShowMyFun)

def run_show():
    global ShowMyFun, _window_signal_connected
    
    if ShowMyFun == True:
        nodesnameslsit, nodesclasslsit = nukendoesget.getcurnodes()
        # 启用：每次显示时定位到鼠标位置
        set_show_at_mouse(True)
        if nodesclasslsit == []:
            nodesclasslsit.append("NoSelectedNode")
            nodesclasslsit.append("AnyTime")
            clist = ["C=:" + i for i in nodesclasslsit]
            classlist = ",".join(clist)

            
            show_search_window(classlist)
        else:
            nodesclasslsit.append("AnySelectedNode")
            nodesclasslsit.append("AnyTime")
            clist = ["C=:" + i for i in nodesclasslsit]
            classlist = ",".join(clist)
            show_search_window(classlist)
        
        # 首次连接信号（只连接一次）
        if not _window_signal_connected:
            window = get_window_instance()
            if window:
                window.window_hidden.connect(on_window_hidden)
                _window_signal_connected = True
                print("已连接窗口隐藏信号")
        
        ShowMyFun = False
    else:
        hide_search_window()
        # ShowMyFun 会在 hideEvent 中自动更新为 True
        
    print("ShowMyFun:", ShowMyFun)
