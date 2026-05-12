
import nuke
import os
import codecs

# try:
    # ---------------------------------
import hotkeysetup as hkst
# ---------------------------------
hkst.menusetup() # menu set here
# except:
    # pass
    
    
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
