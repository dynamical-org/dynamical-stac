# NOAA RRFS forecast, 18 hour, virtual

This dataset is an archive of past and present RRFS forecasts, optimized for spatial (map) access patterns. Forecasts are identified by an initialization time (`init_time`) denoting the start time of the model run, and step forward hourly along the `lead_time` dimension out to 18 hours.

This dataset uses the native RRFS Lambert Conformal Conic projection, with spatial indexing along the `x` and `y` dimensions. The example notebook shows how to use the embedded spatial reference to select geographic areas of interest.

Variables on pressure levels, fixed heights above mean sea level and soil depths live in the `pressure_level`, `height_above_mean_sea_level` and `depth_below_ground` groups.

Note: `dynamical-catalog>=1.0.1` and `gribberish>=1.8.4` (or `zarr>=3.2 icechunk>=2.0 gribberish>=1.8.4`) are required.

The Rapid Refresh Forecast System (RRFS) is a National Oceanic and Atmospheric Administration (NOAA) National Centers for Environmental Prediction (NCEP) convection-allowing weather forecast model with a 3 km grid, built on the Unified Forecast System. The RRFS ensemble (RRFS ENS) adds five perturbed members to this deterministic forecast, and REFS combines both with HRRR into ensemble products.

NOAA RRFS is pre-operational, so expect changes to the model data and to the structure of this dataset.

## License

CC-BY-4.0. NOAA NWS NCEP RRFS data processed by dynamical.org from NOAA Open Data Dissemination archives.

- [CC-BY-4.0](https://creativecommons.org/licenses/by/4.0/)

## Provenance

Produced by [NOAA NWS NCEP](https://www.weather.gov/ncep/). Processed and hosted by [dynamical.org](https://dynamical.org/).
Source: [NOAA RRFS and REFS on NOAA Open Data Dissemination](https://registry.opendata.aws/noaa-rrfs-ops/).

## Details

### Source

The source grib files this archive is constructed from are provided by [NOAA Open Data Dissemination (NODD)](https://www.noaa.gov/information-technology/open-data-dissemination) and accessed from the [AWS Open Data Registry](https://registry.opendata.aws/noaa-rrfs-ops/).

### Storage

Storage for this dataset is generously provided by [AWS Open Data](https://aws.amazon.com/opendata/).

### Chunks

This dataset is stored in [Zarr](https://zarr.dev/) format, which splits each variable into a grid of **chunks** — the smallest unit read from storage. When possible, aligning your reads with this dataset's chunk grid can significantly improve data access speed.

The element count and coordinate span of this dataset:

| dimension | chunk |
|---|---|
| init_time | 1 (3 hours) |
| lead_time | 1 (1 hour) |
| y | 1059 (3177 km) |
| x | 1799 (5397 km) |
| **uncompressed** | 14.5 MiB |

### Validation report

Review the [validation report](https://dynamical.org/catalog/noaa-rrfs-forecast-18-hour-virtual/validation/) for variable availability, missing data, known quirks, fill values, value distributions, and sample plots.

## Links

- STAC collection: https://stac.dynamical.org/noaa-rrfs-forecast-18-hour-virtual/collection.json
- Dataset documentation: https://dynamical.org/catalog/noaa-rrfs-forecast-18-hour-virtual/
- Validation report: https://dynamical.org/catalog/noaa-rrfs-forecast-18-hour-virtual/validation/
