# Test GCS virtual

A synthetic 2x3x4 `temperature_2m` array on Google Cloud Storage whose single chunk is a virtual reference into the same bucket. Published only to the test catalog so dynamical-catalog can exercise anonymous GCS repository and virtual chunk reads against real generator output.

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
exercise its Google Cloud Storage read path — an anonymous `gs://` icechunk
repository whose single chunk is a virtual reference into a `gs://` container —
against real catalog output rather than a hand-written STAC document.

### Storage

The store lives in a public bucket in dynamical.org's Google Cloud project.

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

- STAC collection: https://stac-test.dynamical.org/test-gcs-virtual/collection.json
- Dataset documentation: https://dynamical.org/catalog/test-gcs-virtual/
- Validation report: https://dynamical.org/catalog/test-gcs-virtual/validation/
