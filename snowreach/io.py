"""Reading the archived MRR files.

The monthly files published with the paper come out of ImProToo and are
stored the way that pipeline writes them, which is not the way xarray likes
to be handed a time series. Three things need fixing before anything else
works:

* absolute time is a plain data variable called ``time_UTC``, so ``time`` is
  a dimension without a coordinate and no time-based operation is available;
* the dimensions are ordered ``(range, time)``;
* the files are monthly, so a multi-year record has to be concatenated and
  sorted.

:func:`open_mrr` does those three things and nothing else. It leaves the
values untouched, including the gates ImProToo rejects, which arrive as NaN
in ``Ze`` and as NaN in ``height`` for the two near-field gates and the top
one.
"""

import glob

import xarray as xr


def open_mrr(path, utc_name="time_UTC"):
    """Open one archived file, or a glob matching several, ready to use.

    Parameters
    ----------
    path : str
        A NetCDF path, or a glob pattern. Several files are concatenated
        along time and sorted, so monthly files may arrive in any order.
    utc_name : str
        Name of the variable holding absolute time.

    Returns
    -------
    xarray.Dataset
        With ``time`` as a coordinate and dimensions ordered
        ``(time, range)``.
    """
    paths = sorted(glob.glob(path)) or [path]
    parts = [_prepare(xr.open_dataset(p), utc_name) for p in paths]
    ds = parts[0] if len(parts) == 1 else xr.concat(parts, dim="time")
    return ds.sortby("time")


def _prepare(ds, utc_name):
    if "time" not in ds.dims:
        raise ValueError("no 'time' dimension in this file")
    if utc_name in ds:
        ds = ds.assign_coords(time=ds[utc_name])
    elif "time" not in ds.coords:
        raise ValueError(
            "no '%s' variable and no 'time' coordinate: cannot place the "
            "profiles in time" % utc_name)
    if ds["Ze"].dims[0] != "time":
        ds = ds.transpose("time", "range", ...)
    return ds
