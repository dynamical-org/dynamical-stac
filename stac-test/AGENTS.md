# dynamical.org STAC Catalog: notes for agents

Read https://dynamical.org/prompt.md for context about working with dynamical.org data.

- Each child collection is one dataset. Its AGENTS.md lists the repository
  URLs, dimensions and variables, and its `examples` field holds runnable
  Python.
- With the `dynamical-catalog` package, open a dataset by its collection id:
  `dynamical_catalog.open("<collection id>")`.
- Without it, open the collection's `icechunk-https` asset with
  `icechunk.http_storage` and read it with `xarray.open_zarr`.
- All data is public. No credentials are needed.
