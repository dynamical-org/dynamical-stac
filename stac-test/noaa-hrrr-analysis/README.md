# NOAA HRRR analysis

This analysis dataset is an archive of the model's best estimate of past weather. It is created by concatenating the first hour of each historical forecast to provide a dataset with dimensions time, x, and y.

This dataset uses the native HRRR Lambert Conformal Conic projection, with spatial indexing along the `x` and `y` dimensions. The example notebook shows how to use the embedded spatial reference to select geographic areas of interest.

The High-Resolution Rapid Refresh (HRRR) is a NOAA real-time 3-km resolution, hourly updated, cloud-resolving, convection-allowing atmospheric model, initialized by 3km grids with 3km radar assimilation. Radar data is assimilated in the HRRR every 15 min over a 1-h period adding further detail to that provided by the hourly data assimilation from the 13km radar-enhanced Rapid Refresh.

## License

CC-BY-4.0. NOAA NWS NCEP HRRR data processed by dynamical.org from NOAA Open Data Dissemination archives.

- [CC-BY-4.0](https://creativecommons.org/licenses/by/4.0/)

## Provenance

Produced by [NOAA NWS NCEP](https://www.weather.gov/ncep/). Processed and hosted by [dynamical.org](https://dynamical.org/).
Source: [NOAA HRRR on NOAA Open Data Dissemination](https://registry.opendata.aws/noaa-hrrr-pds/).

## Details

### Construction

HRRR starts a new model run every hour and dynamical.org has created this analysis by concatenating the first step of each forecast along the time dimension. Accumulated variables (e.g. precipitation) are read from the second step of the previous hour's forecast.

### Data availability

There are a significant number of missing source files before August 2018 (HRRR v1 and v2 period), and a small number from August 2018 to December 2020 (HRRR v3 period).

`downward_long_wave_radiation_flux_surface` and `relative_humidity_2m` are unavailable before August 2016 (HRRR v1 period).

This dataset has NaN values where source data are unavailable.

### Source

The source grib files this archive is constructed from are provided by [NOAA Open Data Dissemination (NODD)](https://www.noaa.gov/information-technology/open-data-dissemination) and accessed from the [AWS Open Data Registry](https://registry.opendata.aws/noaa-hrrr-pds/). Operational data is additionally accessed from [NOAA NOMADS](https://nomads.ncep.noaa.gov/).

### Storage

Storage for this dataset is generously provided by [Source Cooperative](https://source.coop/), a [Radiant Earth](https://radiant.earth/) initiative. Icechunk storage generously provided by [AWS Open Data](https://aws.amazon.com/opendata/).

### Chunks and shards

This dataset is stored in [Zarr](https://zarr.dev/) format, which splits each variable into a grid of **chunks** — the smallest unit read from storage. Chunks are grouped into larger **shards** (the objects actually written to storage), which keeps the object count manageable for long-archive datasets. When possible, aligning your reads with this dataset's chunk grid can significantly improve data access speed.

The element count and coordinate span of this dataset:

| dimension | chunk | shard |
|---|---|---|
| time | 2160 (90 days) | 2160 (90 days) |
| y | 45 (135 km) | 540 (1620 km) |
| x | 45 (135 km) | 450 (1350 km) |
| **uncompressed** | 16.7 MiB | 2.0 GiB |

### Validation report

Review the [validation report](https://dynamical.org/catalog/noaa-hrrr-analysis/validation/) for variable availability, missing data, known quirks, fill values, value distributions, and sample plots.

### Compression

The data values in this dataset have been rounded in their binary floating point representation to improve compression. See [Klöwer et al. 2021](https://www.nature.com/articles/s43588-021-00156-2) for more information on this approach. The exact number of rounded bits can be found in our [reformatting code](https://github.com/dynamical-org/reformatters/).

## Links

- STAC collection: https://stac-test.dynamical.org/noaa-hrrr-analysis/collection.json
- Dataset documentation: https://dynamical.org/catalog/noaa-hrrr-analysis/
- Validation report: https://dynamical.org/catalog/noaa-hrrr-analysis/validation/
