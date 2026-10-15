# NOAA GEFS forecast, 16 day, 0.5 degree, virtual: notes for agents

Read https://dynamical.org/prompt.md for context about working with dynamical.org data.

- Collection id: `noaa-gefs-forecast-16-day-0-5-degree-virtual`
- STAC collection: https://stac-staging.dynamical.org/noaa-gefs-forecast-16-day-0-5-degree-virtual/collection.json
- Dataset version: 0.1.0

## Access

All data is public. No credentials are needed.

| asset | href |
|---|---|
| `icechunk` | `s3://dynamical-noaa-gefs/noaa-gefs-forecast-16-day-0-5-degree-virtual/v0.1.0.icechunk/` |
| `icechunk-https` | `https://dynamical-noaa-gefs.s3.us-west-2.amazonaws.com/noaa-gefs-forecast-16-day-0-5-degree-virtual/v0.1.0.icechunk` |

The `icechunk` asset's `xarray:storage_options` are `{"anon": true, "client_kwargs": {"region_name": "us-west-2"}}`.

The repository references chunks in these upstream locations, which are read anonymously:

- `s3://noaa-gefs-pds/`

## Examples

### Ensemble mean temperature map

dynamical-catalog:

```python
import dynamical_catalog  # dynamical-catalog>=0.8.0

ds = dynamical_catalog.open("noaa-gefs-forecast-16-day-0-5-degree-virtual", chunks=None)
ds["temperature_2m"].sel(init_time="2025-01-01T00", lead_time="24h").mean("ensemble_member")

# Variables with a vertical dimension live in the pressure_level, model_level
# and height_above_mean_sea_level groups
ds_pressure = dynamical_catalog.open("noaa-gefs-forecast-16-day-0-5-degree-virtual", group="pressure_level", chunks=None)
ds_model = dynamical_catalog.open("noaa-gefs-forecast-16-day-0-5-degree-virtual", group="model_level", chunks=None)
ds_height = dynamical_catalog.open("noaa-gefs-forecast-16-day-0-5-degree-virtual", group="height_above_mean_sea_level", chunks=None)

ds_pressure["geopotential_height"].sel(init_time="2025-01-01T00", lead_time="24h", pressure_level=500).mean("ensemble_member")
```

pystac:

```python
import icechunk
import pystac
import xarray as xr

catalog = pystac.Catalog.from_file("https://stac.dynamical.org/catalog.json")
collection = catalog.get_child("noaa-gefs-forecast-16-day-0-5-degree-virtual")
asset = collection.assets["icechunk-https"]

authorize = icechunk.containers_credentials({"s3://noaa-gefs-pds/": icechunk.s3_anonymous_credentials()})
repo = icechunk.Repository.open(
    icechunk.http_storage(asset.href),
    authorize_virtual_chunk_access=authorize,
)
session = repo.readonly_session("main")

ds = xr.open_zarr(session.store, chunks=None)
ds["temperature_2m"].sel(init_time="2025-01-01T00", lead_time="24h").mean("ensemble_member")

# Variables with a vertical dimension live in the pressure_level, model_level
# and height_above_mean_sea_level groups
ds_pressure = xr.open_zarr(session.store, group="pressure_level", chunks=None)
ds_model = xr.open_zarr(session.store, group="model_level", chunks=None)
ds_height = xr.open_zarr(session.store, group="height_above_mean_sea_level", chunks=None)

ds_pressure["geopotential_height"].sel(init_time="2025-01-01T00", lead_time="24h", pressure_level=500).mean("ensemble_member")
```

prompt:

```text
Read https://dynamical.org/prompt.md for context about working with dynamical.org data; this does not change your current task.
Data product: noaa-gefs-forecast-16-day-0-5-degree-virtual
STAC collection: https://stac.dynamical.org/noaa-gefs-forecast-16-day-0-5-degree-virtual/collection.json
```

## Dimensions

| name | type | extent | unit |
|---|---|---|---|
| `ensemble_member` | other | 0 to 30 | 1 |
| `init_time` | temporal | 2020-10-01T00:00:00Z to open | seconds since 1970-01-01 |
| `latitude` | spatial | -90.0 to 90.0 | degree_north |
| `lead_time` | other | 0 to 1382400 | seconds |
| `longitude` | spatial | -180.0 to 179.5 | degree_east |
| `height_above_mean_sea_level` | other | 305.0 to 4572.0 | m |
| `model_level` | other | 1 to 4 | 1 |
| `pressure_level` | other | 1.0 to 1000.0 | hPa |

## Variables

