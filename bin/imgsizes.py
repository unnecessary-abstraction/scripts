#! /usr/bin/env python3
# Copyright (c) 2021 Paul Barker <paul@pbarker.dev>
# SPDX-License-Identifier: Apache-2.0

"""
This script creates two new alternative versions of each image in the source
path given on the command line:

* 800: This version is indended for embedding in web pages or using as a
  preview. It's optimised for small file size and progressive loading.

* 1920: This version is indended for full screen viewing on a typical 1080p
  display whilst keeping a moderate file size.

Output directories are created for each of these alternatives so that filenames
remain unchanged.
"""

import os
import subprocess
import sys


def usage():
    print(f"Usage: {sys.argv[0]} SOURCE_PATH")
    print("  Create optimised 800px and 1920px versions of each image in SOURCE_PATH.")


if len(sys.argv) != 2:
    usage()
    sys.exit(1)

if sys.argv[1] in ("-h", "--help"):
    usage()
    sys.exit(0)

SOURCE_PATH = sys.argv[1]
if not os.path.exists(SOURCE_PATH):
    print(f"Source path '{SOURCE_PATH}' does not exist!")
    sys.exit(1)

if os.path.isdir(SOURCE_PATH):
    sources = [os.path.join(SOURCE_PATH, fname) for fname in os.listdir(SOURCE_PATH)]
else:
    sources = [SOURCE_PATH]

count = len(sources)
print(f"Converting {count} image(s)...")
os.makedirs("1920", exist_ok=True)
os.makedirs("800", exist_ok=True)
logfile = open("convert.log", "a")
had_error = False
for i, src in enumerate(sources):
    print(f"[{i+1}/{count}] {src}", end="", flush=True)
    dst = os.path.basename(src)
    try:
        subprocess.run(
            [
                # fmt: off
                "convert",
                "-verbose",
                "-strip",
                "-resize", "1920x1920>",
                "-interlace", "JPEG",
                "-quality", "92%",
                "-colorspace", "RGB",
                src, f"1920/{dst}",
                # fmt: on
            ],
            stdout=logfile,
            stderr=logfile,
            check=True,
        )
        print(" [1920 ✔]", end="", flush=True)
    except subprocess.CalledProcessError:
        had_error = True
        print(" [1920 ✖]", end="", flush=True)
    try:
        subprocess.run(
            [
                # fmt: off
                "convert",
                "-verbose",
                "-strip",
                "-resize", "800x800>",
                "-sampling-factor", "4:2:0",
                "-interlace", "JPEG",
                "-quality", "80%",
                "-colorspace", "RGB",
                src, f"800/{dst}",
                # fmt: on
            ],
            stdout=logfile,
            stderr=logfile,
            check=True,
        )
        print(" [800 ✔]", flush=True)
    except subprocess.CalledProcessError:
        had_error = True
        print(" [800 ✖]", flush=True)

if not had_error:
    print("All succeeded.")
    sys.exit(0)
else:
    print("Failed!")
    sys.exit(1)
