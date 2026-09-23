#!/usr/bin/env python
"""Label the profiles of a vertically pointing radar as precipitation, virga
or noise, and report how often each occurs.

    python classify_profiles.py example/MZS_MRR_2024-01_5min.nc
    python classify_profiles.py "data/*.nc" --gate 2 --hourly --out labels.csv

The input is one NetCDF file or a glob matching several, each carrying ``Ze``
in dBZ over ``(time, range)``. Files are concatenated along time in name
order, so monthly files sort correctly when their names begin with the date.

Reference: Roversi et al., Virga hidden within the blind zone of spaceborne
radars, Atmospheric Chemistry and Physics, submitted.
"""

import argparse
import glob
import sys

from snowreach import classify, occurrence, to_hourly
from snowreach.classify import DEFAULT_GATE, DEFAULT_THRESHOLD
from snowreach.io import open_mrr


def open_all(pattern):
    paths = sorted(glob.glob(pattern))
    if not paths:
        sys.exit("no file matches %r" % pattern)
    return open_mrr(pattern), paths


def main(argv=None):
    p = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("input", help="NetCDF file, or a glob in quotes")
    p.add_argument("--gate", type=int, default=DEFAULT_GATE,
                   help="index of the lowest gate free of ground clutter "
                        "(default %(default)s, about 105 m for an MRR-2)")
    p.add_argument("--threshold", type=float, default=DEFAULT_THRESHOLD,
                   help="reflectivity above which a gate counts as signal, "
                        "in dBZ (default %(default)s, which does not filter)")
    p.add_argument("--hourly", action="store_true",
                   help="also aggregate the labels to hourly resolution by "
                        "majority vote")
    p.add_argument("--out", metavar="CSV",
                   help="write the per-step labels to this file")
    args = p.parse_args(argv)

    ds, paths = open_all(args.input)
    print("read %d file(s), %d time steps"
          % (len(paths), ds.sizes["time"]))
    height = float(ds["height"].isel(time=0, range=args.gate).values)
    print("reference gate %d at %.0f m, threshold %.1f dBZ\n"
          % (args.gate, height, args.threshold))

    labels = classify(ds, gate=args.gate, threshold=args.threshold)
    table = occurrence(labels)
    print(table.to_string(float_format=lambda v: "%.1f" % v))

    bearing = table.loc[["precip", "virga", "noise"], "count"].sum()
    if bearing:
        print("\nvirga is %.1f %% of the %d hydrometeor-bearing profiles"
              % (table.loc["virga", "share_of_bearing"], bearing))

    if args.hourly:
        hourly = to_hourly(labels)
        print("\nhourly, by majority vote:")
        print(occurrence(hourly).to_string(
            float_format=lambda v: "%.1f" % v))

    if args.out:
        labels.to_csv(args.out, header=True)
        print("\nwrote", args.out)


if __name__ == "__main__":
    main()
