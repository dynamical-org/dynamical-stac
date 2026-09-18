### Source

The source grib files this archive is constructed from are provided by
[NOAA Open Data Dissemination (NODD)](https://www.noaa.gov/information-technology/open-data-dissemination)
and accessed from the [AWS Open Data Registry](https://registry.opendata.aws/noaa-gefs/).

### Variable availability

Four variables were added by the source after the archive begins and are empty before those
dates:

- From 2021-07-20T12 UTC: `pressure_reduced_to_mean_sea_level_eta_model`.
- From 2022-10-18T12 UTC: `visibility_surface`, `percent_frozen_precipitation_surface` and
  `geopotential_height_cloud_ceiling`.

### Storage

{{ storage_aws_open_data }}

### Chunks

{{ chunking_unsharded }}

### Validation report

{{ validation_report }}
