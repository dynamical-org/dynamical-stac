### Source

This archive is built from Google's [WeatherNext 2 experimental forecast dataset](https://developers.google.com/earth-engine/datasets/catalog/projects_gcp-public-data-weathernext_assets_weathernext_2_0_0). WeatherNext 2 is a global, medium-range ensemble forecast produced by an operational version of Google DeepMind's Functional Network Generative weather model.

Google licenses forecasts more than 48 hours old under CC BY 4.0 and requires the attribution carried in this collection's metadata. The data is experimental: it is not an official forecast, alert, warning or notice from a meteorological agency.

### Data availability

This product contains four daily initializations from 2025-01-01T00 UTC to the present, subject to a strict 48-hour publication boundary. The fixed 2022–2024 source has a different native chunk layout and is published separately as the [historical WeatherNext 2 archive](https://dynamical.org/catalog/google-weathernext2-forecast-historical-virtual/). The two products share the same variables, dimensions and coordinates, so they can be concatenated along `init_time` when a workflow needs the full record.

### Variables

The dataset carries 8 surface variables at the root and 6 atmospheric variables in the `pressure_level` group. Every forecast contains 64 ensemble members, 60 lead times at 6 hourly intervals, and a global 0.25 degree grid. The spatial dimensions are named `y` and `x`; their coordinates are geographic latitude and 0–360 degree longitude, not a projected grid.

### Storage

The Icechunk repository is served over public HTTPS by dynamical.org. Its virtual chunks reference unchanged, compressed source Zarr chunks through the public `wn.dynamical.org` HTTPS endpoint.

### Chunks

{{ chunking_unsharded }}

### Validation report

{{ validation_report }}
