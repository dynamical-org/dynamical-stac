# NOAA HRRR forecast, 48 hour

This dataset is an archive of past and present HRRR forecasts. Forecasts are identified by an initialization time (`init_time`) denoting the start time of the model run. Each forecast has an hourly forecast step along the `lead_time` dimension. This dataset contains only the 00, 06, 12, and 18 hour UTC initialization times which produce the full length, 48 hour forecast.

This dataset uses the native HRRR Lambert Conformal Conic projection, with spatial indexing along the `x` and `y` dimensions. The example notebook shows how to use the embedded spatial reference to select geographic areas of interest.

The High-Resolution Rapid Refresh (HRRR) is a NOAA real-time 3-km resolution, hourly updated, cloud-resolving, convection-allowing atmospheric model, initialized by 3km grids with 3km radar assimilation. Radar data is assimilated in the HRRR every 15 min over a 1-h period adding further detail to that provided by the hourly data assimilation from the 13km radar-enhanced Rapid Refresh.

## License

CC-BY-4.0. NOAA NWS NCEP HRRR data processed by dynamical.org from NOAA Open Data Dissemination archives.

- [CC-BY-4.0](https://creativecommons.org/licenses/by/4.0/)

## Provenance

Produced by [NOAA NWS NCEP](https://www.weather.gov/ncep/). Processed and hosted by [dynamical.org](https://dynamical.org/).
Source: [NOAA HRRR on NOAA Open Data Dissemination](https://registry.opendata.aws/noaa-hrrr-pds/).

## Details

### Source

The source grib files this archive is constructed from are provided by [NOAA Open Data Dissemination (NODD)](https://www.noaa.gov/information-technology/open-data-dissemination) and accessed from the [AWS Open Data Registry](https://registry.opendata.aws/noaa-hrrr-pds/). Operational data is additionally accessed from [NOAA NOMADS](https://nomads.ncep.noaa.gov/).

### Data availability

Forecasts initialized through 2020-12-02T06 UTC include data only for the first 36 hours; steps 37–48 are filled with NaNs. Starting with the 2020-12-02T12 UTC initialization, forecasts cover the full 48 hours.

### Storage

Storage for this dataset is generously provided by [Source Cooperative](https://source.coop/), a [Radiant Earth](https://radiant.earth/) initiative. Icechunk storage generously provided by [AWS Open Data](https://aws.amazon.com/opendata/).

### Chunks and shards

This dataset is stored in [Zarr](https://zarr.dev/) format, which splits each variable into a grid of **chunks** — the smallest unit read from storage. Chunks are grouped into larger **shards** (the objects actually written to storage), which keeps the object count manageable for long-archive datasets. When possible, aligning your reads with this dataset's chunk grid can significantly improve data access speed.

The element count and coordinate span of this dataset:

| dimension | chunk | shard |
|---|---|---|
| init_time | 1 (6 hours) | 1 (6 hours) |
| lead_time | 49 (49 hours) | 49 (49 hours) |
| y | 265 (795 km) | 1060 (3177 km) |
| x | 300 (900 km) | 1800 (5397 km) |
| **uncompressed** | 14.9 MiB | 356.6 MiB |

### Validation report

Review the [validation report](https://dynamical.org/catalog/noaa-hrrr-forecast-48-hour/validation/) for variable availability, missing data, known quirks, fill values, value distributions, and sample plots.

### Compression

The data values in this dataset have been rounded in their binary floating point representation to improve compression. See [Klöwer et al. 2021](https://www.nature.com/articles/s43588-021-00156-2) for more information on this approach. The exact number of rounded bits can be found in our [reformatting code](https://github.com/dynamical-org/reformatters/).

## Links

- STAC collection: https://stac.dynamical.org/noaa-hrrr-forecast-48-hour/collection.json
- Dataset documentation: https://dynamical.org/catalog/noaa-hrrr-forecast-48-hour/
- Validation report: https://dynamical.org/catalog/noaa-hrrr-forecast-48-hour/validation/
