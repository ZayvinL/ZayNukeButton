
import nuke
import os
import codecs
import importlib
import nuke



import window_panel 
import toaddpanel
import settool
import export_panel




# ---------------------------------------------------------
#toaddpanel.run_show_funa


def make_menu():  
    bar = nuke.menu('Nodes')
    toolbar = bar.addMenu("Z")
    toolbar.addCommand('Button/ZayNukeButton', window_panel.run_show,"ALT+W",shortcutContext=2)
    toolbar.addCommand('Button/Export', export_panel.run_show)
    toolbar.addCommand('Button/ZayButtonInstall', toaddpanel.run_show_funa)
    toolbar.addCommand('Button/Refresh hotkey', reloadhotkey)


    

def reloadhotkey():
    try:
        import window_panel 
        importlib.reload(window_panel)
        make_menu()
    except:
        print("Error: Failed to reload hotkey")

make_menu()
# ---------------------------------------------------------



def execute_tool(s=None,nodenamelist=[]):
    try:
        (root, ext) = os.path.splitext(s)
        if ext == ".py":
            if not os.path.exists(s):
                print("Not find this tool,please refresh install\n%s"%s)
                
            # exec(compile(open(s, "rb").read(), s, 'exec'))
            # nodesnameslsit,nodesclasslsit = nukendoesget.getcurnodes()
            try:
                with open(s, 'r', encoding='utf-8') as f:
                    mpy = f.read()                    
            except:
                f = codecs.open(s,'r',encoding='utf-8')
                mpy = f.read()
                f.close() 
            
            str003 = '\nselected_nodes_list = list({})\n'.format(nodenamelist)
            
            mpy = str003 + mpy
            sp = {}
            exec(mpy, globals(), globals())
            
        elif s.endswith(".nk"):
            nuke.nodePaste(s)
        else:
            nuke.tcl('source',s)
    except:
        pass

try:
    nuke.execute_tool = execute_tool
except:
    pass
