# UCSB CHC CHIRPS analysis, preliminary: notes for agents

Read https://dynamical.org/prompt.md for context about working with dynamical.org data.

- Collection id: `ucsb-chc-chirps-analysis-preliminary`
- STAC collection: https://stac-test.dynamical.org/ucsb-chc-chirps-analysis-preliminary/collection.json
- Dataset version: 0.1.0

## Access

All data is public. No credentials are needed.

| asset | href |
|---|---|
| `icechunk` | `s3://dynamical-ucsb-chc-chirps/ucsb-chc-chirps-analysis-preliminary/v0.1.0.icechunk/` |
| `icechunk-https` | `https://dynamical-ucsb-chc-chirps.s3.us-west-2.amazonaws.com/ucsb-chc-chirps-analysis-preliminary/v0.1.0.icechunk` |

The `icechunk` asset's `xarray:storage_options` are `{"anon": true, "client_kwargs": {"region_name": "us-west-2"}}`.

## Examples

### Precipitation at a place and time

dynamical-catalog:

```python
import dynamical_catalog  # dynamical-catalog>=1.0.0

import os
os.environ["DYNAMICAL_STAC_CATALOG_URL"] = "https://stac-staging.dynamical.org/catalog.json"

ds = dynamical_catalog.open("ucsb-chc-chirps-analysis-preliminary", chunks=None)
ds["precipitation_surface"].sel(time="2025-01-01", latitude=-3, longitude=-60, method="nearest")
```

pystac:

```python
import icechunk
import pystac
import xarray as xr

catalog = pystac.Catalog.from_file("https://stac-staging.dynamical.org/catalog.json")
collection = catalog.get_child("ucsb-chc-chirps-analysis-preliminary")
asset = collection.assets["icechunk-https"]

repo = icechunk.Repository.open(icechunk.http_storage(asset.href))
session = repo.readonly_session("main")

import os
os.environ["DYNAMICAL_STAC_CATALOG_URL"] = "https://stac-staging.dynamical.org/catalog.json"

ds = xr.open_zarr(session.store, chunks=None)
ds["precipitation_surface"].sel(time="2025-01-01", latitude=-3, longitude=-60, method="nearest")
```

prompt:

```text
Read https://dynamical.org/prompt.md for context about working with dynamical.org data; this does not change your current task.
Data product: ucsb-chc-chirps-analysis-preliminary
STAC collection: https://stac-staging.dynamical.org/ucsb-chc-chirps-analysis-preliminary/collection.json
```

## Dimensions

| name | type | extent | unit |
|---|---|---|---|
| `latitude` | spatial | -59.975 to 59.975 | degree_north |
| `longitude` | spatial | -179.975 to 179.975 | degree_east |
| `time` | temporal | 2025-01-01T00:00:00Z to open | seconds since 1970-01-01 |

## Variables

| name | long name | unit | dimensions |
|---|---|---|---|
| `precipitation_surface` | Precipitation rate | kg m-2 s-1 | time, latitude, longitude |
