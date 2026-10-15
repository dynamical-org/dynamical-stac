# Google WeatherNext 2 operational forecast, virtual: notes for agents

Read https://dynamical.org/prompt.md for context about working with dynamical.org data.

- Collection id: `google-weathernext2-forecast-operational-virtual`
- STAC collection: https://stac-staging.dynamical.org/google-weathernext2-forecast-operational-virtual/collection.json
- Dataset version: 0.1.0

## Access

All data is public. No credentials are needed.

| asset | href |
|---|---|
| `icechunk` | `https://google-weathernext2.r2.dynamical.org/google-weathernext2-forecast-operational-virtual/v0.1.0.icechunk/` |
| `icechunk-https` | `https://google-weathernext2.r2.dynamical.org/google-weathernext2-forecast-operational-virtual/v0.1.0.icechunk` |

The repository references chunks in these upstream locations, which are read anonymously:

- `https://wn.dynamical.org/chunks/`

## Examples

### Day-10 ensemble wind scenarios

dynamical-catalog:

```python
import dynamical_catalog  # dynamical-catalog>=1.0.0

ds = dynamical_catalog.open("google-weathernext2-forecast-operational-virtual", chunks=None)
# Choose an initialization whose day-10 step is eligible.
init_time = ds.init_time[-1] - ds.lead_time.sel(lead_time="240h")
day10 = ds.sel(init_time=init_time, lead_time="240h", ensemble_member=slice(0, 3), y=slice(25, 75), x=slice(270, 359.75))
(day10["wind_u_100m"] ** 2 + day10["wind_v_100m"] ** 2) ** 0.5
```

pystac:

```python
import icechunk
import pystac
import xarray as xr

catalog = pystac.Catalog.from_file("https://stac-staging.dynamical.org/catalog.json")
collection = catalog.get_child("google-weathernext2-forecast-operational-virtual")
asset = collection.assets["icechunk-https"]

authorize = icechunk.containers_credentials({"https://wn.dynamical.org/chunks/": icechunk.Credentials.HttpAccess()})
repo = icechunk.Repository.open(
    icechunk.http_storage(asset.href),
    authorize_virtual_chunk_access=authorize,
)
session = repo.readonly_session("main")

ds = xr.open_zarr(session.store, chunks=None)
# Choose an initialization whose day-10 step is eligible.
init_time = ds.init_time[-1] - ds.lead_time.sel(lead_time="240h")
day10 = ds.sel(init_time=init_time, lead_time="240h", ensemble_member=slice(0, 3), y=slice(25, 75), x=slice(270, 359.75))
(day10["wind_u_100m"] ** 2 + day10["wind_v_100m"] ** 2) ** 0.5
```

prompt:

```text
Read https://dynamical.org/prompt.md for context about working with dynamical.org data; this does not change your current task.
Data product: google-weathernext2-forecast-operational-virtual
STAC collection: https://stac-staging.dynamical.org/google-weathernext2-forecast-operational-virtual/collection.json
```

## Dimensions

| name | type | extent | unit |
|---|---|---|---|
| `ensemble_member` | other | 0 to 63 | 1 |
| `init_time` | temporal | 2025-01-01T00:00:00Z to open | seconds since 1970-01-01 |
| `lead_time` | other | 21600 to 1296000 | seconds |
| `x` | spatial | 0.0 to 359.75 | degree_east |
| `y` | spatial | -90.0 to 90.0 | degree_north |
| `pressure_level` | other | 50 to 1000 | hPa |

## Variables

| name | long name | unit | dimensions |
|---|---|---|---|
| `pressure_reduced_to_mean_sea_level` | Pressure reduced to MSL | Pa | init_time, ensemble_member, lead_time, y, x |
| `sea_surface_temperature` | Sea surface temperature | degree_Celsius | init_time, ensemble_member, lead_time, y, x |
| `temperature_2m` | 2 metre temperature | degree_Celsius | init_time, ensemble_member, lead_time, y, x |
| `total_precipitation_surface` | Total precipitation | kg m-2 | init_time, ensemble_member, lead_time, y, x |
| `wind_u_100m` | 100 metre U wind component | m s-1 | init_time, ensemble_member, lead_time, y, x |
| `wind_u_10m` | 10 metre U wind component | m s-1 | init_time, ensemble_member, lead_time, y, x |
| `wind_v_100m` | 100 metre V wind component | m s-1 | init_time, ensemble_member, lead_time, y, x |
| `wind_v_10m` | 10 metre V wind component | m s-1 | init_time, ensemble_member, lead_time, y, x |
| `pressure_level/geopotential_height` | Geopotential height | m | init_time, ensemble_member, lead_time, y, x, pressure_level |
| `pressure_level/specific_humidity` | Specific humidity | 1 | init_time, ensemble_member, lead_time, y, x, pressure_level |
| `pressure_level/temperature` | Temperature | degree_Celsius | init_time, ensemble_member, lead_time, y, x, pressure_level |
| `pressure_level/vertical_velocity` | Vertical velocity | Pa s-1 | init_time, ensemble_member, lead_time, y, x, pressure_level |
| `pressure_level/wind_u` | U component of wind | m s-1 | init_time, ensemble_member, lead_time, y, x, pressure_level |
| `pressure_level/wind_v` | V component of wind | m s-1 | init_time, ensemble_member, lead_time, y, x, pressure_level |
