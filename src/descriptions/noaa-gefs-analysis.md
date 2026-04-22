This analysis dataset is an archive of the model's best estimate of past weather.
It is created by concatenating the first few hours of each historical forecast to
provide a dataset with dimensions time, latitude, and longitude.

## Sources

To provide the longest possible historical record, this dataset in constructed
from three distinct GEFS forecast archives.

* From 2000-01-01 to 2019-12-31 we use the [GEFS reforecast](https://registry.opendata.aws/noaa-gefs-reforecast/).
* From 2020-01-01 to 2020-09-23 we use [GEFS forecast archive](https://registry.opendata.aws/noaa-gefs/) data which has a lower spatial and temporal resolution.
* From 2020-09-23 to Present we use [GEFS operational forecast archives](https://registry.opendata.aws/noaa-gefs/).

Source files are provided by [NOAA Open Data Dissemination (NODD)](https://www.noaa.gov/information-technology/open-data-dissemination)
and accessed from the [AWS Open Data Registry](https://registry.opendata.aws/noaa-gefs/).
Operational data is additionally accessed from [NOAA NOMADS](https://nomads.ncep.noaa.gov/).

## Variable availability

Data is available for all variables at all times with the following exceptions.

* Unavailable before 2020-01-01: `relative_humidity_2m`, `percent_frozen_precipitation_surface`, `categorical_freezing_rain_surface`, `categorical_ice_pellets_surface`, `categorical_rain_surface`, `categorical_snow_surface`
* Unavailable 2020-01-01T00 to 2020-09-22T21: `geopotential_height_cloud_ceiling`

## Construction

To create a single time dimension we concatenate the first few hours of each forecast.
From 2000-01-01 to 2019-12-31 reforecasts are available once per day and this dataset
uses the first 21 or 24 hours of each forecast. From 2020-01-01 to present forecasts
are available every 6 hours and this dataset uses the first 3 or 6 hours of each forecast.
Variables with an instantaneous `step_type` use the shortest possible lead times
(e.g. 0 and 3 hours) while accumulated variables must use one additional forecast
step (e.g. 3 and 6 hours) because they do not have an hour 0 forecast value.

## Interpolation

For most of the time range of the archive the source data is available at 0.25-degree
resolution and a 3 hourly time step and we perform no interpolation. There are two
exceptions to this. 1) From 2020-01-01 to 2020-09-23 the source data has a 1.0-degree
spatial resolution and a 6 hourly time step. 2) From 2020-09-23 to present the 100m
wind components have a 0.5-degree spatial resolution in the source data.
To provide a consistent archive in the above two cases we first perform bilinear
interpolation in space to 0.25-degree resolution followed by linear interpolation in time
to a 3-hourly timestep if necessary. The original, uninterpolated data can be obtained
by selecting latitudes and longitudes evenly divisible by 1 and, in case 1), time steps
whose hour is divisible by 6.

## Storage

Storage for this dataset is generously provided by
[Source Cooperative](https://source.coop/),
a [Radiant Earth](https://radiant.earth/) initiative.
Icechunk storage generously provided by [AWS Open Data](https://aws.amazon.com/opendata/).

## Compression

The data values in this dataset have been rounded in their binary
floating point representation to improve compression. See
[Klöwer et al. 2021](https://www.nature.com/articles/s43588-021-00156-2)
for more information on this approach. The exact number of rounded bits
can be found in our
[reformatting code](https://github.com/dynamical-org/reformatters/blob/main/src/reformatters/noaa/gefs/common_gefs_template_config.py).
