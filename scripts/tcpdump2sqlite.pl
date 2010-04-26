#!/usr/bin/env perl

#
# This script takes libpcap capture file, turns it into text format using
# tcpdump and then parses the results.
#
# Since tcpdump output may change, an attempt has been made to create some DSL
# to write needed regular expressions in fast and easy way.
#
# It worked for our needs but feel free to rewrite it the way you like it ;-)
#
# The most interesing part is the
#     my $parser_4_1 = sub {
# line. And of course entry point at
#     main:
# Starting from there you should be able to find references to other
# subroutines and this way it is easier to understand this functions.
# 

use DBI;
use strict;

our ($dbh);

our ($mode_quiet);

our ($line, $line_left, $store_table, %captured);
sub match_one;
sub switch_on;
sub store;
sub matched;
sub parse;
sub ignore_rest;

sub store_in_database
{
	my $c = join(", ", map {$dbh->quote_identifier($_)} keys %captured);
	my $v = join(", ", map {$dbh->quote(lc($_))}        values %captured);

	$dbh->do("insert into $store_table ($c) values ($v)");
	if ($dbh->err()) { 
		print STDERR ("insert into $store_table ($c) values ($v)\n");
		die "$DBI::errstr\n";
	}
}

sub match
{
	my $regexp = $_[0];
	return match_one {
		$regexp => sub {}
	}
}

sub match_one
{
	my %regexps = %{$_[0]};
	while (my ($regex, $action) = each %regexps) {
		if ($line_left =~ $regex) {
			@captured{keys %+} = map {lc} values %+;

			$line_left = $';
			$action->();
			return 1;
		}
	}
	return 0;
}

sub ignore_rest
{
	$line_left = '';
}

sub warn_and_ignore_rest
{
	if ($line_left ne '' and not $mode_quiet) {
		print STDERR  "ignoring rest of line:\n    $line\nleft part:    $line_left\n\n";
		ignore_rest;
	}
}

sub matched
{
	unless (keys %captured == 0) {
		store_in_database;
	}
}

sub switch_on
{
	my $param   = $_[0];
	my %options = %{$_[1]};

	while (my ($value, $action) = each %options) {
		if ($captured{$param} eq $value) {
			$action->();
			return 1;
		}
	}
	unless ($mode_quiet) {
		print STDERR  "unhandled switch parameter '$captured{$param}' for line:\n    $line\nleft part:    $line_left\n\n";
	}

	return 0;
}

sub store
{
	$store_table = @_[0];
}

sub parse
{
	my ($parser, $string) = @_;

	undef $store_table;
	$line        = $string;
	$line_left   = $line;
	undef %captured;

	#print "parsing:\n";
	#print "   $line\n";

	$parser->();

	if ($line_left eq '')
	{
		matched;
	} else {
		unless ($mode_quiet) {
			print STDERR  "couldn't parse everything from line:\n    $line\nleft part:    $line_left\n\n";
		}
	}
}

my $parser_4_1 = sub {
	my $packet_eth_header = qr/(?<timestamp>\d+-\d+-\d+ \d+:\d+:\d+\.\d+) (?<mac_src>\S+) > (?<mac_dst>\S+),/;

	my $packet_eth        = qr/ethertype (?<ether_proto>(\S| )+?) \(\S+\), length:? (?<length>\d+):?/;
	my $packet_eth_arp    = qr/Ethernet \(len \d+\), (?<net_proto>\S+) \(len \d+\), (((?<type>Request) who-has (?<addr_to>\S+)(?: \(\S+\))? tell (?<addr_from>\S+), length \d+)|((?<type>Reply) (?<addr_from>\S+) is-at (?<mac_from>\S+), length \d+))/;
	my $packet_eth_ipv4   = qr/\((?:tos +(\S+), )?(?:ttl +(\d+), )?(?:id +(\d+), )?(?:offset +(\d+), )?(?:flags \[(\S+)\], )?(?:proto (?<trans_proto>\S+).*?, )?(?:length:? (\d+))?.*?\)\s+(?<ip_src>\d+\.\d+\.\d+\.\d+)(?:\.(?<port_src>\d+))? > (?<ip_dst>\d+\.\d+\.\d+\.\d+)(?:\.(?<port_dst>\d+))?:/; 

	match $packet_eth_header || return;
	store 'packet_eth_others';

	match_one {
		$packet_eth => sub {
		store 'packet_eth';

		switch_on 'ether_proto', {
		'arp' => sub {
			match_one { $packet_eth_arp => sub {
				store('packet_eth_arp');
			}};
			warn_and_ignore_rest;
		},

		'ipv4' => sub {
			match_one { $packet_eth_ipv4 => sub{
				store('packet_eth_ipv4');
				switch_on 'trans_proto', {
				'tcp'  => sub { ignore_rest },
				'udp'  => sub { ignore_rest },
				'igmp' => sub { ignore_rest },
				'icmp' => sub { ignore_rest }
				}
			}}
		},

		'ipv6' => sub {
			warn_and_ignore_rest;
	
		},

		'pppoe d' => sub {
			ignore_rest;
		}};
	}};
	ignore_rest;
};

main:
{
	if ($ARGV[0] eq "-q") {
		$mode_quiet = 1;
		shift @ARGV
	}

	my $dbfile = $ARGV[0] || "packets.db";

	my $dbargs = {AutoCommit => 0, PrintError => 1};
	$dbh = DBI->connect("dbi:SQLite:dbname=$dbfile","","",$dbargs);
	if ($dbh->err()) { die "$DBI::errstr\n"; }

	my ($next_line, $process);
	$_ = <STDIN>;

	while ($next_line = <STDIN>)
	{
		chomp;
		if ($next_line =~ /^\s/) {
			$process .= $_;
		} else {
			$process .= $_;
			parse ($parser_4_1, $process);
			undef $process;
		}
	}
	continue
	{
		$_ = $next_line;
	}

	$dbh->commit();
	$dbh->disconnect();
}

