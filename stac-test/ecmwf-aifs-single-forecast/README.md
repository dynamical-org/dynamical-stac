# ECMWF AIFS Single forecast

This dataset is an archive of past and present ECMWF AIFS Single forecasts. Forecasts are identified by an initialization time (`init_time`) denoting the start time of the model run. Each forecast steps forward in time along the `lead_time` dimension, from 0 to 360 hours (15 days) at a 6 hourly step.

The Artificial Intelligence Forecasting System (AIFS) is a data driven forecast model developed by the European Centre for Medium-Range Weather Forecasts (ECMWF). This is the non-ensemble configuration of AIFS that produces a single forecast trace. AIFS is trained on ECMWF's ERA5 re-analysis and ECMWF's operational numerical weather prediction (NWP) analyses.

## License

CC-BY-4.0. ECMWF AIFS Single forecast data processed by dynamical.org from ECMWF Open Data.

- [CC-BY-4.0](https://creativecommons.org/licenses/by/4.0/)
- [ECMWF Terms of Use (additional terms)](https://apps.ecmwf.int/datasets/licences/general/)

## Provenance

Produced by [ECMWF](https://www.ecmwf.int/). Processed and hosted by [dynamical.org](https://dynamical.org/).
Source: [ECMWF Open Data](https://www.ecmwf.int/en/forecasts/datasets/open-data).

## Details

### Source

The source grib files this archive is constructed from are provided by [ECMWF Open Data](https://www.ecmwf.int/en/forecasts/datasets/open-data) and accessed from the [AWS Open Data Registry](https://registry.opendata.aws/ecmwf-forecasts/).

ECMWF does not provide user support for the free & open datasets. Users should refer to the public [User Forum](https://forum.ecmwf.int/) for any questions related to the source material.

### Model updates

AIFS is updated regularly. Find details of recent and upcoming
[changes to the forecasting system](https://confluence.ecmwf.int/display/FCST/Changes+to+the+forecasting+system)
on the ECMWF website.

### Storage

Storage for this dataset is generously provided by [Source Cooperative](https://source.coop/), a [Radiant Earth](https://radiant.earth/) initiative. Icechunk storage generously provided by [AWS Open Data](https://aws.amazon.com/opendata/).

### Chunks and shards

This dataset is stored in [Zarr](https://zarr.dev/) format, which splits each variable into a grid of **chunks** — the smallest unit read from storage. Chunks are grouped into larger **shards** (the objects actually written to storage), which keeps the object count manageable for long-archive datasets. When possible, aligning your reads with this dataset's chunk grid can significantly improve data access speed.

The element count and coordinate span of this dataset:

| dimension | chunk | shard |
|---|---|---|
| init_time | 1 (6 hours) | 1 (6 hours) |
| lead_time | 61 (366 hours) | 61 (366 hours) |
| latitude | 241 (60.25°) | 723 (180.25°) |
| longitude | 240 (60°) | 1440 (360°) |
| **uncompressed** | 13.5 MiB | 242.3 MiB |

### Validation report

Review the [validation report](https://dynamical.org/catalog/ecmwf-aifs-single-forecast/validation/) for variable availability, missing data, known quirks, fill values, value distributions, and sample plots.

### Compression

The data values in this dataset have been rounded in their binary floating point representation to improve compression. See [Klöwer et al. 2021](https://www.nature.com/articles/s43588-021-00156-2) for more information on this approach. The exact number of rounded bits can be found in our [reformatting code](https://github.com/dynamical-org/reformatters/blob/main/src/reformatters/ecmwf/aifs_single/forecast/template_config.py).

## Links

- STAC collection: https://stac-test.dynamical.org/ecmwf-aifs-single-forecast/collection.json
- Dataset documentation: https://dynamical.org/catalog/ecmwf-aifs-single-forecast/
- Validation report: https://dynamical.org/catalog/ecmwf-aifs-single-forecast/validation/
