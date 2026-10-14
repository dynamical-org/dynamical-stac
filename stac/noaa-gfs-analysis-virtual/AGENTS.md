# NOAA GFS analysis, virtual: notes for agents

Read https://dynamical.org/prompt.md for context about working with dynamical.org data.

- Collection id: `noaa-gfs-analysis-virtual`
- STAC collection: https://stac.dynamical.org/noaa-gfs-analysis-virtual/collection.json
- Dataset version: 0.1.0

## Access

All data is public. No credentials are needed.

| asset | href |
|---|---|
| `icechunk` | `s3://dynamical-noaa-gfs/noaa-gfs-analysis-virtual/v0.1.0.icechunk/` |
| `icechunk-https` | `https://dynamical-noaa-gfs.s3.us-west-2.amazonaws.com/noaa-gfs-analysis-virtual/v0.1.0.icechunk` |

The `icechunk` asset's `xarray:storage_options` are `{"anon": true, "client_kwargs": {"region_name": "us-west-2"}}`.

The repository references chunks in these upstream locations, which are read anonymously:

- `s3://noaa-gfs-bdp-pds/`

## Examples

### Temperature map

dynamical-catalog:

```python
import dynamical_catalog  # dynamical-catalog>=0.8.0

ds = dynamical_catalog.open("noaa-gfs-analysis-virtual", chunks=None)
ds["temperature_2m"].sel(time="2025-01-01T00")

# Variables with a vertical dimension live in the pressure_level
# and height_above_mean_sea_level groups
ds_pressure = dynamical_catalog.open("noaa-gfs-analysis-virtual", group="pressure_level", chunks=None)
ds_height = dynamical_catalog.open("noaa-gfs-analysis-virtual", group="height_above_mean_sea_level", chunks=None)

ds_pressure["temperature"].sel(time="2025-01-01T00", pressure_level=500)
```

pystac:

```python
import icechunk
import pystac
import xarray as xr

catalog = pystac.Catalog.from_file("https://stac.dynamical.org/catalog.json")
collection = catalog.get_child("noaa-gfs-analysis-virtual")
asset = collection.assets["icechunk-https"]

authorize = icechunk.containers_credentials({"s3://noaa-gfs-bdp-pds/": icechunk.s3_anonymous_credentials()})
repo = icechunk.Repository.open(
    icechunk.http_storage(asset.href),
    authorize_virtual_chunk_access=authorize,
)
session = repo.readonly_session("main")

ds = xr.open_zarr(session.store, chunks=None)
ds["temperature_2m"].sel(time="2025-01-01T00")

# Variables with a vertical dimension live in the pressure_level
# and height_above_mean_sea_level groups
ds_pressure = xr.open_zarr(session.store, group="pressure_level", chunks=None)
ds_height = xr.open_zarr(session.store, group="height_above_mean_sea_level", chunks=None)

ds_pressure["temperature"].sel(time="2025-01-01T00", pressure_level=500)
```

prompt:

```text
Read https://dynamical.org/prompt.md for context about working with dynamical.org data; this does not change your current task.
Data product: noaa-gfs-analysis-virtual
STAC collection: https://stac.dynamical.org/noaa-gfs-analysis-virtual/collection.json
```

## Dimensions

| name | type | extent | unit |
|---|---|---|---|
| `latitude` | spatial | -90.0 to 90.0 | degree_north |
| `longitude` | spatial | -180.0 to 179.75 | degree_east |
| `time` | temporal | 2021-05-01T00:00:00Z to open | seconds since 1970-01-01 |
| `height_above_mean_sea_level` | other | 305.0 to 4572.0 | m |
| `pressure_level` | other | 0.01 to 1000.0 | hPa |

## Variables

