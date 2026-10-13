# NOAA GEFS forecast, 10 day, 0.25 degree, virtual: notes for agents

Read https://dynamical.org/prompt.md for context about working with dynamical.org data.

- Collection id: `noaa-gefs-forecast-10-day-0-25-degree-virtual`
- STAC collection: https://stac-test.dynamical.org/noaa-gefs-forecast-10-day-0-25-degree-virtual/collection.json
- Dataset version: 0.1.0

## Access

All data is public. No credentials are needed.

| asset | href |
|---|---|
| `icechunk` | `s3://dynamical-noaa-gefs/noaa-gefs-forecast-10-day-0-25-degree-virtual/v0.1.0.icechunk/` |
| `icechunk-https` | `https://dynamical-noaa-gefs.s3.us-west-2.amazonaws.com/noaa-gefs-forecast-10-day-0-25-degree-virtual/v0.1.0.icechunk` |

The `icechunk` asset's `xarray:storage_options` are `{"anon": true, "client_kwargs": {"region_name": "us-west-2"}}`.

The repository references chunks in these upstream locations, which are read anonymously:

- `s3://noaa-gefs-pds/`

## Examples

### Ensemble mean temperature map

dynamical-catalog:

```python
import dynamical_catalog  # dynamical-catalog>=0.8.0

ds = dynamical_catalog.open("noaa-gefs-forecast-10-day-0-25-degree-virtual", chunks=None)
ds["temperature_2m"].sel(init_time="2025-01-01T00", lead_time="24h").mean("ensemble_member")
```

pystac:

```python
import icechunk
import pystac
import xarray as xr

catalog = pystac.Catalog.from_file("https://stac.dynamical.org/catalog.json")
collection = catalog.get_child("noaa-gefs-forecast-10-day-0-25-degree-virtual")
asset = collection.assets["icechunk-https"]

authorize = icechunk.containers_credentials({"s3://noaa-gefs-pds/": icechunk.s3_anonymous_credentials()})
repo = icechunk.Repository.open(
    icechunk.http_storage(asset.href),
    authorize_virtual_chunk_access=authorize,
)
session = repo.readonly_session("main")

ds = xr.open_zarr(session.store, chunks=None)
ds["temperature_2m"].sel(init_time="2025-01-01T00", lead_time="24h").mean("ensemble_member")
```

prompt:

```text
Read https://dynamical.org/prompt.md for context about working with dynamical.org data; this does not change your current task.
Data product: noaa-gefs-forecast-10-day-0-25-degree-virtual
STAC collection: https://stac.dynamical.org/noaa-gefs-forecast-10-day-0-25-degree-virtual/collection.json
```

## Dimensions

| name | type | extent | unit |
|---|---|---|---|
| `ensemble_member` | other | 0 to 30 | 1 |
| `init_time` | temporal | 2020-10-01T00:00:00Z to open | seconds since 1970-01-01 |
| `latitude` | spatial | -90.0 to 90.0 | degree_north |
| `lead_time` | other | 0 to 864000 | seconds |
| `longitude` | spatial | -180.0 to 179.75 | degree_east |

## Variables

