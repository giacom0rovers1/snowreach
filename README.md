# snowreach

Does the snow that a spaceborne radar detects aloft really reach the ground?

Two methods from Roversi et al., *Virga hidden within the blind zone of
spaceborne radars: implications for surface snowfall estimates in coastal East
Antarctica* (Atmospheric Measurement Techniques, submitted).

1. **A classification** of the profiles of a vertically pointing radar into
   precipitation, virga and noise, according to whether the echo survives to
   the lowest gate free of ground clutter.
2. **A simulation of the lowest observable height** of a spaceborne radar,
   which hides the lower gates of a ground-based record and reports what the
   blind zone costs in occurrence and in accumulated water equivalent.

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
python simulate_loh.py example/MZS_MRR_2020-11_5min.nc --gates 2 8 13 19 26
```

The first prints how often each class occurs. The second prints, for every
simulated height, the virga share, the accumulation, the excess over the
reference gate, and how many virga profiles that height would count as
precipitation reaching the ground.

Both take a glob in quotes instead of a single file, so a whole record is

```
python simulate_loh.py "path/to/MZS_MRR_MeK_*_5min.nc" --gates 2 13 19
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

The simulated heights used in the paper are gates 13 (490 m, EarthCARE-like)
and 19 and 26 (700 and 945 m, CloudSat-like), against the reference gate 2.

## Reproducing the published numbers

Over the four years of the record, 2020, 2021, 2023 and 2024, `simulate_loh.py`
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

On the occurrence side, virga is 38.4 % of the hydrometeor-bearing profiles
at the reference gate, and the sweep follows the 105-m columns profile by
profile:

| height | 105-m virga seen as precipitation | 105-m precipitation with no echo left |
|---|---|---|
| 315 m | 20.2 % | 3.1 % |
| 490 m | 34.5 % | 7.0 % |
| 700 m | 52.3 % | 12.3 % |
| 945 m | 65.0 % | 18.7 % |

The second column is the shallow precipitation that a radar with that lowest
observable height misses entirely.

## Changes

**1.0.2**

* The simulated heights hide the gates below them, as the module
  documentation always said. In 1.0.1 they did not: a column with echo only
  below the simulated height counted as virga, and `sweep` reported the
  virga lost as a net difference of counts (20 % at 490 m in the Mario
  Zucchelli record, against the 35 % found profile by profile).
  `virga_lost_pct` is replaced by `virga_seen_as_precip_pct` and
  `precip_unseen_pct`. The accumulations do not change.
* The top test looks at the two uppermost usable gates, found from the
  heights the processing leaves finite. In 1.0.1 it looked at the last two
  gates of the file, one of which the processing always discards, so in
  practice only 1050 m counted. At the reference gate 77 of 376 080 profiles
  move from noise to virga.
* `sublimation_ratio` divides by the accumulation at the reference gate, as
  in Bracci et al. (2022, URSI AT-AP-RASC). In 1.0.1 it divided by the one at
  the simulated gate.
* The DOIs of three of the Ze–SR sources were wrong in 1.0.1, in the code, in
  this README and in the Zenodo metadata: Bracci et al. (2022) is
  10.3390/rs14010082, Scarchilli et al. (2020) 10.1017/jog.2020.70 and
  Souverijns et al. (2017) 10.1016/j.atmosres.2017.06.001.

## The Ze–SR relations are not ours

`snowreach.zesr` carries five published power laws so that the simulation can
return an accumulation and not only an occurrence. Cite the original papers,
which `snowreach.zesr.SOURCES` names:

* Bracci et al. (2022), aggregate and pristine habits, calibrated at Mario
  Zucchelli Station, doi:10.3390/rs14010082
* Scarchilli et al. (2020), Mario Zucchelli Station,
  doi:10.1017/jog.2020.70
* Souverijns et al. (2017), Princess Elisabeth, doi:10.1016/j.atmosres.2017.06.001
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

## Support

This is research code released alongside a paper. Questions and reports of
things that do not work are welcome through the issue tracker, and are
answered when the author can. If the classification does not run on another
instrument's files, that is worth reporting: the reader in `snowreach.io` is
written for one archive format and will need others.

## Licence

BSD 3-Clause. See `LICENSE`.

## Acknowledgements

The package was assembled from the analysis code of the paper with Claude Opus 5.5
(Anthropic), used through Claude Code: it extracted the two methods from a
larger working repository, wrote the command-line scripts and the
documentation, and checked the result against the published table. The
methods are those of the paper, and the decisions about what to release and
the verification of the outcome are the author's.
