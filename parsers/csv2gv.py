#!/usr/bin/env python

import sys

def unique(seq, keepstr=True):
	t = type(seq)
	if t in (str, unicode):
		t = (list, ''.join)[bool(keepstr)]
	seen = []
	return t(c for c in seq if not (c in seen or seen.append(c)))

data = sys.stdin.readlines()

print 'digraph foo {'

for line in unique(sorted(data)):
	line = line.strip().split(',')
	print '\t\"%s\" -> \"%s\" [ label = \"%s\" ];' % (line[0], line[1], line[3])

print '};'
