# ECMWF IFS ENS forecast, 15 day, 0.25 degree

This dataset is an archive of past and present ECMWF IFS ENS forecasts. Forecasts are identified by an initialization time (`init_time`) denoting the start time of the model run, as well as by the `ensemble_member`. Along the `lead_time` dimension, each forecast begins at a 3 hourly forecast step (0-144 hours) and switches to a 6 hourly step for days 6 through 15 of the forecast (hours 144-360). This dataset contains the 00 UTC initialization times only.

The Integrated Forecasting System (IFS) is a global forecast model developed by ECMWF. ENS is an ensemble configuration of IFS: 51 ensemble members in the medium range and 101 in the sub-seasonal (extended) range. IFS consists of a numerical model of the Earth system, which includes an atmospheric model at its heart, coupled with models of other Earth system components such as the ocean. The data assimilation system combines the latest weather observations with a recent forecast to obtain the best possible estimate of the current state of the Earth system.

## License

CC-BY-4.0. ECMWF IFS ENS forecast data processed by dynamical.org from ECMWF Open Data.

- [CC-BY-4.0](https://creativecommons.org/licenses/by/4.0/)
- [ECMWF Terms of Use (additional terms)](https://apps.ecmwf.int/datasets/licences/general/)

## Provenance

Produced by [ECMWF](https://www.ecmwf.int/). Processed and hosted by [dynamical.org](https://dynamical.org/).
Source: [ECMWF Open Data](https://www.ecmwf.int/en/forecasts/datasets/open-data).

## Details

### Source

The source grib files this archive is constructed from are provided by [ECMWF Open Data](https://www.ecmwf.int/en/forecasts/datasets/open-data) and accessed from the [AWS Open Data Registry](https://registry.opendata.aws/ecmwf-forecasts/).

ECMWF does not provide user support for the free & open datasets. Users should refer to the public [User Forum](https://forum.ecmwf.int/) for any questions related to the source material.

### Data availability

This dataset contains only forecasts initialized on or after 2024-04-01, which are available at the open data 0.25 degree (~20km) resolution. All variables are available for the full period, save for `categorical_precipitation_type_surface` and `wind_gust_10m`, which are filled with NaNs before 2024-11-13 UTC, and `total_cloud_cover_atmosphere`, which is filled with NaNs before 2025-11-21 UTC.

### Ensemble members

Each forecast contains 51 ensemble members, including a control member (0) and 50 perturbed members (1-50). The control forecast is produced with the best available data and unperturbed models. The other 50 members are each produced with slight perturbations of initial conditions and of the models. Taken together, ensemble of 51 forecasts shows the range of possible outcomes and the likelihood of their occurrence.

### Model updates

IFS is updated regularly. Find details of recent and upcoming
[changes to the forecasting system](https://confluence.ecmwf.int/display/FCST/Changes+to+the+forecasting+system)
on the ECMWF website.

### Storage

Storage for this dataset is generously provided by [Source Cooperative](https://source.coop/), a [Radiant Earth](https://radiant.earth/) initiative. Icechunk storage generously provided by [AWS Open Data](https://aws.amazon.com/opendata/).

### Chunks and shards

This dataset is stored in [Zarr](https://zarr.dev/) format, which splits each variable into a grid of **chunks** — the smallest unit read from storage. Chunks are grouped into larger **shards** (the objects actually written to storage), which keeps the object count manageable for long-archive datasets. When possible, aligning your reads with this dataset's chunk grid can significantly improve data access speed.

The element count and coordinate span of this dataset:

| dimension | chunk | shard |
|---|---|---|
| init_time | 1 (1 day) | 1 (1 day) |
| lead_time | 85 (363 hours) | 85 (363 hours) |
| ensemble_member | 51 | 51 |
| latitude | 32 (8°) | 320 (80°) |
| longitude | 32 (8°) | 320 (80°) |
| **uncompressed** | 16.9 MiB | 1.7 GiB |

### Validation report

Review the [validation report](https://dynamical.org/catalog/ecmwf-ifs-ens-forecast-15-day-0-25-degree/validation/) for variable availability, missing data, known quirks, fill values, value distributions, and sample plots.

### Compression

The data values in this dataset have been rounded in their binary floating point representation to improve compression. See [Klöwer et al. 2021](https://www.nature.com/articles/s43588-021-00156-2) for more information on this approach. The exact number of rounded bits can be found in our [reformatting code](https://github.com/dynamical-org/reformatters/blob/main/src/reformatters/ecmwf/ifs_ens/forecast_15_day_0_25_degree/template_config.py).

## Links

- STAC collection: https://stac-staging.dynamical.org/ecmwf-ifs-ens-forecast-15-day-0-25-degree/collection.json
- Dataset documentation: https://dynamical.org/catalog/ecmwf-ifs-ens-forecast-15-day-0-25-degree/
- Validation report: https://dynamical.org/catalog/ecmwf-ifs-ens-forecast-15-day-0-25-degree/validation/
