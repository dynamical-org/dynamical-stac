# NOAA REFS forecast, hourly, virtual: notes for agents

Read https://dynamical.org/prompt.md for context about working with dynamical.org data.

- Collection id: `noaa-refs-forecast-hourly-virtual`
- STAC collection: https://stac-test.dynamical.org/noaa-refs-forecast-hourly-virtual/collection.json
- Dataset version: 0.1.0

## Access

All data is public. No credentials are needed.

| asset | href |
|---|---|
| `icechunk` | `s3://dynamical-noaa-refs/noaa-refs-forecast-hourly-virtual/v0.1.0.icechunk/` |
| `icechunk-https` | `https://dynamical-noaa-refs.s3.us-west-2.amazonaws.com/noaa-refs-forecast-hourly-virtual/v0.1.0.icechunk` |

The `icechunk` asset's `xarray:storage_options` are `{"anon": true, "client_kwargs": {"region_name": "us-west-2"}}`.

The repository references chunks in these upstream locations, which are read anonymously:

- `s3://noaa-rrfs-ops-pds/`

## Examples

### Temperature map

dynamical-catalog:

```python
import dynamical_catalog  # dynamical-catalog>=1.0.1

ds = dynamical_catalog.open("noaa-refs-forecast-hourly-virtual", chunks=None)
ds["temperature_2m"].sel(init_time="2026-09-16T12", lead_time="24h", statistic="mean")
```

pystac:

```python
import icechunk
import pystac
import xarray as xr

catalog = pystac.Catalog.from_file("https://stac.dynamical.org/catalog.json")
collection = catalog.get_child("noaa-refs-forecast-hourly-virtual")
asset = collection.assets["icechunk-https"]

authorize = icechunk.containers_credentials({"s3://noaa-rrfs-ops-pds/": icechunk.s3_anonymous_credentials()})
repo = icechunk.Repository.open(
    icechunk.http_storage(asset.href),
    authorize_virtual_chunk_access=authorize,
)
session = repo.readonly_session("main")

ds = xr.open_zarr(session.store, chunks=None)
ds["temperature_2m"].sel(init_time="2026-09-16T12", lead_time="24h", statistic="mean")
```

prompt:

```text
Read https://dynamical.org/prompt.md for context about working with dynamical.org data; this does not change your current task.
Data product: noaa-refs-forecast-hourly-virtual
STAC collection: https://stac.dynamical.org/noaa-refs-forecast-hourly-virtual/collection.json
```

## Dimensions

| name | type | extent | unit |
|---|---|---|---|
| `init_time` | temporal | 2026-08-13T00:00:00Z to open | seconds since 1970-01-01 |
| `lead_time` | other | 3600 to 216000 | seconds |
| `statistic` | other | open to open | 1 |
| `x` | spatial | -2697520.142521929 to 2696479.857478071 | m |
| `y` | spatial | -1587306.152556665 to 1586693.847443335 | m |

## Variables