| name | long name | unit | dimensions |
|---|---|---|---|
| `categorical_freezing_rain_surface` | Categorical freezing rain | 1 | init_time, ensemble_member, lead_time, latitude, longitude |
| `categorical_ice_pellets_surface` | Categorical ice pellets | 1 | init_time, ensemble_member, lead_time, latitude, longitude |
| `categorical_rain_surface` | Categorical rain | 1 | init_time, ensemble_member, lead_time, latitude, longitude |
| `categorical_snow_surface` | Categorical snow | 1 | init_time, ensemble_member, lead_time, latitude, longitude |
| `convective_available_potential_energy_180_0mb` | Convective available potential energy | J kg-1 | init_time, ensemble_member, lead_time, latitude, longitude |
| `convective_available_potential_energy_surface` | Convective available potential energy | J kg-1 | init_time, ensemble_member, lead_time, latitude, longitude |
| `convective_inhibition_180_0mb` | Convective inhibition | J kg-1 | init_time, ensemble_member, lead_time, latitude, longitude |
| `convective_inhibition_surface` | Convective inhibition | J kg-1 | init_time, ensemble_member, lead_time, latitude, longitude |
| `dew_point_temperature_2m` | 2 metre dewpoint temperature | degree_Celsius | init_time, ensemble_member, lead_time, latitude, longitude |
| `downward_long_wave_radiation_flux_surface` | Surface downward long-wave radiation flux | W m-2 | init_time, ensemble_member, lead_time, latitude, longitude |
| `downward_short_wave_radiation_flux_surface` | Surface downward short-wave radiation flux | W m-2 | init_time, ensemble_member, lead_time, latitude, longitude |
| `geopotential_height_cloud_ceiling` | Geopotential height | m | init_time, ensemble_member, lead_time, latitude, longitude |
| `ice_thickness_surface` | Ice thickness | m | init_time, ensemble_member, lead_time, latitude, longitude |
| `latent_heat_flux_surface` | Latent heat flux | W m-2 | init_time, ensemble_member, lead_time, latitude, longitude |
| `maximum_temperature_2m` | Maximum temperature | degree_Celsius | init_time, ensemble_member, lead_time, latitude, longitude |
| `minimum_temperature_2m` | Minimum temperature | degree_Celsius | init_time, ensemble_member, lead_time, latitude, longitude |
| `percent_frozen_precipitation_surface` | Percent frozen precipitation | percent | init_time, ensemble_member, lead_time, latitude, longitude |
| `precipitable_water_atmosphere` | Precipitable water | kg m-2 | init_time, ensemble_member, lead_time, latitude, longitude |
| `pressure_reduced_to_mean_sea_level` | Pressure reduced to MSL | Pa | init_time, ensemble_member, lead_time, latitude, longitude |
| `pressure_reduced_to_mean_sea_level_eta_model` | MSLP (Eta model reduction) | Pa | init_time, ensemble_member, lead_time, latitude, longitude |
| `pressure_surface` | Surface pressure | Pa | init_time, ensemble_member, lead_time, latitude, longitude |
| `relative_humidity_2m` | 2 metre relative humidity | percent | init_time, ensemble_member, lead_time, latitude, longitude |
| `sensible_heat_flux_surface` | Sensible heat flux | W m-2 | init_time, ensemble_member, lead_time, latitude, longitude |
| `snow_thickness_surface` | Snow depth | m | init_time, ensemble_member, lead_time, latitude, longitude |
| `snow_water_equivalent_surface` | Snow depth water equivalent | m | init_time, ensemble_member, lead_time, latitude, longitude |
| `soil_temperature_0_10cm` | Soil temperature | degree_Celsius | init_time, ensemble_member, lead_time, latitude, longitude |
| `storm_relative_helicity_3000_0m` | Storm relative helicity | m2 s-2 | init_time, ensemble_member, lead_time, latitude, longitude |
| `temperature_2m` | 2 metre temperature | degree_Celsius | init_time, ensemble_member, lead_time, latitude, longitude |
| `total_cloud_cover_atmosphere` | Total cloud cover | percent | init_time, ensemble_member, lead_time, latitude, longitude |
| `total_precipitation_surface` | Total precipitation | kg m-2 | init_time, ensemble_member, lead_time, latitude, longitude |
| `upward_long_wave_radiation_flux_surface` | Surface upward long-wave radiation flux | W m-2 | init_time, ensemble_member, lead_time, latitude, longitude |
| `upward_long_wave_radiation_flux_top_of_atmosphere` | Upward long-wave radiation flux | W m-2 | init_time, ensemble_member, lead_time, latitude, longitude |
| `upward_short_wave_radiation_flux_surface` | Surface upward short-wave radiation flux | W m-2 | init_time, ensemble_member, lead_time, latitude, longitude |
| `visibility_surface` | Visibility | m | init_time, ensemble_member, lead_time, latitude, longitude |
| `volumetric_soil_moisture_0_10cm` | Volumetric soil moisture | 1 | init_time, ensemble_member, lead_time, latitude, longitude |
| `wind_gust_surface` | Wind speed (gust) | m s-1 | init_time, ensemble_member, lead_time, latitude, longitude |
| `wind_u_10m` | 10 metre U wind component | m s-1 | init_time, ensemble_member, lead_time, latitude, longitude |
| `wind_v_10m` | 10 metre V wind component | m s-1 | init_time, ensemble_member, lead_time, latitude, longitude |
