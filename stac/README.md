# dynamical.org STAC Catalog

Cloud-optimized weather and climate datasets from dynamical.org. Each child
collection is one dataset, stored as an Icechunk repository of Zarr arrays
that anyone can read without credentials.

## License

Each collection states its license in its `license` field and in its own
README.md.

## Provenance

Most collections reformat data that other organizations produce. Each
collection names its producer first in `providers`, with dynamical.org last as
host, and links the original source with `rel: via` when it is elsewhere.

## Links

- Website: https://dynamical.org/
- Dataset catalog: https://dynamical.org/catalog/
