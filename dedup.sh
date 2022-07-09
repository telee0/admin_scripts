#!/bin/sh

#
# 20100414
#

usage="Usage: $0 -d dir"

dir=""

while getopts :d: opt; do
	case "$opt" in
	d) dir="$OPTARG";;
	[?]) echo >&2 $usage
		exit 1
		;;
	esac
done

shift `expr $OPTIND - 1`

if [ -z "$dir" ]; then
	echo >&2 $usage
	exit 1
fi

if [ ! -d "$dir" ]; then
	echo >&2 "$dir: directory not found"
	exit 1
fi

files="/tmp/files.$$"
find $dir -type f -print | sort > $files
sed -e 's/\[/\\\[/g; s/\]/\\\]/g' $files > $files.sed

dedup.pl $files

exit

#
#
#

out="/tmp/out.$$"

n=0
while read line; do
	n=`expr $n + 1`
	f[$n]="$line"
	c=`expr $n % 100`
	if [ "$c" = "0" ]; then
		echo $n lines read >> $out
	fi
done < $files

n=0
while read line; do
	n=`expr $n + 1`
	b[$n]="`basename \"$line\"`"
	c=`expr $n % 100`
	if [ "$c" = "0" ]; then
		echo $n lines processed >> $out
	fi
done < $files.sed

if [ "$n" -le 1 ]; then
	exit 0
fi

i=1
while [ "$i" -lt "$n" ]; do
	j=`expr $i + 1`
	while [ "$j" -le "$n" ]; do
		if [ "${b[$i]}" = "${b[$j]}" ]; then
			cmp.sh -d t "${f[$i]}" "${f[$j]}"
		fi
		c=`expr $j % 100`
		if [ "$c" = "0" ]; then
			echo i=$i, j=$j compared >> $out
		fi
		j=`expr $j + 1`
	done
	i=`expr $i + 1`
done

