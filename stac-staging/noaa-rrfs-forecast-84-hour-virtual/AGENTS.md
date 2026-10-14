# NOAA RRFS forecast, 84 hour, virtual: notes for agents

Read https://dynamical.org/prompt.md for context about working with dynamical.org data.

- Collection id: `noaa-rrfs-forecast-84-hour-virtual`
- STAC collection: https://stac-staging.dynamical.org/noaa-rrfs-forecast-84-hour-virtual/collection.json
- Dataset version: 0.1.0

## Access

All data is public. No credentials are needed.

| asset | href |
|---|---|
| `icechunk` | `s3://dynamical-noaa-rrfs/noaa-rrfs-forecast-84-hour-virtual/v0.1.0.icechunk/` |
| `icechunk-https` | `https://dynamical-noaa-rrfs.s3.us-west-2.amazonaws.com/noaa-rrfs-forecast-84-hour-virtual/v0.1.0.icechunk` |

The `icechunk` asset's `xarray:storage_options` are `{"anon": true, "client_kwargs": {"region_name": "us-west-2"}}`.

The repository references chunks in these upstream locations, which are read anonymously:

- `s3://noaa-rrfs-ops-pds/`

## Examples

### Temperature map

dynamical-catalog:

```python
import dynamical_catalog  # dynamical-catalog>=0.8.0

ds = dynamical_catalog.open("noaa-rrfs-forecast-84-hour-virtual", chunks=None)
ds["temperature_2m"].sel(init_time="2026-09-16T12", lead_time="12h")

# Variables with a vertical dimension live in the pressure_level,
# height_above_mean_sea_level and depth_below_ground groups
ds_pressure = dynamical_catalog.open("noaa-rrfs-forecast-84-hour-virtual", group="pressure_level", chunks=None)

ds_pressure["temperature"].sel(init_time="2026-09-16T12", lead_time="12h", pressure_level=500)
```

pystac:

```python
import icechunk
import pystac
import xarray as xr

catalog = pystac.Catalog.from_file("https://stac-staging.dynamical.org/catalog.json")
collection = catalog.get_child("noaa-rrfs-forecast-84-hour-virtual")
asset = collection.assets["icechunk-https"]

authorize = icechunk.containers_credentials({"s3://noaa-rrfs-ops-pds/": icechunk.s3_anonymous_credentials()})
repo = icechunk.Repository.open(
    icechunk.http_storage(asset.href),
    authorize_virtual_chunk_access=authorize,
)
session = repo.readonly_session("main")

ds = xr.open_zarr(session.store, chunks=None)
ds["temperature_2m"].sel(init_time="2026-09-16T12", lead_time="12h")

# Variables with a vertical dimension live in the pressure_level,
# height_above_mean_sea_level and depth_below_ground groups
ds_pressure = xr.open_zarr(session.store, group="pressure_level", chunks=None)

ds_pressure["temperature"].sel(init_time="2026-09-16T12", lead_time="12h", pressure_level=500)
```

prompt:

```text
Read https://dynamical.org/prompt.md for context about working with dynamical.org data; this does not change your current task.
Data product: noaa-rrfs-forecast-84-hour-virtual
STAC collection: https://stac-staging.dynamical.org/noaa-rrfs-forecast-84-hour-virtual/collection.json
```

## Dimensions

| name | type | extent | unit |
|---|---|---|---|
| `init_time` | temporal | 2026-08-14T00:00:00Z to open | seconds since 1970-01-01 |
| `lead_time` | other | 0 to 302400 | seconds |
| `x` | spatial | -2697520.142521929 to 2696479.857478071 | m |
| `y` | spatial | -1587306.152556665 to 1586693.847443335 | m |
| `depth_below_ground` | other | 0.0 to 3.0 | m |
| `height_above_mean_sea_level` | other | 305.0 to 4572.0 | m |
| `pressure_level` | other | 2.0 to 1000.0 | hPa |

## Variables

