This dataset is an archive of past and present GEFS forecasts. Forecasts
are identified by an initialization time (`init_time`) denoting the
start time of the model run as well as by the `ensemble_member`.
Each forecast has a 3 hourly forecast step along the `lead_time`
dimension. This dataset contains only the 00 hour UTC initialization times
which produce the full length, 35 day forecast.

## Interpolation

Source data is available at both 0.25-degree and 0.5-degree resolutions.
All variables except the 100m wind components are derived
from a 0.25-degree grid for the first 240 hours of each forecast and from a
0.5-degree grid for the remainder. 100m wind components are derived from
a 0.5-degree grid for all lead times. Bilinear interpolation is used to convert
0.5-degree data to a 0.25-degree grid. The original 0.5-degree values can be
retrieved by selecting every other pixel starting from offset 0 in both the
latitude and longitude dimensions (e.g. `array[::2, ::2]`).

## Source

The source grib files this archive is constructed from are provided by
[NOAA Open Data Dissemination (NODD)](https://www.noaa.gov/information-technology/open-data-dissemination)
and accessed from the [AWS Open Data Registry](https://registry.opendata.aws/noaa-gefs/).
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
[reformatting code](https://github.com/dynamical-org/reformatters/blob/main/src/reformatters/noaa/gefs/common_gefs_template_config.py).
