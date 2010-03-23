#!/usr/bin/env perl

#NOTE: parsers output of tcpdump run with -vttttnel options.

our ($tcpdump_version, $output);
our ($timestamp,$etherproto,$dip,$sip,$ttl,$tos,$id,$offset,$flags,$len,$sourcemac,$destmac,$ipflags,$sport,$dport,$proto,$rest, $dnshostresponse, $dnslookup, $dnsipresponse, $dnstype, $dnslookup);

sub parse_4_1 {
	# 4.1:
	# 2010-03-17 15:04:05.226949 00:22:b0:69:08:93 > 00:1c:25:9e:34:50, ethertype IPv4 (0x0800), length 66: (tos 0x0, ttl 115, id 32533, offset 0, flags [DF], proto TCP (6), length 52)    86.30.189.176.21458 > 172.16.174.253.48413: Flags [.], cksum 0x4e34 (correct), ack 2824557203, win 256, options [nop,nop,TS val 668903 ecr 87348339], length 0
	my ($line) = @_;
	my $parse = $line;

	if ($parse !~ /(\d+-\d+-\d+ \d+:\d+:\d+\.\d+) (\S+) > (\S+), /)
	{
		print ">>> ERROR ON LINE\n    $line\n";
		die;
	}
	$timestamp        =  $1 || "";
	$sourcemac        =  $2 || "";
	$destmac          =  $3 || "";

	$parse = $';

	if ($parse =~ /ethertype (\S+) \(\S+\), length:? (\d+):?/)
	{
		# ethernet

		$etherproto       =  $1 || "";
		$len              =  $2 || "";

		$parse = $';

		if ($etherproto eq "IPv4") {
			if ($parse =~ /(?:\S+ )?\((?:tos +(\S+), )?(?:ttl +(\d+), )?(?:id +(\d+), )?(?:offset +(\d+), )?(?:flags \[(\S+)\], )?(?:proto (\S+).*?, )?(?:length:? (\d+))?.*?\)\s+(\S+?)(?:\.(\d+))? > (\S+?)(?:\.(\d+))?: +(?:(\S+),? (.*?)|\d+[\+\*\-]* \d+\/\d+\/\d+ (\S+) (\S+) (\S+) .*?|\d+[\+\*\-]* (\S+) (\S+) .*?)?/ ) 
			{
				$tos              =  $1 || "";
				$ttl              =  $2 || "";
				$id               =  $3 || "";
				$offset           =  $4 || "";
				$ipflags          =  $5 || "";
				$proto            =  $6 || "";
				$len              =  $7 || "";
				$sip              =  $8 || "";
				$sport            =  $9 || "";
				$dip              = $10 || "";
				$dport            = $11 || "";
				$flags            = $12 || "";
				$rest             = $13 || "";
				$dnshostresponse  = $14 || "";
				$dnslookup        = $15 || "";
				$dnsipresponse    = $16 || "";
				$dnstype          = $17 || "";
				$dnslookup        = $18 || $dnslookup;
			} else {
				print ">>> ERROR ON LINE\n    $line\n";
				die;
			}
		} elsif($etherproto eq "ARP") {
			if ($parse =~ /Ethernet \(len \d+\), (\S+) \(len \d+\), Request who-has (\S+) tell (\S+), length (\d+)/ ) 
			{
				# Ethernet (len 6), IPv4 (len 4), Request who-has 172.17.76.254 tell 172.17.76.253, length 46
				$netproto = $1 || "";
				$to       = $2 || "";
				$from     = $3 || "";

			} elsif ($parse =~ /Ethernet .../) {
				# Ethernet (len 6), IPv4 (len 4), Reply 172.16.174.253 is-at 00:1c:25:9e:34:50, length 28

			} else {
				print ">>> ERROR ON LINE\n   $line\n";
				die;
			}

		} elsif($etherproto eq "IPv6") {

		} else {
			print ">>> ERROR ON LINE\n    $line\n";
			die;
		}
	} elsif ($parse =~ /^802.3/) {
		# 2010-03-20 16:58:47.675389 00:a0:d1:c5:74:81 > ff:ff:ff:ff:ff:ff, 802.3, length 98: LLC, dsap IPX (0xe0) Individual, ssap IPX (0xe0) Command, ctrl 0x03: IPX 802.2: 00000000.00:a0:d1:c5:74:81.0455 > 00000000.ff:ff:ff:ff:ff:ff.0455: ipx-netbios 50

	} else {
		print ">>> ERROR ON LINE\n    $line\n";
		die;
	}


	$timestamp =~ s/(.*?)\.\d+$/\1/;
	$sourcemac =~ s/,$//;
	$destmac   =~ s/,$//;
	$len       =~ s/:$//;
}

sub parse {
	undef $timestamp,$etherproto,$dip,$sip,$ttl,$tos,$id,$offset,$flags,$len,$sourcemac,$destmac,$ipflags,$sport,$dport,$proto,$rest, $dnshostresponse, $dnslookup, $dnsipresponse, $dnstype, $dnslookup;

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

