create table if not exists packet_eth (
	timestamp TIMESTAMP,
	mac_src TEXT,
	mac_dst TEXT,
	ether_proto TEXT,
	length INTEGER
);

create table if not exists packet_eth_others (
	timestamp TIMESTAMP,
	mac_src TEXT,
	mac_dst TEXT,
	ether_proto TEXT,
	length INTEGER
);

create table if not exists packet_eth_arp (
	timestamp TIMESTAMP,
	mac_src TEXT,
	mac_dst TEXT,
	ether_proto TEXT,
	length INTEGER,
	net_proto TEXT,
	type TEXT,
	addr_from TEXT,
	addr_to TEXT,
	mac_from
);

create table if not exists packet_eth_ipv4 (
	timestamp TIMESTAMP,
	mac_src TEXT,
	mac_dst TEXT,
	ether_proto TEXT,
	length INTEGER,
	ip_src TEXT,
	ip_dst TEXT,
	port_src INTEGER,
	port_dst INTEGER,
	trans_proto TEXT
);

create table if not exists packet_eth_ipv6 (
	timestamp TIMESTAMP,
	mac_src TEXT,
	mac_dst TEXT,
	ether_proto TEXT,
	length INTEGER,
	ip_src TEXT,
	ip_dst TEXT,
	port_src INTEGER,
	port_dst INTEGER,
	trans_proto TEXT
);

create view packet_eth_ipv4_unicast as select * from packet_eth_ipv4 where mac_dst is not 'ff:ff:ff:ff:ff:ff' and mac_dst is not '00:00:00:00:00:00' and mac_dst not like '01:00:5e:%' and ip_src is not '0.0.0.0';
