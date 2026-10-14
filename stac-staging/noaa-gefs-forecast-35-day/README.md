# NOAA GEFS forecast, 35 day

This dataset is an archive of past and present GEFS forecasts. Forecasts are identified by an initialization time (`init_time`) denoting the start time of the model run as well as by the `ensemble_member`. Each forecast has a 3 hourly forecast step along the `lead_time` dimension. This dataset contains only the 00 hour UTC initialization times which produce the full length, 35 day forecast.

The Global Ensemble Forecast System (GEFS) is a National Oceanic and Atmospheric Administration (NOAA) National Centers for Environmental Prediction (NCEP) weather forecast model. GEFS creates 31 separate forecasts (ensemble members) to describe the range of forecast uncertainty.

## License

CC-BY-4.0. NOAA NWS NCEP GEFS data processed by dynamical.org from NOAA Open Data Dissemination archives.

- [CC-BY-4.0](https://creativecommons.org/licenses/by/4.0/)

## Provenance

Produced by [NOAA NWS NCEP](https://www.weather.gov/ncep/). Processed and hosted by [dynamical.org](https://dynamical.org/).
Source: [NOAA GEFS on NOAA Open Data Dissemination](https://registry.opendata.aws/noaa-gefs/).

## Details

### Interpolation

Source data is available at both 0.25-degree and 0.5-degree resolutions. All variables except the 100m wind components are derived from a 0.25-degree grid for the first 240 hours of each forecast and from a 0.5-degree grid for the remainder. 100m wind components are derived from a 0.5-degree grid for all lead times. Bilinear interpolation is used to convert 0.5-degree data to a 0.25-degree grid. The original 0.5-degree values can be retrieved by selecting every other pixel starting from offset 0 in both the latitude and longitude dimensions (e.g. `array[::2, ::2]`).

### Source

The source grib files this archive is constructed from are provided by
[NOAA Open Data Dissemination (NODD)](https://www.noaa.gov/information-technology/open-data-dissemination)
and accessed from the [AWS Open Data Registry](https://registry.opendata.aws/noaa-gefs/).
Operational data is additionally accessed from [NOAA NOMADS](https://nomads.ncep.noaa.gov/).

### Storage

Storage for this dataset is generously provided by [Source Cooperative](https://source.coop/), a [Radiant Earth](https://radiant.earth/) initiative. Icechunk storage generously provided by [AWS Open Data](https://aws.amazon.com/opendata/).

### Chunks and shards

This dataset is stored in [Zarr](https://zarr.dev/) format, which splits each variable into a grid of **chunks** — the smallest unit read from storage. Chunks are grouped into larger **shards** (the objects actually written to storage), which keeps the object count manageable for long-archive datasets. When possible, aligning your reads with this dataset's chunk grid can significantly improve data access speed.

The element count and coordinate span of this dataset:

| dimension | chunk | shard |
|---|---|---|
| init_time | 1 (1 day) | 1 (1 day) |
| ensemble_member | 31 | 31 |
| lead_time | 64 (~8 days) | 192 (843 hours) |
| latitude | 17 (4.25°) | 374 (93.5°) |
| longitude | 16 (4°) | 368 (92°) |
| **uncompressed** | 2.1 MiB | 3.1 GiB |

### Validation report

Review the [validation report](https://dynamical.org/catalog/noaa-gefs-forecast-35-day/validation/) for variable availability, missing data, known quirks, fill values, value distributions, and sample plots.

### Compression

The data values in this dataset have been rounded in their binary floating point representation to improve compression. See [Klöwer et al. 2021](https://www.nature.com/articles/s43588-021-00156-2) for more information on this approach. The exact number of rounded bits can be found in our [reformatting code](https://github.com/dynamical-org/reformatters/blob/main/src/reformatters/noaa/gefs/common_gefs_template_config.py).

## Links

- STAC collection: https://stac-staging.dynamical.org/noaa-gefs-forecast-35-day/collection.json
- Dataset documentation: https://dynamical.org/catalog/noaa-gefs-forecast-35-day/
- Validation report: https://dynamical.org/catalog/noaa-gefs-forecast-35-day/validation/
