#!/usr/bin/env python

import sys
import os
import sqlite3
import getopt
import utilities

class GraphWriter:
    def __init__(self, db_connection, file_prefix):
        self.db_connection = db_connection
        self.file_prefix   = file_prefix

    def write_graphs(self):
        self.graph_ip_port     ( open(self.file_prefix+'ip-port.gv', 'w') )
        self.graph_ip_multicast( open(self.file_prefix+'ip-multicast.gv', 'w') )


        self.graph_mac_ip      ( open(self.file_prefix+'mac-ip.gv', 'w') )

        self.graph_nodes_connections(
                                 open(self.file_prefix+'nodes-connections-count.gv', 'w'),
                                 open(self.file_prefix+'nodes-connections-length.gv', 'w') )
 
    def cursor(self):
        return self.db_connection.cursor()

    def graph_nodes_connections(self, output_count_based, output_length_based):
        def header(f):
            print >> f, 'graph foo {'
            print >> f, 'graph [ overlap = "scale" splines = "true" ]'
            print >> f, 'node [ shape = "circle" label = "\N" fixedsize = "true" style = "filled" fillcolor = "white" id = "\N" URL = "javascript:top.click(\'\N\')" ]'

        def footer(f):
            print >> f, '}'

        header(output_count_based)
        header(output_length_based)

        # print nodes

        c = self.cursor()
        c.execute("select ip, sum(count) as count, sum(length) as length from (\
            select ip_src as ip, count( distinct ip_dst ) as count, sum(length) as length from packet_eth_ipv4_unicast group by ip_src \
            union \
            select ip_dst as ip, count( distinct ip_src ) as count, sum(length) as length from packet_eth_ipv4_unicast group by ip_dst) \
            group by ip order by ip")

        nodes = c.fetchall()

        counts  = map ((lambda x: x[1]), nodes)
        lengths = map ((lambda x: x[2]), nodes)

        node_size_count  = utilities.pen_selector(10, sorted(counts))
        node_size_length = utilities.pen_selector(10, sorted(lengths))

        for ip, count, length in nodes:
            s = node_size_count(count)
            l = node_size_length(length)
            print >> output_count_based,  '"%s" [ width = %s penwidth = %s fontsize = %s ]' % (ip, s/2+1, s/3+1, 6+3*s)
            print >> output_length_based, '"%s" [ width = %s penwidth = %s fontsize = %s ]' % (ip, l/2+1, l/3+1, 6+3*l)

        # print edges

        c.execute("select ip1, ip2, count(*) as count, sum(length) as length, min(timestamp) as start, max(timestamp) as end from ( \
            select ip_src as ip1, ip_dst as ip2, port_src as port1, port_dst as port2, length, timestamp from packet_eth_ipv4_unicast \
            where ip_src < ip_dst group by ip_src, ip_dst, port_src, port_dst \
            union \
            select ip_dst as ip1, ip_src as ip2, port_dst as port1, port_src as port2, length, timestamp from packet_eth_ipv4_unicast \
            where ip_src >= ip_dst group by ip_src, ip_dst, port_src, port_dst) \
            group by ip1, ip2")

        edges = c.fetchall()

        counts  = map ((lambda x: x[2]), edges)
        lengths = map ((lambda x: x[3]), edges)

        edge_size_count  = utilities.pen_selector(10, sorted(counts))
        edge_size_length = utilities.pen_selector(10, sorted(lengths))

        # generate edges in graph
        for ip1, ip2, count, length, start, end in edges:
            time = utilities.time_difference(start, end)

            intensity = 0
            # let's assume that 10 connections in short time is an acceptable level
            if (time > 0 and count > 10):
                intensity = 15 * count / time;

            #print count, " connections in ", time, " us =>", intensity
            print >> output_count_based, '"%s" -- "%s" [penwidth = %s, color = "%s" URL = "#" tooltip = %s]' \
                % (ip1, ip2, edge_size_count(count)+1, utilities.temperature(intensity), count)

            print >> output_length_based, '"%s" -- "%s" [penwidth = %s, color = "%s" URL = "#" tooltip = %s]' \
                % (ip1, ip2, edge_size_length(length)+1, utilities.temperature(intensity), count)

        footer(output_count_based)
        footer(output_length_based)


    def graph_ip_multicast(self, output):
        c = self.cursor()
        c.execute("select sum(length) as length from tmp_packets_multicast group by ip_src")
        counts = map ((lambda x: x[0]), c.fetchall())
        pen_width = utilities.pen_selector(10, sorted(counts))

        print >> output, 'graph foo {'
        print >> output, 'graph [ overlap = "scale" splines = "true" ]'
        print >> output, 'node [ shape = "circle" label="\N" ]'

        c.execute("select ip_src, sum(length) as length from tmp_packets_multicast group by ip_src")
        for ip_src, length in c:
            s = pen_width(length)
            print >> output, '"%s" [ width = %s pendiwth = %s fontsize = %s ]' % (ip_src, s/2+1, s/3+1, 6+3*s)

        c.execute("select distinct(ip_dst) from tmp_packets_multicast")
        print >> output, '{'
        print >> output, 'node [ shape = "rectangle" label="\N" ]'
        for ip_dst in c:
            print >> output, '"%s"'  % ip_dst
        print >> output, '}'

        c.execute("select ip_src, ip_dst from tmp_packets_multicast group by ip_src, ip_dst")
        for ip_src, ip_dst in c:
            print >> output, '"%s" -- "%s"' % (ip_src, ip_dst)

        print >> output, '}'


    def graph_mac_ip(self, output):
        print >> output, 'digraph foo {'
        print >> output, '\tgraph [ rankdir = "LR" overlap = "scale" splines = "true" ];'
        print >> output, '\tnode [ shape = "Mrecord" ];'

        c = self.cursor()
        c.execute("select mac, group_concat(distinct label) from (\
            select mac_src as mac, ip_src as label from tmp_packets_mac_ip where mac not in tmp_routers \
            union \
            select mac_dst as mac, ip_dst as label from tmp_packets_mac_ip where mac not in tmp_routers \
            union \
            select mac, 'router' as label from tmp_routers) group by mac;")
        for mac, label in c:
            print >> output, '\t"%s" [ label = "<mac> %s' % (mac, mac),
            for ip in label.split(','):
                print >> output, '| <%s> %s' % (ip.replace('.',''), ip),
            print >> output, '"];'

        c.execute("select sum(count) as count from tmp_packets_mac_ip group by mac_src, \
            (case (mac_src in tmp_routers) when 1 then 'router' else  ip_src end), mac_dst, \
            (case (mac_dst in tmp_routers) when 1 then 'router' else  ip_dst end);")
        counts = map ((lambda x: x[0]), c.fetchall())
        pen_width = utilities.pen_selector(10, sorted(counts))

        c.execute("select mac_src, \
            (case (mac_src in tmp_routers) when 1 then 'router' else  ip_src end) as ip_src, mac_dst, \
            (case (mac_dst in tmp_routers) when 1 then 'router' else  ip_dst end) as ip_dst, sum(count) as count, \
            trans_proto from tmp_packets_mac_ip group by mac_src, ip_src, mac_dst, ip_dst;")
        for mac_src, ip_src, mac_dst, ip_dst, count, proto in c:
            print >> output, '\t"%s":%s -> "%s":%s [ penwidth = "%f" color = "%s" ];' \
                % (mac_src, ip_src.replace('.',''), mac_dst, ip_dst.replace('.',''), (pen_width(count)+1), utilities.color(proto))

        print >> output, '}'


    def graph_ip_port(self, output):
        print >> output, 'digraph foo {'
        print >> output, 'graph [ rankdir = "LR" overlap = "scale" splines = "true" ];'

        c = self.cursor()

        c.execute("select ip_src, ip_dst, port_dst, trans_proto, count(*) as count from packet_eth_ipv4_unicast \
            group by ip_src, ip_dst, port_dst, trans_proto")

        rows = c.fetchall()

        ports  = set(map ((lambda x: (x[2], x[3])), rows))
        for (port_dst, proto) in ports:
            print >> output, '"%s%s" [ shape = "rectangle" label="%s" ];' % (proto, port_dst, port_dst)

        host_edges = dict()
        port_edges = dict()

        for ip_src, ip_dst, port_dst, proto, count in rows:
            print ip_src, "->", ip_dst, ":", port_dst
            key = (min(ip_src, ip_dst), max(ip_src, ip_dst), proto)
            if key not in host_edges:
                backward = (ip_src != min(ip_src, ip_dst))
                if backward:
                    dir = "back"
                else:
                    dir = "forward"
                host_edges[key] = (count, dir);
            else:
                backward = (ip_src != min(ip_src, ip_dst))
                if backward:
                    dir = "back"
                else:
                    dir = "forward"
                cdir = host_edges[key][1]
                if cdir != dir:
                    dir = "both"

                c = host_edges[key][0]
                host_edges[key] = (c+count, dir);

            key = (ip_dst, port_dst, proto)
            if key not in port_edges:
                port_edges[key] = count;
            else:
                port_edges[key] += count;

        counts = map ((lambda x: x[0]), host_edges.values()) + port_edges.values()
        pen_width = utilities.pen_selector(10, sorted(counts))

        for ((ip_src, ip_dst, proto), (count, dir)) in host_edges.iteritems():
            print >> output, '"%s" -> "%s" [ color = "%s" penwidth = "%f" dir = "%s" URL="#" caption="%i"];' \
                % (ip_src, ip_dst, utilities.color(proto), (pen_width(count)+1), dir, count)

        for ((ip_dst, port_dst, proto), (count)) in port_edges.iteritems():
            print >> output, '"%s" -> "%s%s" [ color = "%s" penwidth = "%f" URL="#" caption="%i"];' \
                % (ip_dst, proto, port_dst, utilities.color(proto), (pen_width(count)+1), count)

        print >> output, '}'


def main(argv=None):
    if argv is None:
        argv = sys.argv

    try:
        opts, args = getopt.getopt(argv[1:], 'd:o:', ['database=', 'output='])

    except getopt.GetoptError, err:
        print str(err)
        return 2

    for o, a in opts:
        if o in ('-d', '--database'):
            database = a
        elif o in ('-o', '--output'):
            output = a
        else:
            return 2

    if not os.path.exists(database):
        print >> sys.stderr, 'No such database file:', database
        return 2

    conn = sqlite3.connect(database)

    gw = GraphWriter(conn, output)
    gw.write_graphs()
    return 0

if __name__ == "__main__":
    sys.exit(main())
