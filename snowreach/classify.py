"""Classification of vertically pointing radar profiles into precipitation,
virga and noise.

The question the classification answers is whether the hydrometeors a radar
detects aloft are still there at the lowest gate that is free of ground
clutter. A profile in which they are is *precipitation*, one in which they
are not is *virga*, and the rest is *noise*.

The two continuity criteria are what separate the classification from a
simple threshold on one gate:

* a profile counts as precipitation only if the reference gate **and the two
  gates above it** are all above threshold, which rejects the isolated
  near-surface spikes that ground clutter produces;
* a profile counts as virga only if at least two adjacent gates anywhere in
  the column are above threshold, or the echo reaches the top of the column,
  which rejects single-gate returns that carry no vertical structure.

Everything that has signal but satisfies neither is noise, so the four
labels partition the record. `almost` is a diagnostic subset of virga, the
profiles whose echo dies in the gate just above the reference one, and it is
not a fifth category.

Reference: Roversi et al., Virga hidden within the blind zone of spaceborne
radars, Atmospheric Chemistry and Physics, submitted.
"""

import numpy as np
import pandas as pd
import xarray as xr

#: Reference gate of the Mario Zucchelli record. The MRR-2 samples every
#: 35 m, ImProToo discards the two near-field gates, so index 2 is the first
#: reliable one at about 105 m above the instrument deck.
DEFAULT_GATE = 2

#: Reflectivity threshold in dBZ. The default does not filter: it sits below
#: the instrument sensitivity, so a gate counts as signal whenever ImProToo
#: reported a value at all.
DEFAULT_THRESHOLD = -20.0

LABELS = ("precip", "virga", "noise", "no_signal")


def _any_two_adjacent(above):
    """True where at least two adjacent range gates are both above threshold."""
    axis = above.get_axis_num("range")
    lower = above.isel(range=slice(0, -1)).values
    upper = above.isel(range=slice(1, None)).values
    pair = (lower & upper).any(axis=axis)
    dims = [d for d in above.dims if d != "range"]
    return xr.DataArray(pair, dims=dims,
                        coords={d: above[d] for d in dims})


def classify(ds, gate=DEFAULT_GATE, threshold=DEFAULT_THRESHOLD):
    """Label every time step of a radar dataset.

    Parameters
    ----------
    ds : xarray.Dataset
        Must carry ``Ze`` in dBZ with dimensions ``(time, range)``. Gates are
        ordered from the ground upwards.
    gate : int
        Index of the reference gate, the lowest one taken to be free of
        ground clutter.
    threshold : float
        Reflectivity above which a gate counts as signal, in dBZ.

    Returns
    -------
    pandas.Series
        One label per time step, from :data:`LABELS`.
    """
    above = ds["Ze"] >= threshold
    n_above = above.sum(dim="range")

    at_gate = above.isel(range=gate)
    two_above_gate = above.isel(range=gate + 1) & above.isel(range=gate + 2)
    at_top = above.isel(range=-2) | above.isel(range=-1)

    has_signal = n_above > 0
    is_precip = has_signal & at_gate & two_above_gate
    is_virga = has_signal & ~at_gate & (_any_two_adjacent(above) | at_top)

    labels = xr.where(
        ~has_signal, "no_signal",
        xr.where(is_precip, "precip",
                 xr.where(is_virga, "virga", "noise")))
    return labels.to_pandas().rename("classification")


def almost_reaching(ds, gate=DEFAULT_GATE, threshold=DEFAULT_THRESHOLD):
    """The virga profiles whose echo survives to the gate just above the
    reference one. A diagnostic subset of virga, already counted there."""
    above = ds["Ze"] >= threshold
    n_above = above.sum(dim="range")
    at_gate = above.isel(range=gate)
    two_above_gate = above.isel(range=gate + 1) & above.isel(range=gate + 2)
    flag = (n_above > 0) & ~at_gate & two_above_gate
    return flag.to_pandas().rename("almost")


def occurrence(labels):
    """Counts and shares per class, with virga as a share of the profiles
    that carry hydrometeors rather than of the whole record."""
    counts = labels.value_counts()
    n = {k: int(counts.get(k, 0)) for k in LABELS}
    bearing = n["precip"] + n["virga"] + n["noise"]
    out = pd.DataFrame({"count": pd.Series(n)})
    out["share_of_record"] = 100.0 * out["count"] / max(len(labels), 1)
    out["share_of_bearing"] = np.where(
        out.index == "no_signal", np.nan,
        100.0 * out["count"] / max(bearing, 1))
    return out


#: Order used to break ties in the hourly vote. An hour with evidence of
#: precipitation reaching the surface in any of its steps is more informative
#: than one of noise, and virga sits between because a coherent echo aloft is
#: a physical signal whereas noise is the residual category.
_TIE_BREAK = ("precip", "virga", "noise")


def to_hourly(labels):
    """Aggregate the per-step labels to hourly resolution by majority vote.

    An hour whose steps are all ``no_signal`` stays ``no_signal``. Otherwise
    the label is the most frequent of the remaining steps, ties broken by
    :data:`_TIE_BREAK`. One consequence is worth stating: an hour labelled
    virga can still show echo at the reference gate, because a minority of
    its steps had precipitation reaching the ground.
    """
    def vote(block):
        valid = block[block != "no_signal"]
        if len(valid) == 0:
            return "no_signal"
        counts = valid.value_counts()
        top = counts[counts == counts.iloc[0]].index.tolist()
        for label in _TIE_BREAK:
            if label in top:
                return label
        return top[0]

    return labels.resample("1h").apply(vote)
