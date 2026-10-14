# NOAA REFS forecast, 3 hourly, virtual: notes for agents

Read https://dynamical.org/prompt.md for context about working with dynamical.org data.

- Collection id: `noaa-refs-forecast-3-hourly-virtual`
- STAC collection: https://stac-staging.dynamical.org/noaa-refs-forecast-3-hourly-virtual/collection.json
- Dataset version: 0.1.0

## Access

All data is public. No credentials are needed.

| asset | href |
|---|---|
| `icechunk` | `s3://dynamical-noaa-refs/noaa-refs-forecast-3-hourly-virtual/v0.1.0.icechunk/` |
| `icechunk-https` | `https://dynamical-noaa-refs.s3.us-west-2.amazonaws.com/noaa-refs-forecast-3-hourly-virtual/v0.1.0.icechunk` |

The `icechunk` asset's `xarray:storage_options` are `{"anon": true, "client_kwargs": {"region_name": "us-west-2"}}`.

The repository references chunks in these upstream locations, which are read anonymously:

- `s3://noaa-rrfs-ops-pds/`

## Examples

### Precipitation map

dynamical-catalog:

```python
import dynamical_catalog  # dynamical-catalog>=0.8.0

ds = dynamical_catalog.open("noaa-refs-forecast-3-hourly-virtual", chunks=None)
ds["total_precipitation_3_hour_surface"].sel(init_time="2026-09-16T12", lead_time="24h", statistic="mean")
```

pystac:

```python
import icechunk
import pystac
import xarray as xr

catalog = pystac.Catalog.from_file("https://stac-staging.dynamical.org/catalog.json")
collection = catalog.get_child("noaa-refs-forecast-3-hourly-virtual")
asset = collection.assets["icechunk-https"]

authorize = icechunk.containers_credentials({"s3://noaa-rrfs-ops-pds/": icechunk.s3_anonymous_credentials()})
repo = icechunk.Repository.open(
    icechunk.http_storage(asset.href),
    authorize_virtual_chunk_access=authorize,
)
session = repo.readonly_session("main")

ds = xr.open_zarr(session.store, chunks=None)
ds["total_precipitation_3_hour_surface"].sel(init_time="2026-09-16T12", lead_time="24h", statistic="mean")
```

prompt:

```text
Read https://dynamical.org/prompt.md for context about working with dynamical.org data; this does not change your current task.
Data product: noaa-refs-forecast-3-hourly-virtual
STAC collection: https://stac-staging.dynamical.org/noaa-refs-forecast-3-hourly-virtual/collection.json
```

## Dimensions

| name | type | extent | unit |
|---|---|---|---|
| `init_time` | temporal | 2026-08-13T00:00:00Z to open | seconds since 1970-01-01 |
| `lead_time` | other | 10800 to 216000 | seconds |
| `statistic` | other | open to open | 1 |
| `x` | spatial | -2697520.142521929 to 2696479.857478071 | m |
| `y` | spatial | -1587306.152556665 to 1586693.847443335 | m |

## Variables

