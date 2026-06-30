### Spatial access

This dataset is optimized for spatial (map) access patterns: each chunk holds a
full latitude/longitude grid for a single `init_time`, `ensemble_member`, and
`lead_time`, so reading a map for one forecast step is fast while reading a long
time series at a single point is comparatively slow.

It is served on the native GEFS 0.25 degree grid. Latitudes run from 90 to -90
and longitudes run from 0 to 360 degrees east (rather than -180 to 180), so
select western-hemisphere locations with positive longitudes (e.g. 270 for
90°W).

### Virtual dataset

This is a virtual dataset: rather than storing a re-chunked copy of the data,
each chunk is a reference to a single GRIB message in NOAA's source archive,
decoded on the fly when you read it. Values are served exactly as encoded in the
source GRIB, which differs from dynamical's materialized GEFS datasets:
temperatures are in Kelvin, and `total_precipitation_surface` is a window
accumulation (the windows reset every 6 forecast hours) rather than a
deaccumulated rate.

This is an experimental dataset used to exercise our virtual dataset tooling;
its structure is not yet settled and it may change or be removed.

### Source

The source grib files this archive is constructed from are provided by
[NOAA Open Data Dissemination (NODD)](https://www.noaa.gov/information-technology/open-data-dissemination)
and accessed from the [AWS Open Data Registry](https://registry.opendata.aws/noaa-gefs/).
Operational data is additionally accessed from [NOAA NOMADS](https://nomads.ncep.noaa.gov/).

### Storage

{{ storage_aws_open_data }}
