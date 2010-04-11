#!/usr/bin/env python

def svg(filename):
    print >> out, '<embed src="' + filename + '.svg" height="90%" />'   # FIXME: Graphs scaling

def style():
    print >> out, '<style>'
    print >> out, '\tdiv#container { text-align: center; }'
    print >> out, '\tul { padding: 0px; margin: 0px; list-style-type: none; }'
    print >> out, '\tli { padding: 0px 10px;  display: inline; }'
    print >> out, '</style>'

def menu():
    print >> out, '<ul>'
    print >> out, '\t<li><a href="index.html">Nodes connections</a></li>'
    print >> out, '\t<li><a href="multicast.html">IP Multicast</a></li>'
    print >> out, '</ul>'
    print >> out, '<hr>'

def header(title):
    print >> out, '<html>'
    print >> out, '<head><title>%s</title></head>' % title
    style()
    print >> out, '<body>'
    print >> out, '<div id="container">'
    menu()

def nodes_connections():
    svg('nodes-connections')

def multicast():
    svg('ip-multicast-neato')   # FIXME: Choose one (;

def footer():
    print >> out, '</div>'
    print >> out, '</body>'
    print >> out, '</html>'

# index.html
out = open('output/merged/index.html', 'w')
header('Nodes Connections')
nodes_connections()
footer()
out.close()

# multicast.html
out = open('output/merged/multicast.html', 'w')
header('IP Multicast')
multicast()
footer()
out.close()
