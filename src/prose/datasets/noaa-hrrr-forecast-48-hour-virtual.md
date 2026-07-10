### Spatial access

This dataset is optimized for spatial (map) access patterns: each chunk holds a
full `y`/`x` grid for a single `init_time` and `lead_time`, so reading a map for
one forecast step is fast while reading a long time series at a single point is
comparatively slow.

It is served on the native HRRR 3 km Lambert Conformal Conic projection, with
spatial indexing along the `x` and `y` dimensions and two-dimensional `latitude`
and `longitude` coordinates. The embedded `spatial_ref` coordinate carries the
CRS, so you can select geographic areas of interest.

### Vertical groups

Alongside the surface and single-level variables in the root group, the store
contains two nested groups holding the full vertical profiles:

- `pressure_level` — variables on 39 isobaric levels (1000 down to 50 hPa).
- `model_level` — variables on the 50 native hybrid (sigma) model levels.

Open a group with xarray's `group` argument, e.g.
`xr.open_zarr(store, group="pressure_level")`. In this dataset's STAC metadata
these variables are listed under `pressure_level/…` and `model_level/…` keys to
keep them distinct from the root variables of the same name.

### Virtual dataset

This is a virtual dataset: rather than storing a re-chunked copy of the data,
each chunk is a reference to a single GRIB message in NOAA's source archive,
decoded on the fly when you read it. Temperatures and dew points are converted to
Celsius and a few variables are unit-scaled on read to match dynamical's
materialized `noaa-hrrr-forecast-48-hour`, but accumulated fields (e.g.
`total_precipitation_surface`) are served as the source GRIB window
accumulations rather than deaccumulated rates.

This is an experimental dataset used to exercise our virtual dataset tooling;
its structure is not yet settled and it may change or be removed.

### Source

{{ nodd_source_hrrr }}

### Storage

{{ storage_aws_open_data }}