| name | long name | unit | dimensions |
|---|---|---|---|
| `categorical_freezing_rain_surface` | Categorical freezing rain | 1 | init_time, lead_time, y, x |
| `categorical_ice_pellets_surface` | Categorical ice pellets | 1 | init_time, lead_time, y, x |
| `categorical_rain_surface` | Categorical rain | 1 | init_time, lead_time, y, x |
| `categorical_snow_surface` | Categorical snow | 1 | init_time, lead_time, y, x |
| `composite_reflectivity` | Maximum/Composite radar reflectivity | dBZ | init_time, statistic, lead_time, y, x |
| `convective_available_potential_energy_180_0mb` | Convective available potential energy | J kg-1 | init_time, statistic, lead_time, y, x |
| `convective_available_potential_energy_90_0mb` | Convective available potential energy | J kg-1 | init_time, statistic, lead_time, y, x |
| `convective_available_potential_energy_surface` | Convective available potential energy | J kg-1 | init_time, statistic, lead_time, y, x |
| `convective_inhibition_180_0mb` | Convective inhibition | J kg-1 | init_time, statistic, lead_time, y, x |
| `convective_inhibition_90_0mb` | Convective inhibition | J kg-1 | init_time, statistic, lead_time, y, x |
| `convective_inhibition_surface` | Convective inhibition | J kg-1 | init_time, statistic, lead_time, y, x |
| `derived_radar_reflectivity_1000m` | Derived radar reflectivity | dBZ | init_time, statistic, lead_time, y, x |
| `dew_point_temperature_2m` | 2 metre dewpoint temperature | degree_Celsius | init_time, statistic, lead_time, y, x |
| `dew_point_temperature_2m_standard_deviation` | Standard deviation of 2 metre dewpoint temperature | K | init_time, lead_time, y, x |
| `dew_point_temperature_500hpa` | Dew point temperature | degree_Celsius | init_time, statistic, lead_time, y, x |
| `dew_point_temperature_500hpa_standard_deviation` | Standard deviation of dew point temperature | K | init_time, lead_time, y, x |
| `dew_point_temperature_700hpa` | Dew point temperature | degree_Celsius | init_time, statistic, lead_time, y, x |
| `dew_point_temperature_700hpa_standard_deviation` | Standard deviation of dew point temperature | K | init_time, lead_time, y, x |
| `dew_point_temperature_850hpa` | Dew point temperature | degree_Celsius | init_time, statistic, lead_time, y, x |
| `dew_point_temperature_850hpa_standard_deviation` | Standard deviation of dew point temperature | K | init_time, lead_time, y, x |
| `dew_point_temperature_925hpa` | Dew point temperature | degree_Celsius | init_time, statistic, lead_time, y, x |
| `dew_point_temperature_925hpa_standard_deviation` | Standard deviation of dew point temperature | K | init_time, lead_time, y, x |
| `echo_top` | Echo top | m | init_time, statistic, lead_time, y, x |
| `ensemble_agreement_scale_probability_of_total_precipitation_1_hour_surface_above_0p254` | Ensemble agreement scale probability of 1 hour total precipitation (surface) above 0.254 kg m-2 | percent | init_time, lead_time, y, x |
| `ensemble_agreement_scale_probability_of_total_precipitation_1_hour_surface_above_12p7` | Ensemble agreement scale probability of 1 hour total precipitation (surface) above 12.7 kg m-2 | percent | init_time, lead_time, y, x |
| `ensemble_agreement_scale_probability_of_total_precipitation_1_hour_surface_above_25p4` | Ensemble agreement scale probability of 1 hour total precipitation (surface) above 25.4 kg m-2 | percent | init_time, lead_time, y, x |
| `ensemble_agreement_scale_probability_of_total_precipitation_1_hour_surface_above_6p35` | Ensemble agreement scale probability of 1 hour total precipitation (surface) above 6.35 kg m-2 | percent | init_time, lead_time, y, x |
| `ensemble_agreement_scale_probability_of_total_snowfall_1_hour_surface_above_0p025` | Ensemble agreement scale probability of 1 hour total snowfall (surface) above 0.025 m | percent | init_time, lead_time, y, x |
| `ensemble_agreement_scale_probability_of_total_snowfall_1_hour_surface_above_0p076` | Ensemble agreement scale probability of 1 hour total snowfall (surface) above 0.076 m | percent | init_time, lead_time, y, x |
| `fog_liquid_water_content_0m` | Fog liquid water content | kg kg-1 | init_time, statistic, lead_time, y, x |
| `geopotential_height_0c_isotherm` | Geopotential height | m | init_time, statistic, lead_time, y, x |
| `geopotential_height_250hpa` | Geopotential height | m | init_time, statistic, lead_time, y, x |
| `geopotential_height_500hpa` | Geopotential height | m | init_time, statistic, lead_time, y, x |
| `geopotential_height_700hpa` | Geopotential height | m | init_time, statistic, lead_time, y, x |
| `geopotential_height_850hpa` | Geopotential height | m | init_time, statistic, lead_time, y, x |
| `geopotential_height_925hpa` | Geopotential height | m | init_time, statistic, lead_time, y, x |
| `geopotential_height_cloud_base` | Geopotential height | m | init_time, statistic, lead_time, y, x |
| `geopotential_height_cloud_ceiling` | Geopotential height | m | init_time, statistic, lead_time, y, x |
| `geopotential_height_surface` | Geopotential height | m | init_time, statistic, lead_time, y, x |
| `high_cloud_cover` | High cloud cover | percent | init_time, statistic, lead_time, y, x |
| `hourly_maximum_radar_reflectivity_1000m` | Hourly maximum of simulated reflectivity | dBZ | init_time, statistic, lead_time, y, x |
| `localized_probability_matched_mean_total_precipitation_1_hour_surface` | Localized probability-matched mean of total precipitation | kg m-2 | init_time, lead_time, y, x |
| `low_cloud_cover` | Low cloud cover | percent | init_time, statistic, lead_time, y, x |
| `maximum_updraft_helicity_5000_2000m` | Updraft Helicity | m2 s-2 | init_time, statistic, lead_time, y, x |
| `mean_probability_matched_mean_average_total_precipitation_1_hour_surface` | Average of the ensemble mean and probability-matched mean of total precipitation | kg m-2 | init_time, lead_time, y, x |
| `medium_cloud_cover` | Medium cloud cover | percent | init_time, statistic, lead_time, y, x |
| `neighborhood_probability_of_composite_reflectivity_above_10` | Neighborhood probability of maximum/composite radar reflectivity (entire atmosphere) above 10 dBZ | percent | init_time, lead_time, y, x |
| `neighborhood_probability_of_composite_reflectivity_above_20` | Neighborhood probability of maximum/composite radar reflectivity (entire atmosphere) above 20 dBZ | percent | init_time, lead_time, y, x |
| `neighborhood_probability_of_composite_reflectivity_above_30` | Neighborhood probability of maximum/composite radar reflectivity (entire atmosphere) above 30 dBZ | percent | init_time, lead_time, y, x |
| `neighborhood_probability_of_composite_reflectivity_above_40` | Neighborhood probability of maximum/composite radar reflectivity (entire atmosphere) above 40 dBZ | percent | init_time, lead_time, y, x |
| `neighborhood_probability_of_composite_reflectivity_above_50` | Neighborhood probability of maximum/composite radar reflectivity (entire atmosphere) above 50 dBZ | percent | init_time, lead_time, y, x |
| `neighborhood_probability_of_derived_radar_reflectivity_1000m_above_30` | Neighborhood probability of derived radar reflectivity (1000 m above ground) above 30 dBZ | percent | init_time, lead_time, y, x |
| `neighborhood_probability_of_derived_radar_reflectivity_1000m_above_40` | Neighborhood probability of derived radar reflectivity (1000 m above ground) above 40 dBZ | percent | init_time, lead_time, y, x |
| `neighborhood_probability_of_derived_radar_reflectivity_1000m_above_50` | Neighborhood probability of derived radar reflectivity (1000 m above ground) above 50 dBZ | percent | init_time, lead_time, y, x |
| `neighborhood_probability_of_echo_top_above_10668` | Neighborhood probability of echo top (entire atmosphere) above 10668 m | percent | init_time, lead_time, y, x |
| `neighborhood_probability_of_echo_top_above_12192` | Neighborhood probability of echo top (entire atmosphere) above 12192 m | percent | init_time, lead_time, y, x |
| `neighborhood_probability_of_echo_top_above_15240` | Neighborhood probability of echo top (entire atmosphere) above 15240 m | percent | init_time, lead_time, y, x |
| `neighborhood_probability_of_echo_top_above_6096` | Neighborhood probability of echo top (entire atmosphere) above 6096 m | percent | init_time, lead_time, y, x |
| `neighborhood_probability_of_echo_top_above_9144` | Neighborhood probability of echo top (entire atmosphere) above 9144 m | percent | init_time, lead_time, y, x |
| `neighborhood_probability_of_freezing_rain_1_hour_surface_above_0p254` | Neighborhood probability of 1 hour freezing rain (surface) above 0.254 kg m-2 | percent | init_time, lead_time, y, x |
| `neighborhood_probability_of_freezing_rain_1_hour_surface_above_2p54` | Neighborhood probability of 1 hour freezing rain (surface) above 2.54 kg m-2 | percent | init_time, lead_time, y, x |
| `neighborhood_probability_of_freezing_rain_1_hour_surface_above_6p35` | Neighborhood probability of 1 hour freezing rain (surface) above 6.35 kg m-2 | percent | init_time, lead_time, y, x |
| `neighborhood_probability_of_hourly_maximum_radar_reflectivity_1000m_above_40` | Neighborhood probability of hourly maximum of simulated reflectivity (1000 m above ground) above 40 dBZ | percent | init_time, lead_time, y, x |
| `neighborhood_probability_of_hourly_maximum_radar_reflectivity_1000m_above_50` | Neighborhood probability of hourly maximum of simulated reflectivity (1000 m above ground) above 50 dBZ | percent | init_time, lead_time, y, x |
| `neighborhood_probability_of_maximum_updraft_helicity_5000_2000m_above_150` | Neighborhood probability of updraft helicity (5000-2000 m above ground) above 150 m2 s-2 | percent | init_time, lead_time, y, x |
| `neighborhood_probability_of_maximum_updraft_helicity_5000_2000m_above_25` | Neighborhood probability of updraft helicity (5000-2000 m above ground) above 25 m2 s-2 | percent | init_time, lead_time, y, x |
| `neighborhood_probability_of_maximum_updraft_helicity_5000_2000m_above_75` | Neighborhood probability of updraft helicity (5000-2000 m above ground) above 75 m2 s-2 | percent | init_time, lead_time, y, x |
| `neighborhood_probability_of_precipitation_exceeding_1_hour_flash_flood_guidance_1_hour_surface` | Neighborhood probability of 1 hour precipitation above the 1 hour flash flood guidance depth | percent | init_time, lead_time, y, x |
| `neighborhood_probability_of_total_precipitation_1_hour_surface_above_12p7` | Neighborhood probability of 1 hour total precipitation (surface) above 12.7 kg m-2 | percent | init_time, lead_time, y, x |
| `neighborhood_probability_of_total_precipitation_1_hour_surface_above_25p4` | Neighborhood probability of 1 hour total precipitation (surface) above 25.4 kg m-2 | percent | init_time, lead_time, y, x |
| `neighborhood_probability_of_total_precipitation_1_hour_surface_above_50p8` | Neighborhood probability of 1 hour total precipitation (surface) above 50.8 kg m-2 | percent | init_time, lead_time, y, x |
| `neighborhood_probability_of_total_precipitation_1_hour_surface_above_76p2` | Neighborhood probability of 1 hour total precipitation (surface) above 76.2 kg m-2 | percent | init_time, lead_time, y, x |
| `neighborhood_probability_of_total_snowfall_1_hour_surface_above_0p025` | Neighborhood probability of 1 hour total snowfall (surface) above 0.025 m | percent | init_time, lead_time, y, x |
| `neighborhood_probability_of_total_snowfall_1_hour_surface_above_0p076` | Neighborhood probability of 1 hour total snowfall (surface) above 0.076 m | percent | init_time, lead_time, y, x |
| `neighborhood_probability_of_wind_speed_10m_above_10p3` | Neighborhood probability of 10 metre wind speed (10 m above ground) above 10.3 m s-1 | percent | init_time, lead_time, y, x |
| `neighborhood_probability_of_wind_speed_10m_above_15p4` | Neighborhood probability of 10 metre wind speed (10 m above ground) above 15.4 m s-1 | percent | init_time, lead_time, y, x |
| `neighborhood_probability_of_wind_speed_10m_above_18p01` | Neighborhood probability of 10 metre wind speed (10 m above ground) above 18.01 m s-1 | percent | init_time, lead_time, y, x |
| `neighborhood_probability_of_wind_speed_10m_above_20p6` | Neighborhood probability of 10 metre wind speed (10 m above ground) above 20.6 m s-1 | percent | init_time, lead_time, y, x |
| `neighborhood_probability_of_wind_speed_10m_above_25p72` | Neighborhood probability of 10 metre wind speed (10 m above ground) above 25.72 m s-1 | percent | init_time, lead_time, y, x |
| `neighborhood_probability_of_wind_speed_10m_above_30p9` | Neighborhood probability of 10 metre wind speed (10 m above ground) above 30.9 m s-1 | percent | init_time, lead_time, y, x |
| `precipitable_water_atmosphere` | Precipitable water | kg m-2 | init_time, statistic, lead_time, y, x |
| `pressure_reduced_to_mean_sea_level` | Pressure reduced to MSL | Pa | init_time, statistic, lead_time, y, x |
| `probability_matched_mean_composite_reflectivity` | Probability-matched mean of maximum/composite radar reflectivity | dBZ | init_time, lead_time, y, x |
| `probability_matched_mean_derived_radar_reflectivity_1000m` | Probability-matched mean of derived radar reflectivity | dBZ | init_time, lead_time, y, x |
| `probability_matched_mean_echo_top` | Probability-matched mean of echo top | m | init_time, lead_time, y, x |
| `probability_matched_mean_geopotential_height_surface` | Probability-matched mean of geopotential height | m | init_time, lead_time, y, x |
| `probability_matched_mean_hourly_maximum_radar_reflectivity_1000m` | Probability-matched mean of hourly maximum of simulated reflectivity | dBZ | init_time, lead_time, y, x |
| `probability_matched_mean_maximum_updraft_helicity_5000_2000m` | Probability-matched mean of updraft helicity | m2 s-2 | init_time, lead_time, y, x |
| `probability_matched_mean_total_precipitation_1_hour_surface` | Probability-matched mean of total precipitation | kg m-2 | init_time, lead_time, y, x |
| `probability_of_categorical_freezing_rain_surface` | Probability of categorical freezing rain (surface) | percent | init_time, lead_time, y, x |
| `probability_of_categorical_ice_pellets_surface` | Probability of categorical ice pellets (surface) | percent | init_time, lead_time, y, x |
| `probability_of_categorical_rain_surface` | Probability of categorical rain (surface) | percent | init_time, lead_time, y, x |
| `probability_of_categorical_snow_surface` | Probability of categorical snow (surface) | percent | init_time, lead_time, y, x |
| `probability_of_clear_air_turbulence_175hpa_at_least_1_below_2` | Probability of clear air turbulence (175 mb) at least 1 and below 2 | percent | init_time, lead_time, y, x |
| `probability_of_clear_air_turbulence_175hpa_at_least_2_below_3` | Probability of clear air turbulence (175 mb) at least 2 and below 3 | percent | init_time, lead_time, y, x |
| `probability_of_clear_air_turbulence_175hpa_at_least_3` | Probability of clear air turbulence (175 mb) at least 3 | percent | init_time, lead_time, y, x |
| `probability_of_clear_air_turbulence_200hpa_at_least_1_below_2` | Probability of clear air turbulence (200 mb) at least 1 and below 2 | percent | init_time, lead_time, y, x |
| `probability_of_clear_air_turbulence_200hpa_at_least_2_below_3` | Probability of clear air turbulence (200 mb) at least 2 and below 3 | percent | init_time, lead_time, y, x |
| `probability_of_clear_air_turbulence_200hpa_at_least_3` | Probability of clear air turbulence (200 mb) at least 3 | percent | init_time, lead_time, y, x |
| `probability_of_clear_air_turbulence_225hpa_at_least_1_below_2` | Probability of clear air turbulence (225 mb) at least 1 and below 2 | percent | init_time, lead_time, y, x |
| `probability_of_clear_air_turbulence_225hpa_at_least_2_below_3` | Probability of clear air turbulence (225 mb) at least 2 and below 3 | percent | init_time, lead_time, y, x |
| `probability_of_clear_air_turbulence_225hpa_at_least_3` | Probability of clear air turbulence (225 mb) at least 3 | percent | init_time, lead_time, y, x |
| `probability_of_clear_air_turbulence_275hpa_at_least_1_below_2` | Probability of clear air turbulence (275 mb) at least 1 and below 2 | percent | init_time, lead_time, y, x |
| `probability_of_clear_air_turbulence_275hpa_at_least_2_below_3` | Probability of clear air turbulence (275 mb) at least 2 and below 3 | percent | init_time, lead_time, y, x |
| `probability_of_clear_air_turbulence_275hpa_at_least_3` | Probability of clear air turbulence (275 mb) at least 3 | percent | init_time, lead_time, y, x |
| `probability_of_clear_air_turbulence_300hpa_at_least_1_below_2` | Probability of clear air turbulence (300 mb) at least 1 and below 2 | percent | init_time, lead_time, y, x |
| `probability_of_clear_air_turbulence_300hpa_at_least_2_below_3` | Probability of clear air turbulence (300 mb) at least 2 and below 3 | percent | init_time, lead_time, y, x |
| `probability_of_clear_air_turbulence_300hpa_at_least_3` | Probability of clear air turbulence (300 mb) at least 3 | percent | init_time, lead_time, y, x |
| `probability_of_clear_air_turbulence_350hpa_at_least_1_below_2` | Probability of clear air turbulence (350 mb) at least 1 and below 2 | percent | init_time, lead_time, y, x |
| `probability_of_clear_air_turbulence_350hpa_at_least_2_below_3` | Probability of clear air turbulence (350 mb) at least 2 and below 3 | percent | init_time, lead_time, y, x |
| `probability_of_clear_air_turbulence_350hpa_at_least_3` | Probability of clear air turbulence (350 mb) at least 3 | percent | init_time, lead_time, y, x |
| `probability_of_clear_air_turbulence_425hpa_at_least_1_below_2` | Probability of clear air turbulence (425 mb) at least 1 and below 2 | percent | init_time, lead_time, y, x |
| `probability_of_clear_air_turbulence_425hpa_at_least_2_below_3` | Probability of clear air turbulence (425 mb) at least 2 and below 3 | percent | init_time, lead_time, y, x |
| `probability_of_clear_air_turbulence_425hpa_at_least_3` | Probability of clear air turbulence (425 mb) at least 3 | percent | init_time, lead_time, y, x |
| `probability_of_clear_air_turbulence_450hpa_at_least_1_below_2` | Probability of clear air turbulence (450 mb) at least 1 and below 2 | percent | init_time, lead_time, y, x |
| `probability_of_clear_air_turbulence_450hpa_at_least_2_below_3` | Probability of clear air turbulence (450 mb) at least 2 and below 3 | percent | init_time, lead_time, y, x |
| `probability_of_clear_air_turbulence_450hpa_at_least_3` | Probability of clear air turbulence (450 mb) at least 3 | percent | init_time, lead_time, y, x |
| `probability_of_clear_air_turbulence_525hpa_at_least_1_below_2` | Probability of clear air turbulence (525 mb) at least 1 and below 2 | percent | init_time, lead_time, y, x |
| `probability_of_clear_air_turbulence_525hpa_at_least_2_below_3` | Probability of clear air turbulence (525 mb) at least 2 and below 3 | percent | init_time, lead_time, y, x |
| `probability_of_clear_air_turbulence_525hpa_at_least_3` | Probability of clear air turbulence (525 mb) at least 3 | percent | init_time, lead_time, y, x |
| `probability_of_convective_available_potential_energy_90_0mb_above_1000` | Probability of convective available potential energy (90-0 mb above ground) above 1000 J kg-1 | percent | init_time, lead_time, y, x |
| `probability_of_convective_available_potential_energy_90_0mb_above_1500` | Probability of convective available potential energy (90-0 mb above ground) above 1500 J kg-1 | percent | init_time, lead_time, y, x |
| `probability_of_convective_available_potential_energy_90_0mb_above_2000` | Probability of convective available potential energy (90-0 mb above ground) above 2000 J kg-1 | percent | init_time, lead_time, y, x |
| `probability_of_convective_available_potential_energy_90_0mb_above_3000` | Probability of convective available potential energy (90-0 mb above ground) above 3000 J kg-1 | percent | init_time, lead_time, y, x |
| `probability_of_convective_available_potential_energy_90_0mb_above_500` | Probability of convective available potential energy (90-0 mb above ground) above 500 J kg-1 | percent | init_time, lead_time, y, x |
| `probability_of_convective_inhibition_90_0mb_below_minus_100` | Probability of convective inhibition (90-0 mb above ground) below -100 J kg-1 | percent | init_time, lead_time, y, x |
| `probability_of_convective_inhibition_90_0mb_below_minus_400` | Probability of convective inhibition (90-0 mb above ground) below -400 J kg-1 | percent | init_time, lead_time, y, x |
| `probability_of_convective_inhibition_90_0mb_below_minus_50` | Probability of convective inhibition (90-0 mb above ground) below -50 J kg-1 | percent | init_time, lead_time, y, x |
| `probability_of_dew_point_temperature_2m_above_283p15` | Probability of 2 metre dewpoint temperature (2 m above ground) above 283.15 K | percent | init_time, lead_time, y, x |
| `probability_of_dew_point_temperature_2m_above_285p93` | Probability of 2 metre dewpoint temperature (2 m above ground) above 285.93 K | percent | init_time, lead_time, y, x |
| `probability_of_dew_point_temperature_2m_above_288p71` | Probability of 2 metre dewpoint temperature (2 m above ground) above 288.71 K | percent | init_time, lead_time, y, x |
| `probability_of_dew_point_temperature_2m_above_291p48` | Probability of 2 metre dewpoint temperature (2 m above ground) above 291.48 K | percent | init_time, lead_time, y, x |
| `probability_of_dew_point_temperature_2m_above_294p26` | Probability of 2 metre dewpoint temperature (2 m above ground) above 294.26 K | percent | init_time, lead_time, y, x |
| `probability_of_flight_category_surface_at_least_1_below_2` | Probability of flight category (surface) at least 1 and below 2 | percent | init_time, lead_time, y, x |
| `probability_of_flight_category_surface_at_least_2_below_3` | Probability of flight category (surface) at least 2 and below 3 | percent | init_time, lead_time, y, x |
| `probability_of_flight_category_surface_at_least_3_below_4` | Probability of flight category (surface) at least 3 and below 4 | percent | init_time, lead_time, y, x |
| `probability_of_flight_category_surface_at_least_4` | Probability of flight category (surface) at least 4 | percent | init_time, lead_time, y, x |
| `probability_of_fog_liquid_water_content_0m_above_0p016` | Probability of fog liquid water content (0 m above ground) above 0.016 g kg-1 | percent | init_time, lead_time, y, x |
| `probability_of_fog_liquid_water_content_0m_above_0p036` | Probability of fog liquid water content (0 m above ground) above 0.036 g kg-1 | percent | init_time, lead_time, y, x |
| `probability_of_fog_liquid_water_content_0m_above_0p103` | Probability of fog liquid water content (0 m above ground) above 0.103 g kg-1 | percent | init_time, lead_time, y, x |
| `probability_of_geopotential_height_cloud_ceiling_below_1372` | Probability of geopotential height (cloud ceiling) below 1372 m | percent | init_time, lead_time, y, x |
| `probability_of_geopotential_height_cloud_ceiling_below_152p4` | Probability of geopotential height (cloud ceiling) below 152.4 m | percent | init_time, lead_time, y, x |
| `probability_of_geopotential_height_cloud_ceiling_below_1830` | Probability of geopotential height (cloud ceiling) below 1830 m | percent | init_time, lead_time, y, x |
| `probability_of_geopotential_height_cloud_ceiling_below_305` | Probability of geopotential height (cloud ceiling) below 305 m | percent | init_time, lead_time, y, x |
| `probability_of_geopotential_height_cloud_ceiling_below_3050` | Probability of geopotential height (cloud ceiling) below 3050 m | percent | init_time, lead_time, y, x |
| `probability_of_geopotential_height_cloud_ceiling_below_610` | Probability of geopotential height (cloud ceiling) below 610 m | percent | init_time, lead_time, y, x |
| `probability_of_geopotential_height_cloud_ceiling_below_915` | Probability of geopotential height (cloud ceiling) below 915 m | percent | init_time, lead_time, y, x |
| `probability_of_icing_1000hpa_at_least_1` | Probability of icing (1000 mb) at least 1 | percent | init_time, lead_time, y, x |
| `probability_of_icing_400hpa_at_least_1` | Probability of icing (400 mb) at least 1 | percent | init_time, lead_time, y, x |
| `probability_of_icing_500hpa_at_least_1` | Probability of icing (500 mb) at least 1 | percent | init_time, lead_time, y, x |
| `probability_of_icing_575hpa_at_least_1` | Probability of icing (575 mb) at least 1 | percent | init_time, lead_time, y, x |
| `probability_of_icing_650hpa_at_least_1` | Probability of icing (650 mb) at least 1 | percent | init_time, lead_time, y, x |
| `probability_of_icing_725hpa_at_least_1` | Probability of icing (725 mb) at least 1 | percent | init_time, lead_time, y, x |
| `probability_of_icing_800hpa_at_least_1` | Probability of icing (800 mb) at least 1 | percent | init_time, lead_time, y, x |
| `probability_of_icing_900hpa_at_least_1` | Probability of icing (900 mb) at least 1 | percent | init_time, lead_time, y, x |
| `probability_of_lightning_atmosphere_above_0p08` | Probability of lightning (entire atmosphere) above 0.08 | percent | init_time, lead_time, y, x |
| `probability_of_maximum_upward_vertical_velocity_100_1000mb_above_1` | Probability of maximum upward vertical velocity (100-1000 mb) above 1 m s-1 | percent | init_time, lead_time, y, x |
| `probability_of_maximum_upward_vertical_velocity_100_1000mb_above_10` | Probability of maximum upward vertical velocity (100-1000 mb) above 10 m s-1 | percent | init_time, lead_time, y, x |
| `probability_of_maximum_upward_vertical_velocity_100_1000mb_above_20` | Probability of maximum upward vertical velocity (100-1000 mb) above 20 m s-1 | percent | init_time, lead_time, y, x |
| `probability_of_precipitable_water_atmosphere_above_25` | Probability of precipitable water (entire atmosphere) above 25 kg m-2 | percent | init_time, lead_time, y, x |
| `probability_of_precipitable_water_atmosphere_above_37p5` | Probability of precipitable water (entire atmosphere) above 37.5 kg m-2 | percent | init_time, lead_time, y, x |
| `probability_of_precipitable_water_atmosphere_above_50` | Probability of precipitable water (entire atmosphere) above 50 kg m-2 | percent | init_time, lead_time, y, x |
| `probability_of_storm_relative_helicity_3000_0m_above_100` | Probability of storm relative helicity (3000-0 m above ground) above 100 m2 s-2 | percent | init_time, lead_time, y, x |
| `probability_of_storm_relative_helicity_3000_0m_above_200` | Probability of storm relative helicity (3000-0 m above ground) above 200 m2 s-2 | percent | init_time, lead_time, y, x |
| `probability_of_storm_relative_helicity_3000_0m_above_400` | Probability of storm relative helicity (3000-0 m above ground) above 400 m2 s-2 | percent | init_time, lead_time, y, x |
| `probability_of_temperature_2m_below_273p15` | Probability of 2 metre temperature (2 m above ground) below 273.15 K | percent | init_time, lead_time, y, x |
| `probability_of_vertical_wind_shear_0_6000m_above_10p3` | Probability of vertical wind shear (0-6000 m above ground) above 10.3 m s-1 | percent | init_time, lead_time, y, x |
| `probability_of_vertical_wind_shear_0_6000m_above_15p4` | Probability of vertical wind shear (0-6000 m above ground) above 15.4 m s-1 | percent | init_time, lead_time, y, x |
| `probability_of_vertical_wind_shear_0_6000m_above_20p6` | Probability of vertical wind shear (0-6000 m above ground) above 20.6 m s-1 | percent | init_time, lead_time, y, x |
| `probability_of_vertical_wind_shear_0_6000m_above_25p7` | Probability of vertical wind shear (0-6000 m above ground) above 25.7 m s-1 | percent | init_time, lead_time, y, x |
| `probability_of_vertical_wind_shear_0_609m_above_10p3` | Probability of vertical wind shear (0-609 m above ground) above 10.3 m s-1 | percent | init_time, lead_time, y, x |
| `probability_of_vertical_wind_shear_0_609m_above_20` | Probability of vertical wind shear (0-609 m above ground) above 20 m s-1 | percent | init_time, lead_time, y, x |
| `probability_of_visibility_surface_below_1600` | Probability of visibility (surface) below 1600 m | percent | init_time, lead_time, y, x |
| `probability_of_visibility_surface_below_3200` | Probability of visibility (surface) below 3200 m | percent | init_time, lead_time, y, x |
| `probability_of_visibility_surface_below_400` | Probability of visibility (surface) below 400 m | percent | init_time, lead_time, y, x |
| `probability_of_visibility_surface_below_4829` | Probability of visibility (surface) below 4829 m | percent | init_time, lead_time, y, x |
| `probability_of_visibility_surface_below_6400` | Probability of visibility (surface) below 6400 m | percent | init_time, lead_time, y, x |
| `probability_of_visibility_surface_below_800` | Probability of visibility (surface) below 800 m | percent | init_time, lead_time, y, x |
| `probability_of_visibility_surface_below_8049` | Probability of visibility (surface) below 8049 m | percent | init_time, lead_time, y, x |
| `probability_of_wind_speed_10m_at_least_9_and_relative_humidity_2m_at_most_20` | Probability of 10 m wind speed at least 9 m s-1 and 2 m relative humidity at most 20 percent | percent | init_time, lead_time, y, x |
| `probability_of_wind_speed_250hpa_above_10p3` | Probability of wind speed (250 mb) above 10.3 m s-1 | percent | init_time, lead_time, y, x |
| `probability_of_wind_speed_250hpa_above_20p6` | Probability of wind speed (250 mb) above 20.6 m s-1 | percent | init_time, lead_time, y, x |
| `probability_of_wind_speed_250hpa_above_30p9` | Probability of wind speed (250 mb) above 30.9 m s-1 | percent | init_time, lead_time, y, x |
| `probability_of_wind_speed_250hpa_above_41p2` | Probability of wind speed (250 mb) above 41.2 m s-1 | percent | init_time, lead_time, y, x |
| `probability_of_wind_speed_250hpa_above_51p5` | Probability of wind speed (250 mb) above 51.5 m s-1 | percent | init_time, lead_time, y, x |
| `probability_of_wind_speed_550hpa_above_10p3` | Probability of wind speed (550 mb) above 10.3 m s-1 | percent | init_time, lead_time, y, x |
| `probability_of_wind_speed_550hpa_above_20p6` | Probability of wind speed (550 mb) above 20.6 m s-1 | percent | init_time, lead_time, y, x |
| `probability_of_wind_speed_550hpa_above_30p9` | Probability of wind speed (550 mb) above 30.9 m s-1 | percent | init_time, lead_time, y, x |
| `probability_of_wind_speed_550hpa_above_41p2` | Probability of wind speed (550 mb) above 41.2 m s-1 | percent | init_time, lead_time, y, x |
| `probability_of_wind_speed_550hpa_above_51p5` | Probability of wind speed (550 mb) above 51.5 m s-1 | percent | init_time, lead_time, y, x |
| `probability_of_wind_speed_80m_above_10p3` | Probability of 80 metre wind speed (80 m above ground) above 10.3 m s-1 | percent | init_time, lead_time, y, x |
| `probability_of_wind_speed_80m_above_15p4` | Probability of 80 metre wind speed (80 m above ground) above 15.4 m s-1 | percent | init_time, lead_time, y, x |
| `probability_of_wind_speed_80m_above_20p6` | Probability of 80 metre wind speed (80 m above ground) above 20.6 m s-1 | percent | init_time, lead_time, y, x |
| `probability_of_wind_speed_850_300mb_below_5` | Probability of wind speed (850-300 mb) below 5 m s-1 | percent | init_time, lead_time, y, x |
| `probability_of_wind_speed_850hpa_above_10p3` | Probability of wind speed (850 mb) above 10.3 m s-1 | percent | init_time, lead_time, y, x |
| `probability_of_wind_speed_850hpa_above_20p6` | Probability of wind speed (850 mb) above 20.6 m s-1 | percent | init_time, lead_time, y, x |
| `probability_of_wind_speed_850hpa_above_30p9` | Probability of wind speed (850 mb) above 30.9 m s-1 | percent | init_time, lead_time, y, x |
| `probability_of_wind_speed_850hpa_above_41p2` | Probability of wind speed (850 mb) above 41.2 m s-1 | percent | init_time, lead_time, y, x |
| `probability_of_wind_speed_850hpa_above_51p5` | Probability of wind speed (850 mb) above 51.5 m s-1 | percent | init_time, lead_time, y, x |
| `relative_humidity_700hpa` | Relative humidity | percent | init_time, statistic, lead_time, y, x |
| `snowfall_water_equivalent_1_hour_surface` | Snowfall water equivalent | kg m-2 | init_time, statistic, lead_time, y, x |
| `soil_temperature_0m` | Soil temperature | degree_Celsius | init_time, statistic, lead_time, y, x |
| `soil_temperature_0m_standard_deviation` | Standard deviation of soil temperature | K | init_time, lead_time, y, x |
| `storm_relative_helicity_3000_0m` | Storm relative helicity | m2 s-2 | init_time, statistic, lead_time, y, x |
| `temperature_250hpa` | Temperature | degree_Celsius | init_time, statistic, lead_time, y, x |
| `temperature_250hpa_standard_deviation` | Standard deviation of temperature | K | init_time, lead_time, y, x |
| `temperature_2m` | 2 metre temperature | degree_Celsius | init_time, statistic, lead_time, y, x |
| `temperature_2m_standard_deviation` | Standard deviation of 2 metre temperature | K | init_time, lead_time, y, x |
| `temperature_500hpa` | Temperature | degree_Celsius | init_time, statistic, lead_time, y, x |
| `temperature_500hpa_standard_deviation` | Standard deviation of temperature | K | init_time, lead_time, y, x |
| `temperature_700hpa` | Temperature | degree_Celsius | init_time, statistic, lead_time, y, x |
| `temperature_700hpa_standard_deviation` | Standard deviation of temperature | K | init_time, lead_time, y, x |
| `temperature_850hpa` | Temperature | degree_Celsius | init_time, statistic, lead_time, y, x |
| `temperature_850hpa_standard_deviation` | Standard deviation of temperature | K | init_time, lead_time, y, x |
| `temperature_925hpa` | Temperature | degree_Celsius | init_time, statistic, lead_time, y, x |
| `temperature_925hpa_standard_deviation` | Standard deviation of temperature | K | init_time, lead_time, y, x |
| `temperature_surface` | Skin temperature | degree_Celsius | init_time, statistic, lead_time, y, x |
| `temperature_surface_standard_deviation` | Standard deviation of skin temperature | K | init_time, lead_time, y, x |
| `total_cloud_cover_atmosphere` | Total cloud cover | percent | init_time, statistic, lead_time, y, x |
| `total_precipitation_1_hour_surface` | Total precipitation | kg m-2 | init_time, statistic, lead_time, y, x |
| `total_snowfall_1_hour_surface` | Total snowfall | m | init_time, statistic, lead_time, y, x |
| `vertical_velocity_geometric_700_500mb` | Vertical velocity (geometric) | m s-1 | init_time, statistic, lead_time, y, x |
| `vertical_velocity_geometric_700hpa` | Vertical velocity (geometric) | m s-1 | init_time, statistic, lead_time, y, x |
| `vertical_wind_shear_0_6000m` | Vertical wind shear | m s-1 | init_time, statistic, lead_time, y, x |
| `vertical_wind_shear_0_609m` | Vertical wind shear | m s-1 | init_time, statistic, lead_time, y, x |
| `visibility_surface` | Visibility | m | init_time, statistic, lead_time, y, x |
| `volumetric_soil_moisture_0m` | Volumetric soil moisture content | 1 | init_time, statistic, lead_time, y, x |
| `wind_speed_10m` | 10 metre wind speed | m s-1 | init_time, statistic, lead_time, y, x |
| `wind_speed_250hpa` | Wind speed | m s-1 | init_time, statistic, lead_time, y, x |
| `wind_speed_550hpa` | Wind speed | m s-1 | init_time, statistic, lead_time, y, x |
| `wind_speed_80m` | 80 metre wind speed | m s-1 | init_time, statistic, lead_time, y, x |
| `wind_speed_850hpa` | Wind speed | m s-1 | init_time, statistic, lead_time, y, x |
| `wind_speed_925hpa` | Wind speed | m s-1 | init_time, statistic, lead_time, y, x |
| `wind_u_10m` | 10 metre U wind component | m s-1 | init_time, statistic, lead_time, y, x |
| `wind_u_250hpa` | U component of wind | m s-1 | init_time, statistic, lead_time, y, x |
| `wind_u_500hpa` | U component of wind | m s-1 | init_time, statistic, lead_time, y, x |
| `wind_u_550hpa` | U component of wind | m s-1 | init_time, statistic, lead_time, y, x |
| `wind_u_700hpa` | U component of wind | m s-1 | init_time, statistic, lead_time, y, x |
| `wind_u_850hpa` | U component of wind | m s-1 | init_time, statistic, lead_time, y, x |
| `wind_u_925hpa` | U component of wind | m s-1 | init_time, statistic, lead_time, y, x |
| `wind_v_10m` | 10 metre V wind component | m s-1 | init_time, statistic, lead_time, y, x |
| `wind_v_250hpa` | V component of wind | m s-1 | init_time, statistic, lead_time, y, x |
| `wind_v_500hpa` | V component of wind | m s-1 | init_time, statistic, lead_time, y, x |
| `wind_v_550hpa` | V component of wind | m s-1 | init_time, statistic, lead_time, y, x |
| `wind_v_700hpa` | V component of wind | m s-1 | init_time, statistic, lead_time, y, x |
| `wind_v_850hpa` | V component of wind | m s-1 | init_time, statistic, lead_time, y, x |
| `wind_v_925hpa` | V component of wind | m s-1 | init_time, statistic, lead_time, y, x |