| name | long name | unit | dimensions |
|---|---|---|---|
| `albedo_surface` | Forecast albedo | percent | init_time, ensemble_member, lead_time, latitude, longitude |
| `apparent_temperature_2m` | Apparent temperature | degree_Celsius | init_time, ensemble_member, lead_time, latitude, longitude |
| `average_high_cloud_cover` | High cloud cover | percent | init_time, ensemble_member, lead_time, latitude, longitude |
| `average_low_cloud_cover` | Low cloud cover | percent | init_time, ensemble_member, lead_time, latitude, longitude |
| `average_medium_cloud_cover` | Medium cloud cover | percent | init_time, ensemble_member, lead_time, latitude, longitude |
| `average_precipitation_rate_surface` | Precipitation rate | kg m-2 s-1 | init_time, ensemble_member, lead_time, latitude, longitude |
| `average_pressure_high_cloud_bottom` | Pressure | Pa | init_time, ensemble_member, lead_time, latitude, longitude |
| `average_pressure_high_cloud_top` | Pressure | Pa | init_time, ensemble_member, lead_time, latitude, longitude |
| `average_pressure_low_cloud_bottom` | Pressure | Pa | init_time, ensemble_member, lead_time, latitude, longitude |
| `average_pressure_low_cloud_top` | Pressure | Pa | init_time, ensemble_member, lead_time, latitude, longitude |
| `average_pressure_middle_cloud_bottom` | Pressure | Pa | init_time, ensemble_member, lead_time, latitude, longitude |
| `average_pressure_middle_cloud_top` | Pressure | Pa | init_time, ensemble_member, lead_time, latitude, longitude |
| `average_snow_area_fraction_surface` | Snow cover | 1 | init_time, ensemble_member, lead_time, latitude, longitude |
| `average_temperature_high_cloud_top` | Temperature | degree_Celsius | init_time, ensemble_member, lead_time, latitude, longitude |
| `average_temperature_low_cloud_top` | Temperature | degree_Celsius | init_time, ensemble_member, lead_time, latitude, longitude |
| `average_temperature_middle_cloud_top` | Temperature | degree_Celsius | init_time, ensemble_member, lead_time, latitude, longitude |
| `average_total_cloud_cover_boundary_layer` | Boundary layer cloud cover | percent | init_time, ensemble_member, lead_time, latitude, longitude |
| `best_4_layer_lifted_index_surface` | Best (4-layer) lifted index | K | init_time, ensemble_member, lead_time, latitude, longitude |
| `brightness_temperature_top_of_atmosphere` | Brightness temperature | K | init_time, ensemble_member, lead_time, latitude, longitude |
| `categorical_freezing_rain_surface` | Categorical freezing rain | 1 | init_time, ensemble_member, lead_time, latitude, longitude |
| `categorical_ice_pellets_surface` | Categorical ice pellets | 1 | init_time, ensemble_member, lead_time, latitude, longitude |
| `categorical_rain_surface` | Categorical rain | 1 | init_time, ensemble_member, lead_time, latitude, longitude |
| `categorical_snow_surface` | Categorical snow | 1 | init_time, ensemble_member, lead_time, latitude, longitude |
| `clear_sky_uv_b_downward_solar_flux_surface` | Clear sky UV-B downward solar flux | W m-2 | init_time, ensemble_member, lead_time, latitude, longitude |
| `cloud_cover_475mb` | Fraction of cloud cover | percent | init_time, ensemble_member, lead_time, latitude, longitude |
| `cloud_water_atmosphere` | Cloud water | kg m-2 | init_time, ensemble_member, lead_time, latitude, longitude |
| `cloud_work_function_atmosphere` | Cloud work function | J kg-1 | init_time, ensemble_member, lead_time, latitude, longitude |
| `convective_available_potential_energy_180_0mb` | Convective available potential energy | J kg-1 | init_time, ensemble_member, lead_time, latitude, longitude |
| `convective_available_potential_energy_255_0mb` | Convective available potential energy | J kg-1 | init_time, ensemble_member, lead_time, latitude, longitude |
| `convective_available_potential_energy_surface` | Convective available potential energy | J kg-1 | init_time, ensemble_member, lead_time, latitude, longitude |
| `convective_cloud_cover` | Convective cloud cover | percent | init_time, ensemble_member, lead_time, latitude, longitude |
| `convective_inhibition_180_0mb` | Convective inhibition | J kg-1 | init_time, ensemble_member, lead_time, latitude, longitude |
| `convective_inhibition_255_0mb` | Convective inhibition | J kg-1 | init_time, ensemble_member, lead_time, latitude, longitude |
| `convective_inhibition_surface` | Convective inhibition | J kg-1 | init_time, ensemble_member, lead_time, latitude, longitude |
| `convective_precipitation_surface` | Convective precipitation | kg m-2 | init_time, ensemble_member, lead_time, latitude, longitude |
| `dew_point_temperature_2m` | 2 metre dewpoint temperature | degree_Celsius | init_time, ensemble_member, lead_time, latitude, longitude |
| `dew_point_temperature_30_0mb` | Dew point temperature | degree_Celsius | init_time, ensemble_member, lead_time, latitude, longitude |
| `downward_long_wave_radiation_flux_surface` | Surface downward long-wave radiation flux | W m-2 | init_time, ensemble_member, lead_time, latitude, longitude |
| `downward_short_wave_radiation_flux_surface` | Surface downward short-wave radiation flux | W m-2 | init_time, ensemble_member, lead_time, latitude, longitude |
| `eastward_gravity_wave_surface_stress` | Eastward gravity wave surface stress | Pa | init_time, ensemble_member, lead_time, latitude, longitude |
| `field_capacity_surface` | Field Capacity | 1 | init_time, ensemble_member, lead_time, latitude, longitude |
| `five_wave_geopotential_height_500mb` | 5-wave geopotential height | m | init_time, ensemble_member, lead_time, latitude, longitude |
| `friction_velocity_surface` | Friction velocity | m s-1 | init_time, ensemble_member, lead_time, latitude, longitude |
| `geopotential_height_0c_isotherm` | Geopotential height | m | init_time, ensemble_member, lead_time, latitude, longitude |
| `geopotential_height_0p5pvu` | Geopotential height | m | init_time, ensemble_member, lead_time, latitude, longitude |
| `geopotential_height_1p5pvu` | Geopotential height | m | init_time, ensemble_member, lead_time, latitude, longitude |
| `geopotential_height_1pvu` | Geopotential height | m | init_time, ensemble_member, lead_time, latitude, longitude |
| `geopotential_height_2pvu` | Geopotential height | m | init_time, ensemble_member, lead_time, latitude, longitude |
| `geopotential_height_cloud_ceiling` | Geopotential height | m | init_time, ensemble_member, lead_time, latitude, longitude |
| `geopotential_height_highest_tropospheric_freezing_level` | Geopotential height | m | init_time, ensemble_member, lead_time, latitude, longitude |
| `geopotential_height_max_wind` | Geopotential height | m | init_time, ensemble_member, lead_time, latitude, longitude |
| `geopotential_height_minus0p5pvu` | Geopotential height | m | init_time, ensemble_member, lead_time, latitude, longitude |
| `geopotential_height_minus1p5pvu` | Geopotential height | m | init_time, ensemble_member, lead_time, latitude, longitude |
| `geopotential_height_minus1pvu` | Geopotential height | m | init_time, ensemble_member, lead_time, latitude, longitude |
| `geopotential_height_minus2pvu` | Geopotential height | m | init_time, ensemble_member, lead_time, latitude, longitude |
| `geopotential_height_tropopause` | Geopotential height | m | init_time, ensemble_member, lead_time, latitude, longitude |
| `ground_heat_flux_surface` | Ground heat flux | W m-2 | init_time, ensemble_member, lead_time, latitude, longitude |
| `haines_index_surface` | Haines Index | 1 | init_time, ensemble_member, lead_time, latitude, longitude |
| `icao_standard_atmosphere_reference_height_max_wind` | ICAO Standard Atmosphere reference height | m | init_time, ensemble_member, lead_time, latitude, longitude |
| `icao_standard_atmosphere_reference_height_tropopause` | ICAO Standard Atmosphere reference height | m | init_time, ensemble_member, lead_time, latitude, longitude |
| `ice_cover_surface` | Ice cover (1=ice, 0=no ice) | 1 | init_time, ensemble_member, lead_time, latitude, longitude |
| `ice_thickness_surface` | Ice thickness | m | init_time, ensemble_member, lead_time, latitude, longitude |
| `land_sea_mask_surface` | Land-sea mask | 1 | init_time, ensemble_member, lead_time, latitude, longitude |
| `large_scale_precipitation_surface` | Large scale precipitation (non-convective) | kg m-2 | init_time, ensemble_member, lead_time, latitude, longitude |
| `latent_heat_flux_surface` | Latent heat flux | W m-2 | init_time, ensemble_member, lead_time, latitude, longitude |
| `liquid_volumetric_soil_moisture_0_10cm` | Liquid volumetric soil moisture (non-frozen) | 1 | init_time, ensemble_member, lead_time, latitude, longitude |
| `liquid_volumetric_soil_moisture_100_200cm` | Liquid volumetric soil moisture (non-frozen) | 1 | init_time, ensemble_member, lead_time, latitude, longitude |
| `liquid_volumetric_soil_moisture_10_40cm` | Liquid volumetric soil moisture (non-frozen) | 1 | init_time, ensemble_member, lead_time, latitude, longitude |
| `liquid_volumetric_soil_moisture_40_100cm` | Liquid volumetric soil moisture (non-frozen) | 1 | init_time, ensemble_member, lead_time, latitude, longitude |
| `maximum_temperature_2m` | Maximum temperature | degree_Celsius | init_time, ensemble_member, lead_time, latitude, longitude |
| `minimum_temperature_2m` | Minimum temperature | degree_Celsius | init_time, ensemble_member, lead_time, latitude, longitude |
| `momentum_flux_u_component_surface` | Momentum flux, u-component | Pa | init_time, ensemble_member, lead_time, latitude, longitude |
| `momentum_flux_v_component_surface` | Momentum flux, v-component | Pa | init_time, ensemble_member, lead_time, latitude, longitude |
| `montgomery_stream_function_320k` | Montgomery stream Function | m2 s-2 | init_time, ensemble_member, lead_time, latitude, longitude |
| `northward_gravity_wave_surface_stress` | Northward gravity wave surface stress | Pa | init_time, ensemble_member, lead_time, latitude, longitude |
| `parcel_lifted_index_30_0mb` | Parcel lifted index (to 500 hPa) | K | init_time, ensemble_member, lead_time, latitude, longitude |
| `percent_frozen_precipitation_surface` | Percent frozen precipitation | percent | init_time, ensemble_member, lead_time, latitude, longitude |
| `planetary_boundary_layer_height_surface` | Boundary layer height | m | init_time, ensemble_member, lead_time, latitude, longitude |
| `plant_canopy_surface_water_surface` | Plant canopy surface water | kg m-2 | init_time, ensemble_member, lead_time, latitude, longitude |
| `potential_evaporation_rate_surface` | Potential evaporation rate | W m-2 | init_time, ensemble_member, lead_time, latitude, longitude |
| `potential_temperature_0p995_sigma` | Potential temperature | K | init_time, ensemble_member, lead_time, latitude, longitude |
| `potential_vorticity_310k` | Potential vorticity | K m2 kg-1 s-1 | init_time, ensemble_member, lead_time, latitude, longitude |
| `potential_vorticity_320k` | Potential vorticity | K m2 kg-1 s-1 | init_time, ensemble_member, lead_time, latitude, longitude |
| `potential_vorticity_350k` | Potential vorticity | K m2 kg-1 s-1 | init_time, ensemble_member, lead_time, latitude, longitude |
| `potential_vorticity_450k` | Potential vorticity | K m2 kg-1 s-1 | init_time, ensemble_member, lead_time, latitude, longitude |
| `potential_vorticity_550k` | Potential vorticity | K m2 kg-1 s-1 | init_time, ensemble_member, lead_time, latitude, longitude |
| `potential_vorticity_650k` | Potential vorticity | K m2 kg-1 s-1 | init_time, ensemble_member, lead_time, latitude, longitude |
| `precipitable_water_30_0mb` | Precipitable water | kg m-2 | init_time, ensemble_member, lead_time, latitude, longitude |
| `precipitable_water_atmosphere` | Precipitable water | kg m-2 | init_time, ensemble_member, lead_time, latitude, longitude |
| `precipitation_convective_surface` | Convective precipitation rate | kg m-2 s-1 | init_time, ensemble_member, lead_time, latitude, longitude |
| `pressure_0p5pvu` | Pressure | Pa | init_time, ensemble_member, lead_time, latitude, longitude |
| `pressure_1p5pvu` | Pressure | Pa | init_time, ensemble_member, lead_time, latitude, longitude |
| `pressure_1pvu` | Pressure | Pa | init_time, ensemble_member, lead_time, latitude, longitude |
| `pressure_2pvu` | Pressure | Pa | init_time, ensemble_member, lead_time, latitude, longitude |
| `pressure_80m` | 80 metre pressure | Pa | init_time, ensemble_member, lead_time, latitude, longitude |
| `pressure_convective_cloud_bottom` | Pressure | Pa | init_time, ensemble_member, lead_time, latitude, longitude |
| `pressure_convective_cloud_top` | Pressure | Pa | init_time, ensemble_member, lead_time, latitude, longitude |
| `pressure_max_wind` | Pressure | Pa | init_time, ensemble_member, lead_time, latitude, longitude |
| `pressure_mean_sea_level` | Pressure | Pa | init_time, ensemble_member, lead_time, latitude, longitude |
| `pressure_minus0p5pvu` | Pressure | Pa | init_time, ensemble_member, lead_time, latitude, longitude |
| `pressure_minus1p5pvu` | Pressure | Pa | init_time, ensemble_member, lead_time, latitude, longitude |
| `pressure_minus1pvu` | Pressure | Pa | init_time, ensemble_member, lead_time, latitude, longitude |
| `pressure_minus2pvu` | Pressure | Pa | init_time, ensemble_member, lead_time, latitude, longitude |
| `pressure_of_lifted_parcel_level_255_0mb` | Pressure of level from which parcel was lifted | Pa | init_time, ensemble_member, lead_time, latitude, longitude |
| `pressure_reduced_to_mean_sea_level` | Pressure reduced to MSL | Pa | init_time, ensemble_member, lead_time, latitude, longitude |
| `pressure_reduced_to_mean_sea_level_eta_model` | MSLP (Eta model reduction) | Pa | init_time, ensemble_member, lead_time, latitude, longitude |
| `pressure_surface` | Surface pressure | Pa | init_time, ensemble_member, lead_time, latitude, longitude |
| `pressure_tropopause` | Pressure | Pa | init_time, ensemble_member, lead_time, latitude, longitude |
| `relative_humidity_0c_isotherm` | Relative humidity | percent | init_time, ensemble_member, lead_time, latitude, longitude |
| `relative_humidity_0p33_1_sigma` | Relative humidity | percent | init_time, ensemble_member, lead_time, latitude, longitude |
| `relative_humidity_0p44_0p72_sigma` | Relative humidity | percent | init_time, ensemble_member, lead_time, latitude, longitude |
| `relative_humidity_0p44_1_sigma` | Relative humidity | percent | init_time, ensemble_member, lead_time, latitude, longitude |
| `relative_humidity_0p72_0p94_sigma` | Relative humidity | percent | init_time, ensemble_member, lead_time, latitude, longitude |
| `relative_humidity_0p995_sigma` | Relative humidity | percent | init_time, ensemble_member, lead_time, latitude, longitude |
| `relative_humidity_120_90mb` | Relative humidity | percent | init_time, ensemble_member, lead_time, latitude, longitude |
| `relative_humidity_150_120mb` | Relative humidity | percent | init_time, ensemble_member, lead_time, latitude, longitude |
| `relative_humidity_180_150mb` | Relative humidity | percent | init_time, ensemble_member, lead_time, latitude, longitude |
| `relative_humidity_2m` | 2 metre relative humidity | percent | init_time, ensemble_member, lead_time, latitude, longitude |
| `relative_humidity_30_0mb` | Relative humidity | percent | init_time, ensemble_member, lead_time, latitude, longitude |
| `relative_humidity_60_30mb` | Relative humidity | percent | init_time, ensemble_member, lead_time, latitude, longitude |
| `relative_humidity_90_60mb` | Relative humidity | percent | init_time, ensemble_member, lead_time, latitude, longitude |
| `relative_humidity_atmosphere` | Relative humidity | percent | init_time, ensemble_member, lead_time, latitude, longitude |
| `relative_humidity_highest_tropospheric_freezing_level` | Relative humidity | percent | init_time, ensemble_member, lead_time, latitude, longitude |
| `sensible_heat_flux_surface` | Sensible heat flux | W m-2 | init_time, ensemble_member, lead_time, latitude, longitude |
| `snow_phase_change_heat_flux_surface` | Snow phase change heat flux | W m-2 | init_time, ensemble_member, lead_time, latitude, longitude |
| `snow_thickness_surface` | Snow depth | m | init_time, ensemble_member, lead_time, latitude, longitude |
| `snow_water_equivalent_surface` | Snow depth water equivalent | m | init_time, ensemble_member, lead_time, latitude, longitude |
| `soil_temperature_0_10cm` | Soil temperature | degree_Celsius | init_time, ensemble_member, lead_time, latitude, longitude |
| `soil_temperature_100_200cm` | Soil temperature | degree_Celsius | init_time, ensemble_member, lead_time, latitude, longitude |
| `soil_temperature_10_40cm` | Soil temperature | degree_Celsius | init_time, ensemble_member, lead_time, latitude, longitude |
| `soil_temperature_40_100cm` | Soil temperature | degree_Celsius | init_time, ensemble_member, lead_time, latitude, longitude |
| `specific_humidity_120_90mb` | Specific humidity | 1 | init_time, ensemble_member, lead_time, latitude, longitude |
| `specific_humidity_150_120mb` | Specific humidity | 1 | init_time, ensemble_member, lead_time, latitude, longitude |
| `specific_humidity_180_150mb` | Specific humidity | 1 | init_time, ensemble_member, lead_time, latitude, longitude |
| `specific_humidity_2m` | Specific humidity | 1 | init_time, ensemble_member, lead_time, latitude, longitude |
| `specific_humidity_30_0mb` | Specific humidity | 1 | init_time, ensemble_member, lead_time, latitude, longitude |
| `specific_humidity_60_30mb` | Specific humidity | 1 | init_time, ensemble_member, lead_time, latitude, longitude |
| `specific_humidity_80m` | Specific humidity | 1 | init_time, ensemble_member, lead_time, latitude, longitude |
| `specific_humidity_90_60mb` | Specific humidity | 1 | init_time, ensemble_member, lead_time, latitude, longitude |
| `storm_relative_helicity_3000_0m` | Storm relative helicity | m2 s-2 | init_time, ensemble_member, lead_time, latitude, longitude |
| `sunshine_duration_surface` | Sunshine Duration | s | init_time, ensemble_member, lead_time, latitude, longitude |
| `surface_lifted_index_surface` | Surface lifted index | K | init_time, ensemble_member, lead_time, latitude, longitude |
| `surface_roughness_surface` | Forecast surface roughness | m | init_time, ensemble_member, lead_time, latitude, longitude |
| `temperature_0p5pvu` | Temperature | degree_Celsius | init_time, ensemble_member, lead_time, latitude, longitude |
| `temperature_0p995_sigma` | Temperature | degree_Celsius | init_time, ensemble_member, lead_time, latitude, longitude |
| `temperature_100m` | Temperature | degree_Celsius | init_time, ensemble_member, lead_time, latitude, longitude |
| `temperature_120_90mb` | Temperature | degree_Celsius | init_time, ensemble_member, lead_time, latitude, longitude |
| `temperature_150_120mb` | Temperature | degree_Celsius | init_time, ensemble_member, lead_time, latitude, longitude |
| `temperature_180_150mb` | Temperature | degree_Celsius | init_time, ensemble_member, lead_time, latitude, longitude |
| `temperature_1p5pvu` | Temperature | degree_Celsius | init_time, ensemble_member, lead_time, latitude, longitude |
| `temperature_1pvu` | Temperature | degree_Celsius | init_time, ensemble_member, lead_time, latitude, longitude |
| `temperature_2m` | 2 metre temperature | degree_Celsius | init_time, ensemble_member, lead_time, latitude, longitude |
| `temperature_2pvu` | Temperature | degree_Celsius | init_time, ensemble_member, lead_time, latitude, longitude |
| `temperature_30_0mb` | Temperature | degree_Celsius | init_time, ensemble_member, lead_time, latitude, longitude |
| `temperature_320k` | Temperature | degree_Celsius | init_time, ensemble_member, lead_time, latitude, longitude |
| `temperature_450k` | Temperature | degree_Celsius | init_time, ensemble_member, lead_time, latitude, longitude |
| `temperature_550k` | Temperature | degree_Celsius | init_time, ensemble_member, lead_time, latitude, longitude |
| `temperature_60_30mb` | Temperature | degree_Celsius | init_time, ensemble_member, lead_time, latitude, longitude |
| `temperature_650k` | Temperature | degree_Celsius | init_time, ensemble_member, lead_time, latitude, longitude |
| `temperature_80m` | 80 metre temperature | degree_Celsius | init_time, ensemble_member, lead_time, latitude, longitude |
| `temperature_90_60mb` | Temperature | degree_Celsius | init_time, ensemble_member, lead_time, latitude, longitude |
| `temperature_max_wind` | Temperature | degree_Celsius | init_time, ensemble_member, lead_time, latitude, longitude |
| `temperature_minus0p5pvu` | Temperature | degree_Celsius | init_time, ensemble_member, lead_time, latitude, longitude |
| `temperature_minus1p5pvu` | Temperature | degree_Celsius | init_time, ensemble_member, lead_time, latitude, longitude |
| `temperature_minus1pvu` | Temperature | degree_Celsius | init_time, ensemble_member, lead_time, latitude, longitude |
| `temperature_minus2pvu` | Temperature | degree_Celsius | init_time, ensemble_member, lead_time, latitude, longitude |
| `temperature_surface` | Skin temperature | degree_Celsius | init_time, ensemble_member, lead_time, latitude, longitude |
| `temperature_tropopause` | Temperature | degree_Celsius | init_time, ensemble_member, lead_time, latitude, longitude |
| `total_cloud_cover_atmosphere` | Total cloud cover | percent | init_time, ensemble_member, lead_time, latitude, longitude |
| `total_ozone_atmosphere` | Total ozone | m | init_time, ensemble_member, lead_time, latitude, longitude |
| `total_precipitation_surface` | Total precipitation | kg m-2 | init_time, ensemble_member, lead_time, latitude, longitude |
| `u_component_storm_motion_6000_0m` | U-component storm motion | m s-1 | init_time, ensemble_member, lead_time, latitude, longitude |
| `upward_long_wave_radiation_flux_surface` | Surface upward long-wave radiation flux | W m-2 | init_time, ensemble_member, lead_time, latitude, longitude |
| `upward_long_wave_radiation_flux_top_of_atmosphere` | Upward long-wave radiation flux | W m-2 | init_time, ensemble_member, lead_time, latitude, longitude |
| `upward_short_wave_radiation_flux_surface` | Surface upward short-wave radiation flux | W m-2 | init_time, ensemble_member, lead_time, latitude, longitude |
| `upward_short_wave_radiation_flux_top_of_atmosphere` | Upward short-wave radiation flux | W m-2 | init_time, ensemble_member, lead_time, latitude, longitude |
| `uv_b_downward_solar_flux_surface` | UV-B downward solar flux | W m-2 | init_time, ensemble_member, lead_time, latitude, longitude |
| `v_component_storm_motion_6000_0m` | V-component storm motion | m s-1 | init_time, ensemble_member, lead_time, latitude, longitude |
| `ventilation_rate_planetary_boundary_layer` | Ventilation Rate | m2 s-1 | init_time, ensemble_member, lead_time, latitude, longitude |
| `vertical_speed_shear_0p5pvu` | Vertical speed shear | s-1 | init_time, ensemble_member, lead_time, latitude, longitude |
| `vertical_speed_shear_1p5pvu` | Vertical speed shear | s-1 | init_time, ensemble_member, lead_time, latitude, longitude |
| `vertical_speed_shear_1pvu` | Vertical speed shear | s-1 | init_time, ensemble_member, lead_time, latitude, longitude |
| `vertical_speed_shear_2pvu` | Vertical speed shear | s-1 | init_time, ensemble_member, lead_time, latitude, longitude |
| `vertical_speed_shear_minus0p5pvu` | Vertical speed shear | s-1 | init_time, ensemble_member, lead_time, latitude, longitude |
| `vertical_speed_shear_minus1p5pvu` | Vertical speed shear | s-1 | init_time, ensemble_member, lead_time, latitude, longitude |
| `vertical_speed_shear_minus1pvu` | Vertical speed shear | s-1 | init_time, ensemble_member, lead_time, latitude, longitude |
| `vertical_speed_shear_minus2pvu` | Vertical speed shear | s-1 | init_time, ensemble_member, lead_time, latitude, longitude |
| `vertical_speed_shear_tropopause` | Vertical speed shear | s-1 | init_time, ensemble_member, lead_time, latitude, longitude |
| `vertical_velocity_0p995_sigma` | Vertical velocity | Pa s-1 | init_time, ensemble_member, lead_time, latitude, longitude |
| `visibility_surface` | Visibility | m | init_time, ensemble_member, lead_time, latitude, longitude |
| `volumetric_soil_moisture_0_10cm` | Volumetric soil moisture | 1 | init_time, ensemble_member, lead_time, latitude, longitude |
| `volumetric_soil_moisture_100_200cm` | Volumetric soil moisture | 1 | init_time, ensemble_member, lead_time, latitude, longitude |
| `volumetric_soil_moisture_10_40cm` | Volumetric soil moisture | 1 | init_time, ensemble_member, lead_time, latitude, longitude |
| `volumetric_soil_moisture_40_100cm` | Volumetric soil moisture | 1 | init_time, ensemble_member, lead_time, latitude, longitude |
| `water_runoff_surface` | Water runoff | kg m-2 | init_time, ensemble_member, lead_time, latitude, longitude |
| `wilting_point_surface` | Wilting point | 1 | init_time, ensemble_member, lead_time, latitude, longitude |
| `wind_gust_surface` | Wind speed (gust) | m s-1 | init_time, ensemble_member, lead_time, latitude, longitude |
| `wind_u_0p5pvu` | U component of wind | m s-1 | init_time, ensemble_member, lead_time, latitude, longitude |
| `wind_u_0p995_sigma` | U component of wind | m s-1 | init_time, ensemble_member, lead_time, latitude, longitude |
| `wind_u_100m` | 100 metre U wind component | m s-1 | init_time, ensemble_member, lead_time, latitude, longitude |
| `wind_u_10m` | 10 metre U wind component | m s-1 | init_time, ensemble_member, lead_time, latitude, longitude |
| `wind_u_120_90mb` | U component of wind | m s-1 | init_time, ensemble_member, lead_time, latitude, longitude |
| `wind_u_150_120mb` | U component of wind | m s-1 | init_time, ensemble_member, lead_time, latitude, longitude |
| `wind_u_180_150mb` | U component of wind | m s-1 | init_time, ensemble_member, lead_time, latitude, longitude |
| `wind_u_1p5pvu` | U component of wind | m s-1 | init_time, ensemble_member, lead_time, latitude, longitude |
| `wind_u_1pvu` | U component of wind | m s-1 | init_time, ensemble_member, lead_time, latitude, longitude |
| `wind_u_2pvu` | U component of wind | m s-1 | init_time, ensemble_member, lead_time, latitude, longitude |
| `wind_u_30_0mb` | U component of wind | m s-1 | init_time, ensemble_member, lead_time, latitude, longitude |
| `wind_u_320k` | U component of wind | m s-1 | init_time, ensemble_member, lead_time, latitude, longitude |
| `wind_u_450k` | U component of wind | m s-1 | init_time, ensemble_member, lead_time, latitude, longitude |
| `wind_u_550k` | U component of wind | m s-1 | init_time, ensemble_member, lead_time, latitude, longitude |
| `wind_u_60_30mb` | U component of wind | m s-1 | init_time, ensemble_member, lead_time, latitude, longitude |
| `wind_u_650k` | U component of wind | m s-1 | init_time, ensemble_member, lead_time, latitude, longitude |
| `wind_u_80m` | 80 metre U wind component | m s-1 | init_time, ensemble_member, lead_time, latitude, longitude |
| `wind_u_90_60mb` | U component of wind | m s-1 | init_time, ensemble_member, lead_time, latitude, longitude |
| `wind_u_max_wind` | U component of wind | m s-1 | init_time, ensemble_member, lead_time, latitude, longitude |
| `wind_u_minus0p5pvu` | U component of wind | m s-1 | init_time, ensemble_member, lead_time, latitude, longitude |
| `wind_u_minus1p5pvu` | U component of wind | m s-1 | init_time, ensemble_member, lead_time, latitude, longitude |
| `wind_u_minus1pvu` | U component of wind | m s-1 | init_time, ensemble_member, lead_time, latitude, longitude |
| `wind_u_minus2pvu` | U component of wind | m s-1 | init_time, ensemble_member, lead_time, latitude, longitude |
| `wind_u_planetary_boundary_layer` | U component of wind | m s-1 | init_time, ensemble_member, lead_time, latitude, longitude |
| `wind_u_tropopause` | U component of wind | m s-1 | init_time, ensemble_member, lead_time, latitude, longitude |
| `wind_v_0p5pvu` | V component of wind | m s-1 | init_time, ensemble_member, lead_time, latitude, longitude |
| `wind_v_0p995_sigma` | V component of wind | m s-1 | init_time, ensemble_member, lead_time, latitude, longitude |
| `wind_v_100m` | 100 metre V wind component | m s-1 | init_time, ensemble_member, lead_time, latitude, longitude |
| `wind_v_10m` | 10 metre V wind component | m s-1 | init_time, ensemble_member, lead_time, latitude, longitude |
| `wind_v_120_90mb` | V component of wind | m s-1 | init_time, ensemble_member, lead_time, latitude, longitude |
| `wind_v_150_120mb` | V component of wind | m s-1 | init_time, ensemble_member, lead_time, latitude, longitude |
| `wind_v_180_150mb` | V component of wind | m s-1 | init_time, ensemble_member, lead_time, latitude, longitude |
| `wind_v_1p5pvu` | V component of wind | m s-1 | init_time, ensemble_member, lead_time, latitude, longitude |
| `wind_v_1pvu` | V component of wind | m s-1 | init_time, ensemble_member, lead_time, latitude, longitude |
| `wind_v_2pvu` | V component of wind | m s-1 | init_time, ensemble_member, lead_time, latitude, longitude |
| `wind_v_30_0mb` | V component of wind | m s-1 | init_time, ensemble_member, lead_time, latitude, longitude |
| `wind_v_320k` | V component of wind | m s-1 | init_time, ensemble_member, lead_time, latitude, longitude |
| `wind_v_450k` | V component of wind | m s-1 | init_time, ensemble_member, lead_time, latitude, longitude |
| `wind_v_550k` | V component of wind | m s-1 | init_time, ensemble_member, lead_time, latitude, longitude |
| `wind_v_60_30mb` | V component of wind | m s-1 | init_time, ensemble_member, lead_time, latitude, longitude |
| `wind_v_650k` | V component of wind | m s-1 | init_time, ensemble_member, lead_time, latitude, longitude |
| `wind_v_80m` | 80 metre V wind component | m s-1 | init_time, ensemble_member, lead_time, latitude, longitude |
| `wind_v_90_60mb` | V component of wind | m s-1 | init_time, ensemble_member, lead_time, latitude, longitude |
| `wind_v_max_wind` | V component of wind | m s-1 | init_time, ensemble_member, lead_time, latitude, longitude |
| `wind_v_minus0p5pvu` | V component of wind | m s-1 | init_time, ensemble_member, lead_time, latitude, longitude |
| `wind_v_minus1p5pvu` | V component of wind | m s-1 | init_time, ensemble_member, lead_time, latitude, longitude |
| `wind_v_minus1pvu` | V component of wind | m s-1 | init_time, ensemble_member, lead_time, latitude, longitude |
| `wind_v_minus2pvu` | V component of wind | m s-1 | init_time, ensemble_member, lead_time, latitude, longitude |
| `wind_v_planetary_boundary_layer` | V component of wind | m s-1 | init_time, ensemble_member, lead_time, latitude, longitude |
| `wind_v_tropopause` | V component of wind | m s-1 | init_time, ensemble_member, lead_time, latitude, longitude |
| `height_above_mean_sea_level/temperature` | Temperature | degree_Celsius | init_time, ensemble_member, lead_time, latitude, longitude, height_above_mean_sea_level |
| `height_above_mean_sea_level/wind_u` | U component of wind | m s-1 | init_time, ensemble_member, lead_time, latitude, longitude, height_above_mean_sea_level |
| `height_above_mean_sea_level/wind_v` | V component of wind | m s-1 | init_time, ensemble_member, lead_time, latitude, longitude, height_above_mean_sea_level |
| `model_level/geopotential_height` | Geopotential height | m | init_time, ensemble_member, lead_time, latitude, longitude, model_level |
| `model_level/pressure` | Pressure | Pa | init_time, ensemble_member, lead_time, latitude, longitude, model_level |
| `model_level/relative_humidity` | Relative humidity | percent | init_time, ensemble_member, lead_time, latitude, longitude, model_level |
| `model_level/temperature` | Temperature | degree_Celsius | init_time, ensemble_member, lead_time, latitude, longitude, model_level |
| `model_level/wind_u` | U component of wind | m s-1 | init_time, ensemble_member, lead_time, latitude, longitude, model_level |
| `model_level/wind_v` | V component of wind | m s-1 | init_time, ensemble_member, lead_time, latitude, longitude, model_level |
| `pressure_level/absolute_vorticity` | Absolute vorticity | s-1 | init_time, ensemble_member, lead_time, latitude, longitude, pressure_level |
| `pressure_level/cloud_mixing_ratio` | Cloud mixing ratio | kg kg-1 | init_time, ensemble_member, lead_time, latitude, longitude, pressure_level |
| `pressure_level/geopotential_height` | Geopotential height | m | init_time, ensemble_member, lead_time, latitude, longitude, pressure_level |
| `pressure_level/icing_probability` | Icing probability | 1 | init_time, ensemble_member, lead_time, latitude, longitude, pressure_level |
| `pressure_level/icing_severity` | Icing severity | 1 | init_time, ensemble_member, lead_time, latitude, longitude, pressure_level |
| `pressure_level/ozone_mixing_ratio` | Ozone mixing ratio | kg kg-1 | init_time, ensemble_member, lead_time, latitude, longitude, pressure_level |
| `pressure_level/relative_humidity` | Relative humidity | percent | init_time, ensemble_member, lead_time, latitude, longitude, pressure_level |
| `pressure_level/specific_humidity` | Specific humidity | 1 | init_time, ensemble_member, lead_time, latitude, longitude, pressure_level |
| `pressure_level/temperature` | Temperature | degree_Celsius | init_time, ensemble_member, lead_time, latitude, longitude, pressure_level |
| `pressure_level/vertical_velocity` | Vertical velocity | Pa s-1 | init_time, ensemble_member, lead_time, latitude, longitude, pressure_level |
| `pressure_level/wind_u` | U component of wind | m s-1 | init_time, ensemble_member, lead_time, latitude, longitude, pressure_level |
| `pressure_level/wind_v` | V component of wind | m s-1 | init_time, ensemble_member, lead_time, latitude, longitude, pressure_level |
