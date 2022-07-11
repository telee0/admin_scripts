# admin_scripts
Scripts for administration

Deduplication of directories

** First thing first, use at your own risk.

Use dedup.py to generate cmp.sh and rm.sh under a job directory, then run cmp.sh to make sure files are identical.

Files are compared with both their hashes (sha256) and sizes.

Python dictionary db_files with hash[0:hash_length]-size as keys. Options to be explored include sqlite/redis/memcached/mysql/mongodb..

Configuration is embedded in the script, but will later be separated.

Multiple directories are supported.

<pre>
paths = [
    '/a1/backup-2021',
    '/a2/backup-2021',
    '/b1/backup-2021'
]

cf = {
    'keep_option': 'i',         # keep files in paths[i]
    # 'keep_option': 'a',       # keep the oldest files
    # 'keep_option': 'z',       # keep the newest files
    'keep_path_i': [1],         # indexes of the paths in paths[] for keep_option == i
    'db_option': 'default',     # db option, default is python dictionary
    'hash_length': 16,          # 16 hex chars from sha256 (256 bits/64 hex chars)
    'skip_empty': 'skip'        # skip empty files to save time
}

root@raspi:~/bin/admin_scripts# python3 dedup.py 

paths[0] = /a1/backup-2021
...........................................
files: 1312
links: 0
dirs: 30

paths[1] = /a2/backup-2021
............................................................................................................
files: 1312
links: 0
dirs: 30

cf {'keep_option': 'i', 'keep_path_i': [1], 'db_option': 'default', 'hash_length': 16, 'skip_empty': 'skip'}

job-110014/cmp.sh: file generated
job-110014/rm.sh: file generated
job-110014/db_files.json: file generated
job-110014/cf.json: file generated

runtime: 196.19 seconds

    # run cmp.sh in the job directory to make sure files are identical
    # run rm.sh to delete duplicate files

    cd job-110014
    sh cmp.sh
    sh rm.sh

    # when the files are deleted, paths may contain empty files and directories
    # use the following commands to clean it up

    cd /a1/backup-2021
    find . -type f -empty -exec rm {} \;
    find . -type d -empty -exec rmdir {} \;
        
root@raspi:~/bin/admin_scripts# cd job-110014/
$ sh cmp.sh
$
</pre>

The following has no more development.

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
