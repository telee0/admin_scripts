#!/bin/sh

#
# [20070909]
#

usage="Usage: $0 [-c] [-d (s | t) ] source target"

cmp_sh="/tmp/cmp.sh"
rm_sh="/tmp/rm.sh"

delete=0

while getopts :cd: opt; do
	case "$opt" in
	c)
		rm -f $cmp_sh
		rm -f $rm_sh
		;;
	d) delete="$OPTARG";;
	[?]) echo >&2 $usage
		exit 1
		;;
	esac
done

shift `expr $OPTIND - 1`

if [ $# -le 1 ]; then
	echo >&2 $usage
	exit 1
fi

source="$1"
target="$2"

if [ ! -f "$source" ]; then
	echo >&2 "$source: file not found"
	exit 1
fi

if [ ! -f "$target" ]; then
	echo >&2 "$target: file not found"
	exit 1
fi

cmp -s "$source" "$target"

if [ $? -eq 0 ]; then
	echo cmp "\"$source\"" "\"$target\"" >> $cmp_sh
	if [ "$delete" = "s" ]; then
		echo rm -f "\"$source\"" >> $rm_sh
	elif [ "$delete" = "t" ]; then
		echo rm -f "\"$target\"" >> $rm_sh
	fi
fi
