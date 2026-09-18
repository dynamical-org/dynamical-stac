### Construction

GEFS starts a new model run every 6 hours and dynamical.org has created this analysis by
concatenating the shortest available forecast step of each run along a 3-hourly time
dimension. Instantaneous variables are read from forecast hour 0 or 3 of the run whose cycle
that time falls in.

Variables that describe a preceding window — accumulations, averages and periodic maxima and
minima — have no meaningful value at hour 0, where the window would be zero length. They are
read instead from forecast hour 6 of the previous run, and describe the window ending at
their timestamp.

Only the control member is used.

### Source

The source grib files this archive is constructed from are provided by
[NOAA Open Data Dissemination (NODD)](https://www.noaa.gov/information-technology/open-data-dissemination)
and accessed from the [AWS Open Data Registry](https://registry.opendata.aws/noaa-gefs/).
This dataset reads the 0.25 degree `pgrb2s` files, which carry a subset of GEFS variables at
the model's highest available resolution.

### Data availability

The archive spans 3-hourly times from 2020-10-01T00 UTC to the present.

Four variables were added by the source after the archive begins and are empty before those
dates:

- From 2022-10-18T12 UTC: `visibility_surface`, `percent_frozen_precipitation_surface` and
  `geopotential_height_cloud_ceiling`.
- From 2021-07-20T12 UTC: `pressure_reduced_to_mean_sea_level_eta_model`.

`storm_relative_helicity_3000_0m` is unusable at 66 scattered times, where the source
publishes a single value repeated across more than 99% of the globe. Most of those values
fall inside the physically plausible range, so they cannot be filtered by magnitude; the
affected timestamps are listed in the validation report. No other variable is affected at any
time.

Several variables carry a `comment` attribute describing values that must be masked or
interpreted specially. Read them before using a variable for the first time.

### Storage

{{ storage_aws_open_data }}

### Chunks

{{ chunking_unsharded }}

### Validation report

{{ validation_report }}
