### Source

{{ ecmwf_source }}

### Data availability

This dataset contains only forecasts initialized on or after 2024-04-01, which are available at the open data 0.25 degree (~20km) resolution. All variables are available for the full period, save for `precipitation_surface`, which is filled with NaNs before 2024-11-13 UTC.

### Ensemble members

Each forecast contains 51 ensemble members, including a control member (0) and 50 perturbed members (1-50). The control forecast is produced with the best available data and unperturbed models. The other 50 members are each produced with slight perturbations of initial conditions and of the models. Taken together, ensemble of 51 forecasts shows the range of possible outcomes and the likelihood of their occurrence.

### Model updates

{{ ecmwf_model_updates_ifs }}

### Storage

{{ storage }}

### Compression

{{ compression }}
