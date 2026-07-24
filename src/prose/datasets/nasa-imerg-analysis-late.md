### Early vs. Late Run

NASA produces several IMERG runs from the same input observations at different latencies. This dataset is the **Late Run**, published approximately 12 to 18 hours after observation time. It incorporates additional satellite sensor input and applies both forward and backward propagation (morphing) of precipitation features, yielding higher quality than the low-latency Early Run.

The companion [NASA IMERG analysis, early](/catalog/nasa-imerg-analysis-early/) dataset is published about 4 hours after observation time and is better suited to time-sensitive applications such as flood and landslide monitoring.

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
