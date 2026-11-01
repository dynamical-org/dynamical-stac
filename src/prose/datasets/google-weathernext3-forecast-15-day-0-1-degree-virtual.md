### Source

This data product is built from Google's [WeatherNext 3 statistics archive](https://developers.google.com/weathernext/guides/gcs). Google supplies the mean and the 10th, 25th, 50th, 75th and 90th percentiles of its ensemble; these are exposed as `mean`, `p10`, `p25`, `p50`, `p75` and `p90` on the `statistic` dimension. Individual ensemble members are not included. Google's [attributions and acknowledgements](https://storage.googleapis.com/weathernext-public/weathernext-3-attributions-acknowledgements.pdf) list third-party materials whose terms may also apply.

**Modifications.** dynamical.org restructures the source into an Icechunk virtual data product with dynamical.org's variable and dimension names and converts units as data is read. Temperatures are converted from kelvin to degrees Celsius, cloud fractions to percent, hourly precipitation amounts to rates in kg m⁻² s⁻¹, and hourly solar energy to flux in W m⁻².

### Data availability

This data product starts with the 2026-01-01T00 UTC initialization and is updated four times a day. Forecasts include steps whose valid time is in the future. Forecasts are initialized at 00, 06, 12 and 18 UTC. Recent initializations may be incomplete while source data arrives; unpublished steps read as NaN.

### Chunks

{{ chunking_unsharded }}

### Validation report

{{ validation_report }}
