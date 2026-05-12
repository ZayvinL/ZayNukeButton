import settool
import nukescripts

nukepgetsear3 = nukescripts.panels.registerWidgetAsPanel("settool.ToolManagerApp","安装工具","QZDFlixuaiobo.settool.ToolManagerApp_ver30",True)

def run_show_funa():
    pane = nuke.getPaneFor("Properties.1")
    nukepgetsear3.addToPane(pane)