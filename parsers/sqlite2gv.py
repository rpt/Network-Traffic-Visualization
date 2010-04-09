#!/usr/bin/env python

import sys
import os
import sqlite3
import getopt
import utilities

ROUTER_IPS = 3        # From how many IPs node is considered a router.
PEN_WIDTHS = 10    # Number of different penwidths.

def color(proto):
    color_map = {    'udp': '#33cc4c',
                        'tcp': '#3366cc',
                        'icmp': '#cc9933',
                        'igmp': '#75581d',
                        'unknown': '#666666',
                        'router': '#cccccc',
                    }

    if proto in color_map:
        return color_map[proto]
    else:
        print >> sys.stderr, 'Unknown proto: %s' % proto
        return "black"

def multiproto_color(protocols):
    tcp    = counters.pop('tcp', 0);
    udp    = counters.pop('udp', 0);
    icmp   = counters.pop('icmp', 0);
    others = sum (counters.values())
    result = [];
    if tcp:
        result.append(color('tcp'))
    if udp:
        result.append(color('udp'))
    if icmp:
        result.append(color('icmp'))
    if others:
        result.append(color('unknown'))

    return reduce(lambda x, y: x+':'+y, result)

try:
    opts, args = getopt.getopt(sys.argv[1:], 'himd:o:', ['help', 'ip-port', 'mac-ip', 'ip-multicast', 'database=', 'output=', 'nodes-connections'])
except getopt.GetOptError, err:
    print str(err)
    usage()
    sys.exit(2)

ip_port = False
mac_ip = False
nodes_connections = False
ip_multicast = False
f = sys.stdout
output = None

for o, a    in opts:
    if o in ('-i', '--ip-port'):
        ip_port = True
    elif o in ('-m', '--mac-ip'):
        mac_ip = True
    elif o in ('--ip-multicast'):
        ip_multicast = True
    elif o in ('--nodes-connections'):
        nodes_connections = True
    elif o in ('-d', '--database'):
        database = a
    elif o in ('-o', '--output'):
        output = a
    elif o in ('-h', '--help'):
        usage()
        sys.exit()

if not os.path.exists(database):
    print >> sys.stderr, 'No such database file.'
    sys.exit(2)
else:
    conn = sqlite3.connect(database)
    conn.create_function('ip_multicast', 1, utilities.ip_multicast)
    c = conn.cursor()

if mac_ip:
    if output:
        f = open(output+'-mac-ip.gv', 'w')

    conn.execute("create temporary table tmp_packets_mac_ip as select mac_src, ip_src, mac_dst, ip_dst, count(*) as count, trans_proto from packet_eth_ipv4 where mac_dst is not 'ff:ff:ff:ff:ff:ff' and mac_dst is not '00:00:00:00:00:00' and mac_dst not like '01:00:5e:%' and ip_src is not '0.0.0.0' group by mac_src, ip_src, mac_dst, ip_dst;")
    conn.execute('create temporary table tmp_routers as select distinct mac from (select mac_dst as mac, count(distinct ip_dst) as c from tmp_packets_mac_ip group by mac union select mac_src as mac, count(distinct ip_src) as c from tmp_packets_mac_ip group by mac) where c >= '+str(ROUTER_IPS)+';')

    print >> f, 'digraph foo {'
    print >> f, '\tgraph [\n\t\trankdir = "LR"\n\t\toverlap = "scale"\n\t\tsplines = "true"\n\t];'
    print >> f, '\tnode [\n\t\t\n\t\tshape = "Mrecord"\n\t];'

    c.execute("select mac, group_concat(distinct label) from (select mac_src as mac, ip_src as label from tmp_packets_mac_ip where mac not in tmp_routers union select mac_dst as mac, ip_dst as label from tmp_packets_mac_ip where mac not in tmp_routers union select mac, 'router' as label from tmp_routers) group by mac;")
    for mac, label in c:

        print >> f, '\t"%s" [' % mac
        print >> f, '\t\tlabel = "<mac> %s' % mac,
        for ip in label.split(','):
            print >> f, '| <%s> %s' % (ip.replace('.',''), ip),
        print >> f, '"\n'
        if label == "router":
            print >> f, '\n\t\tstyle = "filled"'
            print >> f, '\n\t\tfillcolor = "%s"' % color('router')
        print >> f, '\t];'

    c.execute("select sum(count) as count from tmp_packets_mac_ip group by mac_src, (case (mac_src in tmp_routers) when 1 then 'router' else  ip_src end), mac_dst, (case (mac_dst in tmp_routers) when 1 then 'router' else  ip_dst end);")
    counts = map ((lambda x: x[0]), c.fetchall())
    pen_width = utilities.pen_selector(10, sorted(counts))

    c.execute("select mac_src, (case (mac_src in tmp_routers) when 1 then 'router' else  ip_src end) as ip_src, mac_dst, (case (mac_dst in tmp_routers) when 1 then 'router' else  ip_dst end) as ip_dst, sum(count) as count, trans_proto from tmp_packets_mac_ip group by mac_src, ip_src, mac_dst, ip_dst;")
    for mac_src, ip_src, mac_dst, ip_dst, count, proto in c:

        print >> f, '\t"%s":%s -> "%s":%s [' % (mac_src, ip_src.replace('.',''), mac_dst, ip_dst.replace('.',''))
        print >> f, '\t\tpenwidth = "%f"' % (pen_width(count)+1)
        print >> f, '\t\tcolor = "%s"' % color(proto)
        print >> f, '\t];'

    print >> f, '};'

if ip_port:
    if output:
        f = open(output+'-ip-port.gv', 'w')

    conn.execute("create temporary table tmp_packets_ip_port as select ip_src, ip_dst, port_src, port_dst, count(*) as count, sum(length) as length, trans_proto from packet_eth_ipv4 where mac_dst is not 'ff:ff:ff:ff:ff:ff' and mac_dst is not '00:00:00:00:00:00' and mac_dst not like '01:00:5e:%' and ip_src is not '0.0.0.0' group by ip_src, ip_dst, port_src, port_dst, trans_proto;")

    print >> f, 'digraph foo {'
    print >> f, '\tgraph [\n\t\trankdir = "LR"'
    print >> f, '\t\toverlap = "scale"'
    print >> f, '\t\tsplines = "true"'
    print >> f, '\t];'
    print >> f, '\tnode [\n\t\t\n\t];'

    c.execute('select count from tmp_packets_ip_port;')
    counts = map ((lambda x: x[0]), c.fetchall())
    pen_width = utilities.pen_selector(PEN_WIDTHS, sorted(counts))

    c.execute("select ip_src, ip_dst, port_src, port_dst, trans_proto, count, length from tmp_packets_ip_port;")
    for ip_src, ip_dst, port_src, port_dst, proto, count, length in c:
        print >> f, '\t"%s" -> "%s" [' % (ip_src, ip_dst)
        print >> f, '\t\tlabel = "%s"' % port_dst
        print >> f, '\t\tcolor = "%s"' % color(proto)
        print >> f, '\t\tpenwidth = "%f"' % (pen_width(count)+1)
        print >> f, '\t];'

    print >> f, '};'

