### Source

The source grib files this archive references are provided by [ECMWF Open Data](https://www.ecmwf.int/en/forecasts/datasets/open-data). Data is read directly from ECMWF's copy on Google Cloud (`gs://ecmwf-open-data`).

ECMWF does not provide user support for the free & open datasets. Users should refer to the public [User Forum](https://forum.ecmwf.int/) for any questions related to the source material.

### Data availability

Some variables and pressure levels start partway through the archive, when ECMWF open data started publishing them, and are filled with NaNs before then. The [validation report]({{ validation_url }}) lists the dates.

### Model updates

AIFS ENS is updated annually. Find details of recent and upcoming
[changes to the forecasting system](https://confluence.ecmwf.int/display/FCST/Changes+to+the+forecasting+system)
on the ECMWF website.

### Storage

{{ storage_aws_open_data }}

### Chunks

{{ chunking_unsharded }}

### Validation report

{{ validation_report }}
