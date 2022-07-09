#!/usr/bin/python3

"""

[2022070901]

Script to identify duplicate files w/ names and hashes
    from a list of directories then remove them accordingly

    by Terence LEE <telee.hk@gmail.com>

"""

import os.path
import hashlib
import timeit
from datetime import datetime
from os import makedirs

verbose, debug = True, False

paths = [
    '/Downloads/VM',
    '/Downloads/UNIX'
]

conf = {
    # 'keep_option': 'i',   # keep files in paths[i]
    # 'keep_option': 'a',   # keep the oldest files
    'keep_option': 'z',     # keep the newest files
    'keep_path_i': 1,       # index of the path in paths[]
    'skip_empty': 'skip'    # skip empty files to save time
}

db_files = {}


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


def get_files(path, index):
    dirs, files, links = [], [], []

    if os.path.isfile(path):
        files.append(path)
    elif os.path.isdir(path):
        dirs.append(path)
    elif os.path.islink(path):
        links.append(path)

    while len(dirs) > 0:
        d = dirs[0]
        dirs.pop(0)
        for name in os.listdir(d):
            time_start = timeit.default_timer()
            p = os.path.join(d, name)
            if os.path.isfile(p):
                stat = os.stat(p)
                if stat.st_size == 0 and conf["skip_empty"] == "skip":
                    continue  # skip empty files as they can be deleted efficiently with find
                file_hash = gen_hash(p)
                file_hash = "{0}-{1}".format(file_hash[:16], stat.st_size)
                if file_hash not in db_files:
                    db_files[file_hash] = []
                db_files[file_hash].append({'index': index, 'path': p, 'mtime': stat.st_mtime})
                # print("file metadata: ", stat)
                files.append(p)
            elif os.path.isdir(p):
                dirs.append(p)
            elif os.path.islink(p):
                links.append(p)
            time_elapsed = timeit.default_timer() - time_start
            if time_elapsed > 1:
                print(".", end="")

    return files, links


def write_scripts(cmp_list, rm_list):
    t = datetime.now().strftime('%Y%m%d%H%M')
    # yyyymm = t[0:6]
    ddhhmm = t[6:12]
    path = "job-{0}".format(ddhhmm)
    makedirs(path, exist_ok=True)
    cmp_file = "{0}/{1}".format(path, "cmp.sh")
    with open(cmp_file, 'a') as f:
        f.write("\n".join(cmp_list))
    rm_file = "{0}/{1}".format(path, "rm.sh")
    with open(rm_file, 'a') as f:
        f.write("\n".join(rm_list))
    print()
    for file in [cmp_file, rm_file]:
        print("{0}: file generated".format(file))


def go():
    for index, path in enumerate(paths):
        if verbose:
            print()
            print("paths[{0}] = {1}".format(index, path))

        files, links = get_files(path, index)

        if verbose:
            print()
            print("files: {0}".format(len(files)))
            print("links: {0}".format(len(links)))
            for file in files:
                if debug:
                    print("{0}".format(file))

    cmp_list, rm_list = [], []

    for key in db_files.keys():
        files = db_files[key]  # files sharing the same hash
        n_files = len(files)
        if n_files > 1:
            sources = set()

            if conf["keep_option"] == 'i':
                for index, file in enumerate(files):
                    if file["index"] == conf["keep_path_i"]:
                        sources.add(index)
            elif conf["keep_option"] == 'a':
                oldest_i = 0
                for index, file in enumerate(files):
                    if file["mtime"] < files[oldest_i]["mtime"]:
                        oldest_i = index
                sources.add(oldest_i)
            elif conf["keep_option"] == 'z':
                newest_i = 0
                for index, file in enumerate(files):
                    if file["mtime"] > files[newest_i]["mtime"]:
                        newest_i = index
                sources.add(newest_i)
            else:
                print("{0}: unknown option to keep files".format(conf["keep_option"]))
                exit(1)

            if len(sources) == 0:   # skip if no source all targets, because none left after deletion
                continue            # change keep_option to a/z to keep files by mtime

            targets = set(range(n_files)) - sources

            if verbose:
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
        print("\nconf", conf)

    write_scripts(cmp_list, rm_list)

    if debug:
        for line in cmp_list:
            print(line)
        for line in rm_list:
            print(line)


go()
