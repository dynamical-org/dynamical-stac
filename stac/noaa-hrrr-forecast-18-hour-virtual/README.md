# NOAA HRRR forecast, 18 hour, virtual

This dataset is an archive of past and present HRRR forecasts, optimized for spatial (map) access patterns. Forecasts are identified by an initialization time (`init_time`) denoting the start time of the model run, and step forward hourly along the `lead_time` dimension out to 18 hours. A new forecast is initialized every hour.

This dataset uses the native HRRR Lambert Conformal Conic projection, with spatial indexing along the `x` and `y` dimensions. The example notebook shows how to use the embedded spatial reference to select geographic areas of interest.

Note: `dynamical-catalog>=0.8.0` (or `zarr>=3.2 icechunk>=2.0 gribberish>=1.5`) is required.

The High-Resolution Rapid Refresh (HRRR) is a NOAA real-time 3-km resolution, hourly updated, cloud-resolving, convection-allowing atmospheric model, initialized by 3km grids with 3km radar assimilation. Radar data is assimilated in the HRRR every 15 min over a 1-h period adding further detail to that provided by the hourly data assimilation from the 13km radar-enhanced Rapid Refresh.

## License

CC-BY-4.0. NOAA NWS NCEP HRRR data processed by dynamical.org from NOAA Open Data Dissemination archives.

- [CC-BY-4.0](https://creativecommons.org/licenses/by/4.0/)

## Provenance

Produced by [NOAA NWS NCEP](https://www.weather.gov/ncep/). Processed and hosted by [dynamical.org](https://dynamical.org/).
Source: [NOAA HRRR on NOAA Open Data Dissemination](https://registry.opendata.aws/noaa-hrrr-pds/).

## Details

### Source

The source grib files this archive is constructed from are provided by [NOAA Open Data Dissemination (NODD)](https://www.noaa.gov/information-technology/open-data-dissemination) and accessed from the [AWS Open Data Registry](https://registry.opendata.aws/noaa-hrrr-pds/). Operational data is additionally accessed from [NOAA NOMADS](https://nomads.ncep.noaa.gov/).

### Storage

Storage for this dataset is generously provided by [AWS Open Data](https://aws.amazon.com/opendata/).

### Chunks

This dataset is stored in [Zarr](https://zarr.dev/) format, which splits each variable into a grid of **chunks** — the smallest unit read from storage. When possible, aligning your reads with this dataset's chunk grid can significantly improve data access speed.

The element count and coordinate span of this dataset:

| dimension | chunk |
|---|---|
| init_time | 1 (1 hour) |
| lead_time | 1 (1 hour) |
| y | 1059 (3177 km) |
| x | 1799 (5397 km) |
| **uncompressed** | 14.5 MiB |

### Validation report

Review the [validation report](https://dynamical.org/catalog/noaa-hrrr-forecast-18-hour-virtual/validation/) for variable availability, missing data, known quirks, fill values, value distributions, and sample plots.

## Links

- STAC collection: https://stac.dynamical.org/noaa-hrrr-forecast-18-hour-virtual/collection.json
- Dataset documentation: https://dynamical.org/catalog/noaa-hrrr-forecast-18-hour-virtual/
- Validation report: https://dynamical.org/catalog/noaa-hrrr-forecast-18-hour-virtual/validation/
