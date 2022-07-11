#!/usr/bin/python3

"""

[2022070901]

Script to identify duplicate files w/ names and hashes
    from a list of directories then remove them accordingly

    by Terence LEE <telee.hk@gmail.com>

"""

import os.path
import hashlib
import json
import timeit
from datetime import datetime
from os import makedirs

verbose, debug = True, False

paths = [
    '/Downloads/VM',
    '/Downloads/UNIX'
]

cf = {
    # 'keep_option': 'i',         # keep files in paths[i]
    'keep_option': 'a',       # keep the oldest files
    # 'keep_option': 'z',       # keep the newest files
    'keep_path_i': [1],         # indexes of the paths in paths[] for keep_option == i
    'db_option': 'default',     # db option, default is python dictionary
    'hash_length': 16,          # 16 hex chars from sha256 (256 bits/64 hex chars)
    'skip_empty': 'skip'        # skip empty files to save time
}

job_files = {
    'cmp_list': 'cmp.sh',
    'rm_list': 'rm.sh',
    'db_files': 'db_files.json',
    'paths': 'paths.json',
    'cf': 'cf.json',
}

#
# dictionary db_files with hash[0:16]-size as keys.
# (pending) Options to scale include sqlite/redis/memcached/mysql/mongodb..

db_files = {}


#
# https://stackoverflow.com/questions/22058048/hashing-a-file-in-python/44873382

def gen_hash(file):
    h = hashlib.sha256()
    b = bytearray(128*1024)
    mv = memoryview(b)
    with open(file, 'rb', buffering=0) as f:
        while True:
            n = f.readinto(mv)
            if not n:
                break
            h.update(mv[:n])
    return h.hexdigest()


def scan_path(path, index):
    dirs, files, links = [], [], []

    if os.path.isfile(path):
        files.append(path)
    elif os.path.isdir(path):
        dirs.append(path)
    elif os.path.islink(path):
        links.append(path)

    n_dirs = 0
    time_start = timeit.default_timer()

    while len(dirs) > 0:
        d = dirs[0]
        dirs.pop(0)
        for name in os.listdir(d):
            p = os.path.join(d, name)
            if os.path.isfile(p):
                stat = os.stat(p)
                if stat.st_size == 0 and cf["skip_empty"] == "skip":
                    continue  # skip empty files as they can be deleted efficiently with find
                file_hash = gen_hash(p)
                key = "{0}-{1}".format(file_hash[:cf["hash_length"]], stat.st_size)
                if key not in db_files:
                    db_files[key] = []
                db_files[key].append({'index': index, 'path': p, 'mtime': stat.st_mtime, 'hash': file_hash})
                if debug:
                    print("file metadata: ", stat)
                files.append(p)
            elif os.path.isdir(p):
                dirs.append(p)
                n_dirs += 1
            elif os.path.islink(p):
                links.append(p)
            time_elapsed = timeit.default_timer() - time_start
            if time_elapsed > 1:
                print(".", end="", flush=True)
                time_start = timeit.default_timer()

    return files, links, n_dirs


def write_job_files(cmd_lists):
    cmp_list, rm_list = cmd_lists

    if len(rm_list) == 0:
        print("rm_list: nothing to delete per config")
        return ""

    t = datetime.now().strftime('%Y%m%d%H%M')
    ddhhmm = t[6:12]
    job_dir = "job-{0}".format(ddhhmm)
    makedirs(job_dir, exist_ok=True)

    for name, file in job_files.items():
        file = "{0}/{1}".format(job_dir, file)
        with open(file, 'a') as f:
            if file.endswith(".json"):
                f.write(json.dumps(eval(name), indent=4))
            else:
                f.write("\n".join(eval(name)))
        print("{0}: file generated".format(file))

    return job_dir


def go():
    time_start = timeit.default_timer()

    for index, path in enumerate(paths):
        if verbose:
            print()
            print("paths[{0}] = {1}".format(index, path))

        files, links, n_dirs = scan_path(path, index)

        if verbose:
            print()
            print("files: {0}".format(len(files)))
            print("links: {0}".format(len(links)))
            print("dirs: {0}".format(n_dirs))
            if debug:
                for file in files:
                    print("{0}".format(file))

    cmp_list, rm_list = [], []

    for key in db_files.keys():
        files = db_files[key]  # files sharing the same hash
        n_files = len(files)
        if n_files > 1:
            sources = set()

            if cf["keep_option"] == 'i':
                for index, file in enumerate(files):
                    if file["index"] in cf["keep_path_i"]:
                        sources.add(index)
            elif cf["keep_option"] == 'a':
                oldest_i = 0
                for index, file in enumerate(files):
                    if file["mtime"] < files[oldest_i]["mtime"]:
                        oldest_i = index
                sources.add(oldest_i)
            elif cf["keep_option"] == 'z':
                newest_i = 0
                for index, file in enumerate(files):
                    if file["mtime"] > files[newest_i]["mtime"]:
                        newest_i = index
                sources.add(newest_i)
            else:
                print("{0}: unknown option to keep files".format(cf["keep_option"]))
                exit(1)

            targets = set(range(n_files)) - sources

            if not sources or not targets:  # skip if either sources or targets is empty
                continue                    # change keep_option to a/z to keep files by mtime

            if debug:
                print()
                print("sources", sources)
                print("targets", targets)

            for i in targets:
                file_target = files[i]
                for j in sources:
                    file_source = files[j]
                    cmp_list.append('cmp "{0}" "{1}"'.format(file_source["path"], file_target["path"]))
                rm_list.append('rm -f "{0}"'.format(file_target["path"]))

    if verbose:
        print("\ncf {0}\n".format(cf))

    job_dir = write_job_files([cmp_list, rm_list])

    if debug:
        for line in cmp_list:
            print(line)
        for line in rm_list:
            print(line)

    time_elapsed = timeit.default_timer() - time_start

    print("\nruntime: {0} seconds".format(round(time_elapsed, 2)))

    if job_dir:
        path = paths[0]
        if cf['keep_option'] == 'i':
            for i in range(1, len(paths)):
                if i not in cf['keep_path_i']:
                    path = paths[i]
                    break

        message = """
    # run cmp.sh in the job directory to make sure files are identical
    # run rm.sh to delete duplicate files

    cd %s
    sh cmp.sh
    sh rm.sh

    # when the files are deleted, paths may contain empty files and directories
    # use the following commands to clean it up

    cd %s
    find . -type f -empty -exec rm {} \\;
    find . -type d -empty -exec rmdir {} \\;""" % (job_dir, path)

        print(message)


if __name__ == "__main__":
    go()
