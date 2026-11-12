### Source

The source grib files this archive references are provided by [ECMWF Open Data](https://www.ecmwf.int/en/forecasts/datasets/open-data). Data is read directly from ECMWF's copy on Google Cloud (`gs://ecmwf-open-data`) and AWS Open Data (`s3://ecmwf-forecasts`).

ECMWF does not provide user support for the free & open datasets. Users should refer to the public [User Forum](https://forum.ecmwf.int/) for any questions related to the source material.

### Data availability

Some variables and pressure levels cover only part of the archive, matching when ECMWF open data started or stopped publishing them, and are filled with NaNs outside that range. The [validation report]({{ validation_url }}) lists the dates.

### Model updates

IFS is updated regularly. Find details of recent and upcoming
[changes to the forecasting system](https://confluence.ecmwf.int/display/FCST/Changes+to+the+forecasting+system)
on the ECMWF website.

### Storage

{{ storage_aws_open_data }}

### Chunks

{{ chunking_unsharded }}

### Validation report

{{ validation_report }}
