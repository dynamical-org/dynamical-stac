# NOAA MRMS CONUS analysis, hourly

This analysis dataset is an archive of MRMS radar and multi-sensor precipitation and weather analyses over the contiguous United States (CONUS).

The NOAA Multi-Radar/Multi-Sensor System (MRMS) integrates data from multiple radars and radar networks, surface observations, numerical weather prediction (NWP) models, and climatology to generate seamless, high spatio-temporal resolution mosaics at low latency focused on hail, wind, tornado, quantitative precipitation estimations, convection, icing, and turbulence.

## License

CC-BY-4.0. NOAA NWS NCEP MRMS data processed by dynamical.org from NOAA NCEP, NOAA Open Data Dissemination and Iowa Mesonet archives.

- [CC-BY-4.0](https://creativecommons.org/licenses/by/4.0/)

## Provenance

Produced by [NOAA NWS NCEP](https://www.weather.gov/ncep/). Processed and hosted by [dynamical.org](https://dynamical.org/).
Source: [NOAA MRMS on NOAA Open Data Dissemination](https://registry.opendata.aws/noaa-mrms-pds/).

## Details

### Spatial coverage

Use this dataset over the land areas of the contiguous United States. Radar-only and precipitation type variables contain `NaN` values beyond the range of US radar. `precipitation_pass_1_surface` and `precipitation_pass_2_surface` extend further into the ocean, but still contain `NaN` values in the southeast corner of the domain over the Atlantic.

### Temporal coverage

`precipitation_surface` combines multiple MRMS products to minimize missing values. Despite this, some hours (particularly early in the record) contain `NaN` values where data is unavailable.

`precipitation_pass_2_surface` and `precipitation_pass_1_surface` are available starting 2020-10-15. For timestamps prior to this date, these variables are filled with `NaN`.

### Source

The source files this archive is constructed from are provided by
[NOAA Open Data Dissemination (NODD)](https://www.noaa.gov/information-technology/open-data-dissemination)
and accessed from the [AWS Open Data Registry](https://registry.opendata.aws/noaa-mrms-pds/).
Operational data is additionally accessed from [NCEP](https://mrms.ncep.noaa.gov/).

### Storage

Storage for this dataset is generously provided by [Source Cooperative](https://source.coop/), a [Radiant Earth](https://radiant.earth/) initiative. Icechunk storage generously provided by [AWS Open Data](https://aws.amazon.com/opendata/).

### Chunks and shards

This dataset is stored in [Zarr](https://zarr.dev/) format, which splits each variable into a grid of **chunks** — the smallest unit read from storage. Chunks are grouped into larger **shards** (the objects actually written to storage), which keeps the object count manageable for long-archive datasets. When possible, aligning your reads with this dataset's chunk grid can significantly improve data access speed.

The element count and coordinate span of this dataset:

| dimension | chunk | shard |
|---|---|---|
| time | 648 (27 days) | 648 (27 days) |
| latitude | 100 (1°) | 700 (7°) |
| longitude | 100 (1°) | 1400 (14°) |
| **uncompressed** | 24.7 MiB | 2.4 GiB |

### Validation report

Review the [validation report](https://dynamical.org/catalog/noaa-mrms-conus-analysis-hourly/validation/) for variable availability, missing data, known quirks, fill values, value distributions, and sample plots.

### Compression

The data values in this dataset have been rounded in their binary floating point representation to improve compression. See [Klöwer et al. 2021](https://www.nature.com/articles/s43588-021-00156-2) for more information on this approach. The exact number of rounded bits can be found in our [reformatting code](https://github.com/dynamical-org/reformatters/).

## Links

- STAC collection: https://stac.dynamical.org/noaa-mrms-conus-analysis-hourly/collection.json
- Dataset documentation: https://dynamical.org/catalog/noaa-mrms-conus-analysis-hourly/
- Validation report: https://dynamical.org/catalog/noaa-mrms-conus-analysis-hourly/validation/
