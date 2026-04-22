This dataset is an archive of past and present HRRR forecasts. Forecasts
are identified by an initialization time (`init_time`) denoting the
start time of the model run.
Each forecast has an hourly forecast step along the `lead_time`
dimension. This dataset contains only the 00, 06, 12, and 18 hour UTC
initialization times which produce the full length, 48 hour forecast.

This dataset uses the native HRRR Lambert Conformal Conic projection,
with spatial indexing along the `x` and `y` dimensions.
The example notebook shows how to use the embedded spatial reference to
select geographic areas of interest.

## Source

The source grib files this archive is constructed from are provided by
[NOAA Open Data Dissemination (NODD)](https://www.noaa.gov/information-technology/open-data-dissemination)
and accessed from the [AWS Open Data Registry](https://registry.opendata.aws/noaa-hrrr-pds/).
Operational data is additionally accessed from [NOAA NOMADS](https://nomads.ncep.noaa.gov/).

## Data availability

Forecasts initialized through 2020-12-02T06 UTC include data
only for the first 36 hours; steps 37–48 are filled with NaNs. Starting with
the 2020-12-02T12 UTC initialization, forecasts cover the full 48 hours.

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
