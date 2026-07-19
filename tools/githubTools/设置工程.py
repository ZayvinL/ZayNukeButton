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

import nuke
import os


import Toast_show



nd = nuke.selectedNodes("Read")
if nd != []:
    nd = nd[0]
    try:
        rate = float(nd.metadata("input/frame_rate"))
    except:
        rate = 24
    frame_a = nd.firstFrame()
    frame_b = nd.lastFrame()
    width_gt = nd.metadata("input/width")
    height_gt = nd.metadata("input/height")
    fname = nd.format().name()

    p = nuke.Panel("set scripts")
    p.addSingleLineInput("rate:",rate)
    p.addSingleLineInput("firstFrame:",frame_a)
    p.addSingleLineInput("lastFrame:",frame_b)
    p.addSingleLineInput("width:",width_gt)
    p.addSingleLineInput("height:",height_gt)
    ret = p.show()

    if ret:       
        fpsgt = p.value("rate:")
        frgt = p.value("firstFrame:")
        lrgt = p.value("lastFrame:")
        nuke.root()["fps"].setValue(float(fpsgt))
        nuke.root()["first_frame"].setValue(int(frgt))
        nuke.root()["last_frame"].setValue(int(lrgt))
        nuke.root()["lock_range"].setValue(True)
        
        ck = True
        # if ck:
        ft = "Setformat %s" %(str(p.value("width:"))+" x "+str(p.value("height:")))
        newgt = "%s %s %s %s" %(str(p.value("width:")),str(p.value("height:")),1,ft)
        for i in range(0,len(nuke.formats())):
            curfor = nuke.formats()[i]
            if int(curfor.width()) == int(p.value("width:")):
                if int(curfor.height()) == int(p.value("height:")):
                    nnam = nuke.root()["format"].name()
                    if newgt == nnam:
                        nuke.root()["format"].setValue(curfor)
                        ck = False
        if ck:
            nuke.addFormat(newgt)
            nuke.root()["format"].setValue(ft)
        
        Toast_show.B_Toast("提示信息",f"工程已经设置完成! \n工程尺寸是 {ft}\n 测试外部修改代码!!!!!!!!!!!!!!!!!!!")