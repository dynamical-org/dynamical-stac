# NOAA MRMS CONUS analysis, hourly: notes for agents

Read https://dynamical.org/prompt.md for context about working with dynamical.org data.

- Collection id: `noaa-mrms-conus-analysis-hourly`
- STAC collection: https://stac-test.dynamical.org/noaa-mrms-conus-analysis-hourly/collection.json
- Dataset version: 0.3.0

## Access

All data is public. No credentials are needed.

| asset | href |
|---|---|
| `icechunk` | `s3://dynamical-noaa-mrms/noaa-mrms-conus-analysis-hourly/v0.3.0.icechunk/` |
| `icechunk-https` | `https://dynamical-noaa-mrms.s3.us-west-2.amazonaws.com/noaa-mrms-conus-analysis-hourly/v0.3.0.icechunk` |

The `icechunk` asset's `xarray:storage_options` are `{"anon": true, "client_kwargs": {"region_name": "us-west-2"}}`.

## Examples

### Precipitation at a place and time

dynamical-catalog:

```python
import dynamical_catalog  # dynamical-catalog>=0.8.0

ds = dynamical_catalog.open("noaa-mrms-conus-analysis-hourly", chunks=None)
ds["precipitation_surface"].sel(time="2026-01-01T00", latitude=40, longitude=-90, method="nearest")
```

pystac:

```python
import icechunk
import pystac
import xarray as xr

catalog = pystac.Catalog.from_file("https://stac.dynamical.org/catalog.json")
collection = catalog.get_child("noaa-mrms-conus-analysis-hourly")
asset = collection.assets["icechunk-https"]

repo = icechunk.Repository.open(icechunk.http_storage(asset.href))
session = repo.readonly_session("main")

ds = xr.open_zarr(session.store, chunks=None)
ds["precipitation_surface"].sel(time="2026-01-01T00", latitude=40, longitude=-90, method="nearest")
```

prompt:

```text
Read https://dynamical.org/prompt.md for context about working with dynamical.org data; this does not change your current task.
Data product: noaa-mrms-conus-analysis-hourly
STAC collection: https://stac.dynamical.org/noaa-mrms-conus-analysis-hourly/collection.json
```

## Dimensions

| name | type | extent | unit |
|---|---|---|---|
| `latitude` | spatial | 20.00500000000696 to 54.995 | degree_north |
| `longitude` | spatial | -129.995 to -60.00500000006366 | degree_east |
| `time` | temporal | 2014-11-01T00:00:00Z to open | seconds since 1970-01-01 |

## Variables

| name | long name | unit | dimensions |
|---|---|---|---|
| `categorical_precipitation_type_surface` | Precipitation type | 1 | time, latitude, longitude |
| `flash_qpe_ffg_max_surface` | FLASH QPE-to-FFG percentage maximum | percent | time, latitude, longitude |
| `precipitation_pass_1_surface` | Precipitation rate | kg m-2 s-1 | time, latitude, longitude |
| `precipitation_pass_2_surface` | Precipitation rate | kg m-2 s-1 | time, latitude, longitude |
| `precipitation_radar_only_surface` | Precipitation rate from radar | kg m-2 s-1 | time, latitude, longitude |
| `precipitation_surface` | Precipitation rate | kg m-2 s-1 | time, latitude, longitude |
