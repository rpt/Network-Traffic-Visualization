#!/usr/bin/env python

from datetime import datetime

def color(proto):
    color_map = {   'udp': '#33cc4c',
                    'tcp': '#3366cc',
                    'icmp': '#cc9933',
                    'igmp': '#75581d',
                    'unknown': '#666666',
                }

    if proto in color_map:
        return color_map[proto]
    else:
        print >> sys.stderr, 'Unknown proto: %s' % proto
        return "black"

def multiproto_color(counters):
    tcp    = counters.pop('tcp', 0);
    udp    = counters.pop('udp', 0);
    icmp   = counters.pop('icmp', 0);
    others = sum (counters.values())
    result = [];
    if tcp:
        result.append(color('tcp'))
    if udp:
        result.append(color('udp'))
    if icmp:
        result.append(color('icmp'))
    if others:
        result.append(color('unknown'))

    return reduce(lambda x, y: x+':'+y, result)

def temperature(value):
    value = min(value, 1)
    value = max(value, 0)
    return '#'+hex(int(value*255))[2:]+'0000'

def cheapest_merge(buckets):
    cost = merge_cost(buckets, 0)
    cheapest = 0;
    for i in range(len(buckets)-1):
        tmp = merge_cost(buckets, i)
        if tmp < cost:
            cheapest = i
            cost = tmp
        elif tmp == cost:
            if buckets[i][2] + buckets[i+1][2] <= buckets[cheapest][2]:
                cheapest = i
                cost = tmp
            
    return cheapest

def merge(buckets, i):
    buckets[i] = (buckets[i][0], buckets[i+1][1], buckets[i][2] + buckets[i+1][2])

def merge_cost(buckets, i):
    a = buckets[i]
    b = buckets[i+1]
    return b[0] - a[1]

def make_buckets(number, list):
    buckets = map ((lambda x: (x, x, 1)), list)
    while len(buckets) > number:
        i = cheapest_merge(buckets)
        merge(buckets, i)
        del buckets[i+1]

    return buckets

def i_pen_selector(value, buckets):
    for b in range(len(buckets)):
        if value <= buckets[b][1]:
            return b
    return len(buckets)-1

def pen_selector(number, list):
    buckets = make_buckets(number, list)

    return lambda x: i_pen_selector(x, buckets)

def ip_multicast(ip):
    octs = ip.split('.')
    o1 = int(octs[0])
    return (224 <= o1) and (o1 <= 239)


def time_difference(start, end):
    t1 = datetime.strptime(start, '%Y-%m-%d %H:%M:%S.%f')
    t2 = datetime.strptime(end, '%Y-%m-%d %H:%M:%S.%f')

    diff = t2-t1;

    return diff.microseconds + 1.0e6 * diff.seconds + 1.0e6 * 60 * 60 * 24 * diff.days

#test1 = make_pen_selector(3, [1, 2, 3, 4, 5, 6, 7, 8, 9, 10])
#test2 = make_pen_selector(3, [1, 1, 2, 2, 5, 5, 8, 9, 10, 11])

#for i in range(11):
#    print i, "->", test1(i)

#for i in range(11):
#    print i, "->", test2(i)
