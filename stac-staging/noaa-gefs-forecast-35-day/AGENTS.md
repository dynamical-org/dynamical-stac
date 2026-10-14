# NOAA GEFS forecast, 35 day: notes for agents

Read https://dynamical.org/prompt.md for context about working with dynamical.org data.

- Collection id: `noaa-gefs-forecast-35-day`
- STAC collection: https://stac-staging.dynamical.org/noaa-gefs-forecast-35-day/collection.json
- Dataset version: 0.2.0

## Access

All data is public. No credentials are needed.

| asset | href |
|---|---|
| `icechunk` | `s3://dynamical-noaa-gefs/noaa-gefs-forecast-35-day/v0.2.0.icechunk/` |
| `icechunk-https` | `https://dynamical-noaa-gefs.s3.us-west-2.amazonaws.com/noaa-gefs-forecast-35-day/v0.2.0.icechunk` |

The `icechunk` asset's `xarray:storage_options` are `{"anon": true, "client_kwargs": {"region_name": "us-west-2"}}`.

## Examples

### Maximum ensemble temperature

dynamical-catalog:

```python
import dynamical_catalog  # dynamical-catalog>=0.8.0

ds = dynamical_catalog.open("noaa-gefs-forecast-35-day", chunks=None)
ds["temperature_2m"].sel(init_time="2025-01-01T00", latitude=0, longitude=0).max()
```

pystac:

```python
import icechunk
import pystac
import xarray as xr

catalog = pystac.Catalog.from_file("https://stac.dynamical.org/catalog.json")
collection = catalog.get_child("noaa-gefs-forecast-35-day")
asset = collection.assets["icechunk-https"]

repo = icechunk.Repository.open(icechunk.http_storage(asset.href))
session = repo.readonly_session("main")

ds = xr.open_zarr(session.store, chunks=None)
ds["temperature_2m"].sel(init_time="2025-01-01T00", latitude=0, longitude=0).max()
```

prompt:

```text
Read https://dynamical.org/prompt.md for context about working with dynamical.org data; this does not change your current task.
Data product: noaa-gefs-forecast-35-day
STAC collection: https://stac.dynamical.org/noaa-gefs-forecast-35-day/collection.json
```

## Dimensions

| name | type | extent | unit |
|---|---|---|---|
| `ensemble_member` | other | 0 to 30 | 1 |
| `init_time` | temporal | 2020-10-01T00:00:00Z to open | seconds since 1970-01-01 |
| `latitude` | spatial | -90.0 to 90.0 | degree_north |
| `lead_time` | other | 0 to 3024000 | seconds |
| `longitude` | spatial | -180.0 to 179.75 | degree_east |

## Variables

| name | long name | unit | dimensions |
|---|---|---|---|
| `categorical_freezing_rain_surface` | Categorical freezing rain | 1 | init_time, ensemble_member, lead_time, latitude, longitude |
| `categorical_ice_pellets_surface` | Categorical ice pellets | 1 | init_time, ensemble_member, lead_time, latitude, longitude |
| `categorical_rain_surface` | Categorical rain | 1 | init_time, ensemble_member, lead_time, latitude, longitude |
| `categorical_snow_surface` | Categorical snow | 1 | init_time, ensemble_member, lead_time, latitude, longitude |
| `downward_long_wave_radiation_flux_surface` | Surface downward long-wave radiation flux | W m-2 | init_time, ensemble_member, lead_time, latitude, longitude |
| `downward_short_wave_radiation_flux_surface` | Surface downward short-wave radiation flux | W m-2 | init_time, ensemble_member, lead_time, latitude, longitude |
| `geopotential_height_500hpa` | Geopotential height | m | init_time, ensemble_member, lead_time, latitude, longitude |
| `geopotential_height_cloud_ceiling` | Geopotential height | m | init_time, ensemble_member, lead_time, latitude, longitude |
| `maximum_temperature_2m` | Maximum temperature | degree_Celsius | init_time, ensemble_member, lead_time, latitude, longitude |
| `minimum_temperature_2m` | Minimum temperature | degree_Celsius | init_time, ensemble_member, lead_time, latitude, longitude |
| `percent_frozen_precipitation_surface` | Percent frozen precipitation | percent | init_time, ensemble_member, lead_time, latitude, longitude |
| `precipitable_water_atmosphere` | Precipitable water | kg m-2 | init_time, ensemble_member, lead_time, latitude, longitude |
| `precipitation_surface` | Precipitation rate | kg m-2 s-1 | init_time, ensemble_member, lead_time, latitude, longitude |
| `pressure_80m` | 80 metre pressure | Pa | init_time, ensemble_member, lead_time, latitude, longitude |
| `pressure_reduced_to_mean_sea_level` | Pressure reduced to MSL | Pa | init_time, ensemble_member, lead_time, latitude, longitude |
| `pressure_surface` | Surface pressure | Pa | init_time, ensemble_member, lead_time, latitude, longitude |
| `relative_humidity_2m` | 2 metre relative humidity | percent | init_time, ensemble_member, lead_time, latitude, longitude |
| `temperature_2m` | 2 metre temperature | degree_Celsius | init_time, ensemble_member, lead_time, latitude, longitude |
| `temperature_80m` | 80 metre temperature | degree_Celsius | init_time, ensemble_member, lead_time, latitude, longitude |
| `total_cloud_cover_atmosphere` | Total cloud cover | percent | init_time, ensemble_member, lead_time, latitude, longitude |
| `wind_gust_surface` | Wind speed (gust) | m s-1 | init_time, ensemble_member, lead_time, latitude, longitude |
| `wind_u_100m` | 100 metre U wind component | m s-1 | init_time, ensemble_member, lead_time, latitude, longitude |
| `wind_u_10m` | 10 metre U wind component | m s-1 | init_time, ensemble_member, lead_time, latitude, longitude |
| `wind_u_80m` | 80 metre U wind component | m s-1 | init_time, ensemble_member, lead_time, latitude, longitude |
| `wind_v_100m` | 100 metre V wind component | m s-1 | init_time, ensemble_member, lead_time, latitude, longitude |
| `wind_v_10m` | 10 metre V wind component | m s-1 | init_time, ensemble_member, lead_time, latitude, longitude |
| `wind_v_80m` | 80 metre V wind component | m s-1 | init_time, ensemble_member, lead_time, latitude, longitude |
