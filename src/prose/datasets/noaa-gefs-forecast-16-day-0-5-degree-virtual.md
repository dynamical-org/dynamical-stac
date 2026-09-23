### Source

The source grib files this archive is constructed from are provided by
[NOAA Open Data Dissemination (NODD)](https://www.noaa.gov/information-technology/open-data-dissemination)
and accessed from the [AWS Open Data Registry](https://registry.opendata.aws/noaa-gefs/).

### Variable availability

`five_wave_geopotential_height_500mb` is NaN for eight fields the source published without
that record: the run initialized 2023-04-26T12 UTC at lead 240 h for members 11, 12, 16, 18, 20
and 22 and at lead 288 h for member 0, and the run initialized 2025-07-01T18 UTC at lead 24 h for
member 28. Every other variable is present there.

### Storage

{{ storage_aws_open_data }}

### Chunks

{{ chunking_unsharded }}

### Validation report

{{ validation_report }}
