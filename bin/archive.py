#! /usr/bin/env python3
# Copyright (c) 2021 Paul Barker <paul@pbarker.dev>
# SPDX-License-Identifier: Apache-2.0

"""
This script is used to archive files for long-term storage. Given a source
directory of files to be archived, it produces:

    1) A signed checksum file which can be used to verify that data remains
    intact and unmodified.

    2) A compressed and encrypted tarball suitable for long term storage
    off-site or in the cloud.

The following configuration keys are read from the YAML file
`~/.config/archive.yml`:

    keyid: The gpg key to be used for signing and encrypting.
"""

import os
import shutil
import subprocess
import sys
import tempfile
import textwrap
import yaml


def usage():
    print(
        textwrap.dedent(
            f"""\
            Usage: {sys.argv[0]} SOURCE [NAME]
                Archives files in SOURCE for long-term storage.
                Store output in SOURCE.archive or NAME.archive if a name is given.
                Configuration is read from `~/.config/archive.yml`.\
            """
        )
    )


def set_readonly(path):
    ro_mode = os.stat(path).st_mode & 0o555
    os.chmod(path, ro_mode)


if len(sys.argv) >= 2 and sys.argv[1] in ("-h", "--help"):
    usage()
    sys.exit(0)

if len(sys.argv) not in (2, 3):
    usage()
    sys.exit(1)

SOURCE_PATH = sys.argv[1]
if len(sys.argv) == 3:
    IDENT = sys.argv[2]
else:
    IDENT = SOURCE_PATH

with open(os.path.expanduser("~/.config/archive.yml")) as config_file:
    config = yaml.safe_load(config_file)
    KEYID = config["keyid"]

# Set files are read-only
out_dir = os.getcwd()
os.chdir(SOURCE_PATH)
files_list = []
for dirpath, dirnames, fnames in os.walk("."):
    files_list += [os.path.normpath(os.path.join(dirpath, fname)) for fname in fnames]
    for name in fnames + dirnames:
        set_readonly(os.path.join(dirpath, name))

# Create checksums file
checksum_path = "B2SUMS"
with tempfile.NamedTemporaryFile() as tmpf:
    subprocess.run(["b2sum", *files_list], stdout=tmpf, check=True)
    subprocess.run(
        ["gpg", "-as", "--clearsign", "-u", KEYID, "-o", checksum_path, tmpf.name],
        check=True
    )
set_readonly(checksum_path)
set_readonly(".")

# Create encrypted tarball
tarball_path = os.path.join(out_dir, f"{IDENT}.archive")
with tempfile.NamedTemporaryFile(dir=out_dir) as tmpf:
    subprocess.run(["tar", "-c", "--zstd", "B2SUMS", *files_list], stdout=tmpf, check=True)
    subprocess.run(["gpg", "-e", "-r", KEYID, "-o", tarball_path, tmpf.name], check=True)
set_readonly(tarball_path)
print(f"Encrypted archive: {tarball_path}")