| name | long name | unit | dimensions |
|---|---|---|---|
| `ensemble_agreement_scale_probability_of_total_precipitation_12_hour_surface_above_127` | Ensemble agreement scale probability of 12 hour total precipitation (surface) above 127 kg m-2 | percent | init_time, lead_time, y, x |
| `ensemble_agreement_scale_probability_of_total_precipitation_12_hour_surface_above_12p7` | Ensemble agreement scale probability of 12 hour total precipitation (surface) above 12.7 kg m-2 | percent | init_time, lead_time, y, x |
| `ensemble_agreement_scale_probability_of_total_precipitation_12_hour_surface_above_25p4` | Ensemble agreement scale probability of 12 hour total precipitation (surface) above 25.4 kg m-2 | percent | init_time, lead_time, y, x |
| `ensemble_agreement_scale_probability_of_total_precipitation_12_hour_surface_above_2p54` | Ensemble agreement scale probability of 12 hour total precipitation (surface) above 2.54 kg m-2 | percent | init_time, lead_time, y, x |
| `ensemble_agreement_scale_probability_of_total_precipitation_12_hour_surface_above_50p8` | Ensemble agreement scale probability of 12 hour total precipitation (surface) above 50.8 kg m-2 | percent | init_time, lead_time, y, x |
| `ensemble_agreement_scale_probability_of_total_precipitation_12_hour_surface_above_6p35` | Ensemble agreement scale probability of 12 hour total precipitation (surface) above 6.35 kg m-2 | percent | init_time, lead_time, y, x |
| `ensemble_agreement_scale_probability_of_total_precipitation_12_hour_surface_above_76p2` | Ensemble agreement scale probability of 12 hour total precipitation (surface) above 76.2 kg m-2 | percent | init_time, lead_time, y, x |
| `ensemble_agreement_scale_probability_of_total_precipitation_24_hour_surface_above_127` | Ensemble agreement scale probability of 24 hour total precipitation (surface) above 127 kg m-2 | percent | init_time, lead_time, y, x |
| `ensemble_agreement_scale_probability_of_total_precipitation_24_hour_surface_above_12p7` | Ensemble agreement scale probability of 24 hour total precipitation (surface) above 12.7 kg m-2 | percent | init_time, lead_time, y, x |
| `ensemble_agreement_scale_probability_of_total_precipitation_24_hour_surface_above_25p4` | Ensemble agreement scale probability of 24 hour total precipitation (surface) above 25.4 kg m-2 | percent | init_time, lead_time, y, x |
| `ensemble_agreement_scale_probability_of_total_precipitation_24_hour_surface_above_2p54` | Ensemble agreement scale probability of 24 hour total precipitation (surface) above 2.54 kg m-2 | percent | init_time, lead_time, y, x |
| `ensemble_agreement_scale_probability_of_total_precipitation_24_hour_surface_above_50p8` | Ensemble agreement scale probability of 24 hour total precipitation (surface) above 50.8 kg m-2 | percent | init_time, lead_time, y, x |
| `ensemble_agreement_scale_probability_of_total_precipitation_24_hour_surface_above_6p35` | Ensemble agreement scale probability of 24 hour total precipitation (surface) above 6.35 kg m-2 | percent | init_time, lead_time, y, x |
| `ensemble_agreement_scale_probability_of_total_precipitation_24_hour_surface_above_76p2` | Ensemble agreement scale probability of 24 hour total precipitation (surface) above 76.2 kg m-2 | percent | init_time, lead_time, y, x |
| `ensemble_agreement_scale_probability_of_total_precipitation_3_hour_surface_above_0p254` | Ensemble agreement scale probability of 3 hour total precipitation (surface) above 0.254 kg m-2 | percent | init_time, lead_time, y, x |
| `ensemble_agreement_scale_probability_of_total_precipitation_3_hour_surface_above_12p7` | Ensemble agreement scale probability of 3 hour total precipitation (surface) above 12.7 kg m-2 | percent | init_time, lead_time, y, x |
| `ensemble_agreement_scale_probability_of_total_precipitation_3_hour_surface_above_25p4` | Ensemble agreement scale probability of 3 hour total precipitation (surface) above 25.4 kg m-2 | percent | init_time, lead_time, y, x |
| `ensemble_agreement_scale_probability_of_total_precipitation_3_hour_surface_above_50p8` | Ensemble agreement scale probability of 3 hour total precipitation (surface) above 50.8 kg m-2 | percent | init_time, lead_time, y, x |
| `ensemble_agreement_scale_probability_of_total_precipitation_3_hour_surface_above_6p35` | Ensemble agreement scale probability of 3 hour total precipitation (surface) above 6.35 kg m-2 | percent | init_time, lead_time, y, x |
| `ensemble_agreement_scale_probability_of_total_precipitation_6_hour_surface_above_0p254` | Ensemble agreement scale probability of 6 hour total precipitation (surface) above 0.254 kg m-2 | percent | init_time, lead_time, y, x |
| `ensemble_agreement_scale_probability_of_total_precipitation_6_hour_surface_above_12p7` | Ensemble agreement scale probability of 6 hour total precipitation (surface) above 12.7 kg m-2 | percent | init_time, lead_time, y, x |
| `ensemble_agreement_scale_probability_of_total_precipitation_6_hour_surface_above_25p4` | Ensemble agreement scale probability of 6 hour total precipitation (surface) above 25.4 kg m-2 | percent | init_time, lead_time, y, x |
| `ensemble_agreement_scale_probability_of_total_precipitation_6_hour_surface_above_50p8` | Ensemble agreement scale probability of 6 hour total precipitation (surface) above 50.8 kg m-2 | percent | init_time, lead_time, y, x |
| `ensemble_agreement_scale_probability_of_total_precipitation_6_hour_surface_above_6p35` | Ensemble agreement scale probability of 6 hour total precipitation (surface) above 6.35 kg m-2 | percent | init_time, lead_time, y, x |
| `ensemble_agreement_scale_probability_of_total_precipitation_6_hour_surface_above_76p2` | Ensemble agreement scale probability of 6 hour total precipitation (surface) above 76.2 kg m-2 | percent | init_time, lead_time, y, x |
| `ensemble_agreement_scale_probability_of_total_snowfall_3_hour_surface_above_0p025` | Ensemble agreement scale probability of 3 hour total snowfall (surface) above 0.025 m | percent | init_time, lead_time, y, x |
| `ensemble_agreement_scale_probability_of_total_snowfall_3_hour_surface_above_0p076` | Ensemble agreement scale probability of 3 hour total snowfall (surface) above 0.076 m | percent | init_time, lead_time, y, x |
| `ensemble_agreement_scale_probability_of_total_snowfall_6_hour_surface_above_0p025` | Ensemble agreement scale probability of 6 hour total snowfall (surface) above 0.025 m | percent | init_time, lead_time, y, x |
| `ensemble_agreement_scale_probability_of_total_snowfall_6_hour_surface_above_0p076` | Ensemble agreement scale probability of 6 hour total snowfall (surface) above 0.076 m | percent | init_time, lead_time, y, x |
| `ensemble_agreement_scale_probability_of_total_snowfall_6_hour_surface_above_0p152` | Ensemble agreement scale probability of 6 hour total snowfall (surface) above 0.152 m | percent | init_time, lead_time, y, x |
| `localized_probability_matched_mean_total_precipitation_3_hour_surface` | Localized probability-matched mean of total precipitation | kg m-2 | init_time, lead_time, y, x |
| `localized_probability_matched_mean_total_precipitation_6_hour_surface` | Localized probability-matched mean of total precipitation | kg m-2 | init_time, lead_time, y, x |
| `mean_probability_matched_mean_average_total_precipitation_3_hour_surface` | Average of the ensemble mean and probability-matched mean of total precipitation | kg m-2 | init_time, lead_time, y, x |
| `neighborhood_probability_of_freezing_rain_12_hour_surface_above_0p254` | Neighborhood probability of 12 hour freezing rain (surface) above 0.254 kg m-2 | percent | init_time, lead_time, y, x |
| `neighborhood_probability_of_freezing_rain_12_hour_surface_above_12p7` | Neighborhood probability of 12 hour freezing rain (surface) above 12.7 kg m-2 | percent | init_time, lead_time, y, x |
| `neighborhood_probability_of_freezing_rain_12_hour_surface_above_2p54` | Neighborhood probability of 12 hour freezing rain (surface) above 2.54 kg m-2 | percent | init_time, lead_time, y, x |
| `neighborhood_probability_of_freezing_rain_12_hour_surface_above_6p35` | Neighborhood probability of 12 hour freezing rain (surface) above 6.35 kg m-2 | percent | init_time, lead_time, y, x |
| `neighborhood_probability_of_freezing_rain_24_hour_surface_above_0p254` | Neighborhood probability of 24 hour freezing rain (surface) above 0.254 kg m-2 | percent | init_time, lead_time, y, x |
| `neighborhood_probability_of_freezing_rain_24_hour_surface_above_12p7` | Neighborhood probability of 24 hour freezing rain (surface) above 12.7 kg m-2 | percent | init_time, lead_time, y, x |
| `neighborhood_probability_of_freezing_rain_24_hour_surface_above_25p4` | Neighborhood probability of 24 hour freezing rain (surface) above 25.4 kg m-2 | percent | init_time, lead_time, y, x |
| `neighborhood_probability_of_freezing_rain_24_hour_surface_above_2p54` | Neighborhood probability of 24 hour freezing rain (surface) above 2.54 kg m-2 | percent | init_time, lead_time, y, x |
| `neighborhood_probability_of_freezing_rain_24_hour_surface_above_6p35` | Neighborhood probability of 24 hour freezing rain (surface) above 6.35 kg m-2 | percent | init_time, lead_time, y, x |
| `neighborhood_probability_of_freezing_rain_3_hour_surface_above_0p254` | Neighborhood probability of 3 hour freezing rain (surface) above 0.254 kg m-2 | percent | init_time, lead_time, y, x |
| `neighborhood_probability_of_freezing_rain_3_hour_surface_above_2p54` | Neighborhood probability of 3 hour freezing rain (surface) above 2.54 kg m-2 | percent | init_time, lead_time, y, x |
| `neighborhood_probability_of_freezing_rain_3_hour_surface_above_6p35` | Neighborhood probability of 3 hour freezing rain (surface) above 6.35 kg m-2 | percent | init_time, lead_time, y, x |
| `neighborhood_probability_of_freezing_rain_6_hour_surface_above_0p254` | Neighborhood probability of 6 hour freezing rain (surface) above 0.254 kg m-2 | percent | init_time, lead_time, y, x |
| `neighborhood_probability_of_freezing_rain_6_hour_surface_above_12p7` | Neighborhood probability of 6 hour freezing rain (surface) above 12.7 kg m-2 | percent | init_time, lead_time, y, x |
| `neighborhood_probability_of_freezing_rain_6_hour_surface_above_2p54` | Neighborhood probability of 6 hour freezing rain (surface) above 2.54 kg m-2 | percent | init_time, lead_time, y, x |
| `neighborhood_probability_of_freezing_rain_6_hour_surface_above_6p35` | Neighborhood probability of 6 hour freezing rain (surface) above 6.35 kg m-2 | percent | init_time, lead_time, y, x |
| `neighborhood_probability_of_precipitation_exceeding_100_year_average_recurrence_interval_24_hour_surface` | Neighborhood probability of 24 hour precipitation above the 100 year average recurrence interval depth | percent | init_time, lead_time, y, x |
| `neighborhood_probability_of_precipitation_exceeding_100_year_average_recurrence_interval_6_hour_surface` | Neighborhood probability of 6 hour precipitation above the 100 year average recurrence interval depth | percent | init_time, lead_time, y, x |
| `neighborhood_probability_of_precipitation_exceeding_10_year_average_recurrence_interval_24_hour_surface` | Neighborhood probability of 24 hour precipitation above the 10 year average recurrence interval depth | percent | init_time, lead_time, y, x |
| `neighborhood_probability_of_precipitation_exceeding_10_year_average_recurrence_interval_6_hour_surface` | Neighborhood probability of 6 hour precipitation above the 10 year average recurrence interval depth | percent | init_time, lead_time, y, x |
| `neighborhood_probability_of_precipitation_exceeding_1_year_average_recurrence_interval_24_hour_surface` | Neighborhood probability of 24 hour precipitation above the 1 year average recurrence interval depth | percent | init_time, lead_time, y, x |
| `neighborhood_probability_of_precipitation_exceeding_1_year_average_recurrence_interval_6_hour_surface` | Neighborhood probability of 6 hour precipitation above the 1 year average recurrence interval depth | percent | init_time, lead_time, y, x |
| `neighborhood_probability_of_precipitation_exceeding_25_year_average_recurrence_interval_24_hour_surface` | Neighborhood probability of 24 hour precipitation above the 25 year average recurrence interval depth | percent | init_time, lead_time, y, x |
| `neighborhood_probability_of_precipitation_exceeding_25_year_average_recurrence_interval_6_hour_surface` | Neighborhood probability of 6 hour precipitation above the 25 year average recurrence interval depth | percent | init_time, lead_time, y, x |
| `neighborhood_probability_of_precipitation_exceeding_2_year_average_recurrence_interval_24_hour_surface` | Neighborhood probability of 24 hour precipitation above the 2 year average recurrence interval depth | percent | init_time, lead_time, y, x |
| `neighborhood_probability_of_precipitation_exceeding_2_year_average_recurrence_interval_6_hour_surface` | Neighborhood probability of 6 hour precipitation above the 2 year average recurrence interval depth | percent | init_time, lead_time, y, x |
| `neighborhood_probability_of_precipitation_exceeding_3_hour_flash_flood_guidance_3_hour_surface` | Neighborhood probability of 3 hour precipitation above the 3 hour flash flood guidance depth | percent | init_time, lead_time, y, x |
| `neighborhood_probability_of_precipitation_exceeding_50_year_average_recurrence_interval_24_hour_surface` | Neighborhood probability of 24 hour precipitation above the 50 year average recurrence interval depth | percent | init_time, lead_time, y, x |
| `neighborhood_probability_of_precipitation_exceeding_50_year_average_recurrence_interval_6_hour_surface` | Neighborhood probability of 6 hour precipitation above the 50 year average recurrence interval depth | percent | init_time, lead_time, y, x |
| `neighborhood_probability_of_precipitation_exceeding_5_year_average_recurrence_interval_24_hour_surface` | Neighborhood probability of 24 hour precipitation above the 5 year average recurrence interval depth | percent | init_time, lead_time, y, x |
| `neighborhood_probability_of_precipitation_exceeding_5_year_average_recurrence_interval_6_hour_surface` | Neighborhood probability of 6 hour precipitation above the 5 year average recurrence interval depth | percent | init_time, lead_time, y, x |
| `neighborhood_probability_of_precipitation_exceeding_6_hour_flash_flood_guidance_6_hour_surface` | Neighborhood probability of 6 hour precipitation above the 6 hour flash flood guidance depth | percent | init_time, lead_time, y, x |
| `neighborhood_probability_of_total_precipitation_12_hour_surface_above_127` | Neighborhood probability of 12 hour total precipitation (surface) above 127 kg m-2 | percent | init_time, lead_time, y, x |
| `neighborhood_probability_of_total_precipitation_12_hour_surface_above_12p7` | Neighborhood probability of 12 hour total precipitation (surface) above 12.7 kg m-2 | percent | init_time, lead_time, y, x |
| `neighborhood_probability_of_total_precipitation_12_hour_surface_above_203p2` | Neighborhood probability of 12 hour total precipitation (surface) above 203.2 kg m-2 | percent | init_time, lead_time, y, x |
| `neighborhood_probability_of_total_precipitation_12_hour_surface_above_25p4` | Neighborhood probability of 12 hour total precipitation (surface) above 25.4 kg m-2 | percent | init_time, lead_time, y, x |
| `neighborhood_probability_of_total_precipitation_12_hour_surface_above_50p8` | Neighborhood probability of 12 hour total precipitation (surface) above 50.8 kg m-2 | percent | init_time, lead_time, y, x |
| `neighborhood_probability_of_total_precipitation_12_hour_surface_above_76p2` | Neighborhood probability of 12 hour total precipitation (surface) above 76.2 kg m-2 | percent | init_time, lead_time, y, x |
| `neighborhood_probability_of_total_precipitation_24_hour_surface_above_127` | Neighborhood probability of 24 hour total precipitation (surface) above 127 kg m-2 | percent | init_time, lead_time, y, x |
| `neighborhood_probability_of_total_precipitation_24_hour_surface_above_12p7` | Neighborhood probability of 24 hour total precipitation (surface) above 12.7 kg m-2 | percent | init_time, lead_time, y, x |
| `neighborhood_probability_of_total_precipitation_24_hour_surface_above_203p2` | Neighborhood probability of 24 hour total precipitation (surface) above 203.2 kg m-2 | percent | init_time, lead_time, y, x |
| `neighborhood_probability_of_total_precipitation_24_hour_surface_above_25p4` | Neighborhood probability of 24 hour total precipitation (surface) above 25.4 kg m-2 | percent | init_time, lead_time, y, x |
| `neighborhood_probability_of_total_precipitation_24_hour_surface_above_50p8` | Neighborhood probability of 24 hour total precipitation (surface) above 50.8 kg m-2 | percent | init_time, lead_time, y, x |
| `neighborhood_probability_of_total_precipitation_24_hour_surface_above_76p2` | Neighborhood probability of 24 hour total precipitation (surface) above 76.2 kg m-2 | percent | init_time, lead_time, y, x |
| `neighborhood_probability_of_total_precipitation_3_hour_surface_above_127` | Neighborhood probability of 3 hour total precipitation (surface) above 127 kg m-2 | percent | init_time, lead_time, y, x |
| `neighborhood_probability_of_total_precipitation_3_hour_surface_above_12p7` | Neighborhood probability of 3 hour total precipitation (surface) above 12.7 kg m-2 | percent | init_time, lead_time, y, x |
| `neighborhood_probability_of_total_precipitation_3_hour_surface_above_25p4` | Neighborhood probability of 3 hour total precipitation (surface) above 25.4 kg m-2 | percent | init_time, lead_time, y, x |
| `neighborhood_probability_of_total_precipitation_3_hour_surface_above_50p8` | Neighborhood probability of 3 hour total precipitation (surface) above 50.8 kg m-2 | percent | init_time, lead_time, y, x |
| `neighborhood_probability_of_total_precipitation_3_hour_surface_above_76p2` | Neighborhood probability of 3 hour total precipitation (surface) above 76.2 kg m-2 | percent | init_time, lead_time, y, x |
| `neighborhood_probability_of_total_precipitation_6_hour_surface_above_127` | Neighborhood probability of 6 hour total precipitation (surface) above 127 kg m-2 | percent | init_time, lead_time, y, x |
| `neighborhood_probability_of_total_precipitation_6_hour_surface_above_12p7` | Neighborhood probability of 6 hour total precipitation (surface) above 12.7 kg m-2 | percent | init_time, lead_time, y, x |
| `neighborhood_probability_of_total_precipitation_6_hour_surface_above_25p4` | Neighborhood probability of 6 hour total precipitation (surface) above 25.4 kg m-2 | percent | init_time, lead_time, y, x |
| `neighborhood_probability_of_total_precipitation_6_hour_surface_above_50p8` | Neighborhood probability of 6 hour total precipitation (surface) above 50.8 kg m-2 | percent | init_time, lead_time, y, x |
| `neighborhood_probability_of_total_precipitation_6_hour_surface_above_76p2` | Neighborhood probability of 6 hour total precipitation (surface) above 76.2 kg m-2 | percent | init_time, lead_time, y, x |
| `neighborhood_probability_of_total_snowfall_12_hour_surface_above_0p025` | Neighborhood probability of 12 hour total snowfall (surface) above 0.025 m | percent | init_time, lead_time, y, x |
| `neighborhood_probability_of_total_snowfall_12_hour_surface_above_0p076` | Neighborhood probability of 12 hour total snowfall (surface) above 0.076 m | percent | init_time, lead_time, y, x |
| `neighborhood_probability_of_total_snowfall_12_hour_surface_above_0p152` | Neighborhood probability of 12 hour total snowfall (surface) above 0.152 m | percent | init_time, lead_time, y, x |
| `neighborhood_probability_of_total_snowfall_12_hour_surface_above_0p304` | Neighborhood probability of 12 hour total snowfall (surface) above 0.304 m | percent | init_time, lead_time, y, x |
| `neighborhood_probability_of_total_snowfall_12_hour_surface_above_0p457` | Neighborhood probability of 12 hour total snowfall (surface) above 0.457 m | percent | init_time, lead_time, y, x |
| `neighborhood_probability_of_total_snowfall_24_hour_surface_above_0p025` | Neighborhood probability of 24 hour total snowfall (surface) above 0.025 m | percent | init_time, lead_time, y, x |
| `neighborhood_probability_of_total_snowfall_24_hour_surface_above_0p076` | Neighborhood probability of 24 hour total snowfall (surface) above 0.076 m | percent | init_time, lead_time, y, x |
| `neighborhood_probability_of_total_snowfall_24_hour_surface_above_0p152` | Neighborhood probability of 24 hour total snowfall (surface) above 0.152 m | percent | init_time, lead_time, y, x |
| `neighborhood_probability_of_total_snowfall_24_hour_surface_above_0p304` | Neighborhood probability of 24 hour total snowfall (surface) above 0.304 m | percent | init_time, lead_time, y, x |
| `neighborhood_probability_of_total_snowfall_24_hour_surface_above_0p457` | Neighborhood probability of 24 hour total snowfall (surface) above 0.457 m | percent | init_time, lead_time, y, x |
| `neighborhood_probability_of_total_snowfall_3_hour_surface_above_0p025` | Neighborhood probability of 3 hour total snowfall (surface) above 0.025 m | percent | init_time, lead_time, y, x |
| `neighborhood_probability_of_total_snowfall_3_hour_surface_above_0p076` | Neighborhood probability of 3 hour total snowfall (surface) above 0.076 m | percent | init_time, lead_time, y, x |
| `neighborhood_probability_of_total_snowfall_3_hour_surface_above_0p152` | Neighborhood probability of 3 hour total snowfall (surface) above 0.152 m | percent | init_time, lead_time, y, x |
| `neighborhood_probability_of_total_snowfall_6_hour_surface_above_0p025` | Neighborhood probability of 6 hour total snowfall (surface) above 0.025 m | percent | init_time, lead_time, y, x |
| `neighborhood_probability_of_total_snowfall_6_hour_surface_above_0p076` | Neighborhood probability of 6 hour total snowfall (surface) above 0.076 m | percent | init_time, lead_time, y, x |
| `neighborhood_probability_of_total_snowfall_6_hour_surface_above_0p152` | Neighborhood probability of 6 hour total snowfall (surface) above 0.152 m | percent | init_time, lead_time, y, x |
| `neighborhood_probability_of_total_snowfall_6_hour_surface_above_0p304` | Neighborhood probability of 6 hour total snowfall (surface) above 0.304 m | percent | init_time, lead_time, y, x |
| `probability_matched_mean_total_precipitation_3_hour_surface` | Probability-matched mean of total precipitation | kg m-2 | init_time, lead_time, y, x |
| `snowfall_water_equivalent_3_hour_surface` | Snowfall water equivalent | kg m-2 | init_time, statistic, lead_time, y, x |
| `total_precipitation_3_hour_surface` | Total precipitation | kg m-2 | init_time, statistic, lead_time, y, x |
| `total_precipitation_6_hour_surface` | Total precipitation | kg m-2 | init_time, statistic, lead_time, y, x |
| `total_snowfall_12_hour_surface` | Total snowfall | m | init_time, statistic, lead_time, y, x |
| `total_snowfall_24_hour_surface` | Total snowfall | m | init_time, statistic, lead_time, y, x |
| `total_snowfall_3_hour_surface` | Total snowfall | m | init_time, statistic, lead_time, y, x |
| `total_snowfall_6_hour_surface` | Total snowfall | m | init_time, statistic, lead_time, y, x |
