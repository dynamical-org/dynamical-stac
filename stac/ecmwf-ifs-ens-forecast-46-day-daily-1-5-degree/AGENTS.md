# ECMWF IFS ENS forecast, 46 day, daily, 1.5 degree: notes for agents

Read https://dynamical.org/prompt.md for context about working with dynamical.org data.

- Collection id: `ecmwf-ifs-ens-forecast-46-day-daily-1-5-degree`
- STAC collection: https://stac.dynamical.org/ecmwf-ifs-ens-forecast-46-day-daily-1-5-degree/collection.json
- Dataset version: 0.2.0

## Access

All data is public. No credentials are needed.

| asset | href |
|---|---|
| `icechunk` | `s3://dynamical-ecmwf-ifs-ens/ecmwf-ifs-ens-forecast-46-day-daily-1-5-degree/v0.2.0.icechunk/` |
| `icechunk-https` | `https://dynamical-ecmwf-ifs-ens.s3.us-west-2.amazonaws.com/ecmwf-ifs-ens-forecast-46-day-daily-1-5-degree/v0.2.0.icechunk` |

The `icechunk` asset's `xarray:storage_options` are `{"anon": true, "client_kwargs": {"region_name": "us-west-2"}}`.

## Examples

### Maximum ensemble temperature

dynamical-catalog:

```python
import dynamical_catalog  # dynamical-catalog>=0.8.0

ds = dynamical_catalog.open("ecmwf-ifs-ens-forecast-46-day-daily-1-5-degree", chunks=None)
ds["average_temperature_2m"].sel(init_time="2026-08-01T00", latitude=0, longitude=0).max()

# Variables with a vertical dimension live in the pressure_level group
ds_pressure = dynamical_catalog.open("ecmwf-ifs-ens-forecast-46-day-daily-1-5-degree", group="pressure_level", chunks=None)
ds_pressure["geopotential_height"].sel(init_time="2026-08-01T00", lead_time="10D", pressure_level=500).std("ensemble_member")
```

pystac:

```python
import icechunk
import pystac
import xarray as xr

catalog = pystac.Catalog.from_file("https://stac.dynamical.org/catalog.json")
collection = catalog.get_child("ecmwf-ifs-ens-forecast-46-day-daily-1-5-degree")
asset = collection.assets["icechunk-https"]

repo = icechunk.Repository.open(icechunk.http_storage(asset.href))
session = repo.readonly_session("main")

ds = xr.open_zarr(session.store, chunks=None)
ds["average_temperature_2m"].sel(init_time="2026-08-01T00", latitude=0, longitude=0).max()

# Variables with a vertical dimension live in the pressure_level group
ds_pressure = xr.open_zarr(session.store, group="pressure_level", chunks=None)
ds_pressure["geopotential_height"].sel(init_time="2026-08-01T00", lead_time="10D", pressure_level=500).std("ensemble_member")
```

prompt:

```text
Read https://dynamical.org/prompt.md for context about working with dynamical.org data; this does not change your current task.
Data product: ecmwf-ifs-ens-forecast-46-day-daily-1-5-degree
STAC collection: https://stac.dynamical.org/ecmwf-ifs-ens-forecast-46-day-daily-1-5-degree/collection.json
```

## Dimensions

| name | type | extent | unit |
|---|---|---|---|
| `ensemble_member` | other | 0 to 100 | 1 |
| `init_time` | temporal | 2026-01-01T00:00:00Z to open | seconds since 1970-01-01 |
| `latitude` | spatial | -90.0 to 90.0 | degree_north |
| `lead_time` | other | 0 to 3974400 | seconds |
| `longitude` | spatial | -180.0 to 178.5 | degree_east |
| `pressure_level` | other | 10 to 1000 | hPa |

## Variables

