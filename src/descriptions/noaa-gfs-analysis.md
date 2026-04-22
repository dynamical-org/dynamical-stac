This analysis dataset is an archive of the model's best estimate of past weather.
It is created by concatenating the first few hours of each historical forecast to
provide a dataset with dimensions time, latitude, and longitude.

## Construction

GFS starts a new model run every 6 hours and dynamical.org has created this analysis
by concatenating the first 6 hours of each forecast along the time dimension.

## Source

The source grib files this archive is constructed from are provided by
[NOAA Open Data Dissemination (NODD)](https://www.noaa.gov/information-technology/open-data-dissemination)
and accessed from the [AWS Open Data Registry](https://registry.opendata.aws/noaa-gfs-bdp-pds/).
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
[reformatting code](https://github.com/dynamical-org/reformatters/blob/main/src/reformatters/noaa/gfs/analysis/template_config.py).

## Related dataset

[NOAA GEFS analysis](https://dynamical.org/catalog/noaa-gefs-analysis/) provides a much longer historical record.
