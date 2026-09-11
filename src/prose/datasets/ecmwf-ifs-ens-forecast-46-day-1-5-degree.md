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

**This dataset is published to the staging catalog only while it is under review.**

The `init_time` axis begins at 2026-01-01 and every initialization holds data. Operational
updates run daily and append each new initialization once ECDS publishes it, about two days after
its 00 UTC reference time.

The source model changed between the 2026-05-12 and 2026-05-13 initializations (IFS Cycle 50r1).
From 2026-05-13 the snow fields are populated over sea ice, where they were previously missing,
and soil moisture is discontinuous with the initializations before it. See the validation report
for details before comparing values across that date.

### Variables

Because the forecast step is 24 hourly, most surface variables are daily means or daily mean
rates rather than instantaneous values — that is what the `average_` prefix denotes. Surface and
single-level variables are at the dataset root. Temperature, specific humidity, both wind
components, vertical velocity and geopotential height are carried on 10 pressure levels
(1000, 925, 850, 700, 500, 300, 200, 100, 50 and 10 hPa) in the `pressure_level` group.

**The 0 hour lead time carries little surface data.** A 24 hour statistic needs a preceding day, so
31 of the 35 root variables are entirely NaN at `lead_time=0`; only `pressure_reduced_to_mean_sea_level`,
`pressure_surface`, `wind_u_10m` and `wind_v_10m`, which are instantaneous, have values there. Every
variable in the `pressure_level` group is instantaneous and is present at the 0 hour lead time.
Selecting `lead_time=slice("24h", None)` is the safe default for surface fields.

Several variables are masked to the domain they describe, and read as NaN outside it:
`sea_surface_temperature` and `sea_ice_area_fraction` over land; the soil moisture, soil temperature
and runoff fields over ocean; and `snow_albedo_surface` and `snow_density_surface` wherever there is
no snow. In the `pressure_level` group, `specific_humidity` is not provided above 200 hPa and is
NaN on the 100, 50 and 10 hPa levels.

Not every root variable is a daily mean. `maximum_temperature_2m` and `minimum_temperature_2m` are
the extremes over the 24 hours ending at each lead time. `wind_u_10m` and `wind_v_10m` are
instantaneous values at the 00 UTC valid time of each lead, not daily means, so do not compare them
against the averaged fields as if they were. `precipitation_surface` is the total precipitation rate;
`precipitation_convective_surface` is its convective component.

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
