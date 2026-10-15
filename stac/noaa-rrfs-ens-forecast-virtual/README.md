# NOAA RRFS ENS forecast, virtual

This dataset is an archive of past and present RRFS ensemble forecasts, optimized for spatial (map) access patterns. Forecasts are identified by an initialization time (`init_time`) denoting the start time of the model run, and step forward hourly along the `lead_time` dimension out to 60 hours. Each forecast has six members along the `ensemble_member` dimension: member 0 is the deterministic RRFS forecast and members 1 to 5 are perturbed.

This dataset uses the native RRFS Lambert Conformal Conic projection, with spatial indexing along the `x` and `y` dimensions. The example notebook shows how to use the embedded spatial reference to select geographic areas of interest.

Variables on pressure levels live in the `pressure_level` group.

Note: `dynamical-catalog>=1.0.1` and `gribberish>=1.8.4` (or `zarr>=3.2 icechunk>=2.0 gribberish>=1.8.4`) are required.

The Rapid Refresh Forecast System ensemble (RRFS ENS) is a National Oceanic and Atmospheric Administration (NOAA) National Centers for Environmental Prediction (NCEP) convection-allowing ensemble with a 3 km grid. Five members run with different initial conditions, lateral boundary conditions and model physics from the deterministic RRFS forecast, to better cover the range of forecast possibilities. REFS combines these members with the deterministic RRFS and HRRR into ensemble products.

NOAA RRFS ENS is pre-operational, so expect changes to the model data and to the structure of this dataset.

## License

CC-BY-4.0. NOAA NWS NCEP RRFS ensemble data processed by dynamical.org from NOAA Open Data Dissemination archives.

- [CC-BY-4.0](https://creativecommons.org/licenses/by/4.0/)

## Provenance

Produced by [NOAA NWS NCEP](https://www.weather.gov/ncep/). Processed and hosted by [dynamical.org](https://dynamical.org/).
Source: [NOAA RRFS and REFS on NOAA Open Data Dissemination](https://registry.opendata.aws/noaa-rrfs-ops/).

## Details

### Source

The source grib files this archive is constructed from are provided by [NOAA Open Data Dissemination (NODD)](https://www.noaa.gov/information-technology/open-data-dissemination) and accessed from the [AWS Open Data Registry](https://registry.opendata.aws/noaa-rrfs-ops/).

### Storage

Storage for this dataset is generously provided by [AWS Open Data](https://aws.amazon.com/opendata/).

### Chunks

This dataset is stored in [Zarr](https://zarr.dev/) format, which splits each variable into a grid of **chunks** — the smallest unit read from storage. When possible, aligning your reads with this dataset's chunk grid can significantly improve data access speed.

The element count and coordinate span of this dataset:

| dimension | chunk |
|---|---|
| init_time | 1 (6 hours) |
| ensemble_member | 1 |
| lead_time | 1 (1 hour) |
| y | 1059 (3177 km) |
| x | 1799 (5397 km) |
| **uncompressed** | 14.5 MiB |

### Validation report

Review the [validation report](https://dynamical.org/catalog/noaa-rrfs-ens-forecast-virtual/validation/) for variable availability, missing data, known quirks, fill values, value distributions, and sample plots.

## Links

- STAC collection: https://stac.dynamical.org/noaa-rrfs-ens-forecast-virtual/collection.json
- Dataset documentation: https://dynamical.org/catalog/noaa-rrfs-ens-forecast-virtual/
- Validation report: https://dynamical.org/catalog/noaa-rrfs-ens-forecast-virtual/validation/
