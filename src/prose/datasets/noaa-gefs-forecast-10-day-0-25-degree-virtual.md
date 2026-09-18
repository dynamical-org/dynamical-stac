### Construction

GEFS starts a new model run every 6 hours. This dataset carries the first 10 days of every
run, 3 hourly along `lead_time`, for the control member and the 30 perturbed members.

Variables that describe a preceding window (accumulations, averages and window maxima and
minima) have no value at lead time 0, where no window precedes the forecast start.
Instantaneous variables are present from lead time 0.

This dataset reads the 0.25 degree `pgrb2s` files, which carry a subset of GEFS variables at
the model's highest available resolution.

### Source

The source grib files this archive is constructed from are provided by
[NOAA Open Data Dissemination (NODD)](https://www.noaa.gov/information-technology/open-data-dissemination)
and accessed from the [AWS Open Data Registry](https://registry.opendata.aws/noaa-gefs/).

### Variable availability

Four variables were added by the source after the archive begins and are empty before those
dates:

- From 2021-07-20T12 UTC: `pressure_reduced_to_mean_sea_level_eta_model`.
- From 2022-10-18T12 UTC: `visibility_surface`, `percent_frozen_precipitation_surface` and
  `geopotential_height_cloud_ceiling`.

The run initialized at 2022-09-21T06 UTC is missing 112 of its 2,511 source files, whose
published GRIB indexes do not match the GRIB files themselves. Every variable is NaN at those
positions: lead times 120 to 132 hours for most ensemble members and 144, 147 and 153 hours
for the control member.

### Storage

{{ storage_aws_open_data }}

### Chunks

{{ chunking_unsharded }}

### Validation report

{{ validation_report }}
