# NOAA GEFS analysis, 0.25 degree, virtual

This analysis dataset is an archive of the model's best estimate of past weather, optimized for spatial (map) access patterns. It is created by concatenating the shortest available step of each historical forecast to provide a dataset with dimensions time, latitude, and longitude.

Note: `dynamical-catalog>=0.8.0` (or `zarr>=3.2 icechunk>=2.0 gribberish>=1.5`) is required.

The Global Ensemble Forecast System (GEFS) is a National Oceanic and Atmospheric Administration (NOAA) National Centers for Environmental Prediction (NCEP) weather forecast model. GEFS creates 31 separate forecasts (ensemble members) to describe the range of forecast uncertainty.

## License

CC-BY-4.0. NOAA NWS NCEP GEFS data processed by dynamical.org from NOAA Open Data Dissemination archives.

- [CC-BY-4.0](https://creativecommons.org/licenses/by/4.0/)

## Provenance

Produced by [NOAA NWS NCEP](https://www.weather.gov/ncep/). Processed and hosted by [dynamical.org](https://dynamical.org/).
Source: [NOAA GEFS on NOAA Open Data Dissemination](https://registry.opendata.aws/noaa-gefs/).

## Details

### Construction

GEFS starts a new model run every 6 hours and dynamical.org has created this analysis by
concatenating the shortest usable forecast step of each run along the time dimension.
Instantaneous variables are read from forecast hour 0 or 3, and variables that describe a
preceding window (accumulations, averages and window maxima and minima) are read from
forecast hour 3 or 6.

Only the control member is used.

This dataset reads the 0.25 degree `pgrb2s` files, which carry a subset of GEFS variables at
the model's highest available resolution.

### Source

The source grib files this archive is constructed from are provided by
[NOAA Open Data Dissemination (NODD)](https://www.noaa.gov/information-technology/open-data-dissemination)
and accessed from the [AWS Open Data Registry](https://registry.opendata.aws/noaa-gefs/).

### Variable availability

Four variables were added by the source after the archive begins and are empty before those
dates:

- From 2022-10-18T12 UTC: `visibility_surface`, `percent_frozen_precipitation_surface` and
  `geopotential_height_cloud_ceiling`.
- From 2021-07-20T12 UTC: `pressure_reduced_to_mean_sea_level_eta_model`.

### Storage

Storage for this dataset is generously provided by [AWS Open Data](https://aws.amazon.com/opendata/).

### Chunks

This dataset is stored in [Zarr](https://zarr.dev/) format, which splits each variable into a grid of **chunks** — the smallest unit read from storage. When possible, aligning your reads with this dataset's chunk grid can significantly improve data access speed.

The element count and coordinate span of this dataset:

| dimension | chunk |
|---|---|
| time | 1 (3 hours) |
| latitude | 721 (180.25°) |
| longitude | 1440 (360°) |
| **uncompressed** | 7.9 MiB |

### Validation report

Review the [validation report](https://dynamical.org/catalog/noaa-gefs-analysis-0-25-degree-virtual/validation/) for variable availability, missing data, known quirks, fill values, value distributions, and sample plots.

## Links

- STAC collection: https://stac-test.dynamical.org/noaa-gefs-analysis-0-25-degree-virtual/collection.json
- Dataset documentation: https://dynamical.org/catalog/noaa-gefs-analysis-0-25-degree-virtual/
- Validation report: https://dynamical.org/catalog/noaa-gefs-analysis-0-25-degree-virtual/validation/
