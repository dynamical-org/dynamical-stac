### Source

The source grib files this archive references are provided by [ECMWF Open Data](https://www.ecmwf.int/en/forecasts/datasets/open-data). Data is read directly from ECMWF's copy on Google Cloud (`gs://ecmwf-open-data`). For forecasts initialized before 1 March 2025, files unavailable from that copy are read from ECMWF's copy in the [AWS Open Data Registry](https://registry.opendata.aws/ecmwf-forecasts/) instead.

ECMWF does not provide user support for the free & open datasets. Users should refer to the public [User Forum](https://forum.ecmwf.int/) for any questions related to the source material.

### Model updates

AIFS is updated regularly. Find details of recent and upcoming
[changes to the forecasting system](https://confluence.ecmwf.int/display/FCST/Changes+to+the+forecasting+system)
on the ECMWF website.

### Storage

{{ storage_aws_open_data }}

### Chunks

{{ chunking_unsharded }}

### Validation report

{{ validation_report }}
