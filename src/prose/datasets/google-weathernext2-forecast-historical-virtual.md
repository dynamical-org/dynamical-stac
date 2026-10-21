### Source

This dataset is built from Google's [WeatherNext 2 experimental forecast dataset](https://developers.google.com/earth-engine/datasets/catalog/projects_gcp-public-data-weathernext_assets_weathernext_2_0_0). WeatherNext 2 is a global, medium-range ensemble forecast produced by an operational version of Google DeepMind's Functional Generative Network (FGN) weather model.

**Modifications.** dynamical.org restructures the source into an Icechunk virtual dataset with dynamical.org's variable and dimension names, and converts units as the data is read: temperatures from kelvin to degrees Celsius, geopotential to geopotential height (divided by standard gravity), and total precipitation from metres of water to kg m⁻². Values are otherwise the unchanged model output.

### Terms of use

Every value in this dataset relates to a time years in the past, so it is Historic Experimental Data, licensed under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/) by the terms on [Google's dataset page](https://developers.google.com/earth-engine/datasets/catalog/projects_gcp-public-data-weathernext_assets_weathernext_2_0_0#terms-of-use). CC BY 4.0 includes a disclaimer of warranties and limitation of liability.

WeatherNext 2 data is experimental: it is not an official forecast, alert, warning or notice from a meteorological agency.

Google's dataset page notes that the model draws on the following third-party materials, whose use may be governed by separate terms and conditions or license provisions:

* Data and products of the European Centre for Medium-range Weather Forecasts (ECMWF), as modified by Google.
* Modified Copernicus Climate Change Service information 2023. Neither the European Commission nor ECMWF is responsible for any use that may be made of the Copernicus information or data it contains.
* ECMWF HRES datasets
  * Copyright statement: Copyright "© 2023 European Centre for Medium-Range Weather Forecasts (ECMWF)".
  * Source: [www.ecmwf.int](http://www.ecmwf.int)
  * License Statement: ECMWF open data is published under a Creative Commons Attribution 4.0 International (CC BY 4.0). [https://creativecommons.org/licenses/by/4.0/](https://creativecommons.org/licenses/by/4.0/)
  * Disclaimer: ECMWF does not accept any liability whatsoever for any error or omission in the data, their availability, or for any loss or damage arising from their use.

### Data availability

This fixed dataset contains forecasts initialized from 2022-01-01T00 through 2024-12-31T18 UTC. Forecasts from 2025 onward are in the [operational WeatherNext 2 dataset](https://dynamical.org/catalog/google-weathernext2-forecast-operational-virtual/). It has the same variables, dimensions and coordinates, so the two can be concatenated along `init_time`.

### Chunks

{{ chunking_unsharded }}

### Validation report

{{ validation_report }}
