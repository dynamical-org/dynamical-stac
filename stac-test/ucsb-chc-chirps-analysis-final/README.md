# UCSB CHC CHIRPS analysis, final

Daily CHIRPS version 3 precipitation over land from 60 degrees south to 60 degrees north, at 0.05 degree resolution, from 1981 onward. This is the final product, using the reanalysis-based daily distribution (final/rnl).

The Climate Hazards Center Infrared Precipitation with Stations (CHIRPS) version 3 combines satellite estimates and station observations into a precipitation record over land.

## License

CC-BY-4.0. UCSB Climate Hazards Center CHIRPS version 3.0 data processed by dynamical.org from the Climate Hazards Center data archive. Funk, C., Peterson, P., Harrison, L. et al. The Climate Hazards Center Infrared Precipitation with Stations, Version 3. Sci Data 13, 718 (2026), data https://doi.org/10.15780/G2JQ0P.

- [CC-BY-4.0](https://creativecommons.org/licenses/by/4.0/)

## Provenance

Produced by [UCSB Climate Hazards Center](https://www.chc.ucsb.edu/). Processed and hosted by [dynamical.org](https://dynamical.org/).
Source: [CHIRPS v3 at the UCSB Climate Hazards Center](https://www.chc.ucsb.edu/data/chirps3).

## Details

### Product

Final is released monthly, usually two to three weeks after the end of the month. It uses the best available rain-gauge reports with more quality checks than preliminary. ERA5 rainfall is used to split five-day CHIRPS totals into daily amounts.

### Source

The [CHIRPS v3 documentation](https://www.chc.ucsb.edu/data/chirps3) describes the products and release schedule. Source files are provided by the [UCSB Climate Hazards Center daily archive](https://data.chc.ucsb.edu/products/CHIRPS/v3.0/daily/final/rnl/).

### Storage

Storage for this dataset is generously provided by [AWS Open Data](https://aws.amazon.com/opendata/).

### Chunks and shards

This dataset is stored in [Zarr](https://zarr.dev/) format, which splits each variable into a grid of **chunks** — the smallest unit read from storage. Chunks are grouped into larger **shards** (the objects actually written to storage), which keeps the object count manageable for long-archive datasets. When possible, aligning your reads with this dataset's chunk grid can significantly improve data access speed.

The element count and coordinate span of this dataset:

| dimension | chunk | shard |
|---|---|---|
| time | 365 (365 days) | 365 (365 days) |
| latitude | 60 (3°) | 1200 (60°) |
| longitude | 60 (3°) | 1800 (~90°) |
| **uncompressed** | 5.0 MiB | 2.9 GiB |

### Validation report

Review the [validation report](https://dynamical.org/catalog/ucsb-chc-chirps-analysis-final/validation/) for variable availability, missing data, known quirks, fill values, value distributions, and sample plots.

### Compression

The data values in this dataset have been rounded in their binary floating point representation to improve compression. See [Klöwer et al. 2021](https://www.nature.com/articles/s43588-021-00156-2) for more information on this approach. The exact number of rounded bits can be found in our [reformatting code](https://github.com/dynamical-org/reformatters/blob/main/src/reformatters/ucsb_chc/chirps/template_config.py).

## Links

- STAC collection: https://stac-test.dynamical.org/ucsb-chc-chirps-analysis-final/collection.json
- Dataset documentation: https://dynamical.org/catalog/ucsb-chc-chirps-analysis-final/
- Validation report: https://dynamical.org/catalog/ucsb-chc-chirps-analysis-final/validation/
