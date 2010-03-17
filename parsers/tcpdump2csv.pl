#!/usr/bin/env perl

use strict;

our ($tcpdump_version, $output);
our ($timestamp,$etherproto,$dip,$sip,$ttl,$tos,$id,$offset,$flags,$len,$sourcemac,$destmac,$ipflags,$sport,$dport,$proto,$rest, $dnshostresponse, $dnslookup, $dnsipresponse, $dnstype, $dnslookup);

sub parse_4_1 {
	# 4.1:
	# 2010-03-17 15:04:05.226949 00:22:b0:69:08:93 > 00:1c:25:9e:34:50, ethertype IPv4 (0x0800), length 66: (tos 0x0, ttl 115, id 32533, offset 0, flags [DF], proto TCP (6), length 52)    86.30.189.176.21458 > 172.16.174.253.48413: Flags [.], cksum 0x4e34 (correct), ack 2824557203, win 256, options [nop,nop,TS val 668903 ecr 87348339], length 0
	my ($line) = @_;

	if ($line !~ /(\d+-\d+-\d+ \d+:\d+:\d+\.\d+) (\S+) > (\S+), ethertype (\S+) \(\S+\), length:? (\d+):? (?:\S+ )?\((?:tos +(\S+), )?(?:ttl +(\d+),     )?(?:id +(\d+), )?(?:offset +(\d+), )?(?:flags \[(\S+)\], )?(?:proto: (\S+).*?, )?(?:length: (\d+))?.*?\)\s+(\S+?)(?:\.(\d+))? > (\S+?)(?:\.(\d+))?: +(?:(\S+),? (.*?)|\d+[\+\*\-]* \d+\/\d+\/\d+ (\S+) (\S+) (\S+) .*?|\d+[\+\*\-]* (\S+) (\S+) .*?)?/ ) 
	{
		print ">>> ERROR ON LINE\n    $line\n";
		return;
	}

	$timestamp        =  $1 || "";
	$sourcemac        =  $2 || "";
	$destmac          =  $3 || "";
	$etherproto       =  $4 || "";
	$len              =  $5 || "";
	$tos              =  $6 || "";
	$ttl              =  $7 || "";
	$id               =  $8 || "";
	$offset           =  $9 || "";
	$ipflags          = $10 || "";
	$proto            = $11 || "";
	$len              = $12 || "";
	$sip              = $13 || "";
	$sport            = $14 || "";
	$dip              = $15 || "";
	$dport            = $16 || "";
	$flags            = $17 || "";
	$rest             = $18 || "";
	$dnshostresponse  = $20 || "";
	$dnslookup        = $21 || "";
	$dnsipresponse    = $22 || "";
	$dnstype          = $23 || "";
	$dnslookup        = $24 || $dnslookup;

	$timestamp =~ s/(.*?)\.\d+$/\1/;
	$sourcemac =~ s/,$//;
	$destmac   =~ s/,$//;
	$len       =~ s/:$//;
}

sub parse {
	# FIXME: check version
	parse_4_1 @_;

	if ($output eq "full") {
		print "$sip,$dip,$sport,$dport\n";
	} else {
		my @tokens = split / /,$output;
		print ${shift(@tokens)};
		for my $token (@tokens) {
			if (defined($$token)) {
				print ','.$$token;
			}
		}
		print "\n";
	}

}

################################################################

$tcpdump_version = "4.1";
$output = $ARGV[0] || "full";

my ($next_line, $process);
$_ = <>;

while ($next_line = <>)
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

