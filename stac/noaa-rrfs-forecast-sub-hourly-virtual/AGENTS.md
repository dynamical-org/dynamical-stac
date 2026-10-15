# NOAA RRFS forecast, sub-hourly, virtual: notes for agents

Read https://dynamical.org/prompt.md for context about working with dynamical.org data.

- Collection id: `noaa-rrfs-forecast-sub-hourly-virtual`
- STAC collection: https://stac.dynamical.org/noaa-rrfs-forecast-sub-hourly-virtual/collection.json
- Dataset version: 0.1.0

## Access

All data is public. No credentials are needed.

| asset | href |
|---|---|
| `icechunk` | `s3://dynamical-noaa-rrfs/noaa-rrfs-forecast-sub-hourly-virtual/v0.1.0.icechunk/` |
| `icechunk-https` | `https://dynamical-noaa-rrfs.s3.us-west-2.amazonaws.com/noaa-rrfs-forecast-sub-hourly-virtual/v0.1.0.icechunk` |

The `icechunk` asset's `xarray:storage_options` are `{"anon": true, "client_kwargs": {"region_name": "us-west-2"}}`.

The repository references chunks in these upstream locations, which are read anonymously:

- `s3://noaa-rrfs-ops-pds/`

## Examples

### Reflectivity map

dynamical-catalog:

```python
import dynamical_catalog  # dynamical-catalog>=1.0.1

ds = dynamical_catalog.open("noaa-rrfs-forecast-sub-hourly-virtual", chunks=None)
ds["composite_reflectivity"].sel(init_time="2026-09-16T12", lead_time="2h15min")
```

pystac:

```python
import icechunk
import pystac
import xarray as xr

catalog = pystac.Catalog.from_file("https://stac.dynamical.org/catalog.json")
collection = catalog.get_child("noaa-rrfs-forecast-sub-hourly-virtual")
asset = collection.assets["icechunk-https"]

authorize = icechunk.containers_credentials({"s3://noaa-rrfs-ops-pds/": icechunk.s3_anonymous_credentials()})
repo = icechunk.Repository.open(
    icechunk.http_storage(asset.href),
    authorize_virtual_chunk_access=authorize,
)
session = repo.readonly_session("main")

ds = xr.open_zarr(session.store, chunks=None)
ds["composite_reflectivity"].sel(init_time="2026-09-16T12", lead_time="2h15min")
```

prompt:

```text
Read https://dynamical.org/prompt.md for context about working with dynamical.org data; this does not change your current task.
Data product: noaa-rrfs-forecast-sub-hourly-virtual
STAC collection: https://stac.dynamical.org/noaa-rrfs-forecast-sub-hourly-virtual/collection.json
```

## Dimensions

| name | type | extent | unit |
|---|---|---|---|
| `init_time` | temporal | 2026-08-13T00:00:00Z to open | seconds since 1970-01-01 |
| `lead_time` | other | 900 to 64800 | seconds |
| `x` | spatial | -2697520.142521929 to 2696479.857478071 | m |
| `y` | spatial | -1587306.152556665 to 1586693.847443335 | m |

## Variables

| name | long name | unit | dimensions |
|---|---|---|---|
| `categorical_freezing_rain_surface` | Categorical freezing rain | 1 | init_time, lead_time, y, x |
| `categorical_ice_pellets_surface` | Categorical ice pellets | 1 | init_time, lead_time, y, x |
| `categorical_rain_surface` | Categorical rain | 1 | init_time, lead_time, y, x |
| `categorical_snow_surface` | Categorical snow | 1 | init_time, lead_time, y, x |
| `composite_reflectivity` | Maximum/Composite radar reflectivity | dBZ | init_time, lead_time, y, x |
| `derived_radar_reflectivity_1000m` | Derived radar reflectivity | dBZ | init_time, lead_time, y, x |
| `derived_radar_reflectivity_4000m` | Derived radar reflectivity | dBZ | init_time, lead_time, y, x |
| `dew_point_temperature_2m` | 2 metre dewpoint temperature | degree_Celsius | init_time, lead_time, y, x |
| `echo_top` | Echo top | m | init_time, lead_time, y, x |
| `freezing_rain_run_total_surface` | Freezing Rain | kg m-2 | init_time, lead_time, y, x |
| `frozen_precipitation_run_total_surface` | Graupel (snow pellets) precipitation | kg m-2 | init_time, lead_time, y, x |
| `geopotential_height_cloud_base` | Geopotential height | m | init_time, lead_time, y, x |
| `geopotential_height_cloud_ceiling` | Geopotential height | m | init_time, lead_time, y, x |
| `geopotential_height_cloud_top` | Geopotential height | m | init_time, lead_time, y, x |
| `geopotential_height_surface` | Geopotential height | m | init_time, lead_time, y, x |
| `instantaneous_downward_long_wave_radiation_flux_surface` | Surface downward long-wave radiation flux | W m-2 | init_time, lead_time, y, x |
| `instantaneous_downward_short_wave_radiation_flux_surface` | Surface downward short-wave radiation flux | W m-2 | init_time, lead_time, y, x |
| `instantaneous_upward_long_wave_radiation_flux_surface` | Surface upward long-wave radiation flux | W m-2 | init_time, lead_time, y, x |
| `instantaneous_upward_short_wave_radiation_flux_surface` | Surface upward short-wave radiation flux | W m-2 | init_time, lead_time, y, x |
| `percent_frozen_precipitation_surface` | Percent frozen precipitation | percent | init_time, lead_time, y, x |
| `precipitation_rate_surface` | Precipitation rate | kg m-2 s-1 | init_time, lead_time, y, x |
| `pressure_reduced_to_mean_sea_level` | Pressure reduced to MSL | Pa | init_time, lead_time, y, x |
| `pressure_surface` | Surface pressure | Pa | init_time, lead_time, y, x |
| `specific_humidity_2m` | Specific humidity | 1 | init_time, lead_time, y, x |
| `temperature_2m` | 2 metre temperature | degree_Celsius | init_time, lead_time, y, x |
| `total_precipitation_run_total_surface` | Total precipitation | kg m-2 | init_time, lead_time, y, x |
| `total_snow_precipitation_run_total_surface` | Total snow precipitation | kg m-2 | init_time, lead_time, y, x |
| `total_snowfall_run_total_surface` | Total snowfall | m | init_time, lead_time, y, x |
| `updraft_helicity_5000_2000m` | Updraft Helicity | m2 s-2 | init_time, lead_time, y, x |
| `vertically_integrated_liquid_atmosphere` | Vertically-integrated liquid | kg m-2 | init_time, lead_time, y, x |
| `visibility_surface` | Visibility | m | init_time, lead_time, y, x |
| `visible_beam_downward_solar_flux_surface` | Visible Beam Downward Solar Flux | W m-2 | init_time, lead_time, y, x |
| `visible_diffuse_downward_solar_flux_surface` | Visible Diffuse Downward Solar Flux | W m-2 | init_time, lead_time, y, x |
| `wind_gust_surface` | Wind speed (gust) | m s-1 | init_time, lead_time, y, x |
| `wind_u_10m` | 10 metre U wind component | m s-1 | init_time, lead_time, y, x |
| `wind_u_80m` | 80 metre U wind component | m s-1 | init_time, lead_time, y, x |
| `wind_v_10m` | 10 metre V wind component | m s-1 | init_time, lead_time, y, x |
| `wind_v_80m` | 80 metre V wind component | m s-1 | init_time, lead_time, y, x |
