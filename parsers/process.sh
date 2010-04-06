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
		./sqlite2gv.py -d "${DB}" -i -m -o "${OUTPUT}"
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
			do_draw_graph $algo png "${DIR}/tmp-mac-ip.gv" "${DIR}/mac-ip-$algo.png"
			do_draw_graph $algo png "${DIR}/tmp-ip-port.gv" "${DIR}/ip-port-$algo.png"
		done
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
