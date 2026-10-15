# NOAA RRFS ENS forecast, virtual: notes for agents

Read https://dynamical.org/prompt.md for context about working with dynamical.org data.

- Collection id: `noaa-rrfs-ens-forecast-virtual`
- STAC collection: https://stac-test.dynamical.org/noaa-rrfs-ens-forecast-virtual/collection.json
- Dataset version: 0.1.0

## Access

All data is public. No credentials are needed.

| asset | href |
|---|---|
| `icechunk` | `s3://dynamical-noaa-rrfs-ens/noaa-rrfs-ens-forecast-virtual/v0.1.0.icechunk/` |
| `icechunk-https` | `https://dynamical-noaa-rrfs-ens.s3.us-west-2.amazonaws.com/noaa-rrfs-ens-forecast-virtual/v0.1.0.icechunk` |

The `icechunk` asset's `xarray:storage_options` are `{"anon": true, "client_kwargs": {"region_name": "us-west-2"}}`.

The repository references chunks in these upstream locations, which are read anonymously:

- `s3://noaa-rrfs-ops-pds/`

## Examples

### Temperature map

dynamical-catalog:

```python
import dynamical_catalog  # dynamical-catalog>=1.0.1

ds = dynamical_catalog.open("noaa-rrfs-ens-forecast-virtual", chunks=None)
ds["temperature_2m"].sel(init_time="2026-09-16T12", lead_time="24h", ensemble_member=0)

# Variables with a vertical dimension live in the pressure_level group
ds_pressure = dynamical_catalog.open("noaa-rrfs-ens-forecast-virtual", group="pressure_level", chunks=None)

ds_pressure["temperature"].sel(init_time="2026-09-16T12", lead_time="24h", pressure_level=500).mean("ensemble_member")
```

pystac:

```python
import icechunk
import pystac
import xarray as xr

catalog = pystac.Catalog.from_file("https://stac.dynamical.org/catalog.json")
collection = catalog.get_child("noaa-rrfs-ens-forecast-virtual")
asset = collection.assets["icechunk-https"]

authorize = icechunk.containers_credentials({"s3://noaa-rrfs-ops-pds/": icechunk.s3_anonymous_credentials()})
repo = icechunk.Repository.open(
    icechunk.http_storage(asset.href),
    authorize_virtual_chunk_access=authorize,
)
session = repo.readonly_session("main")

ds = xr.open_zarr(session.store, chunks=None)
ds["temperature_2m"].sel(init_time="2026-09-16T12", lead_time="24h", ensemble_member=0)

# Variables with a vertical dimension live in the pressure_level group
ds_pressure = xr.open_zarr(session.store, group="pressure_level", chunks=None)

ds_pressure["temperature"].sel(init_time="2026-09-16T12", lead_time="24h", pressure_level=500).mean("ensemble_member")
```

prompt:

```text
Read https://dynamical.org/prompt.md for context about working with dynamical.org data; this does not change your current task.
Data product: noaa-rrfs-ens-forecast-virtual
STAC collection: https://stac.dynamical.org/noaa-rrfs-ens-forecast-virtual/collection.json
```

## Dimensions

| name | type | extent | unit |
|---|---|---|---|
| `ensemble_member` | other | 0 to 5 | 1 |
| `init_time` | temporal | 2026-09-10T00:00:00Z to open | seconds since 1970-01-01 |
| `lead_time` | other | 0 to 216000 | seconds |
| `x` | spatial | -2697520.142521929 to 2696479.857478071 | m |
| `y` | spatial | -1587306.152556665 to 1586693.847443335 | m |
| `pressure_level` | other | 250.0 to 1000.0 | hPa |

## Variables

