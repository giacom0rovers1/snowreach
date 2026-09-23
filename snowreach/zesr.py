"""Reflectivity to snowfall rate relations, and their uncertainty.

None of the relations below is ours. They are published power laws of the
form

    SR = (Ze / a) ** (1 / b)

with Ze the equivalent reflectivity factor in mm^6 m^-3 and SR the snowfall
rate in mm h^-1 of water equivalent. They are collected here because the
blind-zone simulation needs an accumulation, not only an occurrence, and
because the spread between them is the dominant uncertainty of any
ground-based accumulation at this site. Cite the original papers, not this
package, when using the coefficients.

The percentiles quoted for each relation do not all measure the same thing.
Souverijns et al. (2017) resample over the range of assumed particle
properties, which is why their interval is so wide. Grazioli et al. (2017)
quote the scatter about the fitted line. Bracci et al. (2022) do not state a
method. They are propagated here as published, and the propagation is only
as meaningful as the intervals it starts from.
"""

import numpy as np
import xarray as xr

#: name -> (a, b, a_5th, b_5th, a_95th, b_95th)
RELATIONS = {
    "Bracci (Aggregates)": (134, 1.25, 122, 1.17, 146, 1.32),
    "Bracci (Pristine)": (95, 1.18, 85, 1.12, 107, 1.25),
    "Scarchilli": (54, 1.15, 51, 1.13, 56, 1.17),
    "Souverijns": (18, 1.10, 11, 0.97, 43, 1.17),
    "Grazioli": (76, 0.91, 69, 0.78, 83, 1.09),
}

#: Where each relation comes from, and where it was calibrated.
SOURCES = {
    "Bracci (Aggregates)":
        "Bracci et al. (2022), doi:10.3390/rs14040911, MZS, aggregate habit",
    "Bracci (Pristine)":
        "Bracci et al. (2022), doi:10.3390/rs14040911, MZS, pristine habit",
    "Scarchilli":
        "Scarchilli et al. (2020), doi:10.1007/s00382-020-05161-1, MZS",
    "Souverijns":
        "Souverijns et al. (2017), doi:10.1029/2017JD026862, "
        "Princess Elisabeth",
    "Grazioli":
        "Grazioli et al. (2017), doi:10.5194/tc-11-1797-2017, "
        "Dumont d'Urville",
}

#: The three calibrated at Mario Zucchelli Station, the ones the paper
#: carries. The other two are kept for comparison with other sites.
LOCAL = ("Bracci (Aggregates)", "Bracci (Pristine)", "Scarchilli")

#: Fixed so that two runs on the same input return the same envelope.
SEED = 20260919

_GRID_LO, _GRID_HI, _GRID_N = 1e-6, 1e6, 2401
_Z95 = 1.645  # standard normal quantile for a 5th to 95th percentile pair


def snow_rate(ze_dbz, relation="Bracci (Aggregates)"):
    """Deterministic snowfall rate from reflectivity, in mm h^-1."""
    a, b = RELATIONS[relation][:2]
    return (10.0 ** (np.asarray(ze_dbz, dtype=float) / 10.0) / a) ** (1.0 / b)


def draw_coefficients(relation, n=3000, seed=SEED):
    """Sample the two coefficients from the published percentiles.

    ``a`` is taken log-normal and ``b`` normal, each reconstructed from its
    5th and 95th percentile. The draws are of the coefficients alone, so the
    same sample serves every time step: the coefficients are two numbers that
    hold for the whole record, they are not redrawn hour by hour.
    """
    a, b, a5, b5, a95, b95 = RELATIONS[relation]
    rng = np.random.default_rng(seed)
    sigma_log_a = (np.log(a95) - np.log(a5)) / (2 * _Z95)
    sigma_b = (b95 - b5) / (2 * _Z95)
    a_s = np.exp(rng.normal(np.log(a), sigma_log_a, n))
    b_s = rng.normal(b, sigma_b, n)
    return a_s, b_s


def rate_envelope(ze_dbz, relation="Bracci (Aggregates)", n=3000, seed=SEED):
    """The 5th, 50th and 95th percentile of the rate at each reflectivity.

    The percentiles are evaluated once on a logarithmic reflectivity grid and
    interpolated, which costs ``n`` times the grid instead of ``n`` times the
    record. Each percentile curve is smooth and monotone in log Ze, so the
    interpolation error is a few parts in ten thousand, well under the Monte
    Carlo noise itself.
    """
    a_s, b_s = draw_coefficients(relation, n=n, seed=seed)
    grid = np.logspace(np.log10(_GRID_LO), np.log10(_GRID_HI), _GRID_N)
    rates = (grid[:, None] / a_s[None, :]) ** (1.0 / b_s[None, :])
    q = np.percentile(rates, [5, 50, 95], axis=1)

    z_lin = 10.0 ** (np.asarray(ze_dbz, dtype=float) / 10.0)
    clipped = np.clip(z_lin, grid[0], grid[-1])
    out = {}
    for name, curve in zip(("inf", "med", "sup"), q):
        values = np.where(np.isfinite(z_lin), np.interp(clipped, grid, curve),
                          np.nan)
        if isinstance(ze_dbz, xr.DataArray):
            values = xr.DataArray(values, coords=ze_dbz.coords,
                                  dims=ze_dbz.dims)
        out[name] = values
    return out


def accumulate(ze_dbz, minutes, relation="Bracci (Aggregates)"):
    """Water equivalent accumulated over a series of samples, in mm.

    ``minutes`` is the length of one sample. Samples without signal
    contribute nothing, and the power law is applied to each reflectivity
    before summing, never to their mean, because it is not linear.
    """
    rate = snow_rate(ze_dbz, relation)
    rate = np.where(np.isfinite(rate), rate, 0.0)
    return float(np.sum(rate) * minutes / 60.0)


def accumulation_envelope(ze_dbz, minutes, relation="Bracci (Aggregates)",
                          n=3000, seed=SEED):
    """The 5th and 95th percentile of the accumulated total, in mm.

    This is the spread of the totals that each drawn pair of coefficients
    produces, which is the question a cumulative curve asks. Summing the
    per-step percentiles instead would answer a different one, namely what
    the total would be if the rate sat at its 5th percentile in every step
    independently, and it gives a band that is too narrow.
    """
    a_s, b_s = draw_coefficients(relation, n=n, seed=seed)
    z_lin = 10.0 ** (np.asarray(ze_dbz, dtype=float) / 10.0)
    z_lin = z_lin[np.isfinite(z_lin)]
    totals = np.array([
        float(np.sum((z_lin / a) ** (1.0 / b)) * minutes / 60.0)
        for a, b in zip(a_s, b_s)])
    lo, hi = np.percentile(totals, [5, 95])
    return float(lo), float(hi)
