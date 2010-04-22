#!/usr/bin/env python

import os
import sys
import getopt
import shutil
import utilities

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
            <li><a href="javascript:change(\'nodes-connections-count\')">Nodes Connections</a></li>
            <li><a href="javascript:change(\'ip-port-dot\')">Port Utilisation</a></li>
            <li><a href="javascript:change(\'ip-multicast-circo\')">IP Multicast</a></li>
        </ul>
    </div>
    <div id="zoom" class="trans">
        <img id="zoom_in" src="htmedia/zoom_in.png" />
        <img id="zoom_out" src="htmedia/zoom_out.png" />
    </div>
    <div id="ip_back"></div>
    <div id="ip">
        <object id="ip_stats" data="" type="text/html" height="100%" width="100%"></object> 
        <!--
        <div id="ip_stats" src="http://onet.pl"></div>
        <div id="ip_svg_div">
            <object id="ip_svg" data=""></object>
        </div>
        -->
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

conn = utilities.connect(database)
c = conn.cursor()

ips = []
c.execute("select distinct(ip) from (\
    select ip_src as ip from tmp_packets_ip_port \
    union \
    select ip_dst as ip from tmp_packets_ip_port);")
for ip in c:
    ips.append(ip[0])

if not os.path.isdir(dir + '/htstats'):
    os.mkdir(dir + '/htstats')

for ip in ips:

    ipf = open(dir + '/htstats/ip-' + ip + '.html', 'w')
    print >> ipf, '''<html>
    <link rel="stylesheet" href="../htmedia/style.css" type="text/css" />
    <script src="../htmedia/jquery-1.4.2.min.js"></script>
<body>
<h1>%(ip)s</h1>''' % {'ip': ip}

    c.execute("select src.ip_src as ip_src, src.ip_dst as ip_dst, src.port_src as port_src, src.port_dst as port_dst, src.length as bytes_sent, dst.length as bytes_recv, src.count as packets_sent, dst.count as packets_recv from (select ip_src, ip_dst, port_src, port_dst, trans_proto, sum(length) as length, count(*) as count from packet_eth_ipv4 where ip_dst=? group by ip_src, ip_dst, trans_proto, port_src, port_dst) as dst join (select ip_src, ip_dst, port_src, port_dst, trans_proto, sum(length) as length, count(*) as count from packet_eth_ipv4 where ip_src=? group by ip_src, ip_dst, trans_proto, port_src, port_dst) as src on (src.ip_src = dst.ip_dst and src.port_src = dst.port_dst and src.port_dst = dst.port_src and src.trans_proto = dst.trans_proto);", (ip, ip))
    
    if c.rowcount != 0:
        print >> ipf, '''<h2>Peers (IPv4)</h2>
<table>
    <tr>
        <th>IP</th>
        <th>Port Out</th>
        <th>Port In</th>
        <th>Bytes Sent</th>
        <th>Bytes Recv</th>
        <th>Packets Sent</th>
        <th>Packets Recv</th>
    </tr>''' % {'ip': ip}
        for ip_dst, ip_src, port_dst, port_src, bytes_sent, bytes_recv, packets_sent, packets_recv in c:
            print >> ipf, '''   <tr>
        <td>%s</td>
        <td>%s</td>
        <td>%s</td>
        <td>%s</td>
        <td>%s</td>
        <td>%s</td>
        <td>%s</td>
    </tr>''' % (ip_dst, port_dst, port_src, bytes_sent, bytes_recv, packets_sent, packets_recv)
 
        print >> ipf, '''</table>'''

    c.execute("select src.ip_src as ip_src, src.trans_proto as trans_proto, src.length as bytes_sent, dst.length as bytes_recv, src.count as packets_sent, dst.count as packets_recv from (select ip_dst, trans_proto, sum(length) as length, count(*) as count from packet_eth_ipv4 where ip_dst=? group by ip_dst, trans_proto) as dst join (select ip_src, trans_proto, sum(length) as length, count(*) as count from packet_eth_ipv4 where ip_src=? group by ip_src, trans_proto) as src on (src.ip_src = dst.ip_dst and src.trans_proto = dst.trans_proto);", (ip, ip))

    if not c.rowcount == 0:
        print >> ipf, '''<h2>Protocols (IPv4)</h2>
<table>
    <tr>
        <th>Proto</th>
        <th>Bytes Sent</th>
        <th>Bytes Recv</th>
        <th>Packets Sent</th>
        <th>Packets Recv</th>
    </tr>'''
        for ip_src, trans_proto, bytes_sent, bytes_recv, packets_sent, packets_recv in c:
            print >> ipf, '''   <tr>
        <td>%s</td>
        <td>%s</td>
        <td>%s</td>
        <td>%s</td>
        <td>%s</td>
    </tr>''' % (trans_proto, bytes_sent, bytes_recv, packets_sent, packets_recv)
       
        print >> ipf, '''</table>'''

    str = "select ip_src, ip_dst, sum(length) as bytes_sent, count(*) as packets_sent from packet_eth_ipv4 where ip_src='%s' and ip_multicast(ip_dst) group by ip_src, ip_dst;" % ip
    c.execute(str)

    if not c.rowcount == 0:
        print >> ipf, '''<h2>Multicast (IPv4)</h2>
<table>
    <tr>
        <th>Group</th>
        <th>Bytes Sent</th>
        <th>Packets Sent</th>
    </tr>'''
        for ip_src, ip_dst, bytes_sent, packets_sent in c:
            print >> ipf, '''   <tr>
        <td>%s</td>
        <td>%s</td>
        <td>%s</td>
    </tr>''' % (ip_dst, bytes_sent, packets_sent)
       
        print >> ipf, '''</table>
</body>
</html>'''
    
    str = "select ip_src, ip_dst, sum(length) as bytes_sent, count(*) as packets_sent from packet_eth_ipv4 where ip_src='%s' and mac_dst='ff:ff:ff:ff:ff:ff' group by ip_src, ip_dst;" % ip
    c.execute(str)

    if not c.rowcount == 0:
        print >> ipf, '''<h2>Broadcast (IPv4)</h2>
<table>
    <tr>
        <th>Target</th>
        <th>Bytes Sent</th>
        <th>Packets Sent</th>
    </tr>'''
        for ip_src, ip_dst, bytes_sent, packets_sent in c:
            print >> ipf, '''   <tr>
        <td>%s</td>
        <td>%s</td>
        <td>%s</td>
    </tr>''' % (ip_dst, bytes_sent, packets_sent)
       
        print >> ipf, '''</table>'''

    ipf.close()

if not os.path.isdir(dir):
    os.mkdir(dir)

if os.path.isdir(dir + '/htmedia'):
    shutil.rmtree(dir + '/htmedia')

if not os.path.isdir(dir + '/htmedia'):
    shutil.copytree('htmedia', dir + '/htmedia')

index()
