# DWD ICON-EU forecast, 5 day

This dataset is an archive of past and present ICON-EU forecasts. Forecasts are identified by an initialization time (`init_time`) denoting the start time of the model run and step forward in time along the `lead_time` dimension. This dataset contains only the 00, 06, 12, and 18 hour UTC initialization times which produce the full length, 5 day forecast.

ICON-EU is a regional weather forecast model operated by Deutscher Wetterdienst (DWD), Germany's national meteorological service. ICON-EU is a nested configuration of DWD's global ICON (Icosahedral Non-hydrostatic) model that provides high-resolution forecasts over Europe.

## License

CC-BY-4.0. DWD ICON-EU data processed by dynamical.org.

- [CC-BY-4.0](https://creativecommons.org/licenses/by/4.0/)

## Provenance

Produced by [Deutscher Wetterdienst (DWD)](https://www.dwd.de/). Processed and hosted by [dynamical.org](https://dynamical.org/).
Source: [DWD Open Data](https://www.dwd.de/EN/ourservices/opendata/opendata.html).

## Details

### Source

The source grib files this archive is constructed from are provided by
[DWD Open Data](https://www.dwd.de/EN/ourservices/opendata/opendata.html)
and the [dynamical.org DWD ICON grib archive](https://source.coop/dynamical/dwd-icon-grib)
on [Source Cooperative](https://source.coop/).

### Storage

Icechunk storage generously provided by [AWS Open Data](https://aws.amazon.com/opendata/).
Storage for the dynamical.org DWD ICON-EU grib archive is generously provided by
[Source Cooperative](https://source.coop/), a [Radiant Earth](https://radiant.earth/) initiative.

### Chunks and shards

This dataset is stored in [Zarr](https://zarr.dev/) format, which splits each variable into a grid of **chunks** — the smallest unit read from storage. Chunks are grouped into larger **shards** (the objects actually written to storage), which keeps the object count manageable for long-archive datasets. When possible, aligning your reads with this dataset's chunk grid can significantly improve data access speed.

The element count and coordinate span of this dataset:

| dimension | chunk | shard |
|---|---|---|
| init_time | 1 (6 hours) | 1 (6 hours) |
| lead_time | 93 (121 hours) | 93 (121 hours) |
| latitude | 219 (13.6875°) | 657 (41.0625°) |
| longitude | 153 (9.5625°) | 1377 (86.0625°) |
| **uncompressed** | 11.9 MiB | 321.0 MiB |

### Validation report

Review the [validation report](https://dynamical.org/catalog/dwd-icon-eu-forecast-5-day/validation/) for variable availability, missing data, known quirks, fill values, value distributions, and sample plots.

### Compression

The data values in this dataset have been rounded in their binary floating point representation to improve compression. See [Klöwer et al. 2021](https://www.nature.com/articles/s43588-021-00156-2) for more information on this approach. The exact number of rounded bits can be found in our [reformatting code](https://github.com/dynamical-org/reformatters/blob/main/src/reformatters/dwd/icon_eu/forecast_5_day/template_config.py).

## Links

- STAC collection: https://stac-test.dynamical.org/dwd-icon-eu-forecast-5-day/collection.json
- Dataset documentation: https://dynamical.org/catalog/dwd-icon-eu-forecast-5-day/
- Validation report: https://dynamical.org/catalog/dwd-icon-eu-forecast-5-day/validation/
