#!/usr/bin/env perl

while(<>) {
	($src, $dest, $len) = split /,/;
	$key = $src.','.$dest;
	next if ($key =~ /ff:ff:ff:ff:ff:ff/);
	$counter{$key} += $len;
	if ($counter{$key} > $max) {
		$max = $counter{$key};
	}
}

print "digraph G {\n";
#print "node[label=\"\"];";

foreach $key (keys %counter) {
	($src, $dest) = split /,/, $key;
	$total = $counter{$key};
	$max;
	$width = 1 + 8.0 * $total / $max;
	print "\"$src\" -> \"$dest\" [ penwidth=$width ];\n";
}

print "}\n";
