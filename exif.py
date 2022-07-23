#!/usr/bin/python3

"""

[2022072301]

Script to extract EXIF metadata from image files
    by Terence LEE <telee.hk@gmail.com>

"""

import sys
import exifread

inc_tag_list0 = []
inc_tag_list = [
    'EXIF DateTimeOriginal'
]


def read_exif(image_path):
    with open(image_path, 'rb') as f:
        return exifread.process_file(f)


if __name__ == '__main__':
    path = ""
    argc = len(sys.argv)
    if argc > 1:
        if argc > 2:
            print("{0}: only the first image file is read..".format(sys.argv[0]))
        path = sys.argv[1]
    else:
        exit("{0}: image file not specified".format(sys.argv[0]))

    exif_tags = read_exif(path)

    try:
        inc_tag_list
    except NameError:
        inc_tag_list = []

    if inc_tag_list:
        tags = inc_tag_list
    else:
        tags = exif_tags.keys()

    for tag in tags:
        print("{0}: {1}".format(tag, exif_tags[tag]))
