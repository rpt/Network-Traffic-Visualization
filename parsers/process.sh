#!/bin/sh

TCPDUMP=/usr/sbin/tcpdump
PARSER=./tcpdump2sqlite.pl
SQLITE=sqlite3
DB_SCHEMA=../database/schema.sql

case ${1} in
	"--clean")
		rm -f output/*/packets.db
		rm -f output/*/packets.db-journal
		rm -f output/*/*.gv
		rm -f output/*/*.png
		rmdir output/*
	;;
	*)
		for dump in ${@}; do
			BASE=$(basename "${dump}")
			DIR=output/"$BASE"
			mkdir -p "${DIR}" || exit 1

			DB="${DIR}/packets.db"

			${SQLITE} "${DB}" ".read ${DB_SCHEMA}"

			${TCPDUMP} -vttttnel -r "${dump}" |\
			${PARSER} "${DB}"

			# FIXME tutaj skrypty uruchomić
			# niech czytają z ${DB} i wrzucają obrazki do
			# ${DIR}
			./sqlite2gv.py ${DB} > ${DIR}/tmp-graph.gv
			./sqlite2gv-ip-port.py ${DB} > ${DIR}/tmp-graph-ip-port.gv

			ALGO=( dot neato fdp circo twopi )

			for algo in ${ALGO[@]} ; do
				$algo -Tpng -o ${DIR}/mac-ip-$algo.png ${DIR}/tmp-graph.gv
				$algo -Tpng -o ${DIR}/ip-port-$algo.png ${DIR}/tmp-graph-ip-port.gv
			done
		done
	;;
esac
