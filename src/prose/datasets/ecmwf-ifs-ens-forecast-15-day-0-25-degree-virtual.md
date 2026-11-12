### Source

The source grib files this archive references are provided by [ECMWF Open Data](https://www.ecmwf.int/en/forecasts/datasets/open-data). Data is read directly from ECMWF's copy on Google Cloud (`gs://ecmwf-open-data`). For forecasts initialized before 13 February 2025, files unavailable from that copy are read from ECMWF's copy in the [AWS Open Data Registry](https://registry.opendata.aws/ecmwf-forecasts/) instead.

ECMWF does not provide user support for the free & open datasets. Users should refer to the public [User Forum](https://forum.ecmwf.int/) for any questions related to the source material.

### Data availability

Some variables and pressure levels cover only part of the archive, matching when ECMWF open data started or stopped publishing them, and are filled with NaNs outside that range. The [validation report]({{ validation_url }}) lists the dates.

### Ensemble members

Each forecast contains 51 ensemble members, including a control member (0) and 50 perturbed members (1-50). The control forecast is produced with the best available data and unperturbed models. The other 50 members are each produced with slight perturbations of initial conditions and of the models. Taken together, ensemble of 51 forecasts shows the range of possible outcomes and the likelihood of their occurrence.

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
