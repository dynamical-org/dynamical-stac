### Construction

RTMA Rapid Update (RTMA-RU) analyses every 15 minutes are represented as virtual
references to NOAA's CONUS Western Expansion GRIB files, on their native 2345 by
1597 Lambert Conformal Conic grid. Each chunk contains one complete field at one
analysis time. The 13 fields include temperature, dew point, specific humidity,
surface pressure, terrain height, wind, cloud cover, ceiling, and visibility.
Precipitation is not included.

Wind components are grid-relative; wind direction is relative to true north.
Ceiling and visibility retain the source's finite values. Their historical
bounds vary, and ceiling's vertical reference is not established for this archive.
Consult the validation report before interpreting these fields across eras.

### Source

Source files are provided by [NOAA Open Data Dissemination](https://www.noaa.gov/information-technology/open-data-dissemination)
in the public [NOAA RTMA archive](https://registry.opendata.aws/noaa-rtma/).

### Data availability

The archive begins at 2017-12-13 00:00 UTC and updates every 15 minutes. Missing
source files remain gaps. Total cloud cover begins at 2020-07-28 00:00 UTC;
earlier positions are missing. See the [validation report]({{ validation_url }})
for checked coverage, source-archive gaps, and the ceiling/visibility findings.

### Storage

{{ storage_aws_open_data }}

### Chunks

{{ chunking_unsharded }}

### Validation report

{{ validation_report }}
