#!/usr/bin/env python

import sys

def unique(list):
	seen = []
	for s in seq:
		if not s in seen:
			seen.append(s)
	return seen

data = sys.stdin.readlines()

print 'digraph foo {'

for line in unique(sorted(data)):
	line = line.strip().split(',')
	print '\t\"%s\" -> \"%s\" [ label = \"%s\" ];' % (line[0], line[1], line[3])

print '};'
