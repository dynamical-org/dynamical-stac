# Test Azure virtual

A synthetic 2x3x4 `temperature_2m` array on Azure Blob Storage whose single chunk is a virtual reference into the same container. Published only to the test catalog so dynamical-catalog can exercise anonymous Azure repository and virtual chunk reads against real generator output.

These are tiny synthetic datasets used to exercise dynamical-catalog's read paths against real generator output; they are not weather data.

## License

CC-BY-4.0. dynamical.org

- [CC-BY-4.0](https://creativecommons.org/licenses/by/4.0/)

## Provenance

Produced, processed and hosted by [dynamical.org](https://dynamical.org/).

## Details

### Purpose

A tiny synthetic array — a 2×3×4 `temperature_2m` grid of made-up values. This
is not weather data and should not be used for anything but testing. It exists
so [dynamical-catalog](https://github.com/dynamical-org/dynamical-catalog) can
exercise its Azure Blob Storage read path — an anonymous `az://` icechunk
repository whose single chunk is a virtual reference into an `az://` container —
against real catalog output rather than a hand-written STAC document.

### Storage

The store lives in a public container in dynamical.org's Azure storage account.

### Chunks

This dataset is stored in [Zarr](https://zarr.dev/) format, which splits each variable into a grid of **chunks** — the smallest unit read from storage. When possible, aligning your reads with this dataset's chunk grid can significantly improve data access speed.

The element count and coordinate span of this dataset:

| dimension | chunk |
|---|---|
| time | 2 (12 hours) |
| latitude | 3 (3°) |
| longitude | 4 (4°) |
| **uncompressed** | 96.0 B |

## Links

- STAC collection: https://stac-test.dynamical.org/test-azure-virtual/collection.json
- Dataset documentation: https://dynamical.org/catalog/test-azure-virtual/
- Validation report: https://dynamical.org/catalog/test-azure-virtual/validation/
