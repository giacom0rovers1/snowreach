"""snowreach — does the snow detected aloft reach the ground?

Two methods from Roversi et al., *Virga hidden within the blind zone of
spaceborne radars* (Atmospheric Chemistry and Physics, submitted):

* :mod:`snowreach.classify`, which labels the profiles of a vertically
  pointing radar as precipitation, virga or noise according to whether the
  echo survives to the lowest gate free of ground clutter;
* :mod:`snowreach.loh`, which simulates the lowest observable height of a
  spaceborne radar by hiding the lower gates, and reports what that costs in
  occurrence and in accumulated water equivalent.

:mod:`snowreach.zesr` collects the published reflectivity to snowfall rate
relations the second one needs. Those coefficients are not ours, and the
papers they come from are named in ``snowreach.zesr.SOURCES``.

The package works on any vertically pointing profiler whose data can be
opened as an ``xarray`` dataset with ``Ze`` in dBZ over ``(time, range)``. It
was written for an MRR-2 at Mario Zucchelli Station, Antarctica, at 35 m
vertical resolution and five-minute averaging.
"""

from . import io  # noqa: F401
from . import loh, zesr  # noqa: F401
from .io import open_mrr
from .classify import (DEFAULT_GATE, DEFAULT_THRESHOLD, LABELS,
                       almost_reaching, classify, occurrence, to_hourly)

__all__ = ["classify", "occurrence", "to_hourly", "almost_reaching",
           "LABELS", "DEFAULT_GATE", "DEFAULT_THRESHOLD", "loh", "zesr",
           "open_mrr", "io"]

__version__ = "1.0.1"
