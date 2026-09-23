### Source

The source grib files this archive is constructed from are provided by
[NOAA Open Data Dissemination (NODD)](https://www.noaa.gov/information-technology/open-data-dissemination)
and accessed from the [AWS Open Data Registry](https://registry.opendata.aws/noaa-gefs/).

### Publication timing

NOAA NCEP publishes the first 16 days of each forecast as a continuous stream; the remaining
days out to 35 arrive more slowly and finish about 27 hours after initialization, so the newest
initialization time is usually still filling. See the [source pipeline status](https://dynamical.org/status/pipeline/#pipeline-group-noaa-gefs-long) for detailed timing information.

### Storage

{{ storage_aws_open_data }}

### Chunks

{{ chunking_unsharded }}

### Validation report

{{ validation_report }}
