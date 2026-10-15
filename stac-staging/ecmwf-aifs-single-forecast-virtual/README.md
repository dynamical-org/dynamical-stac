# ECMWF AIFS Single forecast, virtual

This dataset is an archive of past and present ECMWF AIFS Single forecasts, optimized for spatial (map) access patterns. Forecasts are identified by an initialization time (`init_time`) denoting the start time of the model run, and step forward along the `lead_time` dimension from 0 to 360 hours (15 days) at a 6 hourly step.

Chunks reference the bytes of ECMWF's original GRIB files and are decoded on read, so this archive carries every variable ECMWF publishes for AIFS Single. Surface and single-level variables are at the dataset root; variables carried on pressure levels are in the `pressure_level` group.

Note: `dynamical-catalog>=1.0.0` (or `zarr>=3.2 icechunk>=2.0 gribberish>=1.5`) is required.

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

The source grib files this archive references are provided by [ECMWF Open Data](https://www.ecmwf.int/en/forecasts/datasets/open-data). Data is read directly from ECMWF's copy on Google Cloud (`gs://ecmwf-open-data`). For forecasts initialized before 1 March 2025, files unavailable from that copy are read from ECMWF's copy in the [AWS Open Data Registry](https://registry.opendata.aws/ecmwf-forecasts/) instead.

ECMWF does not provide user support for the free & open datasets. Users should refer to the public [User Forum](https://forum.ecmwf.int/) for any questions related to the source material.

### Model updates

AIFS is updated regularly. Find details of recent and upcoming
[changes to the forecasting system](https://confluence.ecmwf.int/display/FCST/Changes+to+the+forecasting+system)
on the ECMWF website.

### Storage

Storage for this dataset is generously provided by [AWS Open Data](https://aws.amazon.com/opendata/).

### Chunks

This dataset is stored in [Zarr](https://zarr.dev/) format, which splits each variable into a grid of **chunks** — the smallest unit read from storage. When possible, aligning your reads with this dataset's chunk grid can significantly improve data access speed.

The element count and coordinate span of this dataset:

| dimension | chunk |
|---|---|
| init_time | 1 (6 hours) |
| lead_time | 1 (6 hours) |
| latitude | 721 (180.25°) |
| longitude | 1440 (360°) |
| **uncompressed** | 7.9 MiB |

### Validation report

Review the [validation report](https://dynamical.org/catalog/ecmwf-aifs-single-forecast-virtual/validation/) for variable availability, missing data, known quirks, fill values, value distributions, and sample plots.

## Links

- STAC collection: https://stac-staging.dynamical.org/ecmwf-aifs-single-forecast-virtual/collection.json
- Dataset documentation: https://dynamical.org/catalog/ecmwf-aifs-single-forecast-virtual/
- Validation report: https://dynamical.org/catalog/ecmwf-aifs-single-forecast-virtual/validation/
