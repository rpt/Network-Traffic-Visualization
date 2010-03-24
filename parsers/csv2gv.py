#!/usr/bin/env python

import sys
import re

#def unique(list):
#	seen = []
#	for s in list:
#		if not s in seen:
#			seen.append(s)
#	return seen

def arp(ip):
	for node in nodes:
		if re.search(ip, nodes[node]):
			return node

nodes = {}
edges = {}
routers = []

data = sys.stdin.readlines()

print 'digraph foo {'
print '\tgraph [\n\t\trankdir = "LR"\n\t];'
print '\tnode [\n\t\tfontsize = "14"\n\t\tshape = "record"\n\t];'

for line in data:
	line = line.strip().split(',')
	mac_src = line[1]
	mac_dst = line[2]
	ip_src = line[5]
	ip_dst = line[6]
	port_dst = line[8]

	if not nodes.has_key(mac_src):
		nodes[mac_src] = 'label = "<src> %s| <%s> %s' % (mac_src, ip_src.replace('.',''), ip_src)
	elif not re.search(ip_src, nodes[mac_src]):
		nodes[mac_src] += '| <%s> %s' % (ip_src.replace('.',''), ip_src)

for node in nodes:
	if nodes[node].count('|') > 10:
		nodes[node] = 'label = "<src> %s | <r0> router' % node
		routers.append(node)

for line in data:
	line = line.strip().split(',')
	mac_src = line[1]
	mac_dst = line[2]
	ip_src = line[5]
	ip_dst = line[6]
	port_dst = line[8]

	if mac_src in routers:	
		ip_src = 'r0'
	if mac_dst in routers:
		ip_dst = 'r0'
	edge = ip_src+','+ip_dst#+','+port_dst
	if not edges.has_key(edge):
		edges[edge] = 0
#		print "edge", edge
	else:
		edges[edge] += 1	
#		print 'up!', edge, edges[edge]

for node in nodes:
	print '\t"%s" [' % node
	print '\t\t%s"' % nodes[node]
	print '\t];'

for edge in edges:
	ips = edge.split(',')
	ip_src = ips[0]
	ip_dst = ips[1]
#	port_dst = ips[2]
	node_src = arp(ip_src)
	node_dst = arp(ip_dst)
	if node_src is not None and node_dst is not None:
		print '\t"%s":%s -> "%s":%s [' % (node_src, ip_src.replace('.',''), node_dst, ip_dst.replace('.',''))
#		print '\t\tlabel = "%s"' % port_dst
#		print '\t\tpenwidth = "%d"' % edges[edge]
		print '\t];'

print '};'