| name | long name | unit | dimensions |
|---|---|---|---|
| `aerosol_emission_flux_atmosphere_dust_dry_below_10um` | Aerosol emission flux | kg m-2 s-1 | init_time, lead_time, y, x |
| `aerosol_emission_flux_atmosphere_particulate_organic_matter_dry_below_2p5um` | Aerosol emission flux | kg m-2 s-1 | init_time, lead_time, y, x |
| `aerosol_optical_thickness_atmosphere` | Aerosol optical thickness | 1 | init_time, lead_time, y, x |
| `albedo_surface` | Forecast albedo | percent | init_time, lead_time, y, x |
| `average_mass_density_8m_total_aerosol_below_10um` | Mass density | kg m-3 | init_time, lead_time, y, x |
| `average_mass_density_8m_total_aerosol_below_2p5um` | Mass density | kg m-3 | init_time, lead_time, y, x |
| `best_4_layer_lifted_index_180_0mb` | Best (4-layer) lifted index | K | init_time, lead_time, y, x |
| `brightness_temperature_goes_16_band_10` | Simulated brightness temperature for ABI GOES-16, band 10 | K | init_time, lead_time, y, x |
| `brightness_temperature_goes_16_band_11` | Simulated brightness temperature for ABI GOES-16, band 11 | K | init_time, lead_time, y, x |
| `brightness_temperature_goes_16_band_12` | Simulated brightness temperature for ABI GOES-16, band 12 | K | init_time, lead_time, y, x |
| `brightness_temperature_goes_16_band_13` | Simulated brightness temperature for ABI GOES-16, band 13 | K | init_time, lead_time, y, x |
| `brightness_temperature_goes_16_band_14` | Simulated brightness temperature for ABI GOES-16, band 14 | K | init_time, lead_time, y, x |
| `brightness_temperature_goes_16_band_15` | Simulated brightness temperature for ABI GOES-16, band 15 | K | init_time, lead_time, y, x |
| `brightness_temperature_goes_16_band_16` | Simulated brightness temperature for ABI GOES-16, band 16 | K | init_time, lead_time, y, x |
| `brightness_temperature_goes_16_band_7` | Simulated brightness temperature for ABI GOES-16, band 7 | K | init_time, lead_time, y, x |
| `brightness_temperature_goes_16_band_8` | Simulated brightness temperature for ABI GOES-16, band 8 | K | init_time, lead_time, y, x |
| `brightness_temperature_goes_16_band_9` | Simulated brightness temperature for ABI GOES-16, band 9 | K | init_time, lead_time, y, x |
| `brightness_temperature_goes_18_band_10` | Simulated brightness temperature for ABI GOES-18, band 10 | K | init_time, lead_time, y, x |
| `brightness_temperature_goes_18_band_11` | Simulated brightness temperature for ABI GOES-18, band 11 | K | init_time, lead_time, y, x |
| `brightness_temperature_goes_18_band_12` | Simulated brightness temperature for ABI GOES-18, band 12 | K | init_time, lead_time, y, x |
| `brightness_temperature_goes_18_band_13` | Simulated brightness temperature for ABI GOES-18, band 13 | K | init_time, lead_time, y, x |
| `brightness_temperature_goes_18_band_14` | Simulated brightness temperature for ABI GOES-18, band 14 | K | init_time, lead_time, y, x |
| `brightness_temperature_goes_18_band_15` | Simulated brightness temperature for ABI GOES-18, band 15 | K | init_time, lead_time, y, x |
| `brightness_temperature_goes_18_band_16` | Simulated brightness temperature for ABI GOES-18, band 16 | K | init_time, lead_time, y, x |
| `brightness_temperature_goes_18_band_8` | Simulated brightness temperature for ABI GOES-18, band 8 | K | init_time, lead_time, y, x |
| `brightness_temperature_goes_18_band_9` | Simulated brightness temperature for ABI GOES-18, band 9 | K | init_time, lead_time, y, x |
| `brightness_temperature_top_of_atmosphere` | Brightness temperature | K | init_time, lead_time, y, x |
| `categorical_freezing_rain_surface` | Categorical freezing rain | 1 | init_time, lead_time, y, x |
| `categorical_ice_pellets_surface` | Categorical ice pellets | 1 | init_time, lead_time, y, x |
| `categorical_precipitation_exceeding_100_year_average_recurrence_interval_run_total_surface` | Precipitation exceeding 100-year average recurrence interval | 1 | init_time, lead_time, y, x |
| `categorical_precipitation_exceeding_100_year_average_recurrence_interval_surface` | Precipitation exceeding 100-year average recurrence interval | 1 | init_time, lead_time, y, x |
| `categorical_precipitation_exceeding_10_year_average_recurrence_interval_run_total_surface` | Precipitation exceeding 10-year average recurrence interval | 1 | init_time, lead_time, y, x |
| `categorical_precipitation_exceeding_10_year_average_recurrence_interval_surface` | Precipitation exceeding 10-year average recurrence interval | 1 | init_time, lead_time, y, x |
| `categorical_precipitation_exceeding_2_year_average_recurrence_interval_run_total_surface` | Precipitation exceeding 2-year average recurrence interval | 1 | init_time, lead_time, y, x |
| `categorical_precipitation_exceeding_2_year_average_recurrence_interval_surface` | Precipitation exceeding 2-year average recurrence interval | 1 | init_time, lead_time, y, x |
| `categorical_precipitation_exceeding_5_year_average_recurrence_interval_run_total_surface` | Precipitation exceeding 5-year average recurrence interval | 1 | init_time, lead_time, y, x |
| `categorical_precipitation_exceeding_5_year_average_recurrence_interval_surface` | Precipitation exceeding 5-year average recurrence interval | 1 | init_time, lead_time, y, x |
| `categorical_rain_surface` | Categorical rain | 1 | init_time, lead_time, y, x |
| `categorical_snow_surface` | Categorical snow | 1 | init_time, lead_time, y, x |
| `clear_sky_downward_solar_flux_surface` | Clear Sky Downward Solar Flux | W m-2 | init_time, lead_time, y, x |
| `cloud_ceiling_height` | Ceiling | m | init_time, lead_time, y, x |
| `column_integrated_mass_density_atmosphere_dust_dry_below_10um` | Column-integrated mass density | kg m-2 | init_time, lead_time, y, x |
| `column_integrated_mass_density_atmosphere_dust_dry_below_2p5um` | Column-integrated mass density | kg m-2 | init_time, lead_time, y, x |
| `column_integrated_mass_density_atmosphere_dust_dry_from_2p5_to_10um` | Column-integrated mass density | kg m-2 | init_time, lead_time, y, x |
| `column_integrated_mass_density_atmosphere_particulate_organic_matter_dry_below_2p5um` | Column-integrated mass density | kg m-2 | init_time, lead_time, y, x |
| `column_integrated_soil_moisture_0m_underground` | Column-integrated soil water | kg m-2 | init_time, lead_time, y, x |
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
| `dew_point_depression_2m` | Dew point depression (or deficit) | K | init_time, lead_time, y, x |
| `dew_point_temperature_2m` | 2 metre dewpoint temperature | degree_Celsius | init_time, lead_time, y, x |
| `dew_point_temperature_30_0mb` | Dew point temperature | degree_Celsius | init_time, lead_time, y, x |
| `direct_evaporation_cease_soil_moisture_surface` | Direct evaporation cease (soil moisture) | 1 | init_time, lead_time, y, x |
| `downdraft_convective_available_potential_energy_400_0mb` | Downdraft convective available potential energy | J kg-1 | init_time, lead_time, y, x |
| `downward_long_wave_radiation_flux_surface` | Surface downward long-wave radiation flux | W m-2 | init_time, lead_time, y, x |
| `downward_short_wave_radiation_flux_surface` | Surface downward short-wave radiation flux | W m-2 | init_time, lead_time, y, x |
| `drag_coefficient_surface` | Drag coefficient | 1 | init_time, lead_time, y, x |
| `echo_top` | Echo top | m | init_time, lead_time, y, x |
| `effective_layer_helicity_surface` | Effective layer helicity | m2 s-2 | init_time, lead_time, y, x |
| `effective_layer_shear_u_level_of_free_convection` | Effective layer U shear | m s-1 | init_time, lead_time, y, x |
| `effective_layer_shear_v_level_of_free_convection` | Effective layer V shear | m s-1 | init_time, lead_time, y, x |
| `effective_layer_storm_motion_u_level_of_free_convection` | Effective layer U storm motion | m s-1 | init_time, lead_time, y, x |
| `effective_layer_storm_motion_v_level_of_free_convection` | Effective layer V storm motion | m s-1 | init_time, lead_time, y, x |
| `equilibrium_level_temperature_equilibrium_level` | Equilibrium level temperature | degree_Celsius | init_time, lead_time, y, x |
| `exchange_coefficient_surface` | Exchange coefficient | kg m-2 s-1 | init_time, lead_time, y, x |
| `fire_radiative_power_surface` | Wildfire radiative power | W | init_time, lead_time, y, x |
| `freezing_rain_run_total_surface` | Freezing Rain | kg m-2 | init_time, lead_time, y, x |
| `freezing_rain_surface` | Freezing Rain | kg m-2 | init_time, lead_time, y, x |
| `friction_velocity_surface` | Friction velocity | m s-1 | init_time, lead_time, y, x |
| `frozen_precipitation_run_total_surface` | Graupel (snow pellets) precipitation | kg m-2 | init_time, lead_time, y, x |
| `frozen_precipitation_surface` | Graupel (snow pellets) precipitation | kg m-2 | init_time, lead_time, y, x |
| `geopotential_height_0c_isotherm` | Geopotential height | m | init_time, lead_time, y, x |
| `geopotential_height_253k` | Geopotential height | m | init_time, lead_time, y, x |
| `geopotential_height_cloud_base` | Geopotential height | m | init_time, lead_time, y, x |
| `geopotential_height_cloud_ceiling` | Geopotential height | m | init_time, lead_time, y, x |
| `geopotential_height_cloud_top` | Geopotential height | m | init_time, lead_time, y, x |
| `geopotential_height_equilibrium_level` | Geopotential height | m | init_time, lead_time, y, x |
| `geopotential_height_highest_tropospheric_freezing_level` | Geopotential height | m | init_time, lead_time, y, x |
| `geopotential_height_max_wind` | Geopotential height | m | init_time, lead_time, y, x |
| `geopotential_height_supercooled_liquid_water_base` | Geopotential height | m | init_time, lead_time, y, x |
| `geopotential_height_supercooled_liquid_water_top` | Geopotential height | m | init_time, lead_time, y, x |
| `geopotential_height_surface` | Geopotential height | m | init_time, lead_time, y, x |
| `geopotential_height_tropopause` | Geopotential height | m | init_time, lead_time, y, x |
| `geopotential_height_wet_bulb_zero` | Geopotential height | m | init_time, lead_time, y, x |
| `ground_heat_flux_surface` | Ground heat flux | W m-2 | init_time, lead_time, y, x |
| `height_above_ground_adiabatic_condensation_level` | Geometric height of adiabatic condensation level above ground | m | init_time, lead_time, y, x |
| `high_cloud_cover` | High cloud cover | percent | init_time, lead_time, y, x |
| `horizontal_moisture_convergence_30_0mb` | Horizontal moisture convergence | s-1 | init_time, lead_time, y, x |
| `horizontal_moisture_convergence_850mb` | Horizontal moisture convergence | s-1 | init_time, lead_time, y, x |
| `horizontal_moisture_convergence_950mb` | Horizontal moisture convergence | s-1 | init_time, lead_time, y, x |
| `horizontal_moisture_convergence_atmosphere` | Horizontal moisture convergence | kg m-2 s-1 | init_time, lead_time, y, x |
| `hourly_maximum_radar_reflectivity_1000m` | Hourly maximum of simulated reflectivity | dBZ | init_time, lead_time, y, x |
| `ice_cover_surface` | Ice concentration | 1 | init_time, lead_time, y, x |
| `ice_growth_rate_10m_amsl` | Ice growth rate | m s-1 | init_time, lead_time, y, x |
| `instantaneous_downward_long_wave_radiation_flux_surface` | Surface downward long-wave radiation flux | W m-2 | init_time, lead_time, y, x |
| `instantaneous_downward_short_wave_radiation_flux_surface` | Surface downward short-wave radiation flux | W m-2 | init_time, lead_time, y, x |
| `instantaneous_ground_heat_flux_surface` | Ground heat flux | W m-2 | init_time, lead_time, y, x |
| `instantaneous_latent_heat_flux_surface` | Latent heat flux | W m-2 | init_time, lead_time, y, x |
| `instantaneous_sensible_heat_flux_surface` | Sensible heat flux | W m-2 | init_time, lead_time, y, x |
| `instantaneous_total_cloud_cover_atmosphere` | Total cloud cover | percent | init_time, lead_time, y, x |
| `instantaneous_upward_long_wave_radiation_flux_surface` | Surface upward long-wave radiation flux | W m-2 | init_time, lead_time, y, x |
| `instantaneous_upward_short_wave_radiation_flux_surface` | Surface upward short-wave radiation flux | W m-2 | init_time, lead_time, y, x |
| `land_sea_mask_surface` | Land-sea mask | 1 | init_time, lead_time, y, x |
| `latent_heat_flux_surface` | Latent heat flux | W m-2 | init_time, lead_time, y, x |
| `layer_thickness_261k_256k` | Layer Thickness | m | init_time, lead_time, y, x |
| `leaf_area_index_surface` | Leaf Area Index | 1 | init_time, lead_time, y, x |
| `low_cloud_cover` | Low cloud cover | percent | init_time, lead_time, y, x |
| `mass_density_8m_dust_dry_below_2p5um` | Mass density | kg m-3 | init_time, lead_time, y, x |
| `mass_density_8m_dust_dry_from_2p5_to_10um` | Mass density | kg m-3 | init_time, lead_time, y, x |
| `mass_density_8m_particulate_organic_matter_dry_below_2p5um` | Mass density | kg m-3 | init_time, lead_time, y, x |
| `mass_density_height_atmosphere` | Height of aerosol mass density | m | init_time, lead_time, y, x |
| `mass_density_height_base` | Height of aerosol mass density | m | init_time, lead_time, y, x |
| `mass_density_height_top` | Height of aerosol mass density | m | init_time, lead_time, y, x |
| `mass_grid_levels_surface` | Number of mass grid levels | 1 | init_time, lead_time, y, x |
| `maximum_derived_radar_reflectivity_263k` | Derived radar reflectivity | dBZ | init_time, lead_time, y, x |
| `maximum_downward_vertical_velocity_100_1000mb` | Maximum downward vertical velocity | m s-1 | init_time, lead_time, y, x |
| `maximum_hail_diameter_surface` | Hail | m | init_time, lead_time, y, x |
| `maximum_lightning_atmosphere` | Lightning | 1 | init_time, lead_time, y, x |
| `maximum_lightning_threat_1m` | Maximum lightning threat 1 (graupel flux) | 1 | init_time, lead_time, y, x |
| `maximum_lightning_threat_2m` | Maximum lightning threat 2 (vertically integrated ice) | 1 | init_time, lead_time, y, x |
| `maximum_precipitation_rate_surface` | Precipitation rate | kg m-2 s-1 | init_time, lead_time, y, x |
| `maximum_relative_humidity_2m` | Time-maximum 2 metre relative humidity | percent | init_time, lead_time, y, x |
| `maximum_relative_vorticity_1000_0m` | Vorticity (relative) | s-1 | init_time, lead_time, y, x |
| `maximum_relative_vorticity_1_hybrid_level` | Vorticity (relative) | s-1 | init_time, lead_time, y, x |
| `maximum_relative_vorticity_2000_0m` | Vorticity (relative) | s-1 | init_time, lead_time, y, x |
| `maximum_snow_albedo_surface` | Maximum snow albedo | percent | init_time, lead_time, y, x |
| `maximum_temperature_2m` | Maximum temperature | degree_Celsius | init_time, lead_time, y, x |
| `maximum_updraft_helicity_3000_0m` | Updraft Helicity | m2 s-2 | init_time, lead_time, y, x |
| `maximum_updraft_helicity_5000_2000m` | Updraft Helicity | m2 s-2 | init_time, lead_time, y, x |
| `maximum_upward_vertical_velocity_100_1000mb` | Maximum upward vertical velocity | m s-1 | init_time, lead_time, y, x |
| `maximum_wind_speed_10m` | Time-maximum 10 metre wind speed | m s-1 | init_time, lead_time, y, x |
| `maximum_wind_u_component_10m` | Maximum 10 metre wind speed u component | m s-1 | init_time, lead_time, y, x |
| `maximum_wind_v_component_10m` | Maximum 10 metre wind speed v component | m s-1 | init_time, lead_time, y, x |
| `medium_cloud_cover` | Medium cloud cover | percent | init_time, lead_time, y, x |
| `minimal_stomatal_resistance_surface` | Minimal stomatal resistance | s m-1 | init_time, lead_time, y, x |
| `minimum_relative_humidity_2m` | Time-minimum 2 metre relative humidity | percent | init_time, lead_time, y, x |
| `minimum_temperature_2m` | Minimum temperature | degree_Celsius | init_time, lead_time, y, x |
| `minimum_updraft_helicity_3000_0m` | Minimum updraft helicity | m2 s-2 | init_time, lead_time, y, x |
| `minimum_updraft_helicity_5000_2000m` | Minimum updraft helicity | m2 s-2 | init_time, lead_time, y, x |
| `moisture_availability_0m_underground` | Moisture availability | percent | init_time, lead_time, y, x |
| `new_snow_density_surface` | Snow density | kg m-3 | init_time, lead_time, y, x |
| `number_of_soil_layers_in_root_zone_surface` | Number of soil layers in root zone | 1 | init_time, lead_time, y, x |
| `parcel_lifted_index_30_0mb` | Parcel lifted index (to 500 hPa) | K | init_time, lead_time, y, x |
| `percent_frozen_precipitation_surface` | Percent frozen precipitation | percent | init_time, lead_time, y, x |
| `planetary_boundary_layer_height_surface` | Boundary layer height | m | init_time, lead_time, y, x |
| `plant_canopy_surface_water_surface` | Plant canopy surface water | kg m-2 | init_time, lead_time, y, x |
| `potential_temperature_30_0mb` | Potential temperature | K | init_time, lead_time, y, x |
| `potential_temperature_surface` | Potential temperature | K | init_time, lead_time, y, x |
| `potential_temperature_tropopause` | Potential temperature | K | init_time, lead_time, y, x |
| `precipitable_water_30_0mb` | Precipitable water | kg m-2 | init_time, lead_time, y, x |
| `precipitable_water_atmosphere` | Precipitable water | kg m-2 | init_time, lead_time, y, x |
| `precipitation_rate_surface` | Precipitation rate | kg m-2 s-1 | init_time, lead_time, y, x |
| `pressure_0c_isotherm` | Pressure | Pa | init_time, lead_time, y, x |
| `pressure_120_90mb` | Pressure | Pa | init_time, lead_time, y, x |
| `pressure_150_120mb` | Pressure | Pa | init_time, lead_time, y, x |
| `pressure_180_150mb` | Pressure | Pa | init_time, lead_time, y, x |
| `pressure_30_0mb` | Pressure | Pa | init_time, lead_time, y, x |
| `pressure_60_30mb` | Pressure | Pa | init_time, lead_time, y, x |
| `pressure_80m` | 80 metre pressure | Pa | init_time, lead_time, y, x |
| `pressure_90_60mb` | Pressure | Pa | init_time, lead_time, y, x |
| `pressure_adiabatic_condensation_level` | Pressure | Pa | init_time, lead_time, y, x |
| `pressure_cloud_base` | Pressure | Pa | init_time, lead_time, y, x |
| `pressure_cloud_top` | Pressure | Pa | init_time, lead_time, y, x |
| `pressure_grid_scale_cloud_bottom_level` | Pressure | Pa | init_time, lead_time, y, x |
| `pressure_highest_tropospheric_freezing_level` | Pressure | Pa | init_time, lead_time, y, x |
| `pressure_max_wind` | Pressure | Pa | init_time, lead_time, y, x |
| `pressure_of_lifted_parcel_level_255_0mb` | Pressure of level from which parcel was lifted | Pa | init_time, lead_time, y, x |
| `pressure_reduced_to_mean_sea_level` | Pressure reduced to MSL | Pa | init_time, lead_time, y, x |
| `pressure_surface` | Surface pressure | Pa | init_time, lead_time, y, x |
| `pressure_top_of_atmosphere` | Pressure | Pa | init_time, lead_time, y, x |
| `pressure_tropopause` | Pressure | Pa | init_time, lead_time, y, x |
| `relative_humidity_0c_isotherm` | Relative humidity | percent | init_time, lead_time, y, x |
| `relative_humidity_120_90mb` | Relative humidity | percent | init_time, lead_time, y, x |
| `relative_humidity_150_120mb` | Relative humidity | percent | init_time, lead_time, y, x |
| `relative_humidity_180_150mb` | Relative humidity | percent | init_time, lead_time, y, x |
| `relative_humidity_2m` | 2 metre relative humidity | percent | init_time, lead_time, y, x |
| `relative_humidity_30_0mb` | Relative humidity | percent | init_time, lead_time, y, x |
| `relative_humidity_60_30mb` | Relative humidity | percent | init_time, lead_time, y, x |
| `relative_humidity_90_60mb` | Relative humidity | percent | init_time, lead_time, y, x |
| `relative_humidity_highest_tropospheric_freezing_level` | Relative humidity | percent | init_time, lead_time, y, x |
| `relative_humidity_with_respect_to_precipitable_water_atmosphere` | Relative humidity with respect to precipitable water | percent | init_time, lead_time, y, x |
| `sensible_heat_flux_surface` | Sensible heat flux | W m-2 | init_time, lead_time, y, x |
| `snow_area_fraction_surface` | Snow cover | 1 | init_time, lead_time, y, x |
| `snow_melt_surface` | Snowmelt | kg m-2 | init_time, lead_time, y, x |
| `snow_phase_change_heat_flux_surface` | Snow phase change heat flux | W m-2 | init_time, lead_time, y, x |
| `snow_thickness_surface` | Snow depth | m | init_time, lead_time, y, x |
| `snow_water_equivalent_surface` | Snow depth water equivalent | m | init_time, lead_time, y, x |
| `soil_porosity_surface` | Soil porosity | 1 | init_time, lead_time, y, x |
| `soil_type_surface` | Soil type | 1 | init_time, lead_time, y, x |
| `source_latitude_surface` | Latitude (-90 to +90) | degree_north | init_time, lead_time, y, x |
| `source_longitude_surface` | East Longitude (0 - 360) | degree_east | init_time, lead_time, y, x |
| `specific_humidity_120_90mb` | Specific humidity | 1 | init_time, lead_time, y, x |
| `specific_humidity_150_120mb` | Specific humidity | 1 | init_time, lead_time, y, x |
| `specific_humidity_180_150mb` | Specific humidity | 1 | init_time, lead_time, y, x |
| `specific_humidity_2m` | Specific humidity | 1 | init_time, lead_time, y, x |
| `specific_humidity_305m_above_mean_sea_level` | Specific humidity | 1 | init_time, lead_time, y, x |
| `specific_humidity_30_0mb` | Specific humidity | 1 | init_time, lead_time, y, x |
| `specific_humidity_60_30mb` | Specific humidity | 1 | init_time, lead_time, y, x |
| `specific_humidity_80m` | Specific humidity | 1 | init_time, lead_time, y, x |
| `specific_humidity_90_60mb` | Specific humidity | 1 | init_time, lead_time, y, x |
| `storm_relative_helicity_1000_0m` | Storm relative helicity | m2 s-2 | init_time, lead_time, y, x |
| `storm_relative_helicity_3000_0m` | Storm relative helicity | m2 s-2 | init_time, lead_time, y, x |
| `storm_surface_runoff_surface` | Storm surface runoff | kg m-2 | init_time, lead_time, y, x |
| `stream_function_250mb` | Stream function | m2 s-1 | init_time, lead_time, y, x |
| `stream_function_500mb` | Stream function | m2 s-1 | init_time, lead_time, y, x |
| `sublimation_evaporation_from_snow_surface` | Sublimation (evaporation from snow) | W m-2 | init_time, lead_time, y, x |
| `surface_roughness_surface` | Forecast surface roughness | m | init_time, lead_time, y, x |
| `temperature_100m` | Temperature | degree_Celsius | init_time, lead_time, y, x |
| `temperature_120_90mb` | Temperature | degree_Celsius | init_time, lead_time, y, x |
| `temperature_150_120mb` | Temperature | degree_Celsius | init_time, lead_time, y, x |
| `temperature_160m` | Temperature | degree_Celsius | init_time, lead_time, y, x |
| `temperature_180_150mb` | Temperature | degree_Celsius | init_time, lead_time, y, x |
| `temperature_2m` | 2 metre temperature | degree_Celsius | init_time, lead_time, y, x |
| `temperature_30_0mb` | Temperature | degree_Celsius | init_time, lead_time, y, x |
| `temperature_30m` | Temperature | degree_Celsius | init_time, lead_time, y, x |
| `temperature_320m` | Temperature | degree_Celsius | init_time, lead_time, y, x |
| `temperature_50m` | Temperature | degree_Celsius | init_time, lead_time, y, x |
| `temperature_60_30mb` | Temperature | degree_Celsius | init_time, lead_time, y, x |
| `temperature_80m` | 80 metre temperature | degree_Celsius | init_time, lead_time, y, x |
| `temperature_90_60mb` | Temperature | degree_Celsius | init_time, lead_time, y, x |
| `temperature_cloud_top` | Temperature | degree_Celsius | init_time, lead_time, y, x |
| `temperature_surface` | Skin temperature | degree_Celsius | init_time, lead_time, y, x |
| `temperature_tropopause` | Temperature | degree_Celsius | init_time, lead_time, y, x |
| `total_cloud_cover_atmosphere` | Total cloud cover | percent | init_time, lead_time, y, x |
| `total_cloud_cover_boundary_layer` | Boundary layer cloud cover | percent | init_time, lead_time, y, x |
| `total_precipitation_run_total_surface` | Total precipitation | kg m-2 | init_time, lead_time, y, x |
| `total_precipitation_surface` | Total precipitation | kg m-2 | init_time, lead_time, y, x |
| `total_snow_precipitation_run_total_surface` | Total snow precipitation | kg m-2 | init_time, lead_time, y, x |
| `total_snow_precipitation_surface` | Total snow precipitation | kg m-2 | init_time, lead_time, y, x |
| `total_snowfall_run_total_surface` | Total snowfall | m | init_time, lead_time, y, x |
| `transpiration_stress_onset_soil_moisture_surface` | Transpiration stress-onset (soil moisture) | 1 | init_time, lead_time, y, x |
| `u_component_storm_motion_6000_0m` | U-component storm motion | m s-1 | init_time, lead_time, y, x |
| `updraft_helicity_5000_2000m` | Updraft Helicity | m2 s-2 | init_time, lead_time, y, x |
| `upward_long_wave_radiation_flux_surface` | Surface upward long-wave radiation flux | W m-2 | init_time, lead_time, y, x |
| `upward_long_wave_radiation_flux_top_of_atmosphere` | Upward long-wave radiation flux | W m-2 | init_time, lead_time, y, x |
| `upward_short_wave_radiation_flux_surface` | Surface upward short-wave radiation flux | W m-2 | init_time, lead_time, y, x |
| `upward_short_wave_radiation_flux_top_of_atmosphere` | Upward short-wave radiation flux | W m-2 | init_time, lead_time, y, x |
| `v_component_storm_motion_6000_0m` | V-component storm motion | m s-1 | init_time, lead_time, y, x |
| `vegetation_surface` | Vegetation fraction | percent | init_time, lead_time, y, x |
| `vegetation_type_surface` | Vegetation Type | 1 | init_time, lead_time, y, x |
| `velocity_grid_levels_surface` | Number of velocity grid levels | 1 | init_time, lead_time, y, x |
| `ventilation_rate_planetary_boundary_layer` | Ventilation Rate | m2 s-1 | init_time, lead_time, y, x |
| `vertical_speed_shear_tropopause` | Vertical speed shear | s-1 | init_time, lead_time, y, x |
| `vertical_u_component_shear_0_6000m` | Vertical u-component shear | m s-1 | init_time, lead_time, y, x |
| `vertical_v_component_shear_0_6000m` | Vertical v-component shear | m s-1 | init_time, lead_time, y, x |
| `vertically_integrated_liquid_atmosphere` | Vertically-integrated liquid | kg m-2 | init_time, lead_time, y, x |
| `visibility_surface` | Visibility | m | init_time, lead_time, y, x |
| `visible_beam_downward_solar_flux_surface` | Visible Beam Downward Solar Flux | W m-2 | init_time, lead_time, y, x |
| `visible_diffuse_downward_solar_flux_surface` | Visible Diffuse Downward Solar Flux | W m-2 | init_time, lead_time, y, x |
| `water_temperature_surface` | Water temperature | degree_Celsius | init_time, lead_time, y, x |
| `wildfire_potential_surface` | Wildfire potential | 1 | init_time, lead_time, y, x |
| `wilting_point_surface` | Wilting point | 1 | init_time, lead_time, y, x |
| `wind_gust_surface` | Wind speed (gust) | m s-1 | init_time, lead_time, y, x |
| `wind_u_100m` | 100 metre U wind component | m s-1 | init_time, lead_time, y, x |
| `wind_u_10m` | 10 metre U wind component | m s-1 | init_time, lead_time, y, x |
| `wind_u_120_90mb` | U component of wind | m s-1 | init_time, lead_time, y, x |
| `wind_u_150_120mb` | U component of wind | m s-1 | init_time, lead_time, y, x |
| `wind_u_160m` | U component of wind | m s-1 | init_time, lead_time, y, x |
| `wind_u_180_150mb` | U component of wind | m s-1 | init_time, lead_time, y, x |
| `wind_u_30_0mb` | U component of wind | m s-1 | init_time, lead_time, y, x |
| `wind_u_30m` | U component of wind | m s-1 | init_time, lead_time, y, x |
| `wind_u_320m` | U component of wind | m s-1 | init_time, lead_time, y, x |
| `wind_u_50m` | U component of wind | m s-1 | init_time, lead_time, y, x |
| `wind_u_60_30mb` | U component of wind | m s-1 | init_time, lead_time, y, x |
| `wind_u_80m` | 80 metre U wind component | m s-1 | init_time, lead_time, y, x |
| `wind_u_90_60mb` | U component of wind | m s-1 | init_time, lead_time, y, x |
| `wind_u_max_wind` | U component of wind | m s-1 | init_time, lead_time, y, x |
| `wind_u_planetary_boundary_layer` | U component of wind | m s-1 | init_time, lead_time, y, x |
| `wind_u_tropopause` | U component of wind | m s-1 | init_time, lead_time, y, x |
| `wind_v_100m` | 100 metre V wind component | m s-1 | init_time, lead_time, y, x |
| `wind_v_10m` | 10 metre V wind component | m s-1 | init_time, lead_time, y, x |
| `wind_v_120_90mb` | V component of wind | m s-1 | init_time, lead_time, y, x |
| `wind_v_150_120mb` | V component of wind | m s-1 | init_time, lead_time, y, x |
| `wind_v_160m` | V component of wind | m s-1 | init_time, lead_time, y, x |
| `wind_v_180_150mb` | V component of wind | m s-1 | init_time, lead_time, y, x |
| `wind_v_30_0mb` | V component of wind | m s-1 | init_time, lead_time, y, x |
| `wind_v_30m` | V component of wind | m s-1 | init_time, lead_time, y, x |
| `wind_v_320m` | V component of wind | m s-1 | init_time, lead_time, y, x |
| `wind_v_50m` | V component of wind | m s-1 | init_time, lead_time, y, x |
| `wind_v_60_30mb` | V component of wind | m s-1 | init_time, lead_time, y, x |
| `wind_v_80m` | 80 metre V wind component | m s-1 | init_time, lead_time, y, x |
| `wind_v_90_60mb` | V component of wind | m s-1 | init_time, lead_time, y, x |
| `wind_v_max_wind` | V component of wind | m s-1 | init_time, lead_time, y, x |
| `wind_v_planetary_boundary_layer` | V component of wind | m s-1 | init_time, lead_time, y, x |
| `wind_v_tropopause` | V component of wind | m s-1 | init_time, lead_time, y, x |
| `depth_below_ground/liquid_volumetric_soil_moisture` | Liquid volumetric soil moisture (non-frozen) | 1 | init_time, lead_time, y, x, depth_below_ground |
| `depth_below_ground/soil_temperature` | Soil temperature | degree_Celsius | init_time, lead_time, y, x, depth_below_ground |
| `depth_below_ground/volumetric_soil_moisture` | Volumetric soil moisture content | 1 | init_time, lead_time, y, x, depth_below_ground |
| `height_above_mean_sea_level/temperature` | Temperature | degree_Celsius | init_time, lead_time, y, x, height_above_mean_sea_level |
| `height_above_mean_sea_level/wind_u` | U component of wind | m s-1 | init_time, lead_time, y, x, height_above_mean_sea_level |
| `height_above_mean_sea_level/wind_v` | V component of wind | m s-1 | init_time, lead_time, y, x, height_above_mean_sea_level |
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
| `pressure_level/vertical_velocity_geometric` | Vertical velocity (geometric) | m s-1 | init_time, lead_time, y, x, pressure_level |
| `pressure_level/wind_u` | U component of wind | m s-1 | init_time, lead_time, y, x, pressure_level |
| `pressure_level/wind_v` | V component of wind | m s-1 | init_time, lead_time, y, x, pressure_level |
