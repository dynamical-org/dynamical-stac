### Construction

GFS starts a new model run every 6 hours and dynamical.org has created this analysis by
concatenating the shortest usable forecast step of each run along the time dimension.
Instantaneous variables are read from forecast hours 0 to 5, and variables that describe a
preceding window (accumulations, averages and window maxima and minima) are read from
forecast hours 1 to 6.

### Source

{{ nodd_source_gfs }}

### Storage

{{ storage_aws_open_data }}

### Chunks

{{ chunking_unsharded }}

### Validation report

{{ validation_report }}
