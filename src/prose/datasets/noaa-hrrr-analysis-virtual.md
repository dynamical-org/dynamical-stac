### Construction

HRRR starts a new model run every hour and dynamical.org has created this analysis by
concatenating the shortest available forecast step of each run along the time dimension.
Instantaneous variables are read from forecast hour 0 of the run initialized at that time.

Variables that describe the preceding hour — accumulations and hourly maxima and minima —
have no value at hour 0, so they are read from forecast hour 1 of the run initialized an
hour earlier and describe the hour ending at their timestamp. A few instantaneous fields
that HRRR does not diagnose at hour 0, including precipitation rate, the lightning fields
and aerosol optical thickness, are read from forecast hour 1 as well.

### Source

{{ nodd_source_hrrr }}

### Data availability

The archive spans hourly times from 2014-10-01T00 UTC to the present. Many fields change
behavior at the HRRR version upgrades — version 2 on 2016-08-23, version 3 on 2018-07-12
and version 4 on 2020-12-02 — and a number of variables begin at one of those dates. See
the [validation report]({{ validation_url }}) for details.

### Storage

{{ storage_aws_open_data }}

### Chunks

{{ chunking_unsharded }}

### Validation report

{{ validation_report }}

### Compression

{{ compression }}
