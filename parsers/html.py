#!/usr/bin/env python

import os
import sys
import getopt
import shutil

def index():
    out = open(dir + '/index.html', 'w')
    print >> out, '''<html>
<head>
    <title>Network-Traffic-Visualisation</title>
</head>

<link rel="stylesheet" href="htmedia/style.css" type="text/css" />
<script src="htmedia/jquery-1.4.2.min.js"></script>
<script src="htmedia/script.js"></script>

<body>
<div id="container">
    <div id="menu" class="trans">
        <ul>
            <li><a href="javascript:change(\'nodes-connections-count\')">Nodes connections (count)</a></li>
            <li><a href="javascript:change(\'nodes-connections-length\')">Nodes connections (length)</a></li>
            <li><a href="javascript:change(\'ip-multicast-circo\')">IP Multicast</a></li>
        </ul>
    </div>
    <div id="zoom" class="trans">
        <img id="zoom_in" src="htmedia/zoom_in.png" />
        <img id="zoom_out" src="htmedia/zoom_out.png" />
    </div>
    <div id="ip_back"></div>
    <div id="ip">
        <div id="ip_stats"></div>
        <div id="ip_svg_div">
            <object id="ip_svg" data=""></object>
        </div>
    </div>
    <div id="svg_frame">
        <object id="svg" data="nodes-connections-count.svg"></object>
    </div>
</div>
</body>
</html>'''
    out.close()

try:
    opts, args = getopt.getopt(sys.argv[1:], '', ['database=', 'dir='])
except getopt.GetoptError, err:
    print str(err)
    sys.exit(1)

for o, a in opts:
    if o in ('--database'):
        database = a
    elif o in ('--dir'):
        dir = a
    else:
        sys.exit(1)

if not os.path.exists(database):
    print >> sys.stderr, 'No such database file.'
    sys.exit(1)

if not os.path.isdir(dir):
    os.mkdir(dir)

if os.path.isdir(dir + '/htmedia'):
    shutil.rmtree(dir + '/htmedia')

if not os.path.isdir(dir + '/htmedia'):
    shutil.copytree('htmedia', dir + '/htmedia')

index()
