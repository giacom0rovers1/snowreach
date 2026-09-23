"""Emulation of a higher lowest observable height.

A spaceborne cloud radar cannot use the gates nearest the surface, because
ground clutter fills them. The height of the first usable gate is the lowest
observable height, and everything below it is the blind zone. A radar
standing on the ground can be made to answer the same question the satellite
faces by simply refusing to look at its own lowest gates.

That is all this module does. The classification of :mod:`snowreach.classify`
is repeated with the reference gate moved upwards, and the accumulation is
recomputed from the reflectivity at that gate. Two numbers come out of the
sweep:

* how many of the profiles that are virga at the true reference gate become
  indistinguishable from precipitation once the lower gates are hidden;
* how much the accumulation derived from the higher gate exceeds the one
  derived from the reference gate.

The second is the bias that a satellite estimate carries at this site from
the observing geometry alone. It contains no retrieval uncertainty, because
there is no retrieval in it.

Reference: Roversi et al., Virga hidden within the blind zone of spaceborne
radars, Atmospheric Chemistry and Physics, submitted.
"""

import numpy as np
import pandas as pd

from . import zesr
from .classify import DEFAULT_GATE, DEFAULT_THRESHOLD, classify

#: The gates of the Mario Zucchelli record that stand in for the two
#: spaceborne radars, at 35 m per gate above a deck 20 m above sea level.
#: EarthCARE cannot use the lowest ~500 m and CloudSat the lowest ~1000 m,
#: and the two CloudSat entries bracket the lowest usable bins reported for
#: it over this region.
SATELLITE_GATES = {2: "reference", 8: None, 13: "EarthCARE-like",
                   19: "CloudSat-like", 26: "CloudSat-like"}


def gate_height(ds, gate):
    """Height of a gate in metres above the instrument deck."""
    return float(ds["height"].isel(time=0, range=gate).values)


def sweep(ds, gates=None, reference=DEFAULT_GATE,
          threshold=DEFAULT_THRESHOLD, relation="Bracci (Aggregates)",
          minutes=5.0):
    """Occurrence and accumulation as a function of the lowest observable gate.

    Parameters
    ----------
    ds : xarray.Dataset
        ``Ze`` in dBZ with dimensions ``(time, range)``, and ``height``.
    gates : sequence of int, optional
        Gate indices to emulate. Defaults to every gate from the reference
        one to three below the top, which is as high as the two-gate
        continuity check can reach.
    reference : int
        The gate the site actually observes, against which the others are
        compared.
    threshold, relation, minutes
        Passed through to the classification and to the accumulation.

    Returns
    -------
    pandas.DataFrame
        One row per gate, indexed by gate, with the height, the class counts,
        the virga share of the hydrometeor-bearing profiles, the accumulation
        in mm, and the accumulation excess over the reference gate in per
        cent.
    """
    n_gates = ds.sizes["range"]
    if gates is None:
        gates = range(reference, n_gates - 3)

    rows = []
    for gate in gates:
        if gate + 2 >= n_gates:
            continue
        labels = classify(ds, gate=gate, threshold=threshold)
        counts = labels.value_counts()
        n = {k: int(counts.get(k, 0)) for k in
             ("precip", "virga", "noise", "no_signal")}
        bearing = n["precip"] + n["virga"] + n["noise"]

        ze = ds["Ze"].isel(range=gate)
        accumulation = zesr.accumulate(ze.values, minutes, relation)

        rows.append({
            "gate": gate,
            "height_m": gate_height(ds, gate),
            "n_precip": n["precip"],
            "n_virga": n["virga"],
            "n_noise": n["noise"],
            "n_no_signal": n["no_signal"],
            "virga_share_pct": 100.0 * n["virga"] / max(bearing, 1),
            "accumulation_mm": accumulation,
        })

    out = pd.DataFrame(rows).set_index("gate")
    if reference in out.index:
        ref = out.loc[reference]
        out["accumulation_excess_pct"] = (
            100.0 * (out["accumulation_mm"] - ref["accumulation_mm"])
            / ref["accumulation_mm"])
        out["virga_lost_pct"] = (
            100.0 * (ref["n_virga"] - out["n_virga"]) / max(ref["n_virga"], 1))
    return out


def sublimation_ratio(sweep_table, reference=DEFAULT_GATE):
    """The share of the accumulation seen at each gate that never reaches the
    reference gate.

    Defined as in Bracci et al. (2022) and used in the paper as *SubR*: one
    minus the ratio of the accumulation at the reference gate to the
    accumulation at the emulated one. It is positive when the higher gate
    sees more snow than the lower one, which is the ordinary case here.
    """
    ref = sweep_table.loc[reference, "accumulation_mm"]
    return 1.0 - ref / sweep_table["accumulation_mm"]


def misclassified_virga(ds, gate, reference=DEFAULT_GATE,
                        threshold=DEFAULT_THRESHOLD):
    """The profiles that are virga at the reference gate and precipitation at
    the emulated one. These are the ones a satellite would count as snow
    reaching the surface."""
    low = classify(ds, gate=reference, threshold=threshold)
    high = classify(ds, gate=gate, threshold=threshold)
    both = pd.concat([low.rename("reference"), high.rename("emulated")],
                     axis=1)
    hit = (both["reference"] == "virga") & (both["emulated"] == "precip")
    n_virga = int((both["reference"] == "virga").sum())
    return {
        "n_virga_at_reference": n_virga,
        "n_seen_as_precipitation": int(hit.sum()),
        "share_pct": 100.0 * int(hit.sum()) / max(n_virga, 1),
        "times": both.index[hit],
    }


def summarise(table):
    """A short text summary of a sweep, for the command line."""
    lines = []
    for gate, row in table.iterrows():
        note = SATELLITE_GATES.get(int(gate)) or ""
        excess = row.get("accumulation_excess_pct", np.nan)
        lines.append(
            "gate %2d  %6.0f m   virga %5.1f %%   accumulation %7.2f mm"
            "   excess %+6.1f %%  %s"
            % (gate, row["height_m"], row["virga_share_pct"],
               row["accumulation_mm"], excess, note))
    return "\n".join(lines)
