### Source

This archive is built from the ECMWF sub-seasonal-range (S2S) forecast, retrieved from the
[ECMWF Data Store (ECDS)](https://ecds.ecmwf.int/) into the
[dynamical.org ECMWF IFS grib archive](https://source.coop/dynamical/ecmwf-ifs-grib)
on [Source Cooperative](https://source.coop/). ECDS serves retrieval jobs rather than
addressable files, so the grib archive — not ECDS — is what this dataset is reformatted from.

ECMWF's licence holds sub-seasonal-range forecasts back for 48 hours, and ECDS publishes an
initialization about 52 hours after its 00 UTC reference time. This is therefore not a
real-time dataset: the most recent initialization available is about two days old.

ECMWF does not provide user support for the free & open datasets. Users should refer to the public
[User Forum](https://forum.ecmwf.int/) for any questions related to the source material.

### Data availability

**This dataset is under construction and is published to the staging catalog only.**

The `init_time` axis declares 1153 daily initializations from 2023-06-28, but only the most
recent 30 — **2026-07-25T00 through 2026-08-23T00 UTC** — hold data. Every earlier
initialization reads as NaN, and operational updates are currently paused, so the archive does
not yet extend to the present. The collection's temporal extent and its `time_domain` summary
describe the declared axis rather than this window; treat the dates above as authoritative.

Backfilling the declared history requires re-creating the store, so both the covered window and
the axis itself will change before this dataset is promoted to production.

### Variables

Because the forecast step is 24 hourly, most surface variables are daily means or daily mean
rates rather than instantaneous values — that is what the `average_` prefix denotes. Surface and
single-level variables are at the dataset root. Temperature, specific humidity, both wind
components, vertical velocity and geopotential height are carried on 10 pressure levels
(1000, 925, 850, 700, 500, 300, 200, 100, 50 and 10 hPa) in the `pressure_level` group.

Two absences are worth knowing about before you plan around this dataset. `precipitation_convective_surface`
is the only precipitation rate carried — there is no total precipitation. And wind is available only on
pressure levels, as `wind_u` and `wind_v`; there are no 10 metre winds, though
`eastward_turbulent_surface_stress` and `northward_turbulent_surface_stress` do describe the
surface momentum flux. Both reflect the variable set retrieved from ECDS into the grib archive
this dataset is built from.

### Ensemble members

Each forecast contains 101 ensemble members: a control member (0) and 100 perturbed members
(1-100). The control forecast is produced with the best available data and unperturbed models.
The other 100 members are each produced with slight perturbations of initial conditions and of
the models. Taken together, the ensemble of 101 forecasts shows the range of possible outcomes
and the likelihood of their occurrence. A 101 member ensemble is larger than the 51 members of
ECMWF's medium-range forecast, which matters at sub-seasonal lead times where the useful signal
is in the distribution rather than in any single trace.

### Model updates

IFS is updated regularly. Find details of recent and upcoming
[changes to the forecasting system](https://confluence.ecmwf.int/display/FCST/Changes+to+the+forecasting+system)
on the ECMWF website.

### Storage

{{ storage }}

### Chunks & shards

{{ chunking }}

### Validation report

{{ validation_report }}

### Compression

{{ compression }}
