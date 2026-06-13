import nuke
nds = nuke.selectedNodes()
for i in nds:
    nd = i
    if nd.Class() == "Merge2":
        nd["operation"].setValue("max")