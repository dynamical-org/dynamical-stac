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

**The 0 hour lead time carries no surface data.** A 24 hour statistic needs a preceding day, so 27
of the 29 root variables are entirely NaN at `lead_time=0`; only `pressure_reduced_to_mean_sea_level`
and `pressure_surface`, which are instantaneous, have values there. Every variable in the
`pressure_level` group is instantaneous and is present at the 0 hour lead time. Selecting
`lead_time=slice("24h", None)` is the safe default for surface fields.

Several variables are masked to the domain they describe, and read as NaN outside it:
`sea_surface_temperature` and `sea_ice_area_fraction` over land; the soil moisture, soil temperature
and runoff fields over ocean; and `snow_albedo_surface` and `snow_density_surface` wherever there is
no snow. In the `pressure_level` group, `specific_humidity` is not provided above 200 hPa and is
NaN on the 100, 50 and 10 hPa levels.

Two absences are worth knowing about before you plan around this dataset.
`precipitation_convective_surface` is the only precipitation rate carried — there is no total
precipitation — and wind is available only on pressure levels, as `wind_u` and `wind_v`, with no
10 metre winds. At the surface, `eastward_turbulent_surface_stress` and
`northward_turbulent_surface_stress` are what describe the momentum flux here.

Neither absence is a limit of the sub-seasonal forecast itself. ECMWF publishes total
precipitation and the 10 metre winds for it, but on a 6 hourly step rather than the 24 hourly step
of this dataset, and the grib archive this dataset is built from does not currently retrieve them.

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