| name | long name | unit | dimensions |
|---|---|---|---|
| `average_convective_available_potential_energy_surface` | Convective available potential energy | J kg-1 | init_time, lead_time, ensemble_member, latitude, longitude |
| `average_dew_point_temperature_2m` | Mean 2 metre dewpoint temperature in the last 24 hours | degree_Celsius | init_time, lead_time, ensemble_member, latitude, longitude |
| `average_temperature_2m` | Mean temperature at 2 metres in the last 24 hours | degree_Celsius | init_time, lead_time, ensemble_member, latitude, longitude |
| `downward_latent_heat_flux_surface` | Time-mean surface latent heat flux | W m-2 | init_time, lead_time, ensemble_member, latitude, longitude |
| `downward_long_wave_radiation_flux_surface` | Surface downward long-wave radiation flux | W m-2 | init_time, lead_time, ensemble_member, latitude, longitude |
| `downward_sensible_heat_flux_surface` | Time-mean surface sensible heat flux | W m-2 | init_time, lead_time, ensemble_member, latitude, longitude |
| `downward_short_wave_radiation_flux_surface` | Surface downward short-wave radiation flux | W m-2 | init_time, lead_time, ensemble_member, latitude, longitude |
| `eastward_turbulent_surface_stress` | Time-mean eastward turbulent surface stress | Pa | init_time, lead_time, ensemble_member, latitude, longitude |
| `maximum_temperature_2m` | Maximum temperature | degree_Celsius | init_time, lead_time, ensemble_member, latitude, longitude |
| `minimum_temperature_2m` | Minimum temperature | degree_Celsius | init_time, lead_time, ensemble_member, latitude, longitude |
| `net_long_wave_radiation_flux_surface` | Surface net long-wave radiation flux | W m-2 | init_time, lead_time, ensemble_member, latitude, longitude |
| `net_long_wave_radiation_flux_top_of_atmosphere` | Top net long-wave radiation flux | W m-2 | init_time, lead_time, ensemble_member, latitude, longitude |
| `net_short_wave_radiation_flux_surface` | Surface net short-wave radiation flux | W m-2 | init_time, lead_time, ensemble_member, latitude, longitude |
| `northward_turbulent_surface_stress` | Time-mean northward turbulent surface stress | Pa | init_time, lead_time, ensemble_member, latitude, longitude |
| `precipitation_convective_surface` | Convective precipitation rate | kg m-2 s-1 | init_time, lead_time, ensemble_member, latitude, longitude |
| `precipitation_surface` | Precipitation rate | kg m-2 s-1 | init_time, lead_time, ensemble_member, latitude, longitude |
| `pressure_reduced_to_mean_sea_level` | Pressure reduced to MSL | Pa | init_time, lead_time, ensemble_member, latitude, longitude |
| `pressure_surface` | Surface pressure | Pa | init_time, lead_time, ensemble_member, latitude, longitude |
| `runoff_surface` | Surface runoff rate | kg m-2 s-1 | init_time, lead_time, ensemble_member, latitude, longitude |
| `runoff_water_equivalent_surface` | Runoff rate water equivalent (surface plus subsurface) | kg m-2 s-1 | init_time, lead_time, ensemble_member, latitude, longitude |
| `sea_ice_area_fraction` | Sea ice area fraction | 1 | init_time, lead_time, ensemble_member, latitude, longitude |
| `sea_surface_temperature` | Sea surface temperature | degree_Celsius | init_time, lead_time, ensemble_member, latitude, longitude |
| `skin_temperature_surface` | Skin temperature | degree_Celsius | init_time, lead_time, ensemble_member, latitude, longitude |
| `snow_albedo_surface` | Snow albedo | percent | init_time, lead_time, ensemble_member, latitude, longitude |
| `snow_density_surface` | Snow density | kg m-3 | init_time, lead_time, ensemble_member, latitude, longitude |
| `snow_water_equivalent_surface` | Snow depth water equivalent | m | init_time, lead_time, ensemble_member, latitude, longitude |
| `snowfall_water_equivalent_rate_surface` | Total snowfall rate water equivalent | kg m-2 s-1 | init_time, lead_time, ensemble_member, latitude, longitude |
| `soil_moisture_0_100cm` | Soil moisture top 100 cm | kg m-3 | init_time, lead_time, ensemble_member, latitude, longitude |
| `soil_moisture_0_20cm` | Soil moisture top 20 cm | kg m-3 | init_time, lead_time, ensemble_member, latitude, longitude |
| `soil_temperature_0_100cm` | Soil temperature top 100 cm | degree_Celsius | init_time, lead_time, ensemble_member, latitude, longitude |
| `soil_temperature_0_20cm` | Soil temperature top 20 cm | degree_Celsius | init_time, lead_time, ensemble_member, latitude, longitude |
| `total_cloud_cover_atmosphere` | Total cloud cover | percent | init_time, lead_time, ensemble_member, latitude, longitude |
| `total_column_water_atmosphere` | Total column water | kg m-2 | init_time, lead_time, ensemble_member, latitude, longitude |
| `wind_u_10m` | 10 metre U wind component | m s-1 | init_time, lead_time, ensemble_member, latitude, longitude |
| `wind_v_10m` | 10 metre V wind component | m s-1 | init_time, lead_time, ensemble_member, latitude, longitude |
| `pressure_level/geopotential_height` | Geopotential height | m | init_time, lead_time, ensemble_member, pressure_level, latitude, longitude |
| `pressure_level/specific_humidity` | Specific humidity | 1 | init_time, lead_time, ensemble_member, pressure_level, latitude, longitude |
| `pressure_level/temperature` | Temperature | degree_Celsius | init_time, lead_time, ensemble_member, pressure_level, latitude, longitude |
| `pressure_level/vertical_velocity` | Vertical velocity | Pa s-1 | init_time, lead_time, ensemble_member, pressure_level, latitude, longitude |
| `pressure_level/wind_u` | U component of wind | m s-1 | init_time, lead_time, ensemble_member, pressure_level, latitude, longitude |
| `pressure_level/wind_v` | V component of wind | m s-1 | init_time, lead_time, ensemble_member, pressure_level, latitude, longitude |
