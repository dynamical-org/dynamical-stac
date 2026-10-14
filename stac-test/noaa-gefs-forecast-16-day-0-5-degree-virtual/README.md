# NOAA GEFS forecast, 16 day, 0.5 degree, virtual

This dataset is an archive of past and present GEFS forecasts at 0.5 degree resolution, optimized for spatial (map) access patterns. Forecasts are identified by an initialization time (`init_time`) denoting the start time of the model run as well as by the `ensemble_member`, and step forward along the `lead_time` dimension. A new forecast is initialized every 6 hours.

Variables on pressure levels, model levels and fixed heights above mean sea level live in the `pressure_level`, `model_level` and `height_above_mean_sea_level` groups.

Note: `dynamical-catalog>=0.8.0` (or `zarr>=3.2 icechunk>=2.2.2 gribberish>=1.5`) is required.

The Global Ensemble Forecast System (GEFS) is a National Oceanic and Atmospheric Administration (NOAA) National Centers for Environmental Prediction (NCEP) weather forecast model. GEFS creates 31 separate forecasts (ensemble members) to describe the range of forecast uncertainty.

## License

CC-BY-4.0. NOAA NWS NCEP GEFS data processed by dynamical.org from NOAA Open Data Dissemination archives.

- [CC-BY-4.0](https://creativecommons.org/licenses/by/4.0/)

## Provenance

Produced by [NOAA NWS NCEP](https://www.weather.gov/ncep/). Processed and hosted by [dynamical.org](https://dynamical.org/).
Source: [NOAA GEFS on NOAA Open Data Dissemination](https://registry.opendata.aws/noaa-gefs/).

## Details

### Source

The source grib files this archive is constructed from are provided by
[NOAA Open Data Dissemination (NODD)](https://www.noaa.gov/information-technology/open-data-dissemination)
and accessed from the [AWS Open Data Registry](https://registry.opendata.aws/noaa-gefs/).

### Storage

Storage for this dataset is generously provided by [AWS Open Data](https://aws.amazon.com/opendata/).

### Chunks

This dataset is stored in [Zarr](https://zarr.dev/) format, which splits each variable into a grid of **chunks** — the smallest unit read from storage. When possible, aligning your reads with this dataset's chunk grid can significantly improve data access speed.

The element count and coordinate span of this dataset:

| dimension | chunk |
|---|---|
| init_time | 1 (6 hours) |
| ensemble_member | 1 |
| lead_time | 1 (~3 hours) |
| latitude | 361 (180.5°) |
| longitude | 720 (360°) |
| **uncompressed** | 2.0 MiB |

### Validation report

Review the [validation report](https://dynamical.org/catalog/noaa-gefs-forecast-16-day-0-5-degree-virtual/validation/) for variable availability, missing data, known quirks, fill values, value distributions, and sample plots.

## Links

- STAC collection: https://stac-test.dynamical.org/noaa-gefs-forecast-16-day-0-5-degree-virtual/collection.json
- Dataset documentation: https://dynamical.org/catalog/noaa-gefs-forecast-16-day-0-5-degree-virtual/
- Validation report: https://dynamical.org/catalog/noaa-gefs-forecast-16-day-0-5-degree-virtual/validation/
