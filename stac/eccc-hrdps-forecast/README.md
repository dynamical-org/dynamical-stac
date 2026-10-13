# ECCC HRDPS forecast

This dataset is an archive of past and present HRDPS continental forecasts. Forecasts are identified by four daily initialization times (`init_time`) denoting the start of the model run and step forward in time along the `lead_time` dimension, hourly out to 48 hours.

The High Resolution Deterministic Prediction System (HRDPS) is the 2.5 km limited-area weather forecast model operated by Environment and Climate Change Canada (ECCC), Canada's national meteorological service. Its continental domain covers Canada and the northern United States at a resolution that captures fine-scale weather features.

## License

CC-BY-4.0. ECCC HRDPS data processed by dynamical.org from Environment and Climate Change Canada, used under the ECCC Data Servers End-use Licence version 2.1 (https://eccc-msc.github.io/open-data/licence/readme_en/).

- [CC-BY-4.0](https://creativecommons.org/licenses/by/4.0/)
- [ECCC Data Servers End-use Licence (additional terms)](https://eccc-msc.github.io/open-data/licence/readme_en/)

## Provenance

Produced by [Environment and Climate Change Canada (ECCC)](https://eccc-msc.github.io/open-data/readme_en/). Processed and hosted by [dynamical.org](https://dynamical.org/).
Source: [HRDPS on ECCC MSC Open Data](https://eccc-msc.github.io/open-data/msc-data/nwp_hrdps/readme_hrdps-datamart_en/).

## Details

### Source

The source grib files this archive is constructed from are provided by
[ECCC MSC Open Data](https://eccc-msc.github.io/open-data/msc-data/nwp_hrdps/readme_hrdps-datamart_en/)
and the [dynamical.org ECCC HRDPS grib archive](https://source.coop/dynamical/eccc-hrdps-grib)
on [Source Cooperative](https://source.coop/).

### Storage

Icechunk storage generously provided by [AWS Open Data](https://aws.amazon.com/opendata/).
Storage for the dynamical.org ECCC HRDPS grib archive is generously provided by
[Source Cooperative](https://source.coop/), a [Radiant Earth](https://radiant.earth/) initiative.

### Chunks and shards

This dataset is stored in [Zarr](https://zarr.dev/) format, which splits each variable into a grid of **chunks** — the smallest unit read from storage. Chunks are grouped into larger **shards** (the objects actually written to storage), which keeps the object count manageable for long-archive datasets. When possible, aligning your reads with this dataset's chunk grid can significantly improve data access speed.

The element count and coordinate span of this dataset:

| dimension | chunk | shard |
|---|---|---|
| init_time | 1 (6 hours) | 1 (6 hours) |
| lead_time | 49 (49 hours) | 49 (49 hours) |
| y | 258 (~5.805°) | 1290 (29.025°) |
| x | 254 (~5.715°) | 2540 (57.15°) |
| **uncompressed** | 12.2 MiB | 612.5 MiB |

### Validation report

Review the [validation report](https://dynamical.org/catalog/eccc-hrdps-forecast/validation/) for variable availability, missing data, known quirks, fill values, value distributions, and sample plots.

### Compression

The data values in this dataset have been rounded in their binary floating point representation to improve compression. See [Klöwer et al. 2021](https://www.nature.com/articles/s43588-021-00156-2) for more information on this approach. The exact number of rounded bits can be found in our [reformatting code](https://github.com/dynamical-org/reformatters/blob/main/src/reformatters/eccc/hrdps/forecast/template_config.py).

## Links

- STAC collection: https://stac.dynamical.org/eccc-hrdps-forecast/collection.json
- Dataset documentation: https://dynamical.org/catalog/eccc-hrdps-forecast/
- Validation report: https://dynamical.org/catalog/eccc-hrdps-forecast/validation/
