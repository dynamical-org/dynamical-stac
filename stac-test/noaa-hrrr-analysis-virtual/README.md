# NOAA HRRR analysis, virtual

This analysis dataset is an archive of the model's best estimate of past weather, optimized for spatial (map) access patterns. It is created by concatenating the first hour of each historical forecast to provide a dataset with dimensions time, x, and y.

This dataset uses the native HRRR Lambert Conformal Conic projection, with spatial indexing along the `x` and `y` dimensions. The example notebook shows how to use the embedded spatial reference to select geographic areas of interest.

Note: `dynamical-catalog>=0.8.0` (or `zarr>=3.2 icechunk>=2.0 gribberish>=1.5`) is required.

The High-Resolution Rapid Refresh (HRRR) is a NOAA real-time 3-km resolution, hourly updated, cloud-resolving, convection-allowing atmospheric model, initialized by 3km grids with 3km radar assimilation. Radar data is assimilated in the HRRR every 15 min over a 1-h period adding further detail to that provided by the hourly data assimilation from the 13km radar-enhanced Rapid Refresh.

## License

CC-BY-4.0. NOAA NWS NCEP HRRR data processed by dynamical.org from NOAA Open Data Dissemination archives.

- [CC-BY-4.0](https://creativecommons.org/licenses/by/4.0/)

## Provenance

Produced by [NOAA NWS NCEP](https://www.weather.gov/ncep/). Processed and hosted by [dynamical.org](https://dynamical.org/).
Source: [NOAA HRRR on NOAA Open Data Dissemination](https://registry.opendata.aws/noaa-hrrr-pds/).

## Details

### Construction

HRRR starts a new model run every hour and dynamical.org has created this analysis by
concatenating the shortest available forecast step of each run along the time dimension.
Instantaneous variables are read from forecast hour 0 of the run initialized at that time.

Variables that describe the preceding hour — accumulations and hourly maxima and minima —
have no value at hour 0, so they are read from forecast hour 1 of the run initialized an
hour earlier and describe the hour ending at their timestamp. A few instantaneous fields
that HRRR does not diagnose at hour 0, including precipitation rate, the lightning fields
and aerosol optical thickness, are read from forecast hour 1 as well.

### Source

The source grib files this archive is constructed from are provided by [NOAA Open Data Dissemination (NODD)](https://www.noaa.gov/information-technology/open-data-dissemination) and accessed from the [AWS Open Data Registry](https://registry.opendata.aws/noaa-hrrr-pds/). Operational data is additionally accessed from [NOAA NOMADS](https://nomads.ncep.noaa.gov/).

### Data availability

The archive spans hourly times from 2014-10-01T00 UTC to the present. Many fields change
behavior at the HRRR version upgrades — version 2 on 2016-08-23, version 3 on 2018-07-12
and version 4 on 2020-12-02 — and a number of variables begin at one of those dates. See
the [validation report](https://dynamical.org/catalog/noaa-hrrr-analysis-virtual/validation/) for details.

### Storage

Storage for this dataset is generously provided by [AWS Open Data](https://aws.amazon.com/opendata/).

### Chunks

This dataset is stored in [Zarr](https://zarr.dev/) format, which splits each variable into a grid of **chunks** — the smallest unit read from storage. When possible, aligning your reads with this dataset's chunk grid can significantly improve data access speed.

The element count and coordinate span of this dataset:

| dimension | chunk |
|---|---|
| time | 1 (1 hour) |
| y | 1059 (3177 km) |
| x | 1799 (5397 km) |
| **uncompressed** | 14.5 MiB |

### Validation report

Review the [validation report](https://dynamical.org/catalog/noaa-hrrr-analysis-virtual/validation/) for variable availability, missing data, known quirks, fill values, value distributions, and sample plots.

## Links

- STAC collection: https://stac-test.dynamical.org/noaa-hrrr-analysis-virtual/collection.json
- Dataset documentation: https://dynamical.org/catalog/noaa-hrrr-analysis-virtual/
- Validation report: https://dynamical.org/catalog/noaa-hrrr-analysis-virtual/validation/