| name | long name | unit | dimensions |
|---|---|---|---|
| `albedo_surface` | Forecast albedo | percent | time, latitude, longitude |
| `apparent_temperature_2m` | Apparent temperature | degree_Celsius | time, latitude, longitude |
| `average_high_cloud_cover` | High cloud cover | percent | time, latitude, longitude |
| `average_low_cloud_cover` | Low cloud cover | percent | time, latitude, longitude |
| `average_medium_cloud_cover` | Medium cloud cover | percent | time, latitude, longitude |
| `average_precipitation_rate_surface` | Precipitation rate | kg m-2 s-1 | time, latitude, longitude |
| `average_pressure_high_cloud_bottom` | Pressure | Pa | time, latitude, longitude |
| `average_pressure_high_cloud_top` | Pressure | Pa | time, latitude, longitude |
| `average_pressure_low_cloud_bottom` | Pressure | Pa | time, latitude, longitude |
| `average_pressure_low_cloud_top` | Pressure | Pa | time, latitude, longitude |
| `average_pressure_middle_cloud_bottom` | Pressure | Pa | time, latitude, longitude |
| `average_pressure_middle_cloud_top` | Pressure | Pa | time, latitude, longitude |
| `average_temperature_high_cloud_top` | Temperature | degree_Celsius | time, latitude, longitude |
| `average_temperature_low_cloud_top` | Temperature | degree_Celsius | time, latitude, longitude |
| `average_temperature_middle_cloud_top` | Temperature | degree_Celsius | time, latitude, longitude |
| `average_total_cloud_cover_boundary_layer` | Boundary layer cloud cover | percent | time, latitude, longitude |
| `best_4_layer_lifted_index_surface` | Best (4-layer) lifted index | K | time, latitude, longitude |
| `categorical_freezing_rain_surface` | Categorical freezing rain | 1 | time, latitude, longitude |
| `categorical_ice_pellets_surface` | Categorical ice pellets | 1 | time, latitude, longitude |
| `categorical_rain_surface` | Categorical rain | 1 | time, latitude, longitude |
| `categorical_snow_surface` | Categorical snow | 1 | time, latitude, longitude |
| `clear_sky_uv_b_downward_solar_flux_surface` | Clear sky UV-B downward solar flux | W m-2 | time, latitude, longitude |
| `cloud_mixing_ratio_model_level_1` | Cloud mixing ratio | kg kg-1 | time, latitude, longitude |
| `cloud_water_atmosphere` | Cloud water | kg m-2 | time, latitude, longitude |
| `cloud_work_function_atmosphere` | Cloud work function | J kg-1 | time, latitude, longitude |
| `composite_reflectivity` | Maximum/Composite radar reflectivity | dBZ | time, latitude, longitude |
| `convective_available_potential_energy_180_0mb` | Convective available potential energy | J kg-1 | time, latitude, longitude |
| `convective_available_potential_energy_255_0mb` | Convective available potential energy | J kg-1 | time, latitude, longitude |
| `convective_available_potential_energy_90_0mb` | Convective available potential energy | J kg-1 | time, latitude, longitude |
| `convective_available_potential_energy_surface` | Convective available potential energy | J kg-1 | time, latitude, longitude |
| `convective_cloud_cover` | Convective cloud cover | percent | time, latitude, longitude |
| `convective_inhibition_180_0mb` | Convective inhibition | J kg-1 | time, latitude, longitude |
| `convective_inhibition_255_0mb` | Convective inhibition | J kg-1 | time, latitude, longitude |
| `convective_inhibition_90_0mb` | Convective inhibition | J kg-1 | time, latitude, longitude |
| `convective_inhibition_surface` | Convective inhibition | J kg-1 | time, latitude, longitude |
| `convective_precipitation_surface` | Convective precipitation | kg m-2 | time, latitude, longitude |
| `derived_radar_reflectivity_1000m` | Derived radar reflectivity | dBZ | time, latitude, longitude |
| `derived_radar_reflectivity_4000m` | Derived radar reflectivity | dBZ | time, latitude, longitude |
| `derived_radar_reflectivity_model_level_1` | Derived radar reflectivity | dBZ | time, latitude, longitude |
| `derived_radar_reflectivity_model_level_2` | Derived radar reflectivity | dBZ | time, latitude, longitude |
| `dew_point_temperature_2m` | 2 metre dewpoint temperature | degree_Celsius | time, latitude, longitude |
| `downward_long_wave_radiation_flux_surface` | Surface downward long-wave radiation flux | W m-2 | time, latitude, longitude |
| `downward_short_wave_radiation_flux_surface` | Surface downward short-wave radiation flux | W m-2 | time, latitude, longitude |
| `eastward_gravity_wave_surface_stress` | Eastward gravity wave surface stress | Pa | time, latitude, longitude |
| `field_capacity_surface` | Field Capacity | 1 | time, latitude, longitude |
| `friction_velocity_surface` | Friction velocity | m s-1 | time, latitude, longitude |
| `geopotential_height_0c_isotherm` | Geopotential height | m | time, latitude, longitude |
| `geopotential_height_0p5pvu` | Geopotential height | m | time, latitude, longitude |
| `geopotential_height_1p5pvu` | Geopotential height | m | time, latitude, longitude |
| `geopotential_height_1pvu` | Geopotential height | m | time, latitude, longitude |
| `geopotential_height_2pvu` | Geopotential height | m | time, latitude, longitude |
| `geopotential_height_cloud_ceiling` | Geopotential height | m | time, latitude, longitude |
| `geopotential_height_highest_tropospheric_freezing_level` | Geopotential height | m | time, latitude, longitude |
| `geopotential_height_max_wind` | Geopotential height | m | time, latitude, longitude |
| `geopotential_height_minus0p5pvu` | Geopotential height | m | time, latitude, longitude |
| `geopotential_height_minus1p5pvu` | Geopotential height | m | time, latitude, longitude |
| `geopotential_height_minus1pvu` | Geopotential height | m | time, latitude, longitude |
| `geopotential_height_minus2pvu` | Geopotential height | m | time, latitude, longitude |
| `geopotential_height_surface` | Geopotential height | m | time, latitude, longitude |
| `geopotential_height_tropopause` | Geopotential height | m | time, latitude, longitude |
| `graupel_model_level_1` | Graupel (snow pellets) | kg kg-1 | time, latitude, longitude |
| `ground_heat_flux_surface` | Ground heat flux | W m-2 | time, latitude, longitude |
| `haines_index_surface` | Haines Index | 1 | time, latitude, longitude |
| `high_cloud_cover` | High cloud cover | percent | time, latitude, longitude |
| `icao_standard_atmosphere_reference_height_max_wind` | ICAO Standard Atmosphere reference height | m | time, latitude, longitude |
| `icao_standard_atmosphere_reference_height_tropopause` | ICAO Standard Atmosphere reference height | m | time, latitude, longitude |
| `ice_cover_surface` | Ice cover (1=ice, 0=no ice) | 1 | time, latitude, longitude |
| `ice_growth_rate_10m_amsl` | Ice growth rate | m s-1 | time, latitude, longitude |
| `ice_temperature_surface` | Sea ice surface temperature | degree_Celsius | time, latitude, longitude |
| `ice_thickness_surface` | Ice thickness | m | time, latitude, longitude |
| `ice_water_mixing_ratio_model_level_1` | Ice water mixing ratio | kg kg-1 | time, latitude, longitude |
| `instantaneous_categorical_freezing_rain_surface` | Categorical freezing rain | 1 | time, latitude, longitude |
| `instantaneous_categorical_ice_pellets_surface` | Categorical ice pellets | 1 | time, latitude, longitude |
| `instantaneous_categorical_rain_surface` | Categorical rain | 1 | time, latitude, longitude |
| `instantaneous_categorical_snow_surface` | Categorical snow | 1 | time, latitude, longitude |
| `instantaneous_precipitation_convective_surface` | Convective precipitation rate | kg m-2 s-1 | time, latitude, longitude |
| `instantaneous_total_cloud_cover_atmosphere` | Total cloud cover | percent | time, latitude, longitude |
| `land_sea_mask_surface` | Land-sea mask | 1 | time, latitude, longitude |
| `latent_heat_flux_surface` | Latent heat flux | W m-2 | time, latitude, longitude |
| `liquid_volumetric_soil_moisture_0_10cm` | Liquid volumetric soil moisture (non-frozen) | 1 | time, latitude, longitude |
| `liquid_volumetric_soil_moisture_100_200cm` | Liquid volumetric soil moisture (non-frozen) | 1 | time, latitude, longitude |
| `liquid_volumetric_soil_moisture_10_40cm` | Liquid volumetric soil moisture (non-frozen) | 1 | time, latitude, longitude |
| `liquid_volumetric_soil_moisture_40_100cm` | Liquid volumetric soil moisture (non-frozen) | 1 | time, latitude, longitude |
| `low_cloud_cover` | Low cloud cover | percent | time, latitude, longitude |
| `maximum_temperature_2m` | Maximum temperature | degree_Celsius | time, latitude, longitude |
| `medium_cloud_cover` | Medium cloud cover | percent | time, latitude, longitude |
| `minimum_temperature_2m` | Minimum temperature | degree_Celsius | time, latitude, longitude |
| `momentum_flux_u_component_surface` | Momentum flux, u-component | Pa | time, latitude, longitude |
| `momentum_flux_v_component_surface` | Momentum flux, v-component | Pa | time, latitude, longitude |
| `northward_gravity_wave_surface_stress` | Northward gravity wave surface stress | Pa | time, latitude, longitude |
| `percent_frozen_precipitation_surface` | Percent frozen precipitation | percent | time, latitude, longitude |
| `planetary_boundary_layer_height_surface` | Boundary layer height | m | time, latitude, longitude |
| `plant_canopy_surface_water_surface` | Plant canopy surface water | kg m-2 | time, latitude, longitude |
| `potential_evaporation_rate_surface` | Potential evaporation rate | W m-2 | time, latitude, longitude |
| `potential_temperature_0p995_sigma` | Potential temperature | K | time, latitude, longitude |
| `precipitable_water_atmosphere` | Precipitable water | kg m-2 | time, latitude, longitude |
| `precipitation_convective_surface` | Convective precipitation rate | kg m-2 s-1 | time, latitude, longitude |
| `precipitation_rate_surface` | Precipitation rate | kg m-2 s-1 | time, latitude, longitude |
| `pressure_0p5pvu` | Pressure | Pa | time, latitude, longitude |
| `pressure_1p5pvu` | Pressure | Pa | time, latitude, longitude |
| `pressure_1pvu` | Pressure | Pa | time, latitude, longitude |
| `pressure_2pvu` | Pressure | Pa | time, latitude, longitude |
| `pressure_80m` | 80 metre pressure | Pa | time, latitude, longitude |
| `pressure_convective_cloud_bottom` | Pressure | Pa | time, latitude, longitude |
| `pressure_convective_cloud_top` | Pressure | Pa | time, latitude, longitude |
| `pressure_max_wind` | Pressure | Pa | time, latitude, longitude |
| `pressure_minus0p5pvu` | Pressure | Pa | time, latitude, longitude |
| `pressure_minus1p5pvu` | Pressure | Pa | time, latitude, longitude |
| `pressure_minus1pvu` | Pressure | Pa | time, latitude, longitude |
| `pressure_minus2pvu` | Pressure | Pa | time, latitude, longitude |
| `pressure_of_lifted_parcel_level_255_0mb` | Pressure of level from which parcel was lifted | Pa | time, latitude, longitude |
| `pressure_reduced_to_mean_sea_level` | Pressure reduced to MSL | Pa | time, latitude, longitude |
| `pressure_reduced_to_mean_sea_level_eta_model` | MSLP (Eta model reduction) | Pa | time, latitude, longitude |
| `pressure_surface` | Surface pressure | Pa | time, latitude, longitude |
| `pressure_tropopause` | Pressure | Pa | time, latitude, longitude |
| `rain_mixing_ratio_model_level_1` | Rain mixing ratio | kg kg-1 | time, latitude, longitude |
| `relative_humidity_0c_isotherm` | Relative humidity | percent | time, latitude, longitude |
| `relative_humidity_0p33_1_sigma` | Relative humidity | percent | time, latitude, longitude |
| `relative_humidity_0p44_0p72_sigma` | Relative humidity | percent | time, latitude, longitude |
| `relative_humidity_0p44_1_sigma` | Relative humidity | percent | time, latitude, longitude |
| `relative_humidity_0p72_0p94_sigma` | Relative humidity | percent | time, latitude, longitude |
| `relative_humidity_0p995_sigma` | Relative humidity | percent | time, latitude, longitude |
| `relative_humidity_120_90mb` | Relative humidity | percent | time, latitude, longitude |
| `relative_humidity_150_120mb` | Relative humidity | percent | time, latitude, longitude |
| `relative_humidity_180_150mb` | Relative humidity | percent | time, latitude, longitude |
| `relative_humidity_2m` | 2 metre relative humidity | percent | time, latitude, longitude |
| `relative_humidity_30_0mb` | Relative humidity | percent | time, latitude, longitude |
| `relative_humidity_60_30mb` | Relative humidity | percent | time, latitude, longitude |
| `relative_humidity_90_60mb` | Relative humidity | percent | time, latitude, longitude |
| `relative_humidity_atmosphere` | Relative humidity | percent | time, latitude, longitude |
| `relative_humidity_highest_tropospheric_freezing_level` | Relative humidity | percent | time, latitude, longitude |
| `sensible_heat_flux_surface` | Sensible heat flux | W m-2 | time, latitude, longitude |
| `snow_mixing_ratio_model_level_1` | Snow mixing ratio | kg kg-1 | time, latitude, longitude |
| `snow_thickness_surface` | Snow depth | m | time, latitude, longitude |
| `snow_water_equivalent_surface` | Snow depth water equivalent | m | time, latitude, longitude |
| `soil_temperature_0_10cm` | Soil temperature | degree_Celsius | time, latitude, longitude |
| `soil_temperature_100_200cm` | Soil temperature | degree_Celsius | time, latitude, longitude |
| `soil_temperature_10_40cm` | Soil temperature | degree_Celsius | time, latitude, longitude |
| `soil_temperature_40_100cm` | Soil temperature | degree_Celsius | time, latitude, longitude |
| `soil_type_surface` | Soil type | 1 | time, latitude, longitude |
| `specific_humidity_120_90mb` | Specific humidity | 1 | time, latitude, longitude |
| `specific_humidity_150_120mb` | Specific humidity | 1 | time, latitude, longitude |
| `specific_humidity_180_150mb` | Specific humidity | 1 | time, latitude, longitude |
| `specific_humidity_2m` | Specific humidity | 1 | time, latitude, longitude |
| `specific_humidity_30_0mb` | Specific humidity | 1 | time, latitude, longitude |
| `specific_humidity_60_30mb` | Specific humidity | 1 | time, latitude, longitude |
| `specific_humidity_80m` | Specific humidity | 1 | time, latitude, longitude |
| `specific_humidity_90_60mb` | Specific humidity | 1 | time, latitude, longitude |
| `storm_relative_helicity_3000_0m` | Storm relative helicity | m2 s-2 | time, latitude, longitude |
| `sunshine_duration_surface` | Sunshine Duration | s | time, latitude, longitude |
| `surface_lifted_index_surface` | Surface lifted index | K | time, latitude, longitude |
| `surface_roughness_surface` | Forecast surface roughness | m | time, latitude, longitude |
| `temperature_0p5pvu` | Temperature | degree_Celsius | time, latitude, longitude |
| `temperature_0p995_sigma` | Temperature | degree_Celsius | time, latitude, longitude |
| `temperature_100m` | Temperature | degree_Celsius | time, latitude, longitude |
| `temperature_120_90mb` | Temperature | degree_Celsius | time, latitude, longitude |
| `temperature_150_120mb` | Temperature | degree_Celsius | time, latitude, longitude |
| `temperature_180_150mb` | Temperature | degree_Celsius | time, latitude, longitude |
| `temperature_1p5pvu` | Temperature | degree_Celsius | time, latitude, longitude |
| `temperature_1pvu` | Temperature | degree_Celsius | time, latitude, longitude |
| `temperature_2m` | 2 metre temperature | degree_Celsius | time, latitude, longitude |
| `temperature_2pvu` | Temperature | degree_Celsius | time, latitude, longitude |
| `temperature_30_0mb` | Temperature | degree_Celsius | time, latitude, longitude |
| `temperature_60_30mb` | Temperature | degree_Celsius | time, latitude, longitude |
| `temperature_80m` | 80 metre temperature | degree_Celsius | time, latitude, longitude |
| `temperature_90_60mb` | Temperature | degree_Celsius | time, latitude, longitude |
| `temperature_max_wind` | Temperature | degree_Celsius | time, latitude, longitude |
| `temperature_minus0p5pvu` | Temperature | degree_Celsius | time, latitude, longitude |
| `temperature_minus1p5pvu` | Temperature | degree_Celsius | time, latitude, longitude |
| `temperature_minus1pvu` | Temperature | degree_Celsius | time, latitude, longitude |
| `temperature_minus2pvu` | Temperature | degree_Celsius | time, latitude, longitude |
| `temperature_surface` | Skin temperature | degree_Celsius | time, latitude, longitude |
| `temperature_tropopause` | Temperature | degree_Celsius | time, latitude, longitude |
| `total_cloud_cover_atmosphere` | Total cloud cover | percent | time, latitude, longitude |
| `total_ozone_atmosphere` | Total ozone | m | time, latitude, longitude |
| `total_precipitation_surface` | Total precipitation | kg m-2 | time, latitude, longitude |
| `u_component_storm_motion_6000_0m` | U-component storm motion | m s-1 | time, latitude, longitude |
| `upward_long_wave_radiation_flux_surface` | Surface upward long-wave radiation flux | W m-2 | time, latitude, longitude |
| `upward_long_wave_radiation_flux_top_of_atmosphere` | Upward long-wave radiation flux | W m-2 | time, latitude, longitude |
| `upward_short_wave_radiation_flux_surface` | Surface upward short-wave radiation flux | W m-2 | time, latitude, longitude |
| `upward_short_wave_radiation_flux_top_of_atmosphere` | Upward short-wave radiation flux | W m-2 | time, latitude, longitude |
| `uv_b_downward_solar_flux_surface` | UV-B downward solar flux | W m-2 | time, latitude, longitude |
| `v_component_storm_motion_6000_0m` | V-component storm motion | m s-1 | time, latitude, longitude |
| `vegetation_surface` | Vegetation fraction | percent | time, latitude, longitude |
| `ventilation_rate_planetary_boundary_layer` | Ventilation Rate | m2 s-1 | time, latitude, longitude |
| `vertical_speed_shear_0p5pvu` | Vertical speed shear | s-1 | time, latitude, longitude |
| `vertical_speed_shear_1p5pvu` | Vertical speed shear | s-1 | time, latitude, longitude |
| `vertical_speed_shear_1pvu` | Vertical speed shear | s-1 | time, latitude, longitude |
| `vertical_speed_shear_2pvu` | Vertical speed shear | s-1 | time, latitude, longitude |
| `vertical_speed_shear_minus0p5pvu` | Vertical speed shear | s-1 | time, latitude, longitude |
| `vertical_speed_shear_minus1p5pvu` | Vertical speed shear | s-1 | time, latitude, longitude |
| `vertical_speed_shear_minus1pvu` | Vertical speed shear | s-1 | time, latitude, longitude |
| `vertical_speed_shear_minus2pvu` | Vertical speed shear | s-1 | time, latitude, longitude |
| `vertical_speed_shear_tropopause` | Vertical speed shear | s-1 | time, latitude, longitude |
| `vertical_velocity_0p995_sigma` | Vertical velocity | Pa s-1 | time, latitude, longitude |
| `visibility_surface` | Visibility | m | time, latitude, longitude |
| `volumetric_soil_moisture_0_10cm` | Volumetric soil moisture | 1 | time, latitude, longitude |
| `volumetric_soil_moisture_100_200cm` | Volumetric soil moisture | 1 | time, latitude, longitude |
| `volumetric_soil_moisture_10_40cm` | Volumetric soil moisture | 1 | time, latitude, longitude |
| `volumetric_soil_moisture_40_100cm` | Volumetric soil moisture | 1 | time, latitude, longitude |
| `water_runoff_surface` | Water runoff | kg m-2 | time, latitude, longitude |
| `wilting_point_surface` | Wilting point | 1 | time, latitude, longitude |
| `wind_gust_surface` | Wind speed (gust) | m s-1 | time, latitude, longitude |
| `wind_u_0p5pvu` | U component of wind | m s-1 | time, latitude, longitude |
| `wind_u_0p995_sigma` | U component of wind | m s-1 | time, latitude, longitude |
| `wind_u_100m` | 100 metre U wind component | m s-1 | time, latitude, longitude |
| `wind_u_10m` | 10 metre U wind component | m s-1 | time, latitude, longitude |
| `wind_u_120_90mb` | U component of wind | m s-1 | time, latitude, longitude |
| `wind_u_150_120mb` | U component of wind | m s-1 | time, latitude, longitude |
| `wind_u_180_150mb` | U component of wind | m s-1 | time, latitude, longitude |
| `wind_u_1p5pvu` | U component of wind | m s-1 | time, latitude, longitude |
| `wind_u_1pvu` | U component of wind | m s-1 | time, latitude, longitude |
| `wind_u_20m` | U component of wind | m s-1 | time, latitude, longitude |
| `wind_u_2pvu` | U component of wind | m s-1 | time, latitude, longitude |
| `wind_u_30_0mb` | U component of wind | m s-1 | time, latitude, longitude |
| `wind_u_30m` | U component of wind | m s-1 | time, latitude, longitude |
| `wind_u_40m` | U component of wind | m s-1 | time, latitude, longitude |
| `wind_u_50m` | U component of wind | m s-1 | time, latitude, longitude |
| `wind_u_60_30mb` | U component of wind | m s-1 | time, latitude, longitude |
| `wind_u_80m` | 80 metre U wind component | m s-1 | time, latitude, longitude |
| `wind_u_90_60mb` | U component of wind | m s-1 | time, latitude, longitude |
| `wind_u_max_wind` | U component of wind | m s-1 | time, latitude, longitude |
| `wind_u_minus0p5pvu` | U component of wind | m s-1 | time, latitude, longitude |
| `wind_u_minus1p5pvu` | U component of wind | m s-1 | time, latitude, longitude |
| `wind_u_minus1pvu` | U component of wind | m s-1 | time, latitude, longitude |
| `wind_u_minus2pvu` | U component of wind | m s-1 | time, latitude, longitude |
| `wind_u_planetary_boundary_layer` | U component of wind | m s-1 | time, latitude, longitude |
| `wind_u_tropopause` | U component of wind | m s-1 | time, latitude, longitude |
| `wind_v_0p5pvu` | V component of wind | m s-1 | time, latitude, longitude |
| `wind_v_0p995_sigma` | V component of wind | m s-1 | time, latitude, longitude |
| `wind_v_100m` | 100 metre V wind component | m s-1 | time, latitude, longitude |
| `wind_v_10m` | 10 metre V wind component | m s-1 | time, latitude, longitude |
| `wind_v_120_90mb` | V component of wind | m s-1 | time, latitude, longitude |
| `wind_v_150_120mb` | V component of wind | m s-1 | time, latitude, longitude |
| `wind_v_180_150mb` | V component of wind | m s-1 | time, latitude, longitude |
| `wind_v_1p5pvu` | V component of wind | m s-1 | time, latitude, longitude |
| `wind_v_1pvu` | V component of wind | m s-1 | time, latitude, longitude |
| `wind_v_20m` | V component of wind | m s-1 | time, latitude, longitude |
| `wind_v_2pvu` | V component of wind | m s-1 | time, latitude, longitude |
| `wind_v_30_0mb` | V component of wind | m s-1 | time, latitude, longitude |
| `wind_v_30m` | V component of wind | m s-1 | time, latitude, longitude |
| `wind_v_40m` | V component of wind | m s-1 | time, latitude, longitude |
| `wind_v_50m` | V component of wind | m s-1 | time, latitude, longitude |
| `wind_v_60_30mb` | V component of wind | m s-1 | time, latitude, longitude |
| `wind_v_80m` | 80 metre V wind component | m s-1 | time, latitude, longitude |
| `wind_v_90_60mb` | V component of wind | m s-1 | time, latitude, longitude |
| `wind_v_max_wind` | V component of wind | m s-1 | time, latitude, longitude |
| `wind_v_minus0p5pvu` | V component of wind | m s-1 | time, latitude, longitude |
| `wind_v_minus1p5pvu` | V component of wind | m s-1 | time, latitude, longitude |
| `wind_v_minus1pvu` | V component of wind | m s-1 | time, latitude, longitude |
| `wind_v_minus2pvu` | V component of wind | m s-1 | time, latitude, longitude |
| `wind_v_planetary_boundary_layer` | V component of wind | m s-1 | time, latitude, longitude |
| `wind_v_tropopause` | V component of wind | m s-1 | time, latitude, longitude |
| `height_above_mean_sea_level/temperature` | Temperature | degree_Celsius | time, latitude, longitude, height_above_mean_sea_level |
| `height_above_mean_sea_level/wind_u` | U component of wind | m s-1 | time, latitude, longitude, height_above_mean_sea_level |
| `height_above_mean_sea_level/wind_v` | V component of wind | m s-1 | time, latitude, longitude, height_above_mean_sea_level |
| `pressure_level/absolute_vorticity` | Absolute vorticity | s-1 | time, latitude, longitude, pressure_level |
| `pressure_level/cloud_cover` | Fraction of cloud cover | percent | time, latitude, longitude, pressure_level |
| `pressure_level/cloud_mixing_ratio` | Cloud mixing ratio | kg kg-1 | time, latitude, longitude, pressure_level |
| `pressure_level/geopotential_height` | Geopotential height | m | time, latitude, longitude, pressure_level |
| `pressure_level/graupel` | Graupel (snow pellets) | kg kg-1 | time, latitude, longitude, pressure_level |
| `pressure_level/ice_water_mixing_ratio` | Ice water mixing ratio | kg kg-1 | time, latitude, longitude, pressure_level |
| `pressure_level/ozone_mixing_ratio` | Ozone mixing ratio | kg kg-1 | time, latitude, longitude, pressure_level |
| `pressure_level/rain_mixing_ratio` | Rain mixing ratio | kg kg-1 | time, latitude, longitude, pressure_level |
| `pressure_level/relative_humidity` | Relative humidity | percent | time, latitude, longitude, pressure_level |
| `pressure_level/snow_mixing_ratio` | Snow mixing ratio | kg kg-1 | time, latitude, longitude, pressure_level |
| `pressure_level/specific_humidity` | Specific humidity | 1 | time, latitude, longitude, pressure_level |
| `pressure_level/temperature` | Temperature | degree_Celsius | time, latitude, longitude, pressure_level |
| `pressure_level/vertical_velocity` | Vertical velocity | Pa s-1 | time, latitude, longitude, pressure_level |
| `pressure_level/vertical_velocity_geometric` | Vertical velocity (geometric) | m s-1 | time, latitude, longitude, pressure_level |
| `pressure_level/wind_u` | U component of wind | m s-1 | time, latitude, longitude, pressure_level |
| `pressure_level/wind_v` | V component of wind | m s-1 | time, latitude, longitude, pressure_level |
