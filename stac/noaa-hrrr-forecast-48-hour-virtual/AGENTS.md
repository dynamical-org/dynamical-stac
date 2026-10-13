# NOAA HRRR forecast, 48 hour, virtual: notes for agents

Read https://dynamical.org/prompt.md for context about working with dynamical.org data.

- Collection id: `noaa-hrrr-forecast-48-hour-virtual`
- STAC collection: https://stac.dynamical.org/noaa-hrrr-forecast-48-hour-virtual/collection.json
- Dataset version: 0.5.0

## Access

All data is public. No credentials are needed.

| asset | href |
|---|---|
| `icechunk` | `s3://dynamical-noaa-hrrr/noaa-hrrr-forecast-48-hour-virtual/v0.5.0.icechunk/` |
| `icechunk-https` | `https://dynamical-noaa-hrrr.s3.us-west-2.amazonaws.com/noaa-hrrr-forecast-48-hour-virtual/v0.5.0.icechunk` |

The `icechunk` asset's `xarray:storage_options` are `{"anon": true, "client_kwargs": {"region_name": "us-west-2"}}`.

The repository references chunks in these upstream locations, which are read anonymously:

- `s3://noaa-hrrr-bdp-pds/`

## Examples

### Temperature map

dynamical-catalog:

```python
import dynamical_catalog  # dynamical-catalog>=0.8.0

ds = dynamical_catalog.open("noaa-hrrr-forecast-48-hour-virtual", chunks=None)
ds["temperature_2m"].sel(init_time="2025-01-01T00", lead_time="24h")

# Variables with a vertical dimension live in the pressure_level and model_level groups
ds_pressure = dynamical_catalog.open("noaa-hrrr-forecast-48-hour-virtual", group="pressure_level", chunks=None)
ds_model = dynamical_catalog.open("noaa-hrrr-forecast-48-hour-virtual", group="model_level", chunks=None)

ds_pressure["temperature"].sel(pressure_level=500)
```

pystac:

```python
import icechunk
import pystac
import xarray as xr

catalog = pystac.Catalog.from_file("https://stac.dynamical.org/catalog.json")
collection = catalog.get_child("noaa-hrrr-forecast-48-hour-virtual")
asset = collection.assets["icechunk-https"]

authorize = icechunk.containers_credentials({"s3://noaa-hrrr-bdp-pds/": icechunk.s3_anonymous_credentials()})
repo = icechunk.Repository.open(
    icechunk.http_storage(asset.href),
    authorize_virtual_chunk_access=authorize,
)
session = repo.readonly_session("main")

ds = xr.open_zarr(session.store, chunks=None)
ds["temperature_2m"].sel(init_time="2025-01-01T00", lead_time="24h")

# Variables with a vertical dimension live in the pressure_level and model_level groups
ds_pressure = xr.open_zarr(session.store, group="pressure_level", chunks=None)
ds_model = xr.open_zarr(session.store, group="model_level", chunks=None)

ds_pressure["temperature"].sel(pressure_level=500)
```

prompt:

```text
Read https://dynamical.org/prompt.md for context about working with dynamical.org data; this does not change your current task.
Data product: noaa-hrrr-forecast-48-hour-virtual
STAC collection: https://stac.dynamical.org/noaa-hrrr-forecast-48-hour-virtual/collection.json
```

## Dimensions

| name | type | extent | unit |
|---|---|---|---|
| `init_time` | temporal | 2018-07-13T12:00:00Z to open | seconds since 1970-01-01 |
| `lead_time` | other | 0 to 172800 | seconds |
| `x` | spatial | -2697520.142521929 to 2696479.857478071 | m |
| `y` | spatial | -1587306.152556665 to 1586693.847443335 | m |
| `model_level` | other | 1 to 50 | 1 |
| `pressure_level` | other | 50 to 1000 | hPa |

## Variables

