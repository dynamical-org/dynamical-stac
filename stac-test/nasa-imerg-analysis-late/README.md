# NASA IMERG analysis, late

This analysis dataset is an archive of global half-hourly precipitation estimates from NASA GPM IMERG, version 07, on a 0.1 degree grid with dimensions time, latitude, and longitude. This is the Late Run, which incorporates additional satellite sensor input for higher quality, published about 14 hours after observation time.

The Integrated Multi-satellitE Retrievals for GPM (IMERG) is a NASA algorithm that merges precipitation estimates from the constellation of passive microwave satellites in the Global Precipitation Measurement (GPM) mission with microwave-calibrated infrared estimates and monthly gauge analyses to produce a global, gridded, half-hourly precipitation record. IMERG intercalibrates, merges, and interpolates these inputs onto a 0.1 degree grid spanning the TRMM and GPM satellite eras.

## License

CC-BY-4.0. NASA GPM IMERG data processed by dynamical.org from NASA GES DISC and PPS archives.

- [CC-BY-4.0](https://creativecommons.org/licenses/by/4.0/)

## Provenance

Produced by [NASA](https://gpm.nasa.gov/). Processed and hosted by [dynamical.org](https://dynamical.org/).
Source: [GPM IMERG Late Run (GPM_3IMERGHHL) at NASA GES DISC](https://disc.gsfc.nasa.gov/datasets/GPM_3IMERGHHL_07/summary).

## Details

### Early vs. Late Run

NASA produces several IMERG runs from the same input observations at different latencies. This dataset is the **Late Run**, published approximately 14 hours after observation time. It incorporates additional satellite sensor input and applies both forward and backward propagation (morphing) of precipitation features, yielding higher quality than the low-latency Early Run.

The companion [NASA IMERG analysis, early](/catalog/nasa-imerg-analysis-early/) dataset is published about 4 hours after observation time.

### Temporal coverage

IMERG version 07 reprocesses the full record back to 1998, spanning both the Tropical Rainfall Measuring Mission (TRMM, 1998 to 2014) and Global Precipitation Measurement (GPM, 2014 to present) satellite eras. Estimates before the GPM era (mid-2014) rely on a smaller satellite constellation and are generally of lower quality, particularly at high latitudes.

### Source

The source files this archive is constructed from are provided by NASA and accessed from the [GES DISC](https://disc.gsfc.nasa.gov/) archive. Operational low-latency data is additionally accessed from the [NASA Precipitation Processing System (PPS)](https://gpm.nasa.gov/data/directory).

### Storage

Storage for this dataset is generously provided by [AWS Open Data](https://aws.amazon.com/opendata/).

### Chunks and shards

This dataset is stored in [Zarr](https://zarr.dev/) format, which splits each variable into a grid of **chunks** — the smallest unit read from storage. Chunks are grouped into larger **shards** (the objects actually written to storage), which keeps the object count manageable for long-archive datasets. When possible, aligning your reads with this dataset's chunk grid can significantly improve data access speed.

The element count and coordinate span of this dataset:

| dimension | chunk | shard |
|---|---|---|
| time | 1440 (30 days) | 1440 (30 days) |
| latitude | 100 (10°) | 900 (90°) |
| longitude | 100 (10°) | 900 (~90°) |
| **uncompressed** | 54.9 MiB | 4.3 GiB |

### Validation report

Review the [validation report](https://dynamical.org/catalog/nasa-imerg-analysis-late/validation/) for variable availability, missing data, known quirks, fill values, value distributions, and sample plots.

### Compression

The data values in this dataset have been rounded in their binary floating point representation to improve compression. See [Klöwer et al. 2021](https://www.nature.com/articles/s43588-021-00156-2) for more information on this approach. The exact number of rounded bits can be found in our [reformatting code](https://github.com/dynamical-org/reformatters/blob/main/src/reformatters/nasa/imerg/template_config.py).

NASA distributes IMERG precipitation values already rounded to 0.01 mm/hr. Our rounding is relative rather than absolute, and adds less than 0.5% error to each value.

## Links

- STAC collection: https://stac-test.dynamical.org/nasa-imerg-analysis-late/collection.json
- Dataset documentation: https://dynamical.org/catalog/nasa-imerg-analysis-late/
- Validation report: https://dynamical.org/catalog/nasa-imerg-analysis-late/validation/
