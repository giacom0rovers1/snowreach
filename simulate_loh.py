#!/usr/bin/env python
"""Simulate the lowest observable height of a spaceborne radar on a
ground-based record, and report what is the cost of the blind zone.

    python simulate_loh.py example/MZS_MRR_2024-01_5min.nc
    python simulate_loh.py "data/*.nc" --gates 2 8 13 19 26 --out sweep.csv

The lower gates are hidden one after another, the classification is repeated
at each height, and the accumulation is recomputed from the reflectivity
there. The outcome is how much virga a radar that cannot see the lowest
few hundred metres would count as precipitation reaching the ground, and how
much the accumulation derived that way exceeds the one derived at the
surface.

The numbers describe the observing geometry alone. A real satellite estimate
adds the uncertainty of its retrieval on top of them.

Reference: Roversi et al., Virga hidden within the blind zone of spaceborne
radars, Atmospheric Chemistry and Physics, submitted.
"""

import argparse

from classify_profiles import open_all
from snowreach import loh, zesr
from snowreach.classify import DEFAULT_GATE, DEFAULT_THRESHOLD


def main(argv=None):
    p = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("input", help="NetCDF file, or a glob in quotes")
    p.add_argument("--gates", type=int, nargs="+", default=None,
                   help="gate indices to simulate (default: every gate from "
                        "the reference one upwards)")
    p.add_argument("--reference", type=int, default=DEFAULT_GATE,
                   help="the gate the site actually observes "
                        "(default %(default)s)")
    p.add_argument("--threshold", type=float, default=DEFAULT_THRESHOLD,
                   help="reflectivity above which a gate counts as signal, "
                        "in dBZ (default %(default)s)")
    p.add_argument("--relation", default="Bracci (Aggregates)",
                   choices=sorted(zesr.RELATIONS),
                   help="reflectivity to snowfall rate relation "
                        "(default %(default)s)")
    p.add_argument("--minutes", type=float, default=5.0,
                   help="length of one sample, in minutes "
                        "(default %(default)s)")
    p.add_argument("--envelope", action="store_true",
                   help="also compute the Monte Carlo interval on the "
                        "accumulation at the reference gate, which is slow")
    p.add_argument("--out", metavar="CSV", help="write the sweep to this file")
    args = p.parse_args(argv)

    ds, paths = open_all(args.input)
    print("read %d file(s), %d time steps" % (len(paths), ds.sizes["time"]))
    print("relation: %s" % args.relation)
    print("          %s\n" % zesr.SOURCES[args.relation])

    table = loh.sweep(ds, gates=args.gates, reference=args.reference,
                      threshold=args.threshold, relation=args.relation,
                      minutes=args.minutes)
    print(loh.summarise(table))

    for gate in table.index:
        if gate == args.reference:
            continue
        hit = loh.misclassified_virga(ds, int(gate), reference=args.reference,
                                      threshold=args.threshold)
        print("\nat gate %d, %d of the %d virga profiles look like "
              "precipitation (%.1f %%)"
              % (gate, hit["n_seen_as_precipitation"],
                 hit["n_virga_at_reference"], hit["share_pct"]))

    if args.envelope:
        ze = ds["Ze"].isel(range=args.reference).values
        lo, hi = zesr.accumulation_envelope(ze, args.minutes, args.relation)
        print("\naccumulation at the reference gate: %.2f mm (%.2f, %.2f)"
              % (table.loc[args.reference, "accumulation_mm"], lo, hi))

    if args.out:
        table.to_csv(args.out)
        print("\nwrote", args.out)


if __name__ == "__main__":
    main()
