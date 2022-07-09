# admin_scripts
Scripts for administration

Deduplication of directories

** First thing first, use at your own risk.

Use dedup.py to generate cmp.sh and rm.sh under a job directory, then run cmp.sh to make sure files are identical.

Files are compared with both their hashes (sha256) and sizes.

<pre>
$ ./dedup.py 

paths[0] = /a1/directory123

files: 15333
links: 0

paths[1] = /a1/directory456

files: 15333
links: 0

conf {'keep_option': 'z', 'keep_path_i': 1, 'skip_empty': 'skip'}

job-100604/cmp.sh: file generated
job-100604/rm.sh: file generated

runtime: 1.38 seconds
$ cd job-100604/
$ sh cmp.sh
$
</pre>

The following is no longer supported.

---

find.sh and cmp.sh are coupled scripts for dedup purpose.
I am not sure if there exists any utility for this task now so keep these small scripts in my bin.

** Use at your own risk. I may make it safer with more checking and verbose to avoid misuse.

1. find.sh searches for files of the same name in a target directory, and calls cmp.sh to compare them with /usr/bin/cmp.
2. /usr/bin/cmp returns 0 for identical files, if will generate 2 scripts in a job directory (e.g. /tmp)
3. The 2 scripts in the job directory, are just named cmp.sh and rm.sh
4. Change to the job directory and run cmp.sh for final check. If it does not gives any error, run rm.sh to remove the duplicates.
5. Deletion can happen either in the source or the target directory.

Usage: $0 -d dir -e (s | t) [-s] file

-d dir    target directory
-e (s|t)  where deletion will eventually happen. s for source and t for target
-s        default no searching so locate duplicates under the same directory structure. When specified, search with /usr/bin/find in the target directory.

Given 2 directories source and target, run this command set to remove duplicates in target (-e t).

<pre>
$ cd source
$ find . -type f -exec find.sh -d ../target -e t {} \;
$ sh /tmp/cmp.sh
$ sh /tmp/rm.sh
</pre>

---

dedup.sh and dedup.pl are similar but for a single directory.

** Again use at your own risk. I may make it safer with more checking and verbose to avoid misuse.

Usage: $0 -d dir

<pre>
$ dedup -d target
</pre>
