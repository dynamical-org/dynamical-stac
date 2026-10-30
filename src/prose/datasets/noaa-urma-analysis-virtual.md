### Construction

This dataset is constructed by concatenating NOAA's URMA analyses along the time
dimension, using virtual references to the source GRIB files.

### Source

Source files are provided by [NOAA Open Data Dissemination](https://www.noaa.gov/information-technology/open-data-dissemination)
in the public [NOAA URMA archive](https://registry.opendata.aws/noaa-rtma/).

### Data availability

Significant wave height is available from 2018-12-03 12:00 UTC. Earlier fields
are excluded because they use zero for both land and calm water.
Great Lakes wave values are available from 2020-07-27 12:00 UTC.

### Storage

{{ storage_aws_open_data }}

### Chunks

{{ chunking_unsharded }}

### Validation report

{{ validation_report }}
