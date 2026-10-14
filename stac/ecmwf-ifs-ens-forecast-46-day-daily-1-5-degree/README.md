# ECMWF IFS ENS forecast, 46 day, daily, 1.5 degree

This dataset is an archive of ECMWF IFS ENS sub-seasonal-range forecasts. Forecasts are identified by an initialization time (`init_time`) denoting the start time of the model run, as well as by the `ensemble_member`. Each forecast steps forward along the `lead_time` dimension from 0 to 1104 hours (0 to 46 days) at a 24 hourly step, and carries 101 ensemble members on a global 1.5 degree grid. This dataset contains the 00 UTC initialization times only.

Because the step is 24 hourly, most surface variables are daily means or rates rather than instantaneous values — hence the `average_` prefixes. Surface and single-level variables are at the dataset root; the six variables carried on pressure levels are in the `pressure_level` group.

Note: ECMWF's licence holds sub-seasonal-range forecasts back for 48 hours, so this is not a real-time dataset — each initialization becomes available about two days after its `init_time`.

The Integrated Forecasting System (IFS) is a global forecast model developed by ECMWF. ENS is an ensemble configuration of IFS: 51 ensemble members in the medium range and 101 in the sub-seasonal (extended) range. IFS consists of a numerical model of the Earth system, which includes an atmospheric model at its heart, coupled with models of other Earth system components such as the ocean. The data assimilation system combines the latest weather observations with a recent forecast to obtain the best possible estimate of the current state of the Earth system.

## License

CC-BY-4.0. ECMWF IFS ENS sub-seasonal-range forecast data processed by dynamical.org from the ECMWF Data Store.

- [CC-BY-4.0](https://creativecommons.org/licenses/by/4.0/)
- [ECMWF Terms of Use (additional terms)](https://apps.ecmwf.int/datasets/licences/general/)

## Provenance

Produced by [ECMWF](https://www.ecmwf.int/). Processed and hosted by [dynamical.org](https://dynamical.org/).
Source: [ECMWF Data Store (ECDS)](https://ecds.ecmwf.int/).

## Details

### Source

This archive is built from the ECMWF sub-seasonal-range (S2S) forecast, retrieved from the
[ECMWF Data Store (ECDS)](https://ecds.ecmwf.int/) into the
[dynamical.org ECMWF IFS grib archive](https://source.coop/dynamical/ecmwf-ifs-grib)
on [Source Cooperative](https://source.coop/).

ECMWF does not provide user support for the free & open datasets. Users should refer to the public
[User Forum](https://forum.ecmwf.int/) for any questions related to the source material.

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
| lead_time | 47 (47 days) | 47 (47 days) |
| ensemble_member | 101 | 101 |
| latitude | 25 (37.5°) | 125 (181.5°) |
| longitude | 24 (36°) | 240 (360°) |
| **uncompressed** | 10.9 MiB | 543.3 MiB |

### Validation report

Review the [validation report](https://dynamical.org/catalog/ecmwf-ifs-ens-forecast-46-day-daily-1-5-degree/validation/) for variable availability, missing data, known quirks, fill values, value distributions, and sample plots.

### Compression

The data values in this dataset have been rounded in their binary floating point representation to improve compression. See [Klöwer et al. 2021](https://www.nature.com/articles/s43588-021-00156-2) for more information on this approach. The exact number of rounded bits can be found in our [reformatting code](https://github.com/dynamical-org/reformatters/blob/main/src/reformatters/ecmwf/ifs_ens/forecast_46_day_1_5_degree/template_config.py).

## Links

- STAC collection: https://stac.dynamical.org/ecmwf-ifs-ens-forecast-46-day-daily-1-5-degree/collection.json
- Dataset documentation: https://dynamical.org/catalog/ecmwf-ifs-ens-forecast-46-day-daily-1-5-degree/
- Validation report: https://dynamical.org/catalog/ecmwf-ifs-ens-forecast-46-day-daily-1-5-degree/validation/
