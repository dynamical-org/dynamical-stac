This dataset is available in the staging catalog. For the dynamical-catalog
example, set `DYNAMICAL_STAC_CATALOG_URL=https://stac-staging.dynamical.org/catalog.json`
before starting Python. The pystac example selects the staging catalog directly.

### Construction

Hourly RTMA analyses are represented as virtual references to NOAA's CONUS
Western Expansion GRIB files, on their native 2345 by 1597 Lambert Conformal
Conic grid. Each chunk contains one complete field at one analysis time.
The 13 fields include temperature, dew point, specific humidity, surface pressure,
terrain height, wind, cloud cover, ceiling, and visibility. Precipitation is not included.

Wind components are grid-relative; wind direction is relative to true north.
Ceiling and visibility retain the source's finite values. Consult the validation
report for their interpretation and historical limitations.

### Source

Source files are provided by [NOAA Open Data Dissemination](https://www.noaa.gov/information-technology/open-data-dissemination)
in the public [NOAA RTMA archive](https://registry.opendata.aws/noaa-rtma/).

### Data availability

The archive begins at 2017-05-02 00:00 UTC and updates hourly. Missing source
files remain gaps. See the [validation report](https://dataset-validation-reports.dynamical.org/noaa-rtma-analysis-virtual/latest/validation_report.html) for checked
coverage, source-archive gaps, and the ceiling/visibility findings.

### Storage

{{ storage_aws_open_data }}

### Chunks

{{ chunking_unsharded }}

### Validation report

{{ validation_report }}

The [standalone report](https://dataset-validation-reports.dynamical.org/noaa-rtma-analysis-virtual/latest/validation_report.html) is also available while the dataset is in staging.
