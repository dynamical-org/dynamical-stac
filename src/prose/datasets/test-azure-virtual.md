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

{{ chunking_unsharded }}
