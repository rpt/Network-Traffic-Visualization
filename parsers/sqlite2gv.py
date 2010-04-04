#!/usr/bin/env python

import sys
import os
import sqlite3
import getopt
from pen_selector import pen_selector

def color(proto):
	if proto == "udp":
		return "blue"
	elif proto == "tcp":
		return "green"
	elif proto == "icmp":
		return "brown"
	elif proto == "igmp":
		return "orange"
	elif proto == "unknown":
		return "gray"
	return "black"

try:
	opts, args = getopt.getopt(sys.argv[1:], 'himd:o:', ['help', 'ip-port', 'mac-ip', 'database=', 'output='])
except getopt.GetOptError, err:
	print str(err)
	usage()
	sys.exit(2)

ip_port = False
mac_ip = False
f = sys.stdout
output = None

for o, a	in opts:
	if o in ('-i', '--ip-port'):
		ip_port = True
	elif o in ('-m', '--mac-ip'):
		mac_ip = True
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
elif mac_ip or ip_port:
	conn = sqlite3.connect(database)
	c = conn.cursor()

if mac_ip:
	if output:
		f = open(output+'-mac-ip.gv', 'w')

	conn.execute("create temporary table tmp_packets_mac_ip as select mac_src, ip_src, mac_dst, ip_dst, count(*) as count, trans_proto from packet_eth_ipv4 where mac_dst is not 'ff:ff:ff:ff:ff:ff' and mac_dst is not '00:00:00:00:00:00' and mac_dst not like '01:00:5e:%' and ip_src is not '0.0.0.0' group by mac_src, ip_src, mac_dst, ip_dst;")
	conn.execute('create temporary table tmp_routers as select distinct mac from (select mac_dst as mac, count(distinct ip_dst) as c from tmp_packets_mac_ip group by mac union select mac_src as mac, count(distinct ip_src) as c from tmp_packets_mac_ip group by mac) where c > 5;')

	print >> f, 'digraph foo {'
	print >> f, '\tgraph [\n\t\trankdir = "LR"\n\t\toverlap = "false"\n\t\tsplines = "true"\n\t];'
	print >> f, '\tnode [\n\t\tfontsize = "14"\n\t\tshape = "Mrecord"\n\t];'

	c.execute("select mac, group_concat(distinct label) from (select mac_src as mac, ip_src as label from tmp_packets_mac_ip where mac not in tmp_routers union select mac_dst as mac, ip_dst as label from tmp_packets_mac_ip where mac not in tmp_routers union select mac, 'router' as label from tmp_routers) group by mac;")
	for mac, label in c:

		print >> f, '\t"%s" [' % mac
		print >> f, '\t\tlabel = "<mac> %s' % mac,
		for ip in label.split(','):
			print >> f, '| <%s> %s' % (ip.replace('.',''), ip),
		print >> f, '"\n'
		if label == "router":
			print >> f, '\n\t\tcolor = "red"'
		print >> f, '\t];'

	c.execute("select sum(count) as count from tmp_packets_mac_ip group by mac_src, (case (mac_src in tmp_routers) when 1 then 'router' else  ip_src end), mac_dst, (case (mac_dst in tmp_routers) when 1 then 'router' else  ip_dst end);")
	counts = map ((lambda x: x[0]), c.fetchall())
	pen_width = pen_selector(10, sorted(counts))

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
	print >> f, '\t\toverlap = "false"'
	print >> f, '\t\tsplines = "true"'
	print >> f, '\t];'
	print >> f, '\tnode [\n\t\tfontsize = "14"\n\t];'

	c.execute('select count from tmp_packets_ip_port;')
	counts = map ((lambda x: x[0]), c.fetchall())
	pen_width = pen_selector(10, sorted(counts))

	c.execute("select ip_src, ip_dst, port_src, port_dst, trans_proto, count, length from tmp_packets_ip_port;")
	for ip_src, ip_dst, port_src, port_dst, proto, count, length in c:
		print >> f, '\t"%s" -> "%s" [' % (ip_src, ip_dst)
		print >> f, '\t\tlabel = "%s"' % port_dst
		print >> f, '\t\tcolor = "%s"' % color(proto)
		print >> f, '\t\tpenwidth = "%f"' % (pen_width(count)+1)
		print >> f, '\t];'

	print >> f, '};'
