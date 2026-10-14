# NOAA GFS forecast, virtual

This dataset is an archive of past and present GFS forecasts, optimized for spatial (map) access patterns. Forecasts are identified by an initialization time (`init_time`) denoting the start time of the model run, and step forward along the `lead_time` dimension. A new forecast is initialized every 6 hours.

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

### Source

The source grib files this archive is constructed from are provided by [NOAA Open Data Dissemination (NODD)](https://www.noaa.gov/information-technology/open-data-dissemination) and accessed from the [AWS Open Data Registry](https://registry.opendata.aws/noaa-gfs-bdp-pds/). Operational data is additionally accessed from [NOAA NOMADS](https://nomads.ncep.noaa.gov/).

### Storage

Storage for this dataset is generously provided by [AWS Open Data](https://aws.amazon.com/opendata/).

### Chunks

This dataset is stored in [Zarr](https://zarr.dev/) format, which splits each variable into a grid of **chunks** — the smallest unit read from storage. When possible, aligning your reads with this dataset's chunk grid can significantly improve data access speed.

The element count and coordinate span of this dataset:

| dimension | chunk |
|---|---|
| init_time | 1 (6 hours) |
| lead_time | 1 (~1 hour) |
| latitude | 721 (180.25°) |
| longitude | 1440 (360°) |
| **uncompressed** | 7.9 MiB |

### Validation report

Review the [validation report](https://dynamical.org/catalog/noaa-gfs-forecast-virtual/validation/) for variable availability, missing data, known quirks, fill values, value distributions, and sample plots.

## Links

- STAC collection: https://stac.dynamical.org/noaa-gfs-forecast-virtual/collection.json
- Dataset documentation: https://dynamical.org/catalog/noaa-gfs-forecast-virtual/
- Validation report: https://dynamical.org/catalog/noaa-gfs-forecast-virtual/validation/
