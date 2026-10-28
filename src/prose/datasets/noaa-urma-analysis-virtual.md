### Construction

Hourly URMA analyses incorporate observations received after RTMA. They are
represented as virtual references to NOAA's CONUS Western Expansion GRIB files,
on their native 2345 by 1597 Lambert Conformal Conic grid. Each chunk contains
one complete field at one analysis time. The 14 fields include temperature,
dew point, specific humidity, surface pressure, terrain height, wind, cloud cover,
ceiling, visibility, and significant wave height. Precipitation is not included.

Wind components are grid-relative; wind direction is relative to true north.
Ceiling and visibility retain the source's finite values. Their historical
bounds vary, and ceiling's vertical reference is not established for this archive.
Consult the validation report before interpreting these fields across eras.

### Source

Source files are provided by [NOAA Open Data Dissemination](https://www.noaa.gov/information-technology/open-data-dissemination)
in the public [NOAA URMA archive](https://registry.opendata.aws/noaa-rtma/).

### Data availability

The archive begins at 2017-05-02 00:00 UTC and updates hourly. Missing source
files remain gaps. Significant wave height begins at 2018-12-03 12:00 UTC;
earlier fields are excluded because they mix land zeros with calm-water zeros.
Wave height is missing where no wave analysis is made,
including land and ice-covered water. Great Lakes wave values begin at
2020-07-27 12:00 UTC. See the [validation report]({{ validation_url }}) for
checked coverage, source-archive gaps, and historical field limitations.

### Storage

{{ storage_aws_open_data }}

### Chunks

{{ chunking_unsharded }}

### Validation report

{{ validation_report }}
