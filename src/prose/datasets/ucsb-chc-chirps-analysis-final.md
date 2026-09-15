### Product

This archive contains the CHIRPS v3 **final** daily product from January 1, 1981 onward. The source's `final/rnl` variant uses ERA5 reanalysis to distribute pentad precipitation totals across days. See the [CHIRPS v3 documentation](https://www.chc.ucsb.edu/data/chirps3) for the methodology.

The companion [UCSB CHC CHIRPS analysis, preliminary](/catalog/ucsb-chc-chirps-analysis-preliminary/) provides the other product. Final and preliminary differ in both their station inputs and their daily distribution method.

### Precipitation

`precipitation_surface` is the average rate over the 24 hours starting at `time`, in kg m-2 s-1 (equivalent to mm/s). Multiply by 86,400 to obtain the daily total in mm. Ocean cells are NaN.

### Source

Source files are provided by the [UCSB Climate Hazards Center daily archive](https://data.chc.ucsb.edu/products/CHIRPS/v3.0/daily/final/rnl/).

### Storage

{{ storage_aws_open_data }}

### Chunks & shards

{{ chunking }}

### Validation report

{{ validation_report }}

### Compression

{{ compression }}
