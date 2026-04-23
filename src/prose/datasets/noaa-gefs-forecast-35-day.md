### Interpolation

Source data is available at both 0.25-degree and 0.5-degree resolutions. All variables except the 100m wind components are derived from a 0.25-degree grid for the first 240 hours of each forecast and from a 0.5-degree grid for the remainder. 100m wind components are derived from a 0.5-degree grid for all lead times. Bilinear interpolation is used to convert 0.5-degree data to a 0.25-degree grid. The original 0.5-degree values can be retrieved by selecting every other pixel starting from offset 0 in both the latitude and longitude dimensions (e.g. `array[::2, ::2]`).

### Source

The source grib files this archive is constructed from are provided by
[NOAA Open Data Dissemination (NODD)](https://www.noaa.gov/information-technology/open-data-dissemination)
and accessed from the [AWS Open Data Registry](https://registry.opendata.aws/noaa-gefs/).
Operational data is additionally accessed from [NOAA NOMADS](https://nomads.ncep.noaa.gov/).

### Storage

{{ storage }}

### Compression

{{ compression }}
