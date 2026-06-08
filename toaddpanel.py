import settool
import nukescripts
import nuke

nukepgetsear3 = nukescripts.panels.registerWidgetAsPanel("settool.ToolManagerApp","ZayButtonInstall","QZDFlixuaiobo.settool.ToolManagerApp_ver30",True)

def run_show_funa():
    pane = nuke.getPaneFor("Properties.1")
    nukepgetsear3.addToPane(pane)