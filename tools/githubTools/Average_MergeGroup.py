import nuke
nds = selected_nodes_list
for i in nds:
    print(i)
    nd = nuke.toNode(i)
    if nd.Class() == "Merge2":
        nd["operation"].setValue("average")