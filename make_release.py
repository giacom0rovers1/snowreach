#!/usr/bin/env python
"""Assemble a standalone zip of the package.

    python make_release.py
    python make_release.py --example path/to/one_month.nc

This is not how releases are made: Zenodo archives the repository itself on
every GitHub release, so see RELEASING.md. What this script is for is handing
someone a self-contained copy without a clone.

The result is snowreach-<version>.zip beside this script, with a single top
level folder so that unpacking it does not scatter files, and a manifest of
what went in. The example month is normally a tracked file and is taken as it
is; --example replaces it, and if it is missing the script copies one in from
the local archive.
"""

import argparse
import hashlib
import os
import shutil
import sys
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_EXAMPLE = os.path.join(
    r"C:\Data\APP_MZS\monthly\MRR\MK\netcdf", "MZS_MRR_MeK_202011_5min.nc")
EXAMPLE_AS = os.path.join("example", "MZS_MRR_2020-11_5min.nc")

INCLUDE = [
    "README.md", "LICENSE", "CITATION.cff", "requirements.txt",
    "classify_profiles.py", "simulate_loh.py",
    os.path.join("snowreach", "__init__.py"),
    os.path.join("snowreach", "classify.py"),
    os.path.join("snowreach", "io.py"),
    os.path.join("snowreach", "loh.py"),
    os.path.join("snowreach", "zesr.py"),
    os.path.join("example", "README.md"),
]


def version():
    text = open(os.path.join(HERE, "snowreach", "__init__.py"),
                encoding="utf-8").read()
    for line in text.splitlines():
        if line.startswith("__version__"):
            return line.split("=")[1].strip().strip('"').strip("'")
    sys.exit("no __version__ in snowreach/__init__.py")


def main(argv=None):
    p = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--example", default=DEFAULT_EXAMPLE,
                   help="the month to ship as the worked example "
                        "(default: November 2020 from the local archive)")
    p.add_argument("--out", help="name of the archive to write")
    args = p.parse_args(argv)

    os.chdir(HERE)
    v = version()
    root = "snowreach-%s" % v
    out = args.out or root + ".zip"

    example = os.path.join(HERE, EXAMPLE_AS)
    if not os.path.exists(example):
        if not os.path.exists(args.example):
            sys.exit("the example month is missing and %s does not exist.\n"
                     "Pass --example with one monthly file from the published "
                     "archive." % args.example)
        os.makedirs(os.path.dirname(example), exist_ok=True)
        shutil.copy2(args.example, example)
        print("example copied from %s" % args.example)

    missing = [f for f in INCLUDE if not os.path.exists(f)]
    if missing:
        sys.exit("missing from the package: %s" % ", ".join(missing))

    files = INCLUDE + [EXAMPLE_AS]
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        for f in files:
            z.write(f, os.path.join(root, f).replace("\\", "/"))

    total = 0
    print("\n%-44s %10s  %s" % ("file", "bytes", "md5"))
    for f in files:
        data = open(f, "rb").read()
        total += len(data)
        print("%-44s %10d  %s"
              % (f.replace("\\", "/"), len(data),
                 hashlib.md5(data).hexdigest()[:12]))
    print("\n%s: %d files, %.2f MB packed, %.2f MB unpacked"
          % (out, len(files), os.path.getsize(out) / 1e6, total / 1e6))

    print("\nThis zip is a convenience copy. Releases are cut on GitHub and "
          "archived by Zenodo\nfrom the repository itself: see RELEASING.md.")


if __name__ == "__main__":
    main()
