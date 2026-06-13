# -*- coding: UTF-8 -*-
import nuke

def getcurnodes():
    global selectedndoes_nodesnameslsit_get
    nodes = nuke.selectedNodes()
    nodesnameslsit = [i.fullName() for i in nodes]
    nodesclasslsit = sorted(set([i.Class() for i in nodes]))
    print(nodesnameslsit,nodesclasslsit)
    return nodesnameslsit,nodesclasslsit