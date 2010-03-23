#!/usr/bin/env perl

use DBI;
use strict;

our ($dbh);

sub store
{
	my $table = @_[0];
	my $c = join(", ", map {$dbh->quote_identifier($_)} keys %+);
	my $v = join(", ", map {$dbh->quote(lc($_))}        values %+);

	#print("insert into $table ($c) values ($v)\n");
	$dbh->do("insert into $table ($c) values ($v)");
	if ($dbh->err()) { die "$DBI::errstr\n"; }
}

sub parse_4_1
{
	my $packet_eth = '(?<timestamp>\d+-\d+-\d+ \d+:\d+:\d+\.\d+) (?<mac_src>\S+) > (?<mac_dst>\S+), ethertype (?<etherproto>\S+) \(\S+\), length:? (?<length>\d+):?';
	my $packet_eth_arp = $packet_eth . '\s+' . '(Ethernet \(len \d+\), (?<net_proto>\S+) \(len \d+\), (?<type>Request) who-has (?<addr_to>\S+) tell (?<addr_from>\S+), length \d+)' . '|' .
		                                   '(Ethernet \(len \d+\), (?<net_proto>\S+) \(len \d+\), (?<type>Reply) (?<addr_from>\S+) is-at (?<mac_from>\S+), length \d+)';

	my %regexps = (
		packet_eth     => qr/$packet_eth/,
		packet_eth_arp => qr/$packet_eth_arp/
	);

	while (my ($table, $regex) = each(%regexps))
	{
		store $table if ($_[0] =~ $regex);
	}
}

sub parse
{
	parse_4_1 @_;
}

main:
{
	my $dbfile = $ARGV[1] || "packets.db";

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
			parse $process;
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

