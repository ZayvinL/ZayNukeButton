#Make : Mr-Cheese
#QQ : 971346144

import nuke
import os


Toast_show



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