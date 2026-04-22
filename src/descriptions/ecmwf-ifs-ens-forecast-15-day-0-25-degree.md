This dataset is an archive of past and present ECMWF IFS ENS forecasts.
Forecasts are identified by an initialization time (`init_time`)
denoting the start time of the model run, as well as by the
`ensemble_member`. Along the `lead_time` dimension,
each forecast begins at a 3 hourly forecast step (0-144 hours) and switches
to a 6 hourly step for days 6 through 15 of the forecast (hours 144-360).
This dataset contains the 00 UTC initialization times only.

## Source

The source grib files this archive is constructed from are provided by
[ECMWF Open Data](https://www.ecmwf.int/en/forecasts/datasets/open-data)
and accessed from the [AWS Open Data Registry](https://registry.opendata.aws/ecmwf-forecasts/).

ECMWF does not provide user support for the free & open datasets. Users should
refer to the public [User Forum](https://forum.ecmwf.int/) for any questions
related to the source material.

## Data availability

This dataset contains only forecasts initialized on or after 2024-04-01,
which are available at the open data 0.25 degree (~20km) resolution.
All variables are available for the full period, save for
`precipitation_surface`, which is filled with NaNs
before 2024-11-13 UTC.

## Ensemble members

Each forecast contains 51 ensemble members, including a control member (0)
and 50 perturbed members (1-50). The control forecast is produced with
the best available data and unperturbed models. The other 50 members
are each produced with slight perturbations of initial conditions
and of the models. Taken together, ensemble of 51 forecasts shows
the range of possible outcomes and the likelihood of their occurrence.

## Model updates

IFS is updated regularly. Find details of recent and upcoming
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
[reformatting code](https://github.com/dynamical-org/reformatters/blob/main/src/reformatters/ecmwf/ifs_ens/forecast_15_day_0_25_degree/template_config.py).
