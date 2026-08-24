### Source

{{ ecmwf_source }}

### Model updates

AIFS is updated regularly. Find details of recent and upcoming
[changes to the forecasting system](https://confluence.ecmwf.int/display/FCST/Changes+to+the+forecasting+system)
on the ECMWF website.

### Data availability

The archive spans init times from 2024-04-01T00 UTC to the present. Eighteen
variables — the 100 metre winds, the four cloud cover fields, precipitation,
snowfall, runoff, both downward radiation fields, the soil layers and the
sub-grid orography fields — begin at 2025-02-24T06 UTC, when ECMWF added them to
the AIFS open data feed. Snow area fraction begins at the 2026-05-13 model
upgrade. The four fixed surface fields (land-sea mask, surface geopotential
height, and the slope and standard deviation of sub-grid orography) are carried
only at the 0 hour lead time.

### Storage

{{ storage_aws_open_data }}

### Chunks

{{ chunking_unsharded }}

### Validation report

{{ validation_report }}
