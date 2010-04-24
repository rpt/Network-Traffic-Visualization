#!/usr/bin/env python

import os
import sys
import getopt
import shutil
import utilities
import sqlite3

class HostSummary:
    PEERS_IPV4      = 0
    PROTOCOLS_IPV4  = 1
    MULTICAST_IPV4  = 2
    BROADCAST_IPV4  = 3

    def __init__(self, db, ip):
        self.db = db
        self.ip = ip

    def execute(self, query):
        self.db.row_factory = sqlite3.Row
        c = self.db.cursor()
        c.execute(query, {'ip': self.ip})
        return c

    def query_peers(self):
        #FIXME: this query is so scary because sqlite doesn't support FULL OUTER JOINS ATM (version 3.6.23.1)
        return '''
            select dst.ip_dst as ip_src, dst.ip_src as ip_dst, dst.trans_proto as trans_proto, dst.port_dst as port_src, dst.port_src as port_dst, src.length as bytes_sent, dst.length as bytes_recv, src.count as packets_sent, dst.count as packets_recv
            from (
                select ip_src, ip_dst, port_src, port_dst, trans_proto, sum(length) as length, count(*) as count
                from packet_eth_ipv4
                where ip_dst=:ip
                group by ip_src, ip_dst, trans_proto, port_src, port_dst
            ) as dst
            left join (
                select ip_src, ip_dst, port_src, port_dst, trans_proto, sum(length) as length, count(*) as count
                from packet_eth_ipv4
                where ip_src=:ip
                group by ip_src, ip_dst, trans_proto, port_src, port_dst
            ) as src
            on (src.ip_src = dst.ip_dst and src.port_src = dst.port_dst and src.port_dst = dst.port_src and src.trans_proto = dst.trans_proto)
            union
            select src.ip_src as ip_src, src.ip_dst as ip_dst, src.trans_proto as trans_proto, src.port_src as port_src, src.port_dst as port_dst, src.length as bytes_sent, dst.length as bytes_recv, src.count as packets_sent, dst.count as packets_recv
            from (
                select ip_src, ip_dst, port_src, port_dst, trans_proto, sum(length) as length, count(*) as count
                from packet_eth_ipv4
                where ip_src=:ip
                group by ip_src, ip_dst, trans_proto, port_src, port_dst
            ) as src
            left join (
                select ip_src, ip_dst, port_src, port_dst, trans_proto, sum(length) as length, count(*) as count
                from packet_eth_ipv4
                where ip_dst=:ip
                group by ip_src, ip_dst, trans_proto, port_src, port_dst
            ) as dst
            on (src.ip_src = dst.ip_dst and src.port_src = dst.port_dst and src.port_dst = dst.port_src and src.trans_proto = dst.trans_proto)'''
    
    def query_protocols(self):
        #FIXME: this query is so scary because sqlite doesn't support FULL OUTER JOINS ATM (version 3.6.23.1)
        return '''
            select dst.ip_dst as ip_src, dst.trans_proto as trans_proto, src.length as bytes_sent, dst.length as bytes_recv, src.count as packets_sent, dst.count as packets_recv
            from (
                select ip_dst, trans_proto, sum(length) as length, count(*) as count
                from packet_eth_ipv4
                where ip_dst=:ip
                group by ip_dst, trans_proto
            ) as dst
            left join (
                select ip_src, trans_proto, sum(length) as length, count(*) as count
                from packet_eth_ipv4
                where ip_src=:ip
                group by ip_src, trans_proto
            ) as src
            on (src.ip_src = dst.ip_dst and src.trans_proto = dst.trans_proto)
            union
            select src.ip_src as ip_src, src.trans_proto as trans_proto, src.length as bytes_sent, dst.length as bytes_recv, src.count as packets_sent, dst.count as packets_recv
            from (
                select ip_src, trans_proto, sum(length) as length, count(*) as count
                from packet_eth_ipv4
                where ip_src=:ip
                group by ip_src, trans_proto
            ) as src
            left join (
                select ip_dst, trans_proto, sum(length) as length, count(*) as count
                from packet_eth_ipv4
                where ip_dst=:ip
                group by ip_dst, trans_proto
            ) as dst
            on (src.ip_src = dst.ip_dst and src.trans_proto = dst.trans_proto)'''

    def query_multicast(self):
        return '''
            select ip_src, ip_dst, sum(length) as bytes_sent, count(*) as packets_sent
            from packet_eth_ipv4
            where ip_src=:ip and ip_multicast(ip_dst)
            group by ip_src, ip_dst'''

    def query_broadcast(self):
        return '''
            select ip_src, ip_dst, sum(length) as bytes_sent, count(*) as packets_sent
            from packet_eth_ipv4
            where ip_src=:ip and mac_dst='ff:ff:ff:ff:ff:ff'
            group by ip_src, ip_dst'''

    def make_table(self, output, query, header, content, footer):
        cursor = self.execute(query)
        common_dict = {'ip': self.ip}
        print >> output, header % common_dict

        if cursor.rowcount == 0:
            pass
        else:
            for row in cursor:
                r = common_dict
                for k in row.keys():
                    r[k] = row[k]
                print >> output, content % r
        print >> output, footer % common_dict

    def make_simple_table(self, output, query, title, columns):
        header   = '<h2>' + title + '</h2>\n<table><tr>'
        content  = '<tr>'

        for (label, col) in columns:
            header  += '<th>' + label + '</th>\n'
            content += '<td>%(' + col + ')s</td>\n'

        header  += '</tr>'
        content += '</tr>'

        footer = '</table>'

        return self.make_table(output, query, header, content, footer)

    def write(self, output, table):
        if table == self.PEERS_IPV4:
            hs.make_simple_table(output, hs.query_peers(),
                    'Peers (IPv4)',
                    [('IP',           'ip_dst'),
                     ('Protocol',     'trans_proto'),
                     ('Port Out',     'port_dst'),
                     ('Port In',      'port_src'),
                     ('Bytes Sent',   'bytes_sent'),
                     ('Bytes Recv',   'bytes_recv'),
                     ('Packets Sent', 'packets_sent'),
                     ('Packets Recv', 'packets_recv')])

        elif table == self.PROTOCOLS_IPV4:
            hs.make_simple_table(output, hs.query_protocols(),
                    'Protocols (IPv4)',
                    [('Protocol',     'trans_proto'),
                     ('Bytes Sent',   'bytes_sent'),
                     ('Bytes Recv',   'bytes_recv'),
                     ('Packets Sent', 'packets_sent'),
                     ('Packets Recv', 'packets_recv')])

        elif table == self.MULTICAST_IPV4:
            hs.make_simple_table(output, hs.query_multicast(),
                    'Multicast (IPv4)',
                    [('Group',        'ip_dst'),
                     ('Bytes Sent',   'bytes_sent'),
                     ('Packets Sent', 'packets_sent')])

        elif table == self.BROADCAST_IPV4:
            hs.make_simple_table(output, hs.query_broadcast(),
                    'Broadcast (IPv4)',
                    [('Target',       'ip_dst'),
                     ('Bytes Sent',   'bytes_sent'),
                     ('Packets Sent', 'packets_sent')])

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
    select ip_src as ip from packets_eth_ipv4 \
    union \
    select ip_dst as ip from packets_eth_ipv4);")
for ip in c:
    ips.append(ip[0])

if not os.path.isdir(dir + '/htstats'):
    os.mkdir(dir + '/htstats')

for ip in ips:
    hs = HostSummary(conn, ip)
    ipf = open(dir + '/htstats/ip-' + ip + '.html', 'w')

    print >> ipf, '''<html>
        <link rel="stylesheet" href="../htmedia/style.css" type="text/css" />
        <script src="../htmedia/jquery-1.4.2.min.js"></script>
        <body>
        <h1>%(ip)s</h1>''' % {'ip': ip}

    hs.write(ipf, HostSummary.PEERS_IPV4)
    hs.write(ipf, HostSummary.PROTOCOLS_IPV4)
    hs.write(ipf, HostSummary.MULTICAST_IPV4)
    hs.write(ipf, HostSummary.BROADCAST_IPV4)

    print >> ipf, '''</body></html>'''

    ipf.close()

if not os.path.isdir(dir):
    os.mkdir(dir)

if os.path.isdir(dir + '/htmedia'):
    shutil.rmtree(dir + '/htmedia')

if not os.path.isdir(dir + '/htmedia'):
    shutil.copytree('htmedia', dir + '/htmedia')

shutil.copy('htdoc/index.html', dir)
