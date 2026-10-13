# ECMWF IFS ENS forecast, 15 day, 0.25 degree: notes for agents

Read https://dynamical.org/prompt.md for context about working with dynamical.org data.

- Collection id: `ecmwf-ifs-ens-forecast-15-day-0-25-degree`
- STAC collection: https://stac-test.dynamical.org/ecmwf-ifs-ens-forecast-15-day-0-25-degree/collection.json
- Dataset version: 0.1.0

## Access

All data is public. No credentials are needed.

| asset | href |
|---|---|
| `icechunk` | `s3://dynamical-ecmwf-ifs-ens/ecmwf-ifs-ens-forecast-15-day-0-25-degree/v0.1.0.icechunk/` |
| `icechunk-https` | `https://dynamical-ecmwf-ifs-ens.s3.us-west-2.amazonaws.com/ecmwf-ifs-ens-forecast-15-day-0-25-degree/v0.1.0.icechunk` |

The `icechunk` asset's `xarray:storage_options` are `{"anon": true, "client_kwargs": {"region_name": "us-west-2"}}`.

## Examples

### Maximum ensemble temperature

dynamical-catalog:

```python
import dynamical_catalog  # dynamical-catalog>=0.8.0

ds = dynamical_catalog.open("ecmwf-ifs-ens-forecast-15-day-0-25-degree", chunks=None)
ds["temperature_2m"].sel(init_time="2025-01-01T00", latitude=0, longitude=0).max()
```

pystac:

```python
import icechunk
import pystac
import xarray as xr

catalog = pystac.Catalog.from_file("https://stac.dynamical.org/catalog.json")
collection = catalog.get_child("ecmwf-ifs-ens-forecast-15-day-0-25-degree")
asset = collection.assets["icechunk-https"]

repo = icechunk.Repository.open(icechunk.http_storage(asset.href))
session = repo.readonly_session("main")

ds = xr.open_zarr(session.store, chunks=None)
ds["temperature_2m"].sel(init_time="2025-01-01T00", latitude=0, longitude=0).max()
```

prompt:

```text
Read https://dynamical.org/prompt.md for context about working with dynamical.org data; this does not change your current task.
Data product: ecmwf-ifs-ens-forecast-15-day-0-25-degree
STAC collection: https://stac.dynamical.org/ecmwf-ifs-ens-forecast-15-day-0-25-degree/collection.json
```

## Dimensions

| name | type | extent | unit |
|---|---|---|---|
| `ensemble_member` | other | 0 to 50 | 1 |
| `init_time` | temporal | 2024-04-01T00:00:00Z to open | seconds since 1970-01-01 |
| `latitude` | spatial | -90.0 to 90.0 | degree_north |
| `lead_time` | other | 0 to 1296000 | seconds |
| `longitude` | spatial | -180.0 to 179.75 | degree_east |

## Variables

| name | long name | unit | dimensions |
|---|---|---|---|
| `categorical_precipitation_type_surface` | Precipitation type | 1 | init_time, lead_time, ensemble_member, latitude, longitude |
| `dew_point_temperature_2m` | 2 metre dewpoint temperature | degree_Celsius | init_time, lead_time, ensemble_member, latitude, longitude |
| `downward_long_wave_radiation_flux_surface` | Surface downward long-wave radiation flux | W m-2 | init_time, lead_time, ensemble_member, latitude, longitude |
| `downward_short_wave_radiation_flux_surface` | Surface downward short-wave radiation flux | W m-2 | init_time, lead_time, ensemble_member, latitude, longitude |
| `geopotential_height_500hpa` | Geopotential height | m | init_time, lead_time, ensemble_member, latitude, longitude |
| `geopotential_height_850hpa` | Geopotential height | m | init_time, lead_time, ensemble_member, latitude, longitude |
| `geopotential_height_925hpa` | Geopotential height | m | init_time, lead_time, ensemble_member, latitude, longitude |
| `precipitation_surface` | Precipitation rate | kg m-2 s-1 | init_time, lead_time, ensemble_member, latitude, longitude |
| `pressure_reduced_to_mean_sea_level` | Pressure reduced to MSL | Pa | init_time, lead_time, ensemble_member, latitude, longitude |
| `pressure_surface` | Surface pressure | Pa | init_time, lead_time, ensemble_member, latitude, longitude |
| `temperature_2m` | 2 metre temperature | degree_Celsius | init_time, lead_time, ensemble_member, latitude, longitude |
| `temperature_850hpa` | Temperature | degree_Celsius | init_time, lead_time, ensemble_member, latitude, longitude |
| `temperature_925hpa` | Temperature | degree_Celsius | init_time, lead_time, ensemble_member, latitude, longitude |
| `total_cloud_cover_atmosphere` | Total cloud cover | percent | init_time, lead_time, ensemble_member, latitude, longitude |
| `wind_gust_10m` | Maximum 10 metre wind gust since previous post-processing | m s-1 | init_time, lead_time, ensemble_member, latitude, longitude |
| `wind_u_100m` | 100 metre U wind component | m s-1 | init_time, lead_time, ensemble_member, latitude, longitude |
| `wind_u_10m` | 10 metre U wind component | m s-1 | init_time, lead_time, ensemble_member, latitude, longitude |
| `wind_v_100m` | 100 metre V wind component | m s-1 | init_time, lead_time, ensemble_member, latitude, longitude |
| `wind_v_10m` | 10 metre V wind component | m s-1 | init_time, lead_time, ensemble_member, latitude, longitude |
