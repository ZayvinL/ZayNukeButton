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