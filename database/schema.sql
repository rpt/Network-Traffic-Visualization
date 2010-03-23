create table if not exists packet_eth (
	timestamp TIMESTAMP,
	mac_src TEXT,
	mac_dst TEXT,
	etherproto TEXT,
	length INTEGER
);

create table if not exists packet_eth_arp (
	timestamp TIMESTAMP,
	mac_src TEXT,
	mac_dst TEXT,
	etherproto TEXT,
	length INTEGER,
	net_proto TEXT,
	type TEXT,
	addr_from TEXT,
	addr_to TEXT,
	mac_from
);
