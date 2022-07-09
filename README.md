# admin_scripts
Scripts for administration

find.sh and cmp.sh are coupled scripts for dedup purpose.
I am not sure if there exists any utility for this task now so keep these small scripts in my bin.

** Use at your own risk. I may make it safer with more checking and verbose to avoid wrong use.

1. find.sh searches for files of the same name in a target directory, and calls cmp.sh to compare them with /usr/bin/cmp.
2. /usr/bin/cmp returns 0 for identical files, if will generate 2 scripts in a job directory (e.g. /tmp)
3. The 2 scripts in the job directory, are just named cmp.sh and rm.sh
4. Change to the job directory and run cmp.sh for final check. If it does not gives any error, run rm.sh to remove the duplicates.
5. Deletion can happen either in the source or the target directory.

Usage: $0 -d dir -e (s | t) [-s] file

-d dir    target directory
-e (s|t)  where deletion will eventually happen. s for source and t for target
-s        default no searching so locate duplicates under the same directory structure. When specified, search with /usr/bin/find in the target directory.

Given 2 directories source and target, run this command set to remove duplicates.

<pre>
$ cd source
$ find . -type f -exec find.sh -d ../target -e t {} \;
$ sh /tmp/cmp.sh
$ sh /tmp/rm.sh
</pre>
