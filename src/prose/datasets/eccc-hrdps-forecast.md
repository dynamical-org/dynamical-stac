### Source

The source grib files this archive is constructed from are provided by
[ECCC MSC Open Data](https://eccc-msc.github.io/open-data/msc-data/nwp_hrdps/readme_hrdps-datamart_en/)
and the [dynamical.org ECCC HRDPS grib archive](https://source.coop/dynamical/eccc-hrdps-grib)
on [Source Cooperative](https://source.coop/). The MSC Datamart keeps a rolling
window of about 30 days, so the Source Cooperative archive is what gives this
dataset a history.

### Grid

HRDPS runs on a rotated latitude-longitude grid, so the `y` and `x` dimensions are
`grid_latitude` and `grid_longitude` in degrees on a sphere whose pole is moved to
put Canada near the equator, where a regular grid distorts least. Two dimensional
`latitude` and `longitude` coordinates give the true position of every cell; use
those to map or to select a location, not `y` and `x`.

For the same reason winds are published as `wind_speed_10m` and `wind_direction_10m`
rather than u and v components. The source's u and v are relative to the rotated
grid, whose north differs from true north by up to 54 degrees across the domain,
while its wind direction is referenced to true north.

### Storage

Icechunk storage generously provided by [AWS Open Data](https://aws.amazon.com/opendata/).
Storage for the dynamical.org ECCC HRDPS grib archive is generously provided by
[Source Cooperative](https://source.coop/), a [Radiant Earth](https://radiant.earth/) initiative.

### Chunks & shards

{{ chunking }}

### Compression

{{ compression }}
