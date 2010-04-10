#!/bin/sh

TCPDUMP=/usr/sbin/tcpdump
PARSER="./tcpdump2sqlite.pl -q"
SQLITE=sqlite3
DB_SCHEMA=../database/schema.sql

cleanflag=off
mergeflag=off
drawflag=off
graphsflag=off
databaseflag=off

function usage {
	echo >&2  "usage: $0 [--merge] file [file ...]"
	echo >&2  "       $0 --db [--merge] file [file ...]"
	echo >&2  "       $0 --graphs"
	echo >&2  "       $0 --draw"
	echo >&2  "       $0 --clean"
}

function do_clean {
	echo -n "Cleaning... "
	rm -rf output
	echo "done."
}

function do_database_aux_tables {
    ${SQLITE} "$1" "create table tmp_packets_mac_ip as select mac_src, ip_src, mac_dst, ip_dst, count(*) as count, trans_proto from packet_eth_ipv4 where mac_dst is not 'ff:ff:ff:ff:ff:ff' and mac_dst is not '00:00:00:00:00:00' and mac_dst not like '01:00:5e:%' and ip_src is not '0.0.0.0' group by mac_src, ip_src, mac_dst, ip_dst;"
    ${SQLITE} "$1" "create table tmp_routers as select distinct mac from (select mac_dst as mac, count(distinct ip_dst) as c from tmp_packets_mac_ip group by mac union select mac_src as mac, count(distinct ip_src) as c from tmp_packets_mac_ip group by mac) where c >= 10;"
    ${SQLITE} "$1" "create table tmp_packets_multicast as select ip_src, ip_dst, count(*) as count, sum(length) as length from packet_eth_ipv4 where ip_multicast(ip_dst) group by ip_src, ip_dst;"
    ${SQLITE} "$1" "create table tmp_packets_ip_port as select ip_src, ip_dst, port_src, port_dst, count(*) as count, sum(length) as length, trans_proto from packet_eth_ipv4 where mac_dst is not 'ff:ff:ff:ff:ff:ff' and mac_dst is not '00:00:00:00:00:00' and mac_dst not like '01:00:5e:%' and ip_src is not '0.0.0.0' group by ip_src, ip_dst, port_src, port_dst, trans_proto;"
}

function do_database {
	if [ "$mergeflag" == "on" ]; then
		DIR=output/merged
		mkdir -p "${DIR}" || exit 1

		DB="${DIR}/packets.db"
		${SQLITE} "${DB}" ".read ${DB_SCHEMA}"

		for dump in ${@}; do
			echo -n "Processing ${dump}... "

			${TCPDUMP} -vttttnel -r "${dump}" 2>/dev/null |\
			${PARSER} "${DB}"

			echo "done."
		done
        do_database_aux_tables "${DB}"

	else
		for dump in ${@}; do
			BASE=$(basename -- "${dump}")
			DIR=output/"$BASE"
			mkdir -p "${DIR}" || exit 1

			DB="${DIR}/packets.db"

			if [ "${dump}" -nt "${DB}" ]; then
				echo -n "Processing ${dump}... "
				rm -f ${DB}
				rm -f ${DB}-journal
				${SQLITE} "${DB}" ".read ${DB_SCHEMA}"

				${TCPDUMP} -vttttnel -r "${dump}" 2>/dev/null |\
				${PARSER} "${DB}"
                do_database_aux_tables "${DB}"
				echo "done."
			fi
		done
	fi
}

function do_graphs {
	find -name 'packets.db' -print | while read DB
	do
		OUTPUT="$(dirname -- ${DB})/tmp"
		echo -n "Generating graph for ${DB}... "
		./sqlite2gv.py -d "${DB}" -i -m --ip-multicast --nodes-connections -o "${OUTPUT}"
		echo "done."
	done
}

function do_draw_graph {
	if [ "$3" -nt "$4" ]; then
		echo -n "Drawing $4... "
		$1 "$3" -T$2 -o "$4"
		echo "done."
	fi
}

function do_draw {
	find -name 'packets.db' -print | while read DB
	do
		DIR="$(dirname -- ${DB})"
		ALGO=( dot neato fdp circo twopi )
		for algo in ${ALGO[@]} ; do
			do_draw_graph $algo svg "${DIR}/tmp-mac-ip.gv" "${DIR}/mac-ip-$algo.svg"
			do_draw_graph $algo svg "${DIR}/tmp-ip-port.gv" "${DIR}/ip-port-$algo.svg"
		done
		do_draw_graph circo svg "${DIR}/tmp-ip-multicast.gv" "${DIR}/ip-multicast-circo.svg"
		do_draw_graph twopi svg "${DIR}/tmp-ip-multicast.gv" "${DIR}/ip-multicast-twopi.svg"
		do_draw_graph neato svg "${DIR}/tmp-ip-multicast.gv" "${DIR}/ip-multicast-neato.svg"
        do_draw_graph twopi svg "${DIR}/tmp-nodes-connections.gv" "${DIR}/nodes-connections.svg"
	done
}

while [ $# -gt 0 ]; do
	case "$1" in
		--db)
			databaseflag=on;;
		--merge)
			mergeflag=on;;
		--graphs)
			graphsflag=on;;
		--draw)
			drawflag=on;;
		--clean)
			cleanflag=on;;
		--) shift; break;;
		-*)
			usage;
			exit 1;;
		*) break;;
	esac
	shift
done

if [ "$graphsflag" == "off" ] && [ "$databaseflag" == "off" ] && [ "$drawflag" == "off" ]; then
	databaseflag=on
	graphsflag=on
	drawflag=on
fi

if [ $cleanflag == "off" ] && [ "$databaseflag" == "on" ] && [ $# -le 0 ]; then
	echo >&2 "no files given on command line"
	usage;
	exit 1;
fi

if [ $cleanflag == "on" ]; then
	do_clean
	exit $?
fi

if [ $databaseflag == "on" ]; then
	do_database $@ || exit 1;
fi

if [ $graphsflag == "on" ]; then
	do_graphs $@ || exit 1;
fi

if [ $drawflag == "on" ]; then
	do_draw $@ || exit 1;
fi
