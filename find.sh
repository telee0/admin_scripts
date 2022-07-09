#!/bin/sh

#
# [20100510]
#

usage="Usage: $0 -d dir -e (s | t) [-s] file"

dir=""
delete=""
search="n"

while getopts :d:e:s opt; do
	case "$opt" in
	d) dir="$OPTARG";;
	e) delete="$OPTARG";;
	s) search="y";;
	[?]) echo >&2 $usage
		exit 1
		;;
	esac
done

shift `expr $OPTIND - 1`

if [ $# -le 0 -o -z "$dir" ]; then
	echo >&2 $usage
	exit 1
fi

if [ "$delete" != "s" -a "$delete" != "t" ]; then
	echo >&2 $usage
	exit 1
fi

if [ ! -d "$dir" ]; then
	echo >&2 "$dir: directory not found"
	exit 1
fi

source1="$1"
source2="`echo $source1 | sed -e 's/\[/\\\[/g' | sed -e 's/\]/\\\]/g'`"
file="`basename \"$source2\"`"

if [ "$search" = "y" ]; then
	find "$dir" -type f -iname "$file" -exec \
		cmp.sh -d $delete "$source1" "{}" \
		\;
else
	cmp.sh -d $delete "$source1" "$dir/$source1"
fi

