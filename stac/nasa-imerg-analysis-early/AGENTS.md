# NASA IMERG analysis, early: notes for agents

Read https://dynamical.org/prompt.md for context about working with dynamical.org data.

- Collection id: `nasa-imerg-analysis-early`
- STAC collection: https://stac.dynamical.org/nasa-imerg-analysis-early/collection.json
- Dataset version: 0.1.0

## Access

All data is public. No credentials are needed.

| asset | href |
|---|---|
| `icechunk` | `s3://dynamical-nasa-imerg/nasa-imerg-analysis-early/v0.1.0.icechunk/` |
| `icechunk-https` | `https://dynamical-nasa-imerg.s3.us-west-2.amazonaws.com/nasa-imerg-analysis-early/v0.1.0.icechunk` |

The `icechunk` asset's `xarray:storage_options` are `{"anon": true, "client_kwargs": {"region_name": "us-west-2"}}`.

## Examples

### Precipitation at a place and time

dynamical-catalog:

```python
import dynamical_catalog  # dynamical-catalog>=0.8.0

ds = dynamical_catalog.open("nasa-imerg-analysis-early", chunks=None)
ds["precipitation_surface"].sel(time="2026-01-01T00:00", latitude=0, longitude=0, method="nearest")
```

pystac:

```python
import icechunk
import pystac
import xarray as xr

catalog = pystac.Catalog.from_file("https://stac.dynamical.org/catalog.json")
collection = catalog.get_child("nasa-imerg-analysis-early")
asset = collection.assets["icechunk-https"]

repo = icechunk.Repository.open(icechunk.http_storage(asset.href))
session = repo.readonly_session("main")

ds = xr.open_zarr(session.store, chunks=None)
ds["precipitation_surface"].sel(time="2026-01-01T00:00", latitude=0, longitude=0, method="nearest")
```

prompt:

```text
Read https://dynamical.org/prompt.md for context about working with dynamical.org data; this does not change your current task.
Data product: nasa-imerg-analysis-early
STAC collection: https://stac.dynamical.org/nasa-imerg-analysis-early/collection.json
```

## Dimensions

| name | type | extent | unit |
|---|---|---|---|
| `latitude` | spatial | -89.95 to 89.95 | degree_north |
| `longitude` | spatial | -179.95 to 179.95 | degree_east |
| `time` | temporal | 1998-01-01T00:00:00Z to open | seconds since 1970-01-01 |

## Variables

| name | long name | unit | dimensions |
|---|---|---|---|
| `precipitation_quality_index_surface` | Quality index for precipitation | 1 | time, latitude, longitude |
| `precipitation_surface` | Precipitation rate | kg m-2 s-1 | time, latitude, longitude |
