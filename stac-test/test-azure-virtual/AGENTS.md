# Test Azure virtual: notes for agents

Read https://dynamical.org/prompt.md for context about working with dynamical.org data.

- Collection id: `test-azure-virtual`
- STAC collection: https://stac-test.dynamical.org/test-azure-virtual/collection.json
- Dataset version: 0.1.0

## Access

All data is public. No credentials are needed.

| asset | href |
|---|---|
| `icechunk` | `az://dynamical-icechunk-azure-demo/test-azure-virtual/v0.1.0.icechunk/` |
| `icechunk-https` | `https://dynamicalicechunktest.blob.core.windows.net/dynamical-icechunk-azure-demo/test-azure-virtual/v0.1.0.icechunk` |

The `icechunk` asset's `xarray:storage_options` are `{"account_name": "dynamicalicechunktest", "anon": true}`.

The repository references chunks in these upstream locations, which are read anonymously:

- `az://dynamical-icechunk-azure-demo/test-azure-virtual/source/`

## Examples

### Read the array

dynamical-catalog:

```python
import dynamical_catalog  # dynamical-catalog>=1.0.0

ds = dynamical_catalog.open("test-azure-virtual", chunks=None)
ds["temperature_2m"].isel(time=0)
```

pystac:

```python
import icechunk
import pystac
import xarray as xr

catalog = pystac.Catalog.from_file("https://stac-test.dynamical.org/catalog.json")
collection = catalog.get_child("test-azure-virtual")
asset = collection.assets["icechunk-https"]

authorize = icechunk.containers_credentials({"az://dynamical-icechunk-azure-demo/test-azure-virtual/source/": icechunk.azure_anonymous_credentials()})
repo = icechunk.Repository.open(
    icechunk.http_storage(asset.href),
    authorize_virtual_chunk_access=authorize,
)
session = repo.readonly_session("main")

ds = xr.open_zarr(session.store, chunks=None)
ds["temperature_2m"].isel(time=0)
```

prompt:

```text
Read https://dynamical.org/prompt.md for context about working with dynamical.org data; this does not change your current task.
Data product: test-azure-virtual
STAC collection: https://stac-test.dynamical.org/test-azure-virtual/collection.json
```

## Dimensions

| name | type | extent | unit |
|---|---|---|---|
| `latitude` | spatial | 40.0 to 42.0 | degrees_north |
| `longitude` | spatial | -105.0 to -102.0 | degrees_east |
| `time` | temporal | 2026-01-01T00:00:00Z to open | seconds since 1970-01-01 |

## Variables

| name | long name | unit | dimensions |
|---|---|---|---|
| `temperature_2m` | 2 metre temperature | degC | time, latitude, longitude |