if ip_multicast:
    if output:
        f = open(output+'-ip-multicast.gv', 'w')

    conn.execute("create temporary table tmp_packets_multicast as select ip_src, ip_dst, count(*) as count, sum(length) as length from packet_eth_ipv4 where ip_multicast(ip_dst) group by ip_src, ip_dst;")

    c = conn.cursor()

    c.execute("select sum(length) as length from tmp_packets_multicast group by ip_src")
    counts = map ((lambda x: x[0]), c.fetchall())
    pen_width = utilities.pen_selector(10, sorted(counts))

    print >> f, 'graph foo {'
    print >> f, 'graph [ overlap = "scale"'
    print >> f, '\t\tsplines = "true" ]'
    print >> f, 'node [shape = "circle" label="\N" ]'

    c.execute("select ip_src, sum(length) as length from tmp_packets_multicast group by ip_src")
    for ip_src, length in c:
        print >> f, '"%s" [ width = %s ]' % (ip_src, pen_width(length)+1)
        # print >> f, '"%s"' % ip_src

    c.execute("select distinct(ip_dst) from tmp_packets_multicast")
    print >> f, '{'
    print >> f, 'node [shape = "rectangle" label="\N"]'
    for ip_dst in c:
        print >> f, '"%s"'  % ip_dst
    print >> f, '}'

    c.execute("select ip_src, ip_dst from tmp_packets_multicast group by ip_src, ip_dst")
    for ip_src, ip_dst in c:
        print >> f, '"%s" -- "%s"' % (ip_src, ip_dst)

    print >> f, '}'

if nodes_connections:
    if output:
        f = open(output+'-nodes-connections.gv', 'w')
    c = conn.cursor()
    c.execute("select ip, sum(count) as count from \
                 (select ip_src as ip, count( distinct ip_dst ) as count from packet_eth_ipv4_unicast group by ip_src \
                  union \
                  select ip_dst as ip, count( distinct ip_src ) as count from packet_eth_ipv4_unicast group by ip_dst) \
                group by ip order by ip")

    print >> f, 'graph foo {'
    print >> f, 'graph [ overlap = "scale" splines="true" ]'
    print >> f, 'node  [ shape = "circle"  label="\N" fixedsize="true" style="filled" fillcolor="white" id="\N" URL="javascript:top.click(\'\N\')"]'

    nodes = c.fetchall()
    counts = map ((lambda x: x[1]), nodes)
    node_size = utilities.pen_selector(10, sorted(counts))

    for ip, count in nodes:
        s = node_size(count)
        print >> f, '"%s" [ width = %s penwidth = %s fontsize = %s ]' % (ip, s/2+1, s/3+1, 6+3*s)

    del nodes, node_size

    c.execute("select ip1, ip2, trans_proto, count(*) as count from ( \
                   select ip_src as ip1, ip_dst as ip2, port_src as port1, port_dst as port2, trans_proto from packet_eth_ipv4_unicast where ip_src < ip_dst group by ip_src, ip_dst, port_src, port_dst, trans_proto \
                   union \
                   select ip_dst as ip1, ip_src as ip2, port_dst as port1, port_src as port2, trans_proto from packet_eth_ipv4_unicast where ip_src >= ip_dst group by ip_src, ip_dst, port_src, port_dst, trans_proto \
               ) group by ip1, ip2, trans_proto order by ip1, ip2, trans_proto")

    edges = c.fetchall()
    counts = map ((lambda x: x[3]), edges)
    edge_size = utilities.pen_selector(10, sorted(counts))

    # merge list (edges)
    #  ip1, ip2, icmp, 2
    #  ip1, ip2, tcp, 3
    #  ip1, ip3, tcp, 4
    # into form (combined)
    #  ip1, ip2, {icmp:2, tcp:3}
    #  ip1, ip3, {tcp:4}
    (lip1, lip2) = (None, None)
    combined = [];
    for (ip1, ip2, proto, count) in edges:
        if (lip1, lip2) != (ip1, ip2):
            combined.append((ip1, ip2, {proto:count}))
            (lip1, lip2) = (ip1, ip2)
        else:
            combined[-1][2].update({proto:count})

    # generate edges in graph
    for ip1, ip2, counters in combined:
        count  = sum (counters.values())

        print >> f, '"%s" -- "%s" [penwidth = %s, color="%s" URL="#" tooltip=%s]' % (ip1, ip2, edge_size(count)+1, multiproto_color(counters), count)

    print >> f, '}'

