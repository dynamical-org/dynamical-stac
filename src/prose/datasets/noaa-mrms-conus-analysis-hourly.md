### Spatial coverage

Use this dataset over the land areas of the contiguous United States. Radar-only and precipitation type variables contain `NaN` values beyond the range of US radar. `precipitation_pass_1_surface` and `precipitation_pass_2_surface` extend further into the ocean, but still contain `NaN` values in the southeast corner of the domain over the Atlantic.

### Temporal coverage

`precipitation_surface` combines multiple MRMS products to minimize missing values. Despite this, some hours (particularly early in the record) contain `NaN` values where data is unavailable.

`precipitation_pass_2_surface` and `precipitation_pass_1_surface` are available starting 2020-10-15. For timestamps prior to this date, these variables are filled with `NaN`.

### Source

{{ nodd_source_mrms }}

### Storage

{{ storage }}

### Compression

{{ compression }}
