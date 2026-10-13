# NOAA GFS forecast

This dataset is an archive of past and present GFS forecasts. Forecasts are identified by an initialization time (`init_time`) denoting the start time of the model run. Each forecast steps forward in time along the `lead_time` dimension.

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

Storage for this dataset is generously provided by [Source Cooperative](https://source.coop/), a [Radiant Earth](https://radiant.earth/) initiative. Icechunk storage generously provided by [AWS Open Data](https://aws.amazon.com/opendata/).

### Chunks and shards

This dataset is stored in [Zarr](https://zarr.dev/) format, which splits each variable into a grid of **chunks** — the smallest unit read from storage. Chunks are grouped into larger **shards** (the objects actually written to storage), which keeps the object count manageable for long-archive datasets. When possible, aligning your reads with this dataset's chunk grid can significantly improve data access speed.

The element count and coordinate span of this dataset:

| dimension | chunk | shard |
|---|---|---|
| init_time | 1 (6 hours) | 1 (6 hours) |
| lead_time | 105 (~105 hours) | 210 (385 hours) |
| latitude | 121 (30.25°) | 726 (180.25°) |
| longitude | 121 (30.25°) | 726 (181.5°) |
| **uncompressed** | 5.9 MiB | 422.2 MiB |

### Validation report

Review the [validation report](https://dynamical.org/catalog/noaa-gfs-forecast/validation/) for variable availability, missing data, known quirks, fill values, value distributions, and sample plots.

### Compression

The data values in this dataset have been rounded in their binary floating point representation to improve compression. See [Klöwer et al. 2021](https://www.nature.com/articles/s43588-021-00156-2) for more information on this approach. The exact number of rounded bits can be found in our [reformatting code](https://github.com/dynamical-org/reformatters/blob/main/src/reformatters/noaa/gfs/forecast/template_config.py).

## Links

- STAC collection: https://stac-test.dynamical.org/noaa-gfs-forecast/collection.json
- Dataset documentation: https://dynamical.org/catalog/noaa-gfs-forecast/
- Validation report: https://dynamical.org/catalog/noaa-gfs-forecast/validation/