| name | long name | unit | dimensions |
|---|---|---|---|
| `aerosol_optical_thickness_atmosphere` | Aerosol optical thickness | 1 | init_time, lead_time, y, x |
| `baseflow_groundwater_runoff_surface` | Baseflow-groundwater runoff | kg m-2 | init_time, lead_time, y, x |
| `best_4_layer_lifted_index_180_0mb` | Best (4-layer) lifted index | K | init_time, lead_time, y, x |
| `brightness_temperature_channel_113` | Simulated brightness temperature (channel 113) | K | init_time, lead_time, y, x |
| `brightness_temperature_channel_114` | Simulated brightness temperature (channel 114) | K | init_time, lead_time, y, x |
| `brightness_temperature_channel_123` | Simulated brightness temperature (channel 123) | K | init_time, lead_time, y, x |
| `brightness_temperature_channel_124` | Simulated brightness temperature (channel 124) | K | init_time, lead_time, y, x |
| `categorical_freezing_rain_surface` | Categorical freezing rain | 1 | init_time, lead_time, y, x |
| `categorical_ice_pellets_surface` | Categorical ice pellets | 1 | init_time, lead_time, y, x |
| `categorical_rain_surface` | Categorical rain | 1 | init_time, lead_time, y, x |
| `categorical_snow_surface` | Categorical snow | 1 | init_time, lead_time, y, x |
| `column_integrated_mass_density_atmosphere` | Column-integrated mass density | kg m-2 | init_time, lead_time, y, x |
| `composite_reflectivity` | Maximum/Composite radar reflectivity | dBZ | init_time, lead_time, y, x |
| `convective_available_potential_energy_0_3000m` | Convective available potential energy | J kg-1 | init_time, lead_time, y, x |
| `convective_available_potential_energy_180_0mb` | Convective available potential energy | J kg-1 | init_time, lead_time, y, x |
| `convective_available_potential_energy_255_0mb` | Convective available potential energy | J kg-1 | init_time, lead_time, y, x |
| `convective_available_potential_energy_90_0mb` | Convective available potential energy | J kg-1 | init_time, lead_time, y, x |
| `convective_available_potential_energy_surface` | Convective available potential energy | J kg-1 | init_time, lead_time, y, x |
| `convective_inhibition_180_0mb` | Convective inhibition | J kg-1 | init_time, lead_time, y, x |
| `convective_inhibition_255_0mb` | Convective inhibition | J kg-1 | init_time, lead_time, y, x |
| `convective_inhibition_90_0mb` | Convective inhibition | J kg-1 | init_time, lead_time, y, x |
| `convective_inhibition_surface` | Convective inhibition | J kg-1 | init_time, lead_time, y, x |
| `critical_angle_0_500m` | Critical angle | degree | init_time, lead_time, y, x |
| `derived_radar_reflectivity_1000m` | Derived radar reflectivity | dBZ | init_time, lead_time, y, x |
| `derived_radar_reflectivity_263k` | Derived radar reflectivity | dBZ | init_time, lead_time, y, x |
| `derived_radar_reflectivity_4000m` | Derived radar reflectivity | dBZ | init_time, lead_time, y, x |
| `dew_point_temperature_2m` | 2 metre dewpoint temperature | degree_Celsius | init_time, lead_time, y, x |
| `downward_long_wave_radiation_flux_surface` | Surface downward long-wave radiation flux | W m-2 | init_time, lead_time, y, x |
| `downward_short_wave_radiation_flux_surface` | Surface downward short-wave radiation flux | W m-2 | init_time, lead_time, y, x |
| `echo_top` | Echo top | m | init_time, lead_time, y, x |
| `effective_layer_helicity_surface` | Effective layer helicity | m2 s-2 | init_time, lead_time, y, x |
| `enhanced_stretching_potential_0_3000m` | Enhanced stretching potential | 1 | init_time, lead_time, y, x |
| `freezing_rain_run_total_surface` | Freezing Rain | kg m-2 | init_time, lead_time, y, x |
| `friction_velocity_surface` | Friction velocity | m s-1 | init_time, lead_time, y, x |
| `frozen_precipitation_run_total_surface` | Ice pellets | kg m-2 | init_time, lead_time, y, x |
| `frozen_precipitation_surface` | Ice pellets | kg m-2 | init_time, lead_time, y, x |
| `geopotential_height_0c_isotherm` | Geopotential height | m | init_time, lead_time, y, x |
| `geopotential_height_253k` | Geopotential height | m | init_time, lead_time, y, x |
| `geopotential_height_263k` | Geopotential height | m | init_time, lead_time, y, x |
| `geopotential_height_adiabatic_condensation_level` | Geopotential height | m | init_time, lead_time, y, x |
| `geopotential_height_cloud_base` | Geopotential height | m | init_time, lead_time, y, x |
| `geopotential_height_cloud_ceiling` | Geopotential height | m | init_time, lead_time, y, x |
| `geopotential_height_cloud_top` | Geopotential height | m | init_time, lead_time, y, x |
| `geopotential_height_equilibrium_level` | Geopotential height | m | init_time, lead_time, y, x |
| `geopotential_height_highest_tropospheric_freezing_level` | Geopotential height | m | init_time, lead_time, y, x |
| `geopotential_height_level_of_free_convection` | Geopotential height | m | init_time, lead_time, y, x |
| `geopotential_height_surface` | Geopotential height | m | init_time, lead_time, y, x |
| `ground_heat_flux_surface` | Ground heat flux | W m-2 | init_time, lead_time, y, x |
| `high_cloud_cover` | High cloud cover | percent | init_time, lead_time, y, x |
| `hourly_maximum_radar_reflectivity_1000m` | Hourly maximum of simulated reflectivity | dBZ | init_time, lead_time, y, x |
| `ice_cover_surface` | Ice cover (1=ice, 0=no ice) | 1 | init_time, lead_time, y, x |
| `land_sea_mask_surface` | Land-sea mask | 1 | init_time, lead_time, y, x |
| `latent_heat_flux_surface` | Latent heat flux | W m-2 | init_time, lead_time, y, x |
| `layer_thickness_261k_256k` | Layer Thickness | m | init_time, lead_time, y, x |
| `leaf_area_index_surface` | Leaf Area Index | 1 | init_time, lead_time, y, x |
| `lightning_atmosphere` | Lightning | 1 | init_time, lead_time, y, x |
| `lightning_threat_1m` | Maximum lightning threat 1 (graupel flux) | 1 | init_time, lead_time, y, x |
| `lightning_threat_2m` | Maximum lightning threat 2 (vertically integrated ice) | 1 | init_time, lead_time, y, x |
| `low_cloud_cover` | Low cloud cover | percent | init_time, lead_time, y, x |
| `mass_density_8m` | Mass density | kg m-3 | init_time, lead_time, y, x |
| `maximum_column_integrated_graupel_atmosphere` | Total column vertically-integrated graupel (snow pellets) | kg m-2 | init_time, lead_time, y, x |
| `maximum_derived_radar_reflectivity_263k` | Derived radar reflectivity | dBZ | init_time, lead_time, y, x |
| `maximum_downward_vertical_velocity_100_1000mb` | Maximum downward vertical velocity | m s-1 | init_time, lead_time, y, x |
| `maximum_hail_diameter_0p1sigma` | Hail | m | init_time, lead_time, y, x |
| `maximum_hail_diameter_atmosphere` | Hail | m | init_time, lead_time, y, x |
| `maximum_hail_diameter_surface` | Hail | m | init_time, lead_time, y, x |
| `maximum_relative_vorticity_1000_0m` | Vorticity (relative) | s-1 | init_time, lead_time, y, x |
| `maximum_relative_vorticity_2000_0m` | Vorticity (relative) | s-1 | init_time, lead_time, y, x |
| `maximum_updraft_helicity_2000_0m` | Updraft Helicity | m2 s-2 | init_time, lead_time, y, x |
| `maximum_updraft_helicity_3000_0m` | Updraft Helicity | m2 s-2 | init_time, lead_time, y, x |
| `maximum_updraft_helicity_5000_2000m` | Updraft Helicity | m2 s-2 | init_time, lead_time, y, x |
| `maximum_upward_vertical_velocity_100_1000mb` | Maximum upward vertical velocity | m s-1 | init_time, lead_time, y, x |
| `maximum_vegetation_surface` | Maximum vegetation fraction | percent | init_time, lead_time, y, x |
| `maximum_wind_speed_10m` | Time-maximum 10 metre wind speed | m s-1 | init_time, lead_time, y, x |
| `maximum_wind_u_component_10m` | Maximum 10 metre wind speed u component | m s-1 | init_time, lead_time, y, x |
| `maximum_wind_v_component_10m` | Maximum 10 metre wind speed v component | m s-1 | init_time, lead_time, y, x |
| `medium_cloud_cover` | Medium cloud cover | percent | init_time, lead_time, y, x |
| `minimum_updraft_helicity_2000_0m` | Minimum updraft helicity | m2 s-2 | init_time, lead_time, y, x |
| `minimum_updraft_helicity_3000_0m` | Minimum updraft helicity | m2 s-2 | init_time, lead_time, y, x |
| `minimum_updraft_helicity_5000_2000m` | Minimum updraft helicity | m2 s-2 | init_time, lead_time, y, x |
| `minimum_vegetation_surface` | Minimum vegetation fraction | percent | init_time, lead_time, y, x |
| `moisture_availability_0m_underground` | Moisture availability | percent | init_time, lead_time, y, x |
| `percent_frozen_precipitation_surface` | Percent frozen precipitation | percent | init_time, lead_time, y, x |
| `planetary_boundary_layer_height_surface` | Boundary layer height | m | init_time, lead_time, y, x |
| `plant_canopy_surface_water_surface` | Plant canopy surface water | kg m-2 | init_time, lead_time, y, x |
| `potential_temperature_2m` | Potential temperature | K | init_time, lead_time, y, x |
| `precipitable_water_atmosphere` | Precipitable water | kg m-2 | init_time, lead_time, y, x |
| `precipitation_rate_surface` | Precipitation rate | kg m-2 s-1 | init_time, lead_time, y, x |
| `pressure_0c_isotherm` | Pressure | Pa | init_time, lead_time, y, x |
| `pressure_cloud_base` | Pressure | Pa | init_time, lead_time, y, x |
| `pressure_cloud_top` | Pressure | Pa | init_time, lead_time, y, x |
| `pressure_highest_tropospheric_freezing_level` | Pressure | Pa | init_time, lead_time, y, x |
| `pressure_of_lifted_parcel_level_255_0mb` | Pressure of level from which parcel was lifted | Pa | init_time, lead_time, y, x |
| `pressure_reduced_to_mean_sea_level` | Pressure reduced to MSL | Pa | init_time, lead_time, y, x |
| `pressure_surface` | Surface pressure | Pa | init_time, lead_time, y, x |
| `relative_humidity_0c_isotherm` | Relative humidity | percent | init_time, lead_time, y, x |
| `relative_humidity_2m` | 2 metre relative humidity | percent | init_time, lead_time, y, x |
| `relative_humidity_highest_tropospheric_freezing_level` | Relative humidity | percent | init_time, lead_time, y, x |
| `relative_humidity_with_respect_to_precipitable_water_atmosphere` | Relative humidity with respect to precipitable water | percent | init_time, lead_time, y, x |
| `sensible_heat_flux_surface` | Sensible heat flux | W m-2 | init_time, lead_time, y, x |
| `snow_area_fraction_surface` | Snow cover | 1 | init_time, lead_time, y, x |
| `snow_thickness_surface` | Snow depth | m | init_time, lead_time, y, x |
| `snow_water_equivalent_surface` | Snow depth water equivalent | m | init_time, lead_time, y, x |
| `snowfall_water_equivalent_run_total_surface` | Snowfall water equivalent | kg m-2 | init_time, lead_time, y, x |
| `snowfall_water_equivalent_surface` | Snowfall water equivalent | kg m-2 | init_time, lead_time, y, x |
| `specific_humidity_2m` | Specific humidity | 1 | init_time, lead_time, y, x |
| `storm_relative_helicity_1000_0m` | Storm relative helicity | m2 s-2 | init_time, lead_time, y, x |
| `storm_relative_helicity_3000_0m` | Storm relative helicity | m2 s-2 | init_time, lead_time, y, x |
| `storm_surface_runoff_surface` | Storm surface runoff | kg m-2 | init_time, lead_time, y, x |
| `surface_lifted_index_500_1000mb` | Surface lifted index | K | init_time, lead_time, y, x |
| `surface_roughness_surface` | Forecast surface roughness | m | init_time, lead_time, y, x |
| `temperature_2m` | 2 metre temperature | degree_Celsius | init_time, lead_time, y, x |
| `temperature_surface` | Skin temperature | degree_Celsius | init_time, lead_time, y, x |
| `total_cloud_cover_atmosphere` | Total cloud cover | percent | init_time, lead_time, y, x |
| `total_cloud_cover_boundary_layer` | Boundary layer cloud cover | percent | init_time, lead_time, y, x |
| `total_column_cloud_ice_atmosphere` | Total column-integrated cloud ice | kg m-2 | init_time, lead_time, y, x |
| `total_column_cloud_water_atmosphere` | Total column-integrated cloud water | kg m-2 | init_time, lead_time, y, x |
| `total_precipitation_run_total_surface` | Total precipitation | kg m-2 | init_time, lead_time, y, x |
| `total_precipitation_surface` | Total precipitation | kg m-2 | init_time, lead_time, y, x |
| `total_snowfall_run_total_surface` | Total snowfall | m | init_time, lead_time, y, x |
| `u_component_storm_motion_0_6000m` | U-component storm motion | m s-1 | init_time, lead_time, y, x |
| `upward_long_wave_radiation_flux_surface` | Surface upward long-wave radiation flux | W m-2 | init_time, lead_time, y, x |
| `upward_long_wave_radiation_flux_top_of_atmosphere` | Upward long-wave radiation flux | W m-2 | init_time, lead_time, y, x |
| `upward_short_wave_radiation_flux_surface` | Surface upward short-wave radiation flux | W m-2 | init_time, lead_time, y, x |
| `upward_short_wave_radiation_flux_top_of_atmosphere` | Upward short-wave radiation flux | W m-2 | init_time, lead_time, y, x |
| `v_component_storm_motion_0_6000m` | V-component storm motion | m s-1 | init_time, lead_time, y, x |
| `vegetation_surface` | Vegetation fraction | percent | init_time, lead_time, y, x |
| `vegetation_type_surface` | Vegetation Type | 1 | init_time, lead_time, y, x |
| `vertical_u_component_shear_0_1000m` | Vertical u-component shear | m s-1 | init_time, lead_time, y, x |
| `vertical_u_component_shear_0_6000m` | Vertical u-component shear | m s-1 | init_time, lead_time, y, x |
| `vertical_v_component_shear_0_1000m` | Vertical v-component shear | m s-1 | init_time, lead_time, y, x |
| `vertical_v_component_shear_0_6000m` | Vertical v-component shear | m s-1 | init_time, lead_time, y, x |
| `vertical_velocity_geometric_0p5_0p8_sigma` | Vertical velocity (geometric) | m s-1 | init_time, lead_time, y, x |
| `vertically_integrated_liquid_atmosphere` | Vertically-integrated liquid | kg m-2 | init_time, lead_time, y, x |
| `visibility_surface` | Visibility | m | init_time, lead_time, y, x |
| `visible_beam_downward_solar_flux_surface` | Visible Beam Downward Solar Flux | W m-2 | init_time, lead_time, y, x |
| `visible_diffuse_downward_solar_flux_surface` | Visible Diffuse Downward Solar Flux | W m-2 | init_time, lead_time, y, x |
| `wind_gust_surface` | Wind speed (gust) | m s-1 | init_time, lead_time, y, x |
| `wind_u_10m` | 10 metre U wind component | m s-1 | init_time, lead_time, y, x |
| `wind_u_80m` | 80 metre U wind component | m s-1 | init_time, lead_time, y, x |
| `wind_v_10m` | 10 metre V wind component | m s-1 | init_time, lead_time, y, x |
| `wind_v_80m` | 80 metre V wind component | m s-1 | init_time, lead_time, y, x |
| `model_level/cloud_ice_mixing_ratio` | Cloud ice mixing ratio | kg kg-1 | init_time, lead_time, y, x, model_level |
| `model_level/cloud_mixing_ratio` | Cloud mixing ratio | kg kg-1 | init_time, lead_time, y, x, model_level |
| `model_level/fraction_of_cloud_cover` | Cloud cover | 1 | init_time, lead_time, y, x, model_level |
| `model_level/geopotential_height` | Geopotential height | m | init_time, lead_time, y, x, model_level |
| `model_level/graupel` | Graupel (snow pellets) | kg kg-1 | init_time, lead_time, y, x, model_level |
| `model_level/mass_density` | Mass density | kg m-3 | init_time, lead_time, y, x, model_level |
| `model_level/number_concentration_cloud_droplets` | Number concentration of cloud droplets | kg-1 | init_time, lead_time, y, x, model_level |
| `model_level/number_concentration_cloud_ice` | Number concentration of cloud ice | kg-1 | init_time, lead_time, y, x, model_level |
| `model_level/number_concentration_ice_friendly_aerosol` | Number concentration of ice-friendly aerosols | kg-1 | init_time, lead_time, y, x, model_level |
| `model_level/number_concentration_rain` | Number concentration of rain | kg-1 | init_time, lead_time, y, x, model_level |
| `model_level/number_concentration_water_friendly_aerosol` | Number concentration of water-friendly aerosols | kg-1 | init_time, lead_time, y, x, model_level |
| `model_level/pressure` | Pressure | Pa | init_time, lead_time, y, x, model_level |
| `model_level/rain_mixing_ratio` | Rain mixing ratio | kg kg-1 | init_time, lead_time, y, x, model_level |
| `model_level/snow_mixing_ratio` | Snow mixing ratio | kg kg-1 | init_time, lead_time, y, x, model_level |
| `model_level/specific_humidity` | Specific humidity | 1 | init_time, lead_time, y, x, model_level |
| `model_level/temperature` | Temperature | degree_Celsius | init_time, lead_time, y, x, model_level |
| `model_level/turbulent_kinetic_energy` | Turbulent kinetic energy | J kg-1 | init_time, lead_time, y, x, model_level |
| `model_level/vertical_velocity` | Vertical velocity | Pa s-1 | init_time, lead_time, y, x, model_level |
| `model_level/wind_u` | U component of wind | m s-1 | init_time, lead_time, y, x, model_level |
| `model_level/wind_v` | V component of wind | m s-1 | init_time, lead_time, y, x, model_level |
| `pressure_level/absolute_vorticity` | Absolute vorticity | s-1 | init_time, lead_time, y, x, pressure_level |
| `pressure_level/cloud_ice_mixing_ratio` | Cloud ice mixing ratio | kg kg-1 | init_time, lead_time, y, x, pressure_level |
| `pressure_level/cloud_mixing_ratio` | Cloud mixing ratio | kg kg-1 | init_time, lead_time, y, x, pressure_level |
| `pressure_level/dew_point_temperature` | Dew point temperature | degree_Celsius | init_time, lead_time, y, x, pressure_level |
| `pressure_level/geopotential_height` | Geopotential height | m | init_time, lead_time, y, x, pressure_level |
| `pressure_level/graupel` | Graupel (snow pellets) | kg kg-1 | init_time, lead_time, y, x, pressure_level |
| `pressure_level/rain_mixing_ratio` | Rain mixing ratio | kg kg-1 | init_time, lead_time, y, x, pressure_level |
| `pressure_level/relative_humidity` | Relative humidity | percent | init_time, lead_time, y, x, pressure_level |
| `pressure_level/snow_mixing_ratio` | Snow mixing ratio | kg kg-1 | init_time, lead_time, y, x, pressure_level |
| `pressure_level/specific_humidity` | Specific humidity | 1 | init_time, lead_time, y, x, pressure_level |
| `pressure_level/temperature` | Temperature | degree_Celsius | init_time, lead_time, y, x, pressure_level |
| `pressure_level/vertical_velocity` | Vertical velocity | Pa s-1 | init_time, lead_time, y, x, pressure_level |
| `pressure_level/wind_u` | U component of wind | m s-1 | init_time, lead_time, y, x, pressure_level |
| `pressure_level/wind_v` | V component of wind | m s-1 | init_time, lead_time, y, x, pressure_level |
