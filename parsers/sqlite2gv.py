#!/usr/bin/env python

import sys
import sqlite3
from pen_selector import pen_selector

database = sys.argv[1]

conn = sqlite3.connect(database)
c = conn.cursor()

conn.execute('create temporary table tmp_packets as select mac_src, ip_src, mac_dst, ip_dst, count(*) as count from packet_eth_ipv4 where mac_dst is not \'ff:ff:ff:ff:ff:ff\' and mac_dst is not \'00:00:00:00:00:00\' and mac_dst not like \'01:00:5e:%\' and ip_src is not \'0.0.0.0\' group by mac_src, ip_src, mac_dst, ip_dst;')

conn.execute('create temporary table tmp_routers as select distinct mac from (select mac_dst as mac, count(distinct ip_dst) as c from tmp_packets group by mac union select mac_src as mac, count(distinct ip_src) as c from tmp_packets group by mac) where c >10;')

print 'digraph foo {'
print '\tgraph [\n\t\trankdir = "LR"\n\t\toverlap = "false"\n\t\tsplines = "true"\n\t];'
print '\tnode [\n\t\tfontsize = "14"\n\t\tshape = "Mrecord"\n\t];'

c.execute('select mac_src as mac, group_concat(distinct ip_src) as label from tmp_packets where mac_src not in tmp_routers group by mac_src union select mac_dst as mac, group_concat(distinct ip_dst) as label from tmp_packets where mac_dst not in tmp_routers group by mac_dst union select mac, \'router\' as label from tmp_routers;')
for mac, label in c:

	print '\t"%s" [' % mac
	print '\t\tlabel = "<mac> %s' % mac,
	for ip in label.split(','):
		print '| <%s> %s' % (ip.replace('.',''), ip),
	print '"\n\t];'

c.execute('select sum(count) as count from tmp_packets group by mac_src, (case (mac_src in tmp_routers) when 1 then \'router\' else  ip_src end), mac_dst, (case (mac_dst in tmp_routers) when 1 then \'router\' else  ip_dst end);')

counts = map ((lambda x: x[0]), c.fetchall())

pen_width = pen_selector(10, sorted(counts))

c.execute('select mac_src, (case (mac_src in tmp_routers) when 1 then \'router\' else  ip_src end) as ip_src, mac_dst, (case (mac_dst in tmp_routers) when 1 then \'router\' else  ip_dst end) as ip_dst, sum(count) as count from tmp_packets group by mac_src, ip_src, mac_dst, ip_dst;')
for mac_src, ip_src, mac_dst, ip_dst, count in c:

	print >> sys.stderr, mac_src,ip_src,mac_dst,ip_dst,count

	print '\t"%s":%s -> "%s":%s [' % (mac_src, ip_src.replace('.',''), mac_dst, ip_dst.replace('.',''))
#	print '\t\tlabel = "%s"' % #TODO
	print '\t\tpenwidth = "%f"' % (pen_width(count)+1)
	print '\t];'

print '};'
