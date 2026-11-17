### Source

Forecasts initialized on or after 2024-04-01 are built from source grib files provided by
[ECMWF Open Data](https://www.ecmwf.int/en/forecasts/datasets/open-data)
and accessed from the [AWS Open Data Registry](https://registry.opendata.aws/ecmwf-forecasts/).
Earlier forecasts are built from ECMWF's MARS archive, retrieved into the
[dynamical.org ECMWF IFS grib archive](https://source.coop/dynamical/ecmwf-ifs-grib)
on [Source Cooperative](https://source.coop/).

ECMWF does not provide user support for the free & open datasets. Users should refer to the public
[User Forum](https://forum.ecmwf.int/) for any questions related to the source material.

### Data availability

This dataset contains forecasts initialized from 2020-10-15 to the present at 0.25 degree (~20km) resolution. All variables are available for the full period, save for `categorical_precipitation_type_surface` and `wind_gust_10m`, which are filled with NaNs for forecasts initialized 2024-04-01 through 2024-11-12 UTC, and `total_cloud_cover_atmosphere`, which is filled with NaNs for forecasts initialized 2024-04-01 through 2025-11-20 UTC.

### Ensemble members

Each forecast contains 51 ensemble members, including a control member (0) and 50 perturbed members (1-50). The control forecast is produced with the best available data and unperturbed models. The other 50 members are each produced with slight perturbations of initial conditions and of the models. Taken together, ensemble of 51 forecasts shows the range of possible outcomes and the likelihood of their occurrence.

### Model updates

IFS is updated regularly. Find details of recent and upcoming
[changes to the forecasting system](https://confluence.ecmwf.int/display/FCST/Changes+to+the+forecasting+system)
on the ECMWF website.

### Storage

{{ storage }}

### Chunks and shards

{{ chunking }}

### Validation report

{{ validation_report }}

### Compression

{{ compression }}
