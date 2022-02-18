#!/usr/bin/env python
# coding: utf-8

import os
import json
import itertools
import plotly.graph_objects as go

def openBmarkFileFiles(directory):
    with open(os.path.join(directory, "coverage.json"), 'r') as fd:
        coverages = json.load(fd)

    with open(os.path.join(directory, "sccs.json"), 'r') as fd:
        sccs = json.load(fd)

    with open(os.path.join(directory, "compatible.json"), 'r') as fd:
        compatibles = json.load(fd)

    return coverages, sccs, compatibles


# return the loop indexes for loops that have largest S-SCC lower than threshold
def filterGoodLoops(sccs, threshold):
    idxs = []
    for idx, triplet in enumerate(sccs):
        if triplet[0] <= threshold:
            idxs.append(idx)
    return idxs


def isCompatible(compatible, s):
    if len(compatible) > 1 and type(compatible[0]) == list:
        compatible = [tuple(i) for i in compatible]
    
    if len(s) < 2:
        return True

    for s in list(itertools.combinations(s, 2)):
        if s not in compatible:
            return False
    return True

# in the loops allowed, find a set of loops with max coverage
# and compatible with each other
def findMaxCoverage(coverages, compatible, idxs):
    # TODO: a max clique problem: ebk algorithm
    maxCoverage = 0
    curLen = len(idxs)
    if curLen == 0:
        return 0

    while curLen > 0:
        for s in list(itertools.combinations(idxs, curLen)):
            if (isCompatible(compatible, s)):
                curCoverage = 0
                for i in s:
                    curCoverage += coverages[i]
                maxCoverage = max(maxCoverage, curCoverage)
        # try smaller set
        curLen -= 1
    
    return maxCoverage


def getCdfs(bmark_coverage, bmark_sccs, bmark_compatible):
    bmarkCdf = {}
    for bmark in sorted(bmark_sccs):
        sccs = bmark_sccs[bmark]
        compatible = bmark_compatible[bmark.replace("-ignorefn", "")]
        coverages = bmark_coverage[bmark.replace("-ignorefn", "")]
        
        coverageCdf = []
        for thres in range(101):
            idxs = filterGoodLoops(sccs, thres)
            maxCoverage = findMaxCoverage(coverages, compatible, idxs)
            coverageCdf.append(maxCoverage)
        bmarkCdf[bmark] = coverageCdf

    return bmarkCdf

# # Plot Explanation
# 
# - Each threshold correspond to the maximum coverage of loops with the
#   largest sequential SCC smaller than the threshold.
#     
#     For example, when **threshold=0%**, only **DOALL** loops are selected.
#     When **threshold=100%**, **all** loops are selected.
# 
# - Loops have to be more than 10% of the program execution and on
#   average 8 iteration/invocation.
#   
# - When multiple loops meet threshold requirement, a max clique algorithm
#   is run to select the max coverage.
def getCdfFig(directory, onlyIgnoreFn=False, onlyNotIgnoreFn=False):

    coverages, sccs, compatibles = openBmarkFileFiles(directory)
    bmarkCdf = getCdfs(coverages, sccs, compatibles)

    fig = go.Figure()

    bmarks = []
    for bmark in bmarkCdf:
        if onlyIgnoreFn:
            if "ignorefn" not in bmark:
                continue
        if onlyNotIgnoreFn:
            if "ignorefn" in bmark:
                continue
        bmarks.append(bmark)

    for bmark in bmarks:
        fig.add_trace(go.Scatter(x=list(range(101)), y=bmarkCdf[bmark],
                                 mode='lines',
                                 name=bmark))

    fig.update_layout(title="Threshold-Coverage:",
                      xaxis_title='Threshold of Largest Sequential SCC (%)',
                      yaxis_title='Coverage of Whole Program Execution Time(%)')

    bar_fig= go.Figure()
    bar_fig.add_trace(go.Bar(
        x=bmarks,
        y=[bmarkCdf[bmark][0] for bmark in bmarks],
        name='Largest SCC<=0 (DOALL)',
        marker_color='indianred'
    ))
    bar_fig.add_trace(go.Bar(
        x=bmarks,
        y=[bmarkCdf[bmark][100] for bmark in bmarks],
        name='Largest SCC <=100 (All selected loops)',
        marker_color='lightsalmon'
    ))

    return fig, bar_fig


