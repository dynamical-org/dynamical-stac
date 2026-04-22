This analysis dataset is an archive of MRMS radar and multi-sensor
precipitation and weather analyses over the contiguous United States (CONUS).

## Spatial coverage

Use this dataset over the land areas of the contiguous United States.
Radar-only and precipitation type variables contain `NaN` values beyond the
range of US radar. `precipitation_pass_1_surface` and
`precipitation_pass_2_surface` extend further into the ocean, but still
contain `NaN` values in the southeast corner of the domain over the Atlantic.

## Temporal coverage

`precipitation_surface` combines multiple MRMS products to minimize missing
values. Despite this, some hours (particularly early in the record) contain
`NaN` values where data is unavailable.

`precipitation_pass_2_surface` and `precipitation_pass_1_surface` are
available starting 2020-10-15. For timestamps prior to this date, these
variables are filled with `NaN`.

## Source

The source files this archive is constructed from are provided by
[NOAA Open Data Dissemination (NODD)](https://www.noaa.gov/information-technology/open-data-dissemination)
and accessed from the [AWS Open Data Registry](https://registry.opendata.aws/noaa-mrms-pds/).
Operational data is additionally accessed from [NCEP](https://mrms.ncep.noaa.gov/).

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
