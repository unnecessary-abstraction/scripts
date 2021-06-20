#! /usr/bin/env python3
# Copyright (c) 2021 Paul Barker <paul@pbarker.dev>
# SPDX-License-Identifier: Apache-2.0

"""
This script is used to archive files for long-term storage. Given a source
directory of files to be archived, it produces 3 outputs:

    1) `files`: A copy of the archived files in their original form, marked as
    read-only to prevent accidental modification.

    2) `checksums`: A signed checksum file for each set of archived files which can
    be used to verify that the copy under `files` is intact and unmodified.

    3) `tarballs`: A compressed and encrypted tarball for each set of archived
    files, suitable for long term storage off-site or in the cloud.

The following configuration keys are read from the YAML file
`~/.config/archive.yml`:

    archive_path: The destination path for archived content.

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
            Usage: {sys.argv[0]} IDENT SOURCE
                Archives files in SOURCE for long-term storage with the identifier IDENT.
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

if len(sys.argv) != 3:
    usage()
    sys.exit(1)

IDENT, SOURCE_PATH = sys.argv[1:]

with open(os.path.expanduser("~/.config/archive.yml")) as config_file:
    config = yaml.safe_load(config_file)
    ARCHIVE_PATH = os.path.expanduser(os.path.expanduser(config["archive_path"]))
    KEYID = config["keyid"]

# Copy files to destination
files_dest_path = os.path.join(ARCHIVE_PATH, "files", IDENT)
os.makedirs(os.path.dirname(files_dest_path))
shutil.copytree(SOURCE_PATH, files_dest_path)
os.chdir(files_dest_path)
files_list = []
for dirpath, dirnames, fnames in os.walk("."):
    files_list += [os.path.normpath(os.path.join(dirpath, fname)) for fname in fnames]
    for name in fnames + dirnames:
        set_readonly(os.path.join(dirpath, name))
set_readonly(".")
print(f"Archived to: {files_dest_path}")

# Create checksums file
checksum_path = os.path.join(ARCHIVE_PATH, "checksums", f"{IDENT}.b2sum")
os.makedirs(os.path.dirname(checksum_path))
with tempfile.NamedTemporaryFile() as tmpf:
    subprocess.run(["b2sum", *files_list], stdout=tmpf, check=True)
    subprocess.run(
        ["gpg", "-as", "--clearsign", "-u", KEYID, "-o", checksum_path, tmpf.name]
    )
set_readonly(checksum_path)
print(f"Checksums: {checksum_path}")

# Create encrypted tarball
tarball_path = os.path.join(ARCHIVE_PATH, "tarballs", f"{IDENT}.archive")
os.makedirs(os.path.dirname(tarball_path))
with tempfile.NamedTemporaryFile() as tmpf:
    subprocess.run(["tar", "cJ", *files_list], stdout=tmpf, check=True)
    subprocess.run(["gpg", "-e", "-r", KEYID, "-o", tarball_path, tmpf.name])
set_readonly(tarball_path)
print(f"Encrypted tarball: {tarball_path}")
