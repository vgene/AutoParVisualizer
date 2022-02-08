import os
import json
from dash import html

def getStatusLayout(resultProvider):
    path = os.path.join(resultProvider._path)

    def getLatestDir(path):
        dirs = [d for d in os.listdir(path) if os.path.isdir(os.path.join(path, d))]
        if len(dirs) == 0:
            return None
        return sorted(dirs)[-1]

    latestDir = getLatestDir(path) 
    if not latestDir:
        return [html.Div([html.H1("No valid status file")])]

    statusJson = os.path.join(path, latestDir, "status.json")
    with open(statusJson, 'r') as fd:
        status = json.load(fd)
 
    passes = ["Loop", "LAMP", "SLAMP"] #, "SpecPriv", "HeaderPhi", "Experiment"]

    tb = [html.Tr([html.Th(c) for c in (["bmark"] + passes)])]
    for bmark, st in status.items():
        td = [bmark]

        for p in passes:
            if p not in st:
                td.append("-")
            else:
                if st[p] == True:
                    td.append("Y")
                else:
                    td.append("X")
        td = [html.Td(c) for c in td]
        tb.append(html.Tr(td))

    return [html.Div([
        html.H1("Status"),
        html.Table(tb)])]

