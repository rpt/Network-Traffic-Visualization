#!/usr/bin/env python

import sys
import sqlite3
from pen_selector import pen_selector

database = sys.argv[1]

conn = sqlite3.connect(database)
c = conn.cursor()

conn.execute("create temporary table tmp_packets as select ip_src, ip_dst, port_src, port_dst, count(*) as count, sum(length) as length, trans_proto from packet_eth_ipv4 where mac_dst is not 'ff:ff:ff:ff:ff:ff' and mac_dst is not '00:00:00:00:00:00' and mac_dst not like '01:00:5e:%' and ip_src is not '0.0.0.0' group by ip_src, ip_dst, port_src, port_dst, trans_proto;")

print 'digraph foo {'
print '\tgraph [\n\t\trankdir = "LR"\n\t\toverlap = "false"\n\t\tsplines = "true"\n\t];'
print '\tnode [\n\t\tfontsize = "14"\n\t];'

c.execute('select count from tmp_packets;')
counts = map ((lambda x: x[0]), c.fetchall())
pen_width = pen_selector(10, sorted(counts))

c.execute("select ip_src, ip_dst, port_src, port_dst, trans_proto, count, length from tmp_packets;")
for ip_src, ip_dst, port_src, port_dst, photo, count, length in c:
#	print '\t"%s" [' % ip_src
#	print '\t\tlabel = "<mac> %s' % mac,
#	print '"\n\t];'
	print '\t"%s" -> "%s" [' % (ip_src, ip_dst)
	print '\t\tlabel = "%s"' % port_dst
	print '\t\tpenwidth = "%f"' % (pen_width(count)+1)
	print '\t];'

print '};'
