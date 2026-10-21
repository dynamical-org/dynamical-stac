### Source

This data product is built from Google's [WeatherNext 2 experimental forecast dataset](https://developers.google.com/earth-engine/datasets/catalog/projects_gcp-public-data-weathernext_assets_weathernext_2_0_0). WeatherNext 2 is a global, medium-range ensemble forecast produced by an operational version of Google DeepMind's Functional Generative Network (FGN) weather model. The [Acknowledgements](https://developers.google.com/earth-engine/datasets/catalog/projects_gcp-public-data-weathernext_assets_weathernext_2_0_0#description) on Google's dataset page list third-party materials whose terms may also apply.

**Modifications.** dynamical.org restructures the source into an Icechunk virtual data product with dynamical.org's variable and dimension names, and converts units as the data is read: temperatures from kelvin to degrees Celsius, geopotential to geopotential height (divided by standard gravity), and total precipitation from metres of water to kg m⁻². Values are otherwise the unchanged model output.

### Data availability

This fixed data product contains forecasts initialized from 2022-01-01T00 through 2024-12-31T18 UTC. Forecasts from 2025 onward are in the [operational WeatherNext 2 data product](https://dynamical.org/catalog/google-weathernext2-forecast-operational-virtual/). It has the same variables, dimensions and coordinates, so the two can be concatenated along `init_time`.

### Chunks

{{ chunking_unsharded }}

### Validation report

{{ validation_report }}
