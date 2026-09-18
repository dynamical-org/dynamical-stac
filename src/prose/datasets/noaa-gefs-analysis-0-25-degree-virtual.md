### Construction

GEFS starts a new model run every 6 hours and dynamical.org has created this analysis by
concatenating the shortest usable forecast step of each run along the time dimension.
Instantaneous variables are read from forecast hour 0 or 3, and variables that describe a
preceding window (accumulations, averages and window maxima and minima) are read from
forecast hour 3 or 6.

Only the control member is used.

This dataset reads the 0.25 degree `pgrb2s` files, which carry a subset of GEFS variables at
the model's highest available resolution.

### Source

The source grib files this archive is constructed from are provided by
[NOAA Open Data Dissemination (NODD)](https://www.noaa.gov/information-technology/open-data-dissemination)
and accessed from the [AWS Open Data Registry](https://registry.opendata.aws/noaa-gefs/).

### Variable availability

Four variables were added by the source after the archive begins and are empty before those
dates:

- From 2022-10-18T12 UTC: `visibility_surface`, `percent_frozen_precipitation_surface` and
  `geopotential_height_cloud_ceiling`.
- From 2021-07-20T12 UTC: `pressure_reduced_to_mean_sea_level_eta_model`.

### Storage

{{ storage_aws_open_data }}

### Chunks

{{ chunking_unsharded }}

### Validation report

{{ validation_report }}