| name | long name | unit | dimensions |
|---|---|---|---|
| `categorical_freezing_rain_surface` | Categorical freezing rain | 1 | init_time, ensemble_member, lead_time, y, x |
| `categorical_ice_pellets_surface` | Categorical ice pellets | 1 | init_time, ensemble_member, lead_time, y, x |
| `categorical_rain_surface` | Categorical rain | 1 | init_time, ensemble_member, lead_time, y, x |
| `categorical_snow_surface` | Categorical snow | 1 | init_time, ensemble_member, lead_time, y, x |
| `cloud_ceiling_height` | Ceiling | m | init_time, ensemble_member, lead_time, y, x |
| `composite_reflectivity` | Maximum/Composite radar reflectivity | dBZ | init_time, ensemble_member, lead_time, y, x |
| `convective_available_potential_energy_surface` | Convective available potential energy | J kg-1 | init_time, ensemble_member, lead_time, y, x |
| `convective_inhibition_surface` | Convective inhibition | J kg-1 | init_time, ensemble_member, lead_time, y, x |
| `dew_point_temperature_2m` | 2 metre dewpoint temperature | degree_Celsius | init_time, ensemble_member, lead_time, y, x |
| `downward_short_wave_radiation_flux_surface` | Surface downward short-wave radiation flux | W m-2 | init_time, ensemble_member, lead_time, y, x |
| `echo_top` | Echo top | m | init_time, ensemble_member, lead_time, y, x |
| `freezing_rain_run_total_surface` | Freezing Rain | kg m-2 | init_time, ensemble_member, lead_time, y, x |
| `freezing_rain_surface` | Freezing Rain | kg m-2 | init_time, ensemble_member, lead_time, y, x |
| `geopotential_height_surface` | Geopotential height | m | init_time, ensemble_member, lead_time, y, x |
| `high_cloud_cover` | High cloud cover | percent | init_time, ensemble_member, lead_time, y, x |
| `instantaneous_downward_short_wave_radiation_flux_surface` | Surface downward short-wave radiation flux | W m-2 | init_time, ensemble_member, lead_time, y, x |
| `instantaneous_total_cloud_cover_atmosphere` | Total cloud cover | percent | init_time, ensemble_member, lead_time, y, x |
| `low_cloud_cover` | Low cloud cover | percent | init_time, ensemble_member, lead_time, y, x |
| `maximum_downward_vertical_velocity_100_1000mb` | Maximum downward vertical velocity | m s-1 | init_time, ensemble_member, lead_time, y, x |
| `maximum_lightning_atmosphere` | Lightning | 1 | init_time, ensemble_member, lead_time, y, x |
| `maximum_relative_humidity_2m` | Time-maximum 2 metre relative humidity | percent | init_time, ensemble_member, lead_time, y, x |
| `maximum_updraft_helicity_3000_0m` | Updraft Helicity | m2 s-2 | init_time, ensemble_member, lead_time, y, x |
| `maximum_updraft_helicity_5000_2000m` | Updraft Helicity | m2 s-2 | init_time, ensemble_member, lead_time, y, x |
| `maximum_upward_vertical_velocity_100_1000mb` | Maximum upward vertical velocity | m s-1 | init_time, ensemble_member, lead_time, y, x |
| `maximum_wind_speed_10m` | Time-maximum 10 metre wind speed | m s-1 | init_time, ensemble_member, lead_time, y, x |
| `medium_cloud_cover` | Medium cloud cover | percent | init_time, ensemble_member, lead_time, y, x |
| `minimum_relative_humidity_2m` | Time-minimum 2 metre relative humidity | percent | init_time, ensemble_member, lead_time, y, x |
| `minimum_updraft_helicity_3000_0m` | Minimum updraft helicity | m2 s-2 | init_time, ensemble_member, lead_time, y, x |
| `minimum_updraft_helicity_5000_2000m` | Minimum updraft helicity | m2 s-2 | init_time, ensemble_member, lead_time, y, x |
| `percent_frozen_precipitation_surface` | Percent frozen precipitation | percent | init_time, ensemble_member, lead_time, y, x |
| `precipitable_water_atmosphere` | Precipitable water | kg m-2 | init_time, ensemble_member, lead_time, y, x |
| `pressure_reduced_to_mean_sea_level` | Pressure reduced to MSL | Pa | init_time, ensemble_member, lead_time, y, x |
| `pressure_surface` | Surface pressure | Pa | init_time, ensemble_member, lead_time, y, x |
| `relative_humidity_2m` | 2 metre relative humidity | percent | init_time, ensemble_member, lead_time, y, x |
| `storm_relative_helicity_1000_0m` | Storm relative helicity | m2 s-2 | init_time, ensemble_member, lead_time, y, x |
| `storm_relative_helicity_3000_0m` | Storm relative helicity | m2 s-2 | init_time, ensemble_member, lead_time, y, x |
| `temperature_2m` | 2 metre temperature | degree_Celsius | init_time, ensemble_member, lead_time, y, x |
| `total_cloud_cover_atmosphere` | Total cloud cover | percent | init_time, ensemble_member, lead_time, y, x |
| `total_cloud_cover_boundary_layer` | Boundary layer cloud cover | percent | init_time, ensemble_member, lead_time, y, x |
| `total_precipitation_run_total_surface` | Total precipitation | kg m-2 | init_time, ensemble_member, lead_time, y, x |
| `total_precipitation_surface` | Total precipitation | kg m-2 | init_time, ensemble_member, lead_time, y, x |
| `total_snowfall_run_total_surface` | Total snowfall | m | init_time, ensemble_member, lead_time, y, x |
| `vertical_u_component_shear_0_6000m` | Vertical u-component shear | m s-1 | init_time, ensemble_member, lead_time, y, x |
| `vertical_v_component_shear_0_6000m` | Vertical v-component shear | m s-1 | init_time, ensemble_member, lead_time, y, x |
| `visibility_surface` | Visibility | m | init_time, ensemble_member, lead_time, y, x |
| `wind_gust_surface` | Wind speed (gust) | m s-1 | init_time, ensemble_member, lead_time, y, x |
| `wind_u_10m` | 10 metre U wind component | m s-1 | init_time, ensemble_member, lead_time, y, x |
| `wind_u_160m` | U component of wind | m s-1 | init_time, ensemble_member, lead_time, y, x |
| `wind_u_320m` | U component of wind | m s-1 | init_time, ensemble_member, lead_time, y, x |
| `wind_u_80m` | 80 metre U wind component | m s-1 | init_time, ensemble_member, lead_time, y, x |
| `wind_v_10m` | 10 metre V wind component | m s-1 | init_time, ensemble_member, lead_time, y, x |
| `wind_v_160m` | V component of wind | m s-1 | init_time, ensemble_member, lead_time, y, x |
| `wind_v_320m` | V component of wind | m s-1 | init_time, ensemble_member, lead_time, y, x |
| `wind_v_80m` | 80 metre V wind component | m s-1 | init_time, ensemble_member, lead_time, y, x |
| `pressure_level/absolute_vorticity` | Absolute vorticity | s-1 | init_time, ensemble_member, lead_time, y, x, pressure_level |
| `pressure_level/dew_point_temperature` | Dew point temperature | degree_Celsius | init_time, ensemble_member, lead_time, y, x, pressure_level |
| `pressure_level/geopotential_height` | Geopotential height | m | init_time, ensemble_member, lead_time, y, x, pressure_level |
| `pressure_level/relative_humidity` | Relative humidity | percent | init_time, ensemble_member, lead_time, y, x, pressure_level |
| `pressure_level/specific_humidity` | Specific humidity | 1 | init_time, ensemble_member, lead_time, y, x, pressure_level |
| `pressure_level/temperature` | Temperature | degree_Celsius | init_time, ensemble_member, lead_time, y, x, pressure_level |
| `pressure_level/wind_u` | U component of wind | m s-1 | init_time, ensemble_member, lead_time, y, x, pressure_level |
| `pressure_level/wind_v` | V component of wind | m s-1 | init_time, ensemble_member, lead_time, y, x, pressure_level |
