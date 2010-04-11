#!/usr/bin/env python

import os
import sys
import sqlite3
import getopt

pages = [
            ('index', 'Nodes connections (count)', 'nodes-connections-count'),
            ('nclength', 'Nodes connections (length)', 'nodes-connections-length'),
            ('multicast', 'IP Multicast', 'ip-multicast-circo')
        ]

def svg(filename):
    print >> out, '<object id="svg" data="../' + filename + '.svg" />'

def style():
    print >> out, '<style>'
    print >> out, '\tdiv#container { text-align: center; }'
    print >> out, '\tul { padding: 0px; margin: 0px; list-style-type: none; }'
    print >> out, '\tli { padding: 0px 10px;  display: inline; }'
    print >> out, '\tobject#svg { height: 90%; }'
    print >> out, '</style>'

def javascript():
    print >> out, '<script>'
    print >> out, 'function click(id){'
    print >> out, '\tdocument.location = \'htdocs/ip-\' + id + \'.html\';'
    print >> out, '}'
    print >> out, '</script>'

def menu():
    print >> out, '<ul>'
    for filename, title, graphname in pages:
        print >> out, '\t<li><a href="%s.html">%s</a></li>' % (filename, title)
#    print >> out, '\t<li><a href="javascript:;" onclick="document.getElementById(\'svg\').style.height=">Zoom In</a></li>'
    print >> out, '</ul>'
    print >> out, '<hr>'

def info(ip):
    print >> out, '<h1>' + ip + '</h1>'
    print >> out, '<hr>'

def header(title, filename):
    global out
    out = open(dir+'/htdocs/' + filename + '.html', 'w')
    print >> out, '<html>'
    print >> out, '<head><title>%s</title></head>' % title
#   print >> out, '<link rel="stylesheet" href="/site_media/style.css" type="text/css" />'
    style()
    javascript()
    print >> out, '<body>'
    print >> out, '<div id="container">'

def footer():
    print >> out, '</div>'
    print >> out, '</body>'
    print >> out, '</html>'
    out.close()

def create_page(filename, title, graphname):
    header(title, filename)
    menu()
    svg(graphname)
    footer()

def create_ip_page(ip):
    header(ip, 'ip-'+ip)
    info(ip)
    svg('ip-'+ip)
    footer()

def create_htdocs(ips):
    if not os.path.isdir(dir+'/htdocs'):
        os.mkdir(dir+'/htdocs')

    for filename, title, graphname in pages:
        create_page(filename, title, graphname)

    for ip in ips:
        create_ip_page(ip)

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

print >> sys.stderr, sys.argv

if not os.path.exists(database):
    print >> sys.stderr, 'No such database file.'
    sys.exit(1)

conn = sqlite3.connect(database)
c = conn.cursor()

ips = []
c.execute("select distinct(ip) from (\
    select ip_src as ip from tmp_packets_ip_port \
    union \
    select ip_dst as ip from tmp_packets_ip_port);")
for ip in c:
    ips.append(ip[0])

create_htdocs(ips)
