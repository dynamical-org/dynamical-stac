This dataset is an archive of past and present ECMWF AIFS Single forecasts.
Forecasts are identified by an initialization time (`init_time`) denoting the
start time of the model run. Each forecast steps forward in time along the
`lead_time` dimension, from 0 to 360 hours (15 days) at a 6 hourly step.

## Source

The source grib files this archive is constructed from are provided by
[ECMWF Open Data](https://www.ecmwf.int/en/forecasts/datasets/open-data)
and accessed from the [AWS Open Data Registry](https://registry.opendata.aws/ecmwf-forecasts/).

ECMWF does not provide user support for the free & open datasets. Users should
refer to the public [User Forum](https://forum.ecmwf.int/) for any questions
related to the source material.

## Model updates

AIFS is updated regularly. Find details of recent and upcoming
[changes to the forecasting system](https://confluence.ecmwf.int/display/FCST/Changes+to+the+forecasting+system)
on the ECMWF website.

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
[reformatting code](https://github.com/dynamical-org/reformatters/blob/main/src/reformatters/ecmwf/aifs_single/forecast/template_config.py).
