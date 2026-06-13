

try:
    import PySide6.QtCore as QtCore
    import PySide6.QtGui as QtGui
except:
    import PySide2.QtCore as QtCore
    import PySide2.QtGui as QtGui

import nuke
import os

nd = nuke.selectedNodes("Read")
nd2 = nuke.selectedNodes("Write")

nd3 = nd + nd2

if nd3 != []:
    cund = nd3[0]
    fv = cund["file"].value()
    dina = os.path.dirname(fv)+"/"
    
    # 读取系统剪贴板内容
    clipboard = QtGui.QGuiApplication.clipboard()
    clipboard_content = clipboard.text()


    # 写入系统剪贴板内容
    new_text = dina
    clipboard.setText(new_text)