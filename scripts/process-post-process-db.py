#!/usr/bin/env python

# This script is run by ./process to supplement database with some constant
# data that will later speed up most queries used by ./sqlite2gv.py
#
# It is written in python because it uses some user defined (i.e. not built
# into SQLite) functions

import utilities
import getopt
import sys
import os
import sqlite3

try:
    opts, args = getopt.getopt(sys.argv[1:], '', ['database='])
except getopt.GetoptError, err:
    print str(err)
    sys.exit(1)

for o, a in opts:
    if o in ('--database'):
        database = a
    else:
        sys.exit(1)

if not os.path.exists(database):
    print >> sys.stderr, 'No such database file.'
    sys.exit(1)

conn = utilities.connect(database)

conn.execute("create table tmp_packets_multicast as select ip_src, ip_dst, count(*) as count, sum(length) as length from packet_eth_ipv4 where ip_multicast(ip_dst) group by ip_src, ip_dst;")
conn.execute("create table tmp_packets_mac_ip as select mac_src, ip_src, mac_dst, ip_dst, count(*) as count, trans_proto from packet_eth_ipv4 where mac_dst is not 'ff:ff:ff:ff:ff:ff' and mac_dst is not '00:00:00:00:00:00' and mac_dst not like '01:00:5e:%' and ip_src is not '0.0.0.0' group by mac_src, ip_src, mac_dst, ip_dst;")
conn.execute("create table tmp_routers as select distinct mac from (select mac_dst as mac, count(distinct ip_dst) as c from tmp_packets_mac_ip group by mac union select mac_src as mac, count(distinct ip_src) as c from tmp_packets_mac_ip group by mac) where c >= 10;")
conn.execute("create table tmp_packets_ip_port as select ip_src, ip_dst, port_src, port_dst, count(*) as count, sum(length) as length, trans_proto from packet_eth_ipv4 where mac_dst is not 'ff:ff:ff:ff:ff:ff' and mac_dst is not '00:00:00:00:00:00' and mac_dst not like '01:00:5e:%' and ip_src is not '0.0.0.0' group by ip_src, ip_dst, port_src, port_dst, trans_proto;")
