# DWD ICON-EU forecast, 5 day: notes for agents

Read https://dynamical.org/prompt.md for context about working with dynamical.org data.

- Collection id: `dwd-icon-eu-forecast-5-day`
- STAC collection: https://stac.dynamical.org/dwd-icon-eu-forecast-5-day/collection.json
- Dataset version: 0.2.0

## Access

All data is public. No credentials are needed.

| asset | href |
|---|---|
| `icechunk` | `s3://dynamical-dwd-icon-eu/dwd-icon-eu-forecast-5-day/v0.2.0.icechunk/` |
| `icechunk-https` | `https://dynamical-dwd-icon-eu.s3.us-west-2.amazonaws.com/dwd-icon-eu-forecast-5-day/v0.2.0.icechunk` |

The `icechunk` asset's `xarray:storage_options` are `{"anon": true, "client_kwargs": {"region_name": "us-west-2"}}`.

## Examples

### Maximum temperature

dynamical-catalog:

```python
import dynamical_catalog  # dynamical-catalog>=0.8.0

ds = dynamical_catalog.open("dwd-icon-eu-forecast-5-day", chunks=None)
ds["temperature_2m"].sel(init_time="2026-04-01T00", latitude=50, longitude=10).max()
```

pystac:

```python
import icechunk
import pystac
import xarray as xr

catalog = pystac.Catalog.from_file("https://stac.dynamical.org/catalog.json")
collection = catalog.get_child("dwd-icon-eu-forecast-5-day")
asset = collection.assets["icechunk-https"]

repo = icechunk.Repository.open(icechunk.http_storage(asset.href))
session = repo.readonly_session("main")

ds = xr.open_zarr(session.store, chunks=None)
ds["temperature_2m"].sel(init_time="2026-04-01T00", latitude=50, longitude=10).max()
```

prompt:

```text
Read https://dynamical.org/prompt.md for context about working with dynamical.org data; this does not change your current task.
Data product: dwd-icon-eu-forecast-5-day
STAC collection: https://stac.dynamical.org/dwd-icon-eu-forecast-5-day/collection.json
```

## Dimensions

| name | type | extent | unit |
|---|---|---|---|
| `init_time` | temporal | 2026-02-10T00:00:00Z to open | seconds since 1970-01-01 |
| `latitude` | spatial | 29.5 to 70.5 | degree_north |
| `lead_time` | other | 0 to 432000 | seconds |
| `longitude` | spatial | -23.5 to 62.5 | degree_east |

## Variables

| name | long name | unit | dimensions |
|---|---|---|---|
| `cloud_cover_high` | High cloud cover | percent | init_time, lead_time, latitude, longitude |
| `cloud_cover_low` | Low cloud cover | percent | init_time, lead_time, latitude, longitude |
| `cloud_cover_medium` | Medium cloud cover | percent | init_time, lead_time, latitude, longitude |
| `convective_available_potential_energy_atmosphere` | Convective available potential energy | J kg-1 | init_time, lead_time, latitude, longitude |
| `dew_point_temperature_2m` | 2 metre dewpoint temperature | degree_Celsius | init_time, lead_time, latitude, longitude |
| `downward_diffuse_short_wave_radiation_flux_surface` | Surface diffuse short-wave radiation flux | W m-2 | init_time, lead_time, latitude, longitude |
| `downward_direct_short_wave_radiation_flux_surface` | Surface direct short-wave radiation flux | W m-2 | init_time, lead_time, latitude, longitude |
| `precipitable_water_atmosphere` | Precipitable water | kg m-2 | init_time, lead_time, latitude, longitude |
| `precipitation_surface` | Precipitation rate | kg m-2 s-1 | init_time, lead_time, latitude, longitude |
| `pressure_reduced_to_mean_sea_level` | Pressure reduced to MSL | Pa | init_time, lead_time, latitude, longitude |
| `pressure_surface` | Surface pressure | Pa | init_time, lead_time, latitude, longitude |
| `relative_humidity_2m` | 2 metre relative humidity | percent | init_time, lead_time, latitude, longitude |
| `snow_thickness_surface` | Snow depth | m | init_time, lead_time, latitude, longitude |
| `snow_water_equivalent_surface` | Snow depth water equivalent | m | init_time, lead_time, latitude, longitude |
| `temperature_2m` | 2 metre temperature | degree_Celsius | init_time, lead_time, latitude, longitude |
| `total_cloud_cover_atmosphere` | Total cloud cover | percent | init_time, lead_time, latitude, longitude |
| `wind_gust_10m` | Maximum 10 metre wind gust since previous post-processing | m s-1 | init_time, lead_time, latitude, longitude |
| `wind_u_10m` | 10 metre U wind component | m s-1 | init_time, lead_time, latitude, longitude |
| `wind_v_10m` | 10 metre V wind component | m s-1 | init_time, lead_time, latitude, longitude |
