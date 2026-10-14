# NOAA GFS analysis, virtual

This analysis dataset is an archive of the model's best estimate of past weather, optimized for spatial (map) access patterns. It is created by concatenating the shortest available step of each historical forecast to provide a dataset with dimensions time, latitude, and longitude.

Variables on pressure levels and fixed heights above mean sea level live in the `pressure_level` and `height_above_mean_sea_level` groups.

Note: `dynamical-catalog>=0.8.0` (or `zarr>=3.2 icechunk>=2.0 gribberish>=1.5`) is required.

The Global Forecast System (GFS) is a National Oceanic and Atmospheric Administration (NOAA) National Centers for Environmental Prediction (NCEP) weather forecast model that generates data for dozens of atmospheric and land-soil variables, including temperatures, winds, precipitation, soil moisture, and atmospheric ozone concentration. The system couples four separate models (atmosphere, ocean model, land/soil model, and sea ice) that work together to depict weather conditions.

## License

CC-BY-4.0. NOAA NWS NCEP GFS data processed by dynamical.org from NOAA Open Data Dissemination archives.

- [CC-BY-4.0](https://creativecommons.org/licenses/by/4.0/)

## Provenance

Produced by [NOAA NWS NCEP](https://www.weather.gov/ncep/). Processed and hosted by [dynamical.org](https://dynamical.org/).
Source: [NOAA GFS on NOAA Open Data Dissemination](https://registry.opendata.aws/noaa-gfs-bdp-pds/).

## Details

### Construction

GFS starts a new model run every 6 hours and dynamical.org has created this analysis by
concatenating the shortest usable forecast step of each run along the time dimension.
Instantaneous variables are read from forecast hours 0 to 5, and variables that describe a
preceding window (accumulations, averages and window maxima and minima) are read from
forecast hours 1 to 6.

### Source

The source grib files this archive is constructed from are provided by [NOAA Open Data Dissemination (NODD)](https://www.noaa.gov/information-technology/open-data-dissemination) and accessed from the [AWS Open Data Registry](https://registry.opendata.aws/noaa-gfs-bdp-pds/). Operational data is additionally accessed from [NOAA NOMADS](https://nomads.ncep.noaa.gov/).

### Storage

Storage for this dataset is generously provided by [AWS Open Data](https://aws.amazon.com/opendata/).

### Chunks

This dataset is stored in [Zarr](https://zarr.dev/) format, which splits each variable into a grid of **chunks** — the smallest unit read from storage. When possible, aligning your reads with this dataset's chunk grid can significantly improve data access speed.

The element count and coordinate span of this dataset:

| dimension | chunk |
|---|---|
| time | 1 (1 hour) |
| latitude | 721 (180.25°) |
| longitude | 1440 (360°) |
| **uncompressed** | 7.9 MiB |

### Validation report

Review the [validation report](https://dynamical.org/catalog/noaa-gfs-analysis-virtual/validation/) for variable availability, missing data, known quirks, fill values, value distributions, and sample plots.

## Links

- STAC collection: https://stac-staging.dynamical.org/noaa-gfs-analysis-virtual/collection.json
- Dataset documentation: https://dynamical.org/catalog/noaa-gfs-analysis-virtual/
- Validation report: https://dynamical.org/catalog/noaa-gfs-analysis-virtual/validation/
