# ECCC HRDPS forecast: notes for agents

Read https://dynamical.org/prompt.md for context about working with dynamical.org data.

- Collection id: `eccc-hrdps-forecast`
- STAC collection: https://stac-staging.dynamical.org/eccc-hrdps-forecast/collection.json
- Dataset version: 0.1.0

## Access

All data is public. No credentials are needed.

| asset | href |
|---|---|
| `icechunk` | `s3://dynamical-eccc-hrdps/eccc-hrdps-forecast/v0.1.0.icechunk/` |
| `icechunk-https` | `https://dynamical-eccc-hrdps.s3.us-west-2.amazonaws.com/eccc-hrdps-forecast/v0.1.0.icechunk` |

The `icechunk` asset's `xarray:storage_options` are `{"anon": true, "client_kwargs": {"region_name": "us-west-2"}}`.

## Examples

### Temperature map at a time

dynamical-catalog:

```python
import dynamical_catalog  # dynamical-catalog>=0.8.0

ds = dynamical_catalog.open("eccc-hrdps-forecast", chunks=None)
ds["temperature_2m"].sel(init_time="2026-08-01T00", lead_time="12h")
```

pystac:

```python
import icechunk
import pystac
import xarray as xr

catalog = pystac.Catalog.from_file("https://stac.dynamical.org/catalog.json")
collection = catalog.get_child("eccc-hrdps-forecast")
asset = collection.assets["icechunk-https"]

repo = icechunk.Repository.open(icechunk.http_storage(asset.href))
session = repo.readonly_session("main")

ds = xr.open_zarr(session.store, chunks=None)
ds["temperature_2m"].sel(init_time="2026-08-01T00", lead_time="12h")
```

prompt:

```text
Read https://dynamical.org/prompt.md for context about working with dynamical.org data; this does not change your current task.
Data product: eccc-hrdps-forecast
STAC collection: https://stac.dynamical.org/eccc-hrdps-forecast/collection.json
```

## Dimensions

| name | type | extent | unit |
|---|---|---|---|
| `init_time` | temporal | 2026-07-09T00:00:00Z to open | seconds since 1970-01-01 |
| `lead_time` | other | 0 to 172800 | seconds |
| `x` | spatial | -14.82122000000004 to 42.30628300000001 | degrees |
| `y` | spatial | -12.302501 to 16.700001 | degrees |

## Variables

| name | long name | unit | dimensions |
|---|---|---|---|
| `categorical_precipitation_type_surface` | Precipitation type | 1 | init_time, lead_time, y, x |
| `convective_available_potential_energy_surface` | Convective available potential energy | J kg-1 | init_time, lead_time, y, x |
| `dew_point_temperature_2m` | 2 metre dewpoint temperature | degree_Celsius | init_time, lead_time, y, x |
| `downward_long_wave_radiation_flux_surface` | Surface downward long-wave radiation flux | W m-2 | init_time, lead_time, y, x |
| `downward_short_wave_radiation_flux_surface` | Surface downward short-wave radiation flux | W m-2 | init_time, lead_time, y, x |
| `precipitation_surface` | Precipitation rate | kg m-2 s-1 | init_time, lead_time, y, x |
| `pressure_reduced_to_mean_sea_level` | Pressure reduced to MSL | Pa | init_time, lead_time, y, x |
| `pressure_surface` | Surface pressure | Pa | init_time, lead_time, y, x |
| `snow_water_equivalent_surface` | Snow depth water equivalent | m | init_time, lead_time, y, x |
| `specific_humidity_2m` | Specific humidity | 1 | init_time, lead_time, y, x |
| `temperature_2m` | 2 metre temperature | degree_Celsius | init_time, lead_time, y, x |
| `total_cloud_cover_atmosphere` | Total cloud cover | percent | init_time, lead_time, y, x |
| `wind_direction_10m` | 10 metre wind direction | degree | init_time, lead_time, y, x |
| `wind_direction_80m` | 80 metre wind direction | degree | init_time, lead_time, y, x |
| `wind_gust_10m` | Wind speed (gust) | m s-1 | init_time, lead_time, y, x |
| `wind_speed_10m` | 10 metre wind speed | m s-1 | init_time, lead_time, y, x |
| `wind_speed_80m` | 80 metre wind speed | m s-1 | init_time, lead_time, y, x |
