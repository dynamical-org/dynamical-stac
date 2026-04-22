This analysis dataset is an archive of the model's best estimate of past weather.
It is created by concatenating the first hour of each historical forecast to
provide a dataset with dimensions time, x, and y.

This dataset uses the native HRRR Lambert Conformal Conic projection,
with spatial indexing along the `x` and `y` dimensions.
The example notebook shows how to use the embedded spatial reference to
select geographic areas of interest.

## Construction

HRRR starts a new model run every hour and dynamical.org has created this
analysis by concatenating the first step of each forecast along the time
dimension. Accumulated variables (e.g. precipitation) are read from the
second step of the previous hour's forecast.

## Data availability

There are a significant number of missing source files before August 2018
(HRRR v1 and v2 period), and a small number from August 2018 to December 2020
(HRRR v3 period).

`downward_long_wave_radiation_flux_surface` and `relative_humidity_2m` are
unavailable before August 2016 (HRRR v1 period).

This dataset has NaN values where source data are unavailable.

## Source

The source grib files this archive is constructed from are provided by
[NOAA Open Data Dissemination (NODD)](https://www.noaa.gov/information-technology/open-data-dissemination)
and accessed from the [AWS Open Data Registry](https://registry.opendata.aws/noaa-hrrr-pds/).
Operational data is additionally accessed from [NOAA NOMADS](https://nomads.ncep.noaa.gov/).

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
[reformatting code](https://github.com/dynamical-org/reformatters/).
