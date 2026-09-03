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

{{ chunking_unsharded }}
