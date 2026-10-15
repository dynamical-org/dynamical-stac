# ECMWF AIFS Single forecast, virtual: notes for agents

Read https://dynamical.org/prompt.md for context about working with dynamical.org data.

- Collection id: `ecmwf-aifs-single-forecast-virtual`
- STAC collection: https://stac-staging.dynamical.org/ecmwf-aifs-single-forecast-virtual/collection.json
- Dataset version: 0.2.0

## Access

All data is public. No credentials are needed.

| asset | href |
|---|---|
| `icechunk` | `s3://dynamical-ecmwf-aifs-single/ecmwf-aifs-single-forecast-virtual/v0.2.0.icechunk/` |
| `icechunk-https` | `https://dynamical-ecmwf-aifs-single.s3.us-west-2.amazonaws.com/ecmwf-aifs-single-forecast-virtual/v0.2.0.icechunk` |

The `icechunk` asset's `xarray:storage_options` are `{"anon": true, "client_kwargs": {"region_name": "us-west-2"}}`.

The repository references chunks in these upstream locations, which are read anonymously:

- `gs://ecmwf-open-data/`
- `s3://ecmwf-forecasts/`

## Examples

### Temperature map

dynamical-catalog:

```python
import dynamical_catalog  # dynamical-catalog>=1.0.0

ds = dynamical_catalog.open("ecmwf-aifs-single-forecast-virtual", chunks=None)
ds["temperature_2m"].sel(init_time="2026-03-01T00", lead_time="24h")

# Variables with a vertical dimension live in the pressure_level group
ds_pressure = dynamical_catalog.open("ecmwf-aifs-single-forecast-virtual", group="pressure_level", chunks=None)
ds_pressure["geopotential_height"].sel(pressure_level=500)
```

pystac:

```python
import icechunk
import pystac
import xarray as xr

catalog = pystac.Catalog.from_file("https://stac.dynamical.org/catalog.json")
collection = catalog.get_child("ecmwf-aifs-single-forecast-virtual")
asset = collection.assets["icechunk-https"]

authorize = icechunk.containers_credentials({"gs://ecmwf-open-data/": icechunk.gcs_credentials(anonymous=True), "s3://ecmwf-forecasts/": icechunk.s3_anonymous_credentials()})
repo = icechunk.Repository.open(
    icechunk.http_storage(asset.href),
    authorize_virtual_chunk_access=authorize,
)
session = repo.readonly_session("main")

ds = xr.open_zarr(session.store, chunks=None)
ds["temperature_2m"].sel(init_time="2026-03-01T00", lead_time="24h")

# Variables with a vertical dimension live in the pressure_level group
ds_pressure = xr.open_zarr(session.store, group="pressure_level", chunks=None)
ds_pressure["geopotential_height"].sel(pressure_level=500)
```

prompt:

```text
Read https://dynamical.org/prompt.md for context about working with dynamical.org data; this does not change your current task.
Data product: ecmwf-aifs-single-forecast-virtual
STAC collection: https://stac.dynamical.org/ecmwf-aifs-single-forecast-virtual/collection.json
```

## Dimensions

| name | type | extent | unit |
|---|---|---|---|
| `init_time` | temporal | 2024-04-01T00:00:00Z to open | seconds since 1970-01-01 |
| `latitude` | spatial | -90.0 to 90.0 | degree_north |
| `lead_time` | other | 0 to 1296000 | seconds |
| `longitude` | spatial | -180.0 to 179.75 | degree_east |
| `pressure_level` | other | 10 to 1000 | hPa |

## Variables

