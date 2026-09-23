#!/usr/bin/env python
"""Assemble the archive to deposit on Zenodo.

    python make_release.py
    python make_release.py --example path/to/one_month.nc

The repository does not carry the example month: it is 3 MB of NetCDF that is
already published, so it is gitignored and copied in here instead. Everything
else goes in as it stands, minus the caches.

The result is snowreach-<version>.zip beside this script, with a single top
level folder so that unpacking it does not scatter files, and a manifest of
what went in. Nothing is uploaded: depositing is a deliberate act and it
needs a token and a person.
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
    "classify_profiles.py", "emulate_loh.py",
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

    print("""
Next, by hand, because depositing is not something a script should do on its
own:

  1. zenodo.org, New upload, drop %s
  2. paste the metadata from zenodo.json
  3. reserve the DOI before publishing, so it can go into the paper
  4. publish, then send the DOI to papers/P1_virga_mzs (codedataavailability)
""" % out)


if __name__ == "__main__":
    main()
