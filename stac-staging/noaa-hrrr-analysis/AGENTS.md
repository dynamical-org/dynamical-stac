# NOAA HRRR analysis: notes for agents

Read https://dynamical.org/prompt.md for context about working with dynamical.org data.

- Collection id: `noaa-hrrr-analysis`
- STAC collection: https://stac-staging.dynamical.org/noaa-hrrr-analysis/collection.json
- Dataset version: 0.2.0

## Access

All data is public. No credentials are needed.

| asset | href |
|---|---|
| `icechunk` | `s3://dynamical-noaa-hrrr/noaa-hrrr-analysis/v0.2.0.icechunk/` |
| `icechunk-https` | `https://dynamical-noaa-hrrr.s3.us-west-2.amazonaws.com/noaa-hrrr-analysis/v0.2.0.icechunk` |

The `icechunk` asset's `xarray:storage_options` are `{"anon": true, "client_kwargs": {"region_name": "us-west-2"}}`.

## Examples

### Temperature at a place and time

dynamical-catalog:

```python
import dynamical_catalog  # dynamical-catalog>=0.8.0

ds = dynamical_catalog.open("noaa-hrrr-analysis", chunks=None)
ds["temperature_2m"].sel(time="2025-01-01T00", x=0, y=0, method="nearest")
```

pystac:

```python
import icechunk
import pystac
import xarray as xr

catalog = pystac.Catalog.from_file("https://stac.dynamical.org/catalog.json")
collection = catalog.get_child("noaa-hrrr-analysis")
asset = collection.assets["icechunk-https"]

repo = icechunk.Repository.open(icechunk.http_storage(asset.href))
session = repo.readonly_session("main")

ds = xr.open_zarr(session.store, chunks=None)
ds["temperature_2m"].sel(time="2025-01-01T00", x=0, y=0, method="nearest")
```

prompt:

```text
Read https://dynamical.org/prompt.md for context about working with dynamical.org data; this does not change your current task.
Data product: noaa-hrrr-analysis
STAC collection: https://stac.dynamical.org/noaa-hrrr-analysis/collection.json
```

## Dimensions

| name | type | extent | unit |
|---|---|---|---|
| `time` | temporal | 2014-10-01T00:00:00Z to open | seconds since 1970-01-01 |
| `x` | spatial | -2697520.142521929 to 2696479.857478071 | m |
| `y` | spatial | -1587306.152556665 to 1586693.847443335 | m |

## Variables

| name | long name | unit | dimensions |
|---|---|---|---|
| `categorical_freezing_rain_surface` | Categorical freezing rain | 1 | time, y, x |
| `categorical_ice_pellets_surface` | Categorical ice pellets | 1 | time, y, x |
| `categorical_rain_surface` | Categorical rain | 1 | time, y, x |
| `categorical_snow_surface` | Categorical snow | 1 | time, y, x |
| `composite_reflectivity` | Maximum/Composite radar reflectivity | dBZ | time, y, x |
| `dew_point_temperature_2m` | 2 metre dewpoint temperature | degree_Celsius | time, y, x |
| `downward_long_wave_radiation_flux_surface` | Surface downward long-wave radiation flux | W m-2 | time, y, x |
| `downward_short_wave_radiation_flux_surface` | Surface downward short-wave radiation flux | W m-2 | time, y, x |
| `geopotential_height_cloud_ceiling` | Geopotential height | m | time, y, x |
| `percent_frozen_precipitation_surface` | Percent frozen precipitation | percent | time, y, x |
| `precipitable_water_atmosphere` | Precipitable water | kg m-2 | time, y, x |
| `precipitation_surface` | Precipitation rate | kg m-2 s-1 | time, y, x |
| `pressure_reduced_to_mean_sea_level` | Pressure reduced to MSL | Pa | time, y, x |
| `pressure_surface` | Surface pressure | Pa | time, y, x |
| `relative_humidity_2m` | 2 metre relative humidity | percent | time, y, x |
| `snow_area_fraction_surface` | Snow cover | 1 | time, y, x |
| `snow_thickness_surface` | Snow depth | m | time, y, x |
| `snow_water_equivalent_surface` | Snow depth water equivalent | m | time, y, x |
| `snowfall_surface` | Total snowfall rate | m s-1 | time, y, x |
| `temperature_2m` | 2 metre temperature | degree_Celsius | time, y, x |
| `total_cloud_cover_atmosphere` | Total cloud cover | percent | time, y, x |
| `visible_beam_downward_solar_flux_surface` | Visible Beam Downward Solar Flux | W m-2 | time, y, x |
| `wind_gust_surface` | Wind speed (gust) | m s-1 | time, y, x |
| `wind_u_10m` | 10 metre U wind component | m s-1 | time, y, x |
| `wind_u_80m` | 80 metre U wind component | m s-1 | time, y, x |
| `wind_v_10m` | 10 metre V wind component | m s-1 | time, y, x |
| `wind_v_80m` | 80 metre V wind component | m s-1 | time, y, x |