| name | long name | unit | dimensions |
|---|---|---|---|
| `convective_precipitation_run_total_surface` | Convective precipitation | kg m-2 | init_time, lead_time, latitude, longitude |
| `dew_point_temperature_2m` | 2 metre dewpoint temperature | degree_Celsius | init_time, lead_time, latitude, longitude |
| `downward_long_wave_radiation_run_total_surface` | Surface long-wave (thermal) radiation downwards | W s m-2 | init_time, lead_time, latitude, longitude |
| `downward_short_wave_radiation_run_total_surface` | Surface short-wave (solar) radiation downwards | W s m-2 | init_time, lead_time, latitude, longitude |
| `geopotential_height_surface` | Geopotential height | m | init_time, lead_time, latitude, longitude |
| `high_cloud_cover` | High cloud cover | percent | init_time, lead_time, latitude, longitude |
| `land_sea_mask_surface` | Land-sea mask | 1 | init_time, lead_time, latitude, longitude |
| `low_cloud_cover` | Low cloud cover | percent | init_time, lead_time, latitude, longitude |
| `medium_cloud_cover` | Medium cloud cover | percent | init_time, lead_time, latitude, longitude |
| `pressure_reduced_to_mean_sea_level` | Pressure reduced to MSL | Pa | init_time, lead_time, latitude, longitude |
| `pressure_surface` | Surface pressure | Pa | init_time, lead_time, latitude, longitude |
| `runoff_water_equivalent_run_total_surface` | Runoff water equivalent (surface plus subsurface) | kg m-2 | init_time, lead_time, latitude, longitude |
| `skin_temperature_surface` | Skin temperature | degree_Celsius | init_time, lead_time, latitude, longitude |
| `slope_of_sub_gridscale_orography_surface` | Slope of sub-gridscale orography | 1 | init_time, lead_time, latitude, longitude |
| `snow_area_fraction_surface` | Snow cover | 1 | init_time, lead_time, latitude, longitude |
| `snowfall_water_equivalent_run_total_surface` | Snowfall water equivalent | kg m-2 | init_time, lead_time, latitude, longitude |
| `soil_temperature_layer_1` | Soil temperature | degree_Celsius | init_time, lead_time, latitude, longitude |
| `soil_temperature_layer_2` | Soil temperature | degree_Celsius | init_time, lead_time, latitude, longitude |
| `standard_deviation_of_sub_gridscale_orography_surface` | Standard deviation of sub-gridscale orography | m | init_time, lead_time, latitude, longitude |
| `temperature_2m` | 2 metre temperature | degree_Celsius | init_time, lead_time, latitude, longitude |
| `total_cloud_cover_atmosphere` | Total cloud cover | percent | init_time, lead_time, latitude, longitude |
| `total_column_water_atmosphere` | Total column water | kg m-2 | init_time, lead_time, latitude, longitude |
| `total_precipitation_run_total_surface` | Total precipitation | kg m-2 | init_time, lead_time, latitude, longitude |
| `volumetric_soil_moisture_layer_1` | Volumetric soil moisture | 1 | init_time, lead_time, latitude, longitude |
| `volumetric_soil_moisture_layer_2` | Volumetric soil moisture | 1 | init_time, lead_time, latitude, longitude |
| `wind_u_100m` | 100 metre U wind component | m s-1 | init_time, lead_time, latitude, longitude |
| `wind_u_10m` | 10 metre U wind component | m s-1 | init_time, lead_time, latitude, longitude |
| `wind_v_100m` | 100 metre V wind component | m s-1 | init_time, lead_time, latitude, longitude |
| `wind_v_10m` | 10 metre V wind component | m s-1 | init_time, lead_time, latitude, longitude |
| `pressure_level/geopotential_height` | Geopotential height | m | init_time, lead_time, latitude, longitude, pressure_level |
| `pressure_level/specific_humidity` | Specific humidity | 1 | init_time, lead_time, latitude, longitude, pressure_level |
| `pressure_level/temperature` | Temperature | degree_Celsius | init_time, lead_time, latitude, longitude, pressure_level |
| `pressure_level/vertical_velocity` | Vertical velocity | Pa s-1 | init_time, lead_time, latitude, longitude, pressure_level |
| `pressure_level/wind_u` | U component of wind | m s-1 | init_time, lead_time, latitude, longitude, pressure_level |
| `pressure_level/wind_v` | V component of wind | m s-1 | init_time, lead_time, latitude, longitude, pressure_level |
