### Source

This dataset is built from Google's [WeatherNext 2 experimental forecast dataset](https://developers.google.com/earth-engine/datasets/catalog/projects_gcp-public-data-weathernext_assets_weathernext_2_0_0). WeatherNext 2 is a global, medium-range ensemble forecast produced by an operational version of Google DeepMind's Functional Generative Network (FGN) weather model.

**Modifications.** dynamical.org restructures the source into an Icechunk virtual dataset with dynamical.org's variable and dimension names, and converts units as the data is read: temperatures from kelvin to degrees Celsius, geopotential to geopotential height (divided by standard gravity), and total precipitation from metres of water to kg m⁻². Values are otherwise the unchanged model output.

### Terms of use

Forecast values whose valid time (`init_time` + `lead_time`) is less than 1 hour ago or in the future are Real-Time Data & Forecasts under the [GDM Real-Time Weather Forecasting Experimental Data Terms of Use](https://storage.googleapis.com/weathernext-public/terms-of-use.pdf). Values whose valid time is 1 hour ago or more are Historical Data under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). A [copy of the Terms](https://google-weathernext2.r2.dynamical.org/google-weathernext2-forecast-operational-virtual/TERMS_OF_USE.pdf) and the [Legally Binding Terms of Use](https://google-weathernext2.r2.dynamical.org/google-weathernext2-forecast-operational-virtual/LEGALLY_BINDING_TERMS_OF_USE.txt) notice are published next to the store.

The Terms do not permit real-time data to be used in or made available to a Restricted Country, which they list as “Japan, South Korea, Indonesia, Cuba, Iran, North Korea, Crimea and the so-called Donetsk People’s Republic and Luhansk People’s Republic”. wn.dynamical.org refuses WeatherNext data requests from those locations, and requests whose location cannot be determined.

WeatherNext 2 data is experimental: it is not an official forecast, alert, warning or notice from a meteorological agency. dynamical.org and this dataset are not sponsored, endorsed, or granted official status by Google or any meteorological agency or department.

Google's dataset page notes that the model draws on the following third-party materials, whose use may be governed by separate terms and conditions or license provisions:

* Data and products of the European Centre for Medium-range Weather Forecasts (ECMWF), as modified by Google.
* Modified Copernicus Climate Change Service information 2023. Neither the European Commission nor ECMWF is responsible for any use that may be made of the Copernicus information or data it contains.
* ECMWF HRES datasets
  * Copyright statement: Copyright "© 2023 European Centre for Medium-Range Weather Forecasts (ECMWF)".
  * Source: [www.ecmwf.int](http://www.ecmwf.int)
  * License Statement: ECMWF open data is published under a Creative Commons Attribution 4.0 International (CC BY 4.0). [https://creativecommons.org/licenses/by/4.0/](https://creativecommons.org/licenses/by/4.0/)
  * Disclaimer: ECMWF does not accept any liability whatsoever for any error or omission in the data, their availability, or for any loss or damage arising from their use.

### Data availability

The archive starts with the 2025-01-01T00 UTC initialization and is updated four times a day. Forecasts include steps whose valid time is in the future. Recent initializations may be incomplete while source files arrive or await a subsequent update; unpublished steps read as NaN.

Forecasts initialized from 2022 through 2024 are in the [historical WeatherNext 2 dataset](https://dynamical.org/catalog/google-weathernext2-forecast-historical-virtual/). It has the same variables, dimensions and coordinates, so the two can be concatenated along `init_time`.

### Chunks

{{ chunking_unsharded }}

### Validation report

{{ validation_report }}
