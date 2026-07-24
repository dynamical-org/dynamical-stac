### Early vs. Late Run

NASA produces several IMERG runs from the same input observations at different latencies. This dataset is the **Early Run**, published approximately 4 hours after observation time. It relies on forward propagation (morphing) of precipitation features only and is intended for time-sensitive applications such as flood and landslide monitoring.

The companion [NASA IMERG analysis, late](/catalog/nasa-imerg-analysis-late/) dataset incorporates additional satellite sensor input and both forward and backward morphing for higher quality, at the cost of a longer, roughly 12 to 18 hour, latency.

### Temporal coverage

IMERG version 07 reprocesses the full record back to 1998, spanning both the Tropical Rainfall Measuring Mission (TRMM, 1998 to 2014) and Global Precipitation Measurement (GPM, 2014 to present) satellite eras. Estimates before the GPM era (mid-2014) rely on a smaller satellite constellation and are generally of lower quality, particularly at high latitudes.

### Source

The source files this archive is constructed from are provided by NASA and accessed from the [GES DISC](https://disc.gsfc.nasa.gov/) archive. Operational low-latency data is additionally accessed from the [NASA Precipitation Processing System (PPS)](https://gpm.nasa.gov/data/directory).

### Storage

{{ storage_aws_open_data }}

### Chunks & shards

{{ chunking }}

### Compression

{{ compression }}
