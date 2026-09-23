# snowreach

Does the snow a radar detects aloft reach the ground?

Two methods from Roversi et al., *Virga hidden within the blind zone of
spaceborne radars: implications for surface snowfall estimates in coastal East
Antarctica* (Atmospheric Chemistry and Physics, submitted).

1. **A classification** of the profiles of a vertically pointing radar into
   precipitation, virga and noise, according to whether the echo survives to
   the lowest gate free of ground clutter.
2. **An emulation of the lowest observable height** of a spaceborne radar,
   which hides the lower gates of a ground-based record and reports what the
   blind zone costs in occurrence and in accumulated water equivalent.

This is the method, not the analysis pipeline of the paper. It carries no
figure scripts and no intermediate files. The observations are published
separately and openly, and what is here runs on them as downloaded.

## Install

```
pip install -r requirements.txt
```

Python 3.9 or later, with numpy, pandas and xarray. Reading NetCDF also needs
netcdf4 or h5netcdf.

## Run it

One month of the Mario Zucchelli record is included under `example/`, so both
scripts work as soon as the package is unpacked.

```
python classify_profiles.py example/MZS_MRR_2020-11_5min.nc --hourly
python emulate_loh.py example/MZS_MRR_2020-11_5min.nc --gates 2 8 13 19 26
```

The first prints how often each class occurs. The second prints, for every
emulated height, the virga share, the accumulation, the excess over the
reference gate, and how many virga profiles that height would count as
precipitation reaching the ground.

Both take a glob in quotes instead of a single file, so a whole record is

```
python emulate_loh.py "path/to/MZS_MRR_MeK_*_5min.nc" --gates 2 13 19
```

## Using it as a library

```python
from snowreach import open_mrr, classify, occurrence, loh

ds = open_mrr("MZS_MRR_MeK_2024*_5min.nc")
labels = classify(ds, gate=2)          # per time step
print(occurrence(labels))              # counts and shares
print(loh.sweep(ds, gates=[2, 13, 19]))
```

`classify` needs only `Ze` in dBZ over `(time, range)`, with the gates ordered
from the ground upwards, so it applies to any vertically pointing profiler.
`open_mrr` is specific to the archived MRR files, which store absolute time as
a data variable and order their dimensions the other way round.

## What the defaults mean

| | value | why |
|---|---|---|
| reference gate | index 2, about 105 m | the first gate of an MRR-2 that ImProToo keeps and that is clear of ground clutter |
| threshold | −20 dBZ | below the instrument sensitivity, so it does not filter: a gate counts as signal whenever a value was reported |
| sample length | 5 minutes | the averaging of the archived files |
| relation | Bracci (Aggregates) | calibrated on site, aggregate habit, the primary estimate of the paper |

The emulated heights used in the paper are gates 13 (490 m, EarthCARE-like)
and 19 and 26 (700 and 945 m, CloudSat-like), against the reference gate 2.

## Reproducing the published numbers

Over the four years of the record, 2020, 2021, 2023 and 2024, `emulate_loh.py`
gives

| height | accumulation | excess | published |
|---|---|---|---|
| 105 m | 212.5 mm | | 213.1 mm |
| 315 m | 254.7 mm | +19.9 % | +20 % |
| 490 m | 273.7 mm | +28.8 % | +29 % |
| 700 m | 284.8 mm | +34.0 % | +34 % |
| 945 m | 278.0 mm | +30.8 % | +31 % |

with the Bracci (Aggregates) relation, and the same agreement with Scarchilli.
The totals differ from the published table by 0.3 %, which comes from the gap
handling of the full pipeline. Both sit well inside the Monte Carlo interval
of the relation itself, which is 189 to 240 mm at the reference gate.

## The Ze–SR relations are not ours

`snowreach.zesr` carries five published power laws so that the emulation can
return an accumulation and not only an occurrence. Cite the original papers,
which `snowreach.zesr.SOURCES` names:

* Bracci et al. (2022), aggregate and pristine habits, calibrated at Mario
  Zucchelli Station, doi:10.3390/rs14040911
* Scarchilli et al. (2020), Mario Zucchelli Station,
  doi:10.1007/s00382-020-05161-1
* Souverijns et al. (2017), Princess Elisabeth, doi:10.1029/2017JD026862
* Grazioli et al. (2017), Dumont d'Urville, doi:10.5194/tc-11-1797-2017

The three calibrated on site are the ones the paper carries. The published
uncertainty intervals do not all measure the same quantity, and the
propagation in `zesr.rate_envelope` is only as meaningful as the intervals it
starts from. The docstring says which is which.

## Observations

MRR-2 vertical profiles and Parsivel size and velocity distributions at Mario
Zucchelli Station are openly available as monthly NetCDF archives:

* <https://doi.org/10.5281/zenodo.7907540> (MRR-2)
* <https://doi.org/10.5281/zenodo.7907496> (Parsivel)

The file under `example/` is one month taken from the first of those.

## What is not here

The figures and tables of the paper, the ERA5 comparison, the ceilometer and
radiosonde analyses, and the machine-learning reconstruction of the
classification. Those are the analysis of one site rather than a method, and
they need intermediate files that are of no use anywhere else.

## Licence

BSD 3-Clause. See `LICENSE`.
