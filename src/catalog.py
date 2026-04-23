from __future__ import annotations

from enum import StrEnum
from typing import Literal
from urllib.parse import urlparse

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, model_validator


class DatasetLicense(StrEnum):
    CC_BY_4_0 = "CC-BY-4.0"


class AdditionalTerms(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    href: HttpUrl
    title: str = Field(min_length=1)


class Model(BaseModel):
    """Model-level metadata shared by every CatalogItem with the same model_id."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    description: str = Field(min_length=1)


_NOAA_GFS_DESCRIPTION = """\
The Global Forecast System (GFS) is a National Oceanic and Atmospheric \
Administration (NOAA) National Centers for Environmental Prediction (NCEP) \
weather forecast model that generates data for dozens of atmospheric and \
land-soil variables, including temperatures, winds, precipitation, soil \
moisture, and atmospheric ozone concentration. The system couples four \
separate models (atmosphere, ocean model, land/soil model, and sea ice) that \
work together to depict weather conditions."""

_NOAA_GEFS_DESCRIPTION = """\
The Global Ensemble Forecast System (GEFS) is a National Oceanic and \
Atmospheric Administration (NOAA) National Centers for Environmental \
Prediction (NCEP) weather forecast model. GEFS creates 31 separate forecasts \
(ensemble members) to describe the range of forecast uncertainty."""

_NOAA_HRRR_DESCRIPTION = """\
The High-Resolution Rapid Refresh (HRRR) is a NOAA real-time 3-km resolution, \
hourly updated, cloud-resolving, convection-allowing atmospheric model, \
initialized by 3km grids with 3km radar assimilation. Radar data is \
assimilated in the HRRR every 15 min over a 1-h period adding further detail \
to that provided by the hourly data assimilation from the 13km radar-enhanced \
Rapid Refresh."""

_NOAA_MRMS_DESCRIPTION = """\
The NOAA Multi-Radar/Multi-Sensor System (MRMS) integrates data from multiple \
radars and radar networks, surface observations, numerical weather prediction \
(NWP) models, and climatology to generate seamless, high spatio-temporal \
resolution mosaics at low latency focused on hail, wind, tornado, \
quantitative precipitation estimations, convection, icing, and turbulence."""

_ECMWF_AIFS_SINGLE_DESCRIPTION = """\
The Artificial Intelligence Forecasting System (AIFS) is a data driven \
forecast model developed by the European Centre for Medium-Range Weather \
Forecasts (ECMWF). This is the non-ensemble configuration of AIFS that \
produces a single forecast trace. AIFS is trained on ECMWF's ERA5 \
re-analysis and ECMWF's operational numerical weather prediction (NWP) \
analyses."""

_ECMWF_IFS_ENS_DESCRIPTION = """\
The Integrated Forecasting System (IFS) is a global forecast model developed \
by ECMWF. ENS is an ensemble configuration of IFS, containing 51 ensemble \
members. IFS consists of a numerical model of the Earth system, which \
includes an atmospheric model at its heart, coupled with models of other \
Earth system components such as the ocean. The data assimilation system \
combines the latest weather observations with a recent forecast to obtain \
the best possible estimate of the current state of the Earth system."""


MODELS: dict[str, Model] = {
    "noaa-gfs": Model(
        id="noaa-gfs",
        name="NOAA GFS",
        description=_NOAA_GFS_DESCRIPTION,
    ),
    "noaa-gefs": Model(
        id="noaa-gefs",
        name="NOAA GEFS",
        description=_NOAA_GEFS_DESCRIPTION,
    ),
    "noaa-hrrr": Model(
        id="noaa-hrrr",
        name="NOAA HRRR",
        description=_NOAA_HRRR_DESCRIPTION,
    ),
    "noaa-mrms": Model(
        id="noaa-mrms",
        name="NOAA MRMS",
        description=_NOAA_MRMS_DESCRIPTION,
    ),
    "ecmwf-aifs-single": Model(
        id="ecmwf-aifs-single",
        name="ECMWF AIFS Single",
        description=_ECMWF_AIFS_SINGLE_DESCRIPTION,
    ),
    "ecmwf-ifs-ens": Model(
        id="ecmwf-ifs-ens",
        name="ECMWF IFS ENS",
        description=_ECMWF_IFS_ENS_DESCRIPTION,
    ),
}


class DatasetExample(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    title: str = Field(min_length=1)
    code: str = Field(min_length=1)
    language: Literal["python"] = "python"


class CatalogItem(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str = Field(min_length=1)
    icechunk_href: str = Field(pattern=r"^s3://[^/]+/.+$")
    icechunk_region: str = Field(min_length=1)
    model_id: str = Field(min_length=1)
    description_summary: str = Field(min_length=1)
    description_details: str = Field(min_length=1)
    examples: tuple[DatasetExample, ...] = Field(min_length=1)
    additional_terms: AdditionalTerms | None = None

    @property
    def icechunk_bucket(self) -> str:
        return urlparse(self.icechunk_href).netloc

    @property
    def icechunk_prefix(self) -> str:
        return urlparse(self.icechunk_href).path.lstrip("/")

    @model_validator(mode="after")
    def _id_matches_href_path(self) -> CatalogItem:
        first = self.icechunk_prefix.split("/", 1)[0]
        if first != self.id:
            raise ValueError(
                f"id {self.id!r} must be the first path fragment of icechunk_href "
                f"(got {first!r} from {self.icechunk_href!r})"
            )
        return self

    @model_validator(mode="after")
    def _model_id_is_registered(self) -> CatalogItem:
        if self.model_id not in MODELS:
            raise ValueError(
                f"model_id {self.model_id!r} is not registered in MODELS; "
                f"known ids: {sorted(MODELS)}"
            )
        return self


ECMWF_TERMS = AdditionalTerms(
    href="https://apps.ecmwf.int/datasets/licences/general/",  # type: ignore[arg-type]
    title="ECMWF Terms of Use (additional terms)",
)


# Shared prose fragments used across multiple datasets. Kept as module-level
# constants so descriptions stay wrapped consistently and edits propagate.

_NODD_SOURCE_GFS = """\
The source grib files this archive is constructed from are provided by \
[NOAA Open Data Dissemination (NODD)](https://www.noaa.gov/information-technology/open-data-dissemination) \
and accessed from the [AWS Open Data Registry](https://registry.opendata.aws/noaa-gfs-bdp-pds/). \
Operational data is additionally accessed from [NOAA NOMADS](https://nomads.ncep.noaa.gov/)."""

_NODD_SOURCE_GEFS = """\
The source grib files this archive is constructed from are provided by \
[NOAA Open Data Dissemination (NODD)](https://www.noaa.gov/information-technology/open-data-dissemination) \
and accessed from the [AWS Open Data Registry](https://registry.opendata.aws/noaa-gefs/). \
Operational data is additionally accessed from [NOAA NOMADS](https://nomads.ncep.noaa.gov/)."""

_NODD_SOURCE_HRRR = """\
The source grib files this archive is constructed from are provided by \
[NOAA Open Data Dissemination (NODD)](https://www.noaa.gov/information-technology/open-data-dissemination) \
and accessed from the [AWS Open Data Registry](https://registry.opendata.aws/noaa-hrrr-pds/). \
Operational data is additionally accessed from [NOAA NOMADS](https://nomads.ncep.noaa.gov/)."""

_NODD_SOURCE_MRMS = """\
The source files this archive is constructed from are provided by \
[NOAA Open Data Dissemination (NODD)](https://www.noaa.gov/information-technology/open-data-dissemination) \
and accessed from the [AWS Open Data Registry](https://registry.opendata.aws/noaa-mrms-pds/). \
Operational data is additionally accessed from [NCEP](https://mrms.ncep.noaa.gov/)."""

_ECMWF_SOURCE = """\
The source grib files this archive is constructed from are provided by \
[ECMWF Open Data](https://www.ecmwf.int/en/forecasts/datasets/open-data) \
and accessed from the [AWS Open Data Registry](https://registry.opendata.aws/ecmwf-forecasts/).

ECMWF does not provide user support for the free & open datasets. Users should refer to the public [User Forum](https://forum.ecmwf.int/) for any questions related to the source material."""

_ECMWF_MODEL_UPDATES = """\
AIFS is updated regularly. Find details of recent and upcoming \
[changes to the forecasting system](https://confluence.ecmwf.int/display/FCST/Changes+to+the+forecasting+system) on the ECMWF website."""

_ECMWF_MODEL_UPDATES_IFS = """\
IFS is updated regularly. Find details of recent and upcoming \
[changes to the forecasting system](https://confluence.ecmwf.int/display/FCST/Changes+to+the+forecasting+system) on the ECMWF website."""

_STORAGE = """\
Storage for this dataset is generously provided by \
[Source Cooperative](https://source.coop/), \
a [Radiant Earth](https://radiant.earth/) initiative. \
Icechunk storage generously provided by [AWS Open Data](https://aws.amazon.com/opendata/)."""


def _compression(template_config_path: str) -> str:
    return (
        "The data values in this dataset have been rounded in their binary "
        "floating point representation to improve compression. See "
        "[Klöwer et al. 2021](https://www.nature.com/articles/s43588-021-00156-2) "
        "for more information on this approach. The exact number of rounded bits "
        f"can be found in our [reformatting code]({template_config_path})."
    )


_GFS_ANALYSIS_REFORMATTER = (
    "https://github.com/dynamical-org/reformatters/blob/main/"
    "src/reformatters/noaa/gfs/analysis/template_config.py"
)
_GFS_FORECAST_REFORMATTER = (
    "https://github.com/dynamical-org/reformatters/blob/main/"
    "src/reformatters/noaa/gfs/forecast/template_config.py"
)
_GEFS_REFORMATTER = (
    "https://github.com/dynamical-org/reformatters/blob/main/"
    "src/reformatters/noaa/gefs/common_gefs_template_config.py"
)
_HRRR_REFORMATTER = "https://github.com/dynamical-org/reformatters/"
_MRMS_REFORMATTER = "https://github.com/dynamical-org/reformatters/"
_AIFS_SINGLE_REFORMATTER = (
    "https://github.com/dynamical-org/reformatters/blob/main/"
    "src/reformatters/ecmwf/aifs_single/forecast/template_config.py"
)
_IFS_ENS_REFORMATTER = (
    "https://github.com/dynamical-org/reformatters/blob/main/"
    "src/reformatters/ecmwf/ifs_ens/forecast_15_day_0_25_degree/template_config.py"
)


# Per-dataset prose — summary, details, and example code snippets.

_NOAA_GFS_ANALYSIS_SUMMARY = """\
This analysis dataset is an archive of the model's best estimate of past \
weather. It is created by concatenating the first few hours of each \
historical forecast to provide a dataset with dimensions time, latitude, and \
longitude."""

_NOAA_GFS_ANALYSIS_DETAILS = f"""\
### Construction

GFS starts a new model run every 6 hours and dynamical.org has created this \
analysis by concatenating the first 6 hours of each forecast along the time \
dimension.

### Source

{_NODD_SOURCE_GFS}

### Storage

{_STORAGE}

### Compression

{_compression(_GFS_ANALYSIS_REFORMATTER)}

### Related dataset

[NOAA GEFS analysis](/catalog/noaa-gefs-analysis/) provides a much longer historical record."""

_NOAA_GFS_ANALYSIS_CODE = """\
import xarray as xr  # xarray>=2025.1.2 and zarr>=3.0.8 for zarr v3 support

ds = xr.open_zarr("https://data.dynamical.org/noaa/gfs/analysis/latest.zarr")
ds["temperature_2m"].sel(time="2026-01-01T00", latitude=0, longitude=0).compute()"""


_NOAA_GFS_FORECAST_SUMMARY = """\
This dataset is an archive of past and present GFS forecasts. Forecasts are \
identified by an initialization time (`init_time`) denoting the start time \
of the model run. Each forecast steps forward in time along the `lead_time` \
dimension."""

_NOAA_GFS_FORECAST_DETAILS = f"""\
### Source

{_NODD_SOURCE_GFS}

### Storage

{_STORAGE}

### Compression

{_compression(_GFS_FORECAST_REFORMATTER)}"""

_NOAA_GFS_FORECAST_CODE = """\
import xarray as xr  # xarray>=2025.1.2 and zarr>=3.0.8 for zarr v3 support

ds = xr.open_zarr("https://data.dynamical.org/noaa/gfs/forecast/latest.zarr")
ds["temperature_2m"].sel(init_time="2025-01-01T00", latitude=0, longitude=0).max().compute()"""


_NOAA_GEFS_FORECAST_SUMMARY = """\
This dataset is an archive of past and present GEFS forecasts. Forecasts are \
identified by an initialization time (`init_time`) denoting the start time \
of the model run as well as by the `ensemble_member`. Each forecast has a 3 \
hourly forecast step along the `lead_time` dimension. This dataset contains \
only the 00 hour UTC initialization times which produce the full length, 35 \
day forecast."""

_NOAA_GEFS_FORECAST_DETAILS = f"""\
### Interpolation

Source data is available at both 0.25-degree and 0.5-degree resolutions. All \
variables except the 100m wind components are derived from a 0.25-degree \
grid for the first 240 hours of each forecast and from a 0.5-degree grid \
for the remainder. 100m wind components are derived from a 0.5-degree grid \
for all lead times. Bilinear interpolation is used to convert 0.5-degree \
data to a 0.25-degree grid. The original 0.5-degree values can be retrieved \
by selecting every other pixel starting from offset 0 in both the latitude \
and longitude dimensions (e.g. `array[::2, ::2]`).

### Source

{_NODD_SOURCE_GEFS}

### Storage

{_STORAGE}

### Compression

{_compression(_GEFS_REFORMATTER)}"""

_NOAA_GEFS_FORECAST_CODE = """\
import xarray as xr  # xarray>=2025.1.2 and zarr>=3.0.8 for zarr v3 support

ds = xr.open_zarr("https://data.dynamical.org/noaa/gefs/forecast-35-day/latest.zarr")
ds["temperature_2m"].sel(init_time="2025-01-01T00", latitude=0, longitude=0).max().compute()"""


_NOAA_GEFS_ANALYSIS_SUMMARY = """\
This analysis dataset is an archive of the model's best estimate of past \
weather. It is created by concatenating the first few hours of each \
historical forecast to provide a dataset with dimensions time, latitude, and \
longitude."""

_NOAA_GEFS_ANALYSIS_DETAILS = f"""\
### Sources

To provide the longest possible historical record, this dataset in \
constructed from three distinct GEFS forecast archives.

- From 2000-01-01 to 2019-12-31 we use the [GEFS reforecast](https://registry.opendata.aws/noaa-gefs-reforecast/).
- From 2020-01-01 to 2020-09-23 we use [GEFS forecast archive](https://registry.opendata.aws/noaa-gefs/) data which has a lower spatial and temporal resolution.
- From 2020-09-23 to Present we use [GEFS operational forecast archives](https://registry.opendata.aws/noaa-gefs/).

Source files are provided by [NOAA Open Data Dissemination (NODD)](https://www.noaa.gov/information-technology/open-data-dissemination) \
and accessed from the [AWS Open Data Registry](https://registry.opendata.aws/noaa-gefs/). \
Operational data is additionally accessed from [NOAA NOMADS](https://nomads.ncep.noaa.gov/).

### Variable availability

Data is available for all variables at all times with the following exceptions.

- Unavailable before 2020-01-01: `relative_humidity_2m`, `percent_frozen_precipitation_surface`, `categorical_freezing_rain_surface`, `categorical_ice_pellets_surface`, `categorical_rain_surface`, `categorical_snow_surface`
- Unavailable 2020-01-01T00 to 2020-09-22T21: `geopotential_height_cloud_ceiling`

### Construction

To create a single time dimension we concatenate the first few hours of each \
forecast. From 2000-01-01 to 2019-12-31 reforecasts are available once per \
day and this dataset uses the first 21 or 24 hours of each forecast. From \
2020-01-01 to present forecasts are available every 6 hours and this dataset \
uses the first 3 or 6 hours of each forecast. Variables with an \
instantaneous `step_type` use the shortest possible lead times (e.g. 0 and 3 \
hours) while accumulated variables must use one additional forecast step \
(e.g. 3 and 6 hours) because they do not have an hour 0 forecast value.

### Interpolation

For most of the time range of the archive the source data is available at \
0.25-degree resolution and a 3 hourly time step and we perform no \
interpolation. There are two exceptions to this. 1) From 2020-01-01 to \
2020-09-23 the source data has a 1.0-degree spatial resolution and a 6 \
hourly time step. 2) From 2020-09-23 to present the 100m wind components \
have a 0.5-degree spatial resolution in the source data. To provide a \
consistent archive in the above two cases we first perform bilinear \
interpolation in space to 0.25-degree resolution followed by linear \
interpolation in time to a 3-hourly timestep if necessary. The original, \
uninterpolated data can be obtained by selecting latitudes and longitudes \
evenly divisible by 1 and, in case 1), time steps whose hour is divisible by 6.

### Storage

{_STORAGE}

### Compression

{_compression(_GEFS_REFORMATTER)}"""

_NOAA_GEFS_ANALYSIS_CODE = """\
import xarray as xr  # xarray>=2025.1.2 and zarr>=3.0.8 for zarr v3 support

ds = xr.open_zarr("https://data.dynamical.org/noaa/gefs/analysis/latest.zarr")
ds["temperature_2m"].sel(time="2025-01-01T00", latitude=0, longitude=0).compute()"""


_NOAA_HRRR_FORECAST_SUMMARY = """\
This dataset is an archive of past and present HRRR forecasts. Forecasts are \
identified by an initialization time (`init_time`) denoting the start time \
of the model run. Each forecast has an hourly forecast step along the \
`lead_time` dimension. This dataset contains only the 00, 06, 12, and 18 \
hour UTC initialization times which produce the full length, 48 hour \
forecast.

This dataset uses the native HRRR Lambert Conformal Conic projection, with \
spatial indexing along the `x` and `y` dimensions. The example notebook \
shows how to use the embedded spatial reference to select geographic areas \
of interest."""

_NOAA_HRRR_FORECAST_DETAILS = f"""\
### Source

{_NODD_SOURCE_HRRR}

### Data availability

Forecasts initialized through 2020-12-02T06 UTC include data only for the \
first 36 hours; steps 37\u201348 are filled with NaNs. Starting with the \
2020-12-02T12 UTC initialization, forecasts cover the full 48 hours.

### Storage

{_STORAGE}

### Compression

{_compression(_HRRR_REFORMATTER)}"""

_NOAA_HRRR_FORECAST_CODE = """\
import xarray as xr  # xarray>=2025.1.2 and zarr>=3.0.8 for zarr v3 support

ds = xr.open_zarr("https://data.dynamical.org/noaa/hrrr/forecast-48-hour/latest.zarr")
ds["temperature_2m"].sel(init_time="2025-01-01T00", x=0, y=0, method="nearest").max().compute()"""


_NOAA_HRRR_ANALYSIS_SUMMARY = """\
This analysis dataset is an archive of the model's best estimate of past \
weather. It is created by concatenating the first hour of each historical \
forecast to provide a dataset with dimensions time, x, and y.

This dataset uses the native HRRR Lambert Conformal Conic projection, with \
spatial indexing along the `x` and `y` dimensions. The example notebook \
shows how to use the embedded spatial reference to select geographic areas \
of interest."""

_NOAA_HRRR_ANALYSIS_DETAILS = f"""\
### Construction

HRRR starts a new model run every hour and dynamical.org has created this \
analysis by concatenating the first step of each forecast along the time \
dimension. Accumulated variables (e.g. precipitation) are read from the \
second step of the previous hour's forecast.

### Data availability

There are a significant number of missing source files before August 2018 \
(HRRR v1 and v2 period), and a small number from August 2018 to December \
2020 (HRRR v3 period).

`downward_long_wave_radiation_flux_surface` and `relative_humidity_2m` are \
unavailable before August 2016 (HRRR v1 period).

This dataset has NaN values where source data are unavailable.

### Source

{_NODD_SOURCE_HRRR}

### Storage

{_STORAGE}

### Compression

{_compression(_HRRR_REFORMATTER)}"""

_NOAA_HRRR_ANALYSIS_CODE = """\
import xarray as xr  # xarray>=2025.1.2 and zarr>=3.0.8 for zarr v3 support

ds = xr.open_zarr("https://data.dynamical.org/noaa/hrrr/analysis/latest.zarr")
ds["temperature_2m"].sel(time="2025-01-01T00", x=0, y=0, method="nearest").compute()"""


_NOAA_MRMS_SUMMARY = """\
This analysis dataset is an archive of MRMS radar and multi-sensor \
precipitation and weather analyses over the contiguous United States \
(CONUS)."""

_NOAA_MRMS_DETAILS = f"""\
### Spatial coverage

Use this dataset over the land areas of the contiguous United States. \
Radar-only and precipitation type variables contain `NaN` values beyond the \
range of US radar. `precipitation_pass_1_surface` and \
`precipitation_pass_2_surface` extend further into the ocean, but still \
contain `NaN` values in the southeast corner of the domain over the Atlantic.

### Temporal coverage

`precipitation_surface` combines multiple MRMS products to minimize missing \
values. Despite this, some hours (particularly early in the record) contain \
`NaN` values where data is unavailable.

`precipitation_pass_2_surface` and `precipitation_pass_1_surface` are \
available starting 2020-10-15. For timestamps prior to this date, these \
variables are filled with `NaN`.

### Source

{_NODD_SOURCE_MRMS}

### Storage

{_STORAGE}

### Compression

{_compression(_MRMS_REFORMATTER)}"""

_NOAA_MRMS_CODE = """\
import xarray as xr  # xarray>=2025.1.2 and zarr>=3.0.8 for zarr v3 support

ds = xr.open_zarr("https://data.dynamical.org/noaa/mrms/conus-analysis-hourly/latest.zarr")
ds["precipitation_surface"].sel(time="2026-01-01T00", latitude=40, longitude=-90, method="nearest").compute()"""


_ECMWF_AIFS_SINGLE_SUMMARY = """\
This dataset is an archive of past and present ECMWF AIFS Single forecasts. \
Forecasts are identified by an initialization time (`init_time`) denoting \
the start time of the model run. Each forecast steps forward in time along \
the `lead_time` dimension, from 0 to 360 hours (15 days) at a 6 hourly step."""

_ECMWF_AIFS_SINGLE_DETAILS = f"""\
### Source

{_ECMWF_SOURCE}

### Model updates

{_ECMWF_MODEL_UPDATES}

### Storage

{_STORAGE}

### Compression

{_compression(_AIFS_SINGLE_REFORMATTER)}"""

_ECMWF_AIFS_SINGLE_CODE = """\
import xarray as xr  # xarray>=2025.1.2 and zarr>=3.0.8 for zarr v3 support

ds = xr.open_zarr("https://data.dynamical.org/ecmwf/aifs-single/forecast/latest.zarr")
ds["temperature_2m"].sel(init_time="2025-01-01T00", latitude=0, longitude=0).max().compute()"""


_ECMWF_IFS_ENS_SUMMARY = """\
This dataset is an archive of past and present ECMWF IFS ENS forecasts. \
Forecasts are identified by an initialization time (`init_time`) denoting \
the start time of the model run, as well as by the `ensemble_member`. Along \
the `lead_time` dimension, each forecast begins at a 3 hourly forecast step \
(0-144 hours) and switches to a 6 hourly step for days 6 through 15 of the \
forecast (hours 144-360). This dataset contains the 00 UTC initialization \
times only."""

_ECMWF_IFS_ENS_DETAILS = f"""\
### Source

{_ECMWF_SOURCE}

### Data availability

This dataset contains only forecasts initialized on or after 2024-04-01, \
which are available at the open data 0.25 degree (~20km) resolution. All \
variables are available for the full period, save for \
`precipitation_surface`, which is filled with NaNs before 2024-11-13 UTC.

### Ensemble members

Each forecast contains 51 ensemble members, including a control member (0) \
and 50 perturbed members (1-50). The control forecast is produced with the \
best available data and unperturbed models. The other 50 members are each \
produced with slight perturbations of initial conditions and of the models. \
Taken together, ensemble of 51 forecasts shows the range of possible \
outcomes and the likelihood of their occurrence.

### Model updates

{_ECMWF_MODEL_UPDATES_IFS}

### Storage

{_STORAGE}

### Compression

{_compression(_IFS_ENS_REFORMATTER)}"""

_ECMWF_IFS_ENS_CODE = """\
import xarray as xr  # xarray>=2025.1.2 and zarr>=3.0.8 for zarr v3 support

ds = xr.open_zarr("https://data.dynamical.org/ecmwf/ifs-ens/forecast-15-day-0-25-degree/latest.zarr")
ds["temperature_2m"].sel(init_time="2025-01-01T00", latitude=0, longitude=0).max().compute()"""


CATALOG_ITEMS: list[CatalogItem] = [
    CatalogItem(
        id="noaa-gfs-analysis",
        icechunk_href="s3://dynamical-noaa-gfs/noaa-gfs-analysis/v0.1.0.icechunk/",
        icechunk_region="us-west-2",
        model_id="noaa-gfs",
        description_summary=_NOAA_GFS_ANALYSIS_SUMMARY,
        description_details=_NOAA_GFS_ANALYSIS_DETAILS,
        examples=(
            DatasetExample(
                title="Temperature at a specific place and time",
                code=_NOAA_GFS_ANALYSIS_CODE,
            ),
        ),
    ),
    CatalogItem(
        id="noaa-gfs-forecast",
        icechunk_href="s3://dynamical-noaa-gfs/noaa-gfs-forecast/v0.2.7.icechunk/",
        icechunk_region="us-west-2",
        model_id="noaa-gfs",
        description_summary=_NOAA_GFS_FORECAST_SUMMARY,
        description_details=_NOAA_GFS_FORECAST_DETAILS,
        examples=(
            DatasetExample(
                title="Maximum temperature in a forecast",
                code=_NOAA_GFS_FORECAST_CODE,
            ),
        ),
    ),
    CatalogItem(
        id="noaa-gefs-forecast-35-day",
        icechunk_href="s3://dynamical-noaa-gefs/noaa-gefs-forecast-35-day/v0.2.0.icechunk/",
        icechunk_region="us-west-2",
        model_id="noaa-gefs",
        description_summary=_NOAA_GEFS_FORECAST_SUMMARY,
        description_details=_NOAA_GEFS_FORECAST_DETAILS,
        examples=(
            DatasetExample(
                title="Maximum temperature in ensemble forecast",
                code=_NOAA_GEFS_FORECAST_CODE,
            ),
        ),
    ),
    CatalogItem(
        id="noaa-gefs-analysis",
        icechunk_href="s3://dynamical-noaa-gefs/noaa-gefs-analysis/v0.1.2.icechunk/",
        icechunk_region="us-west-2",
        model_id="noaa-gefs",
        description_summary=_NOAA_GEFS_ANALYSIS_SUMMARY,
        description_details=_NOAA_GEFS_ANALYSIS_DETAILS,
        examples=(
            DatasetExample(
                title="Temperature at a specific place and time",
                code=_NOAA_GEFS_ANALYSIS_CODE,
            ),
        ),
    ),
    CatalogItem(
        id="noaa-hrrr-forecast-48-hour",
        icechunk_href="s3://dynamical-noaa-hrrr/noaa-hrrr-forecast-48-hour/v0.1.0.icechunk/",
        icechunk_region="us-west-2",
        model_id="noaa-hrrr",
        description_summary=_NOAA_HRRR_FORECAST_SUMMARY,
        description_details=_NOAA_HRRR_FORECAST_DETAILS,
        examples=(
            DatasetExample(
                title="Maximum temperature in a forecast",
                code=_NOAA_HRRR_FORECAST_CODE,
            ),
        ),
    ),
    CatalogItem(
        id="noaa-hrrr-analysis",
        icechunk_href="s3://dynamical-noaa-hrrr/noaa-hrrr-analysis/v0.2.0.icechunk/",
        icechunk_region="us-west-2",
        model_id="noaa-hrrr",
        description_summary=_NOAA_HRRR_ANALYSIS_SUMMARY,
        description_details=_NOAA_HRRR_ANALYSIS_DETAILS,
        examples=(
            DatasetExample(
                title="Temperature at a specific place and time",
                code=_NOAA_HRRR_ANALYSIS_CODE,
            ),
        ),
    ),
    CatalogItem(
        id="noaa-mrms-conus-analysis-hourly",
        icechunk_href="s3://dynamical-noaa-mrms/noaa-mrms-conus-analysis-hourly/v0.3.0.icechunk/",
        icechunk_region="us-west-2",
        model_id="noaa-mrms",
        description_summary=_NOAA_MRMS_SUMMARY,
        description_details=_NOAA_MRMS_DETAILS,
        examples=(
            DatasetExample(
                title="Precipitation at a place and time",
                code=_NOAA_MRMS_CODE,
            ),
        ),
    ),
    CatalogItem(
        id="ecmwf-aifs-single-forecast",
        icechunk_href="s3://dynamical-ecmwf-aifs-single/ecmwf-aifs-single-forecast/v0.1.0.icechunk/",
        icechunk_region="us-west-2",
        model_id="ecmwf-aifs-single",
        description_summary=_ECMWF_AIFS_SINGLE_SUMMARY,
        description_details=_ECMWF_AIFS_SINGLE_DETAILS,
        examples=(
            DatasetExample(
                title="Maximum temperature in a forecast",
                code=_ECMWF_AIFS_SINGLE_CODE,
            ),
        ),
        additional_terms=ECMWF_TERMS,
    ),
    CatalogItem(
        id="ecmwf-ifs-ens-forecast-15-day-0-25-degree",
        icechunk_href="s3://dynamical-ecmwf-ifs-ens/ecmwf-ifs-ens-forecast-15-day-0-25-degree/v0.1.0.icechunk/",
        icechunk_region="us-west-2",
        model_id="ecmwf-ifs-ens",
        description_summary=_ECMWF_IFS_ENS_SUMMARY,
        description_details=_ECMWF_IFS_ENS_DETAILS,
        examples=(
            DatasetExample(
                title="Maximum temperature in ensemble",
                code=_ECMWF_IFS_ENS_CODE,
            ),
        ),
        additional_terms=ECMWF_TERMS,
    ),
]


_COLLECTION_IDS = [item.id for item in CATALOG_ITEMS]
