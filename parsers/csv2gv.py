#!/usr/bin/env python

import sys
import re
import math

nodes = {}

class Node:
	def __init__(self, mac):
		self.mac = mac
		self.ips = set()
		self.edges = {}
		self.router = False
	
	def __str__(self):
		return '%s' % self.mac

class Edge:
	def __init__(self, node, src_ip, dst_ip, port):
		self.src_ip = src_ip
		self.dst_ip = dst_ip
		self.port = port
		self.node = node
#		self.thickness = 0

	def __str__(self):
		return '%s -> %s.%s' % (self.src_ip, self.node.mac, self.dst_ip)

	def __eq__(self, other):
		# TODO Comparing only ips and mac, not port
		return self.src_ip == other.src_ip and self.dst_ip == other.dst_ip and self.node.mac == other.node.mac

	def __hash__(self):
		return hash(self.src_ip) + hash(self.dst_ip) + hash(self.node.mac)

#others = new Node('others')
#nodes['others'] = others

data = sys.stdin.readlines()

print >> sys.stderr, 'Analyzing nodes...'

for line in data:
#	print >> sys.stderr, ' Line: %s' % line,

	line = line.strip().split(',')
	mac_src = line[1]
	mac_dst = line[2]
	ip_src = line[5]
	ip_dst = line[6]
	port_src = line[7]
	port_dst = line[8]

	if mac_src not in nodes:
		print >> sys.stderr, '  New source mac found: %s' % mac_src
		new_node = Node(mac_src)
		nodes[mac_src] = new_node
		new_node.ips.add(ip_src)
	else:
		nodes[mac_src].ips.add(ip_src)

	# Not adding edges to broadcast and multicast FIXME Other broadcasts
	filter = re.compile('^(([fF]{2}:){5}[fF]{2}|00:00:00:00:00:00|01:00:5[Ee]:[0-7].:..:..)$')
	if mac_dst not in nodes and not filter.match(mac_dst):
		print >> sys.stderr, '  New destination mac found: %s' % mac_dst
		new_node = Node(mac_dst)
		new_node.ips.add(ip_dst)
		nodes[mac_dst] = new_node
	elif not filter.match(mac_dst):
		nodes[mac_dst].ips.add(ip_dst)

print >> sys.stderr, 'Searching for routers...'

for mac in nodes:
	node = nodes[mac]
	if len(node.ips) > 10:
		print >> sys.stderr, ' Node %s is a router' % mac
		node.router = True
		node.ips.clear()
		node.ips.add('router')

print >> sys.stderr, 'Analyzing edges...'

for line in data:
#	print >> sys.stderr, ' Line: %s' % line,
	line = line.strip().split(',')
	mac_src = line[1]
	mac_dst = line[2]
	ip_src = line[5]
	ip_dst = line[6]
	port_src = line[7]
	port_dst = line[8]

	if nodes.has_key(mac_src) and nodes[mac_src].router is True:
#		print >> sys.stderr, ' Source node (%s) is a router' % mac_src
		ip_src = 'router'

	if nodes.has_key(mac_dst) and nodes[mac_dst].router is True:
#		print >> sys.stderr, ' Destination node (%s) is a router' % mac_dst
		ip_dst = 'router'

	if nodes.has_key(mac_src) and nodes.has_key(mac_dst):
		edge = Edge(nodes[mac_dst], ip_src, ip_dst, port_dst)

		if edge in nodes[mac_src].edges:
#			print >> sys.stderr, ' Edge %s already added' % edge
			nodes[mac_src].edges[edge] += 1
		else:
#			print >> sys.stderr, ' New edge %s found' % edge
			nodes[mac_src].edges[edge] = 0

print 'digraph foo {'
print '\tgraph [\n\t\trankdir = "LR"\n\t];'
print '\tnode [\n\t\tfontsize = "14"\n\t\tshape = "record"\n\t];'

for mac in nodes:
	node = nodes[mac]

	if len(node.ips) > 0:# and len(node.edges) > 0:
		print '\t"%s" [' % node.mac
		print '\t\tlabel = "<mac> %s' % node.mac,
		for ip in node.ips:
			print '| <%s> %s' % (ip.replace('.',''), ip),
		print '"\n\t];'

for mac in nodes:
	node = nodes[mac]

	if len(node.ips) > 0 and len(node.edges) > 0:
		for edge in node.edges:
			print '\t"%s":%s -> "%s":%s [' % (mac, edge.src_ip.replace('.',''), edge.node.mac, edge.dst_ip.replace('.',''))
#			print '\t\tlabel = "%s"' % edge.dst_port
#			print '\t\tpenwidth = "%f"' % math.log(node.edges[edge])
			print '\t];'

print '};'
