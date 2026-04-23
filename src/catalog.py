from __future__ import annotations

import pathlib
from enum import StrEnum
from typing import Literal
from urllib.parse import urlparse

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, model_validator

PROSE_DIR = pathlib.Path(__file__).parent / "prose"


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


class DatasetExample(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    title: str = Field(min_length=1)
    code: str = Field(min_length=1)
    language: Literal["python"] = "python"


# Shared prose fragments, substituted into markdown files via {{ name }} tokens.

STORAGE = (
    "Storage for this dataset is generously provided by "
    "[Source Cooperative](https://source.coop/), "
    "a [Radiant Earth](https://radiant.earth/) initiative. "
    "Icechunk storage generously provided by [AWS Open Data](https://aws.amazon.com/opendata/)."
)

NODD_SOURCE_GFS = (
    "The source grib files this archive is constructed from are provided by "
    "[NOAA Open Data Dissemination (NODD)](https://www.noaa.gov/information-technology/open-data-dissemination) "
    "and accessed from the [AWS Open Data Registry](https://registry.opendata.aws/noaa-gfs-bdp-pds/). "
    "Operational data is additionally accessed from [NOAA NOMADS](https://nomads.ncep.noaa.gov/)."
)

NODD_SOURCE_GEFS = (
    "The source grib files this archive is constructed from are provided by "
    "[NOAA Open Data Dissemination (NODD)](https://www.noaa.gov/information-technology/open-data-dissemination) "
    "and accessed from the [AWS Open Data Registry](https://registry.opendata.aws/noaa-gefs/). "
    "Operational data is additionally accessed from [NOAA NOMADS](https://nomads.ncep.noaa.gov/)."
)

NODD_SOURCE_HRRR = (
    "The source grib files this archive is constructed from are provided by "
    "[NOAA Open Data Dissemination (NODD)](https://www.noaa.gov/information-technology/open-data-dissemination) "
    "and accessed from the [AWS Open Data Registry](https://registry.opendata.aws/noaa-hrrr-pds/). "
    "Operational data is additionally accessed from [NOAA NOMADS](https://nomads.ncep.noaa.gov/)."
)

NODD_SOURCE_MRMS = (
    "The source files this archive is constructed from are provided by "
    "[NOAA Open Data Dissemination (NODD)](https://www.noaa.gov/information-technology/open-data-dissemination) "
    "and accessed from the [AWS Open Data Registry](https://registry.opendata.aws/noaa-mrms-pds/). "
    "Operational data is additionally accessed from [NCEP](https://mrms.ncep.noaa.gov/)."
)

ECMWF_SOURCE = (
    "The source grib files this archive is constructed from are provided by "
    "[ECMWF Open Data](https://www.ecmwf.int/en/forecasts/datasets/open-data) "
    "and accessed from the [AWS Open Data Registry](https://registry.opendata.aws/ecmwf-forecasts/).\n\n"
    "ECMWF does not provide user support for the free & open datasets. Users should refer to the public "
    "[User Forum](https://forum.ecmwf.int/) for any questions related to the source material."
)

ECMWF_MODEL_UPDATES = (
    "AIFS is updated regularly. Find details of recent and upcoming "
    "[changes to the forecasting system](https://confluence.ecmwf.int/display/FCST/Changes+to+the+forecasting+system) "
    "on the ECMWF website."
)

ECMWF_MODEL_UPDATES_IFS = (
    "IFS is updated regularly. Find details of recent and upcoming "
    "[changes to the forecasting system](https://confluence.ecmwf.int/display/FCST/Changes+to+the+forecasting+system) "
    "on the ECMWF website."
)

# Compression references {{ reformatter_url }} — supplied per-dataset at load time.
COMPRESSION = (
    "The data values in this dataset have been rounded in their binary "
    "floating point representation to improve compression. See "
    "[Klöwer et al. 2021](https://www.nature.com/articles/s43588-021-00156-2) "
    "for more information on this approach. The exact number of rounded bits "
    "can be found in our [reformatting code]({{ reformatter_url }})."
)

FRAGMENTS: dict[str, str] = {
    "storage": STORAGE,
    "nodd_source_gfs": NODD_SOURCE_GFS,
    "nodd_source_gefs": NODD_SOURCE_GEFS,
    "nodd_source_hrrr": NODD_SOURCE_HRRR,
    "nodd_source_mrms": NODD_SOURCE_MRMS,
    "ecmwf_source": ECMWF_SOURCE,
    "ecmwf_model_updates": ECMWF_MODEL_UPDATES,
    "ecmwf_model_updates_ifs": ECMWF_MODEL_UPDATES_IFS,
    "compression": COMPRESSION,
}


def _load_prose(path: str, **extra: str) -> str:
    """Read a prose file and expand ``{{ name }}`` tokens.

    Two-pass so a fragment can reference another token — e.g. ``{{ compression }}``
    itself contains ``{{ reformatter_url }}``, supplied per-dataset via ``extra``.
    """
    text = (PROSE_DIR / path).read_text().strip()
    fragments = {**FRAGMENTS, **extra}
    for _ in range(2):
        for name, value in fragments.items():
            text = text.replace(f"{{{{ {name} }}}}", value)
    return text


def _model(model_id: str, name: str) -> Model:
    return Model(
        id=model_id,
        name=name,
        description=_load_prose(f"models/{model_id}.md"),
    )


MODELS: dict[str, Model] = {
    "noaa-gfs": _model("noaa-gfs", "NOAA GFS"),
    "noaa-gefs": _model("noaa-gefs", "NOAA GEFS"),
    "noaa-hrrr": _model("noaa-hrrr", "NOAA HRRR"),
    "noaa-mrms": _model("noaa-mrms", "NOAA MRMS"),
    "ecmwf-aifs-single": _model("ecmwf-aifs-single", "ECMWF AIFS Single"),
    "ecmwf-ifs-ens": _model("ecmwf-ifs-ens", "ECMWF IFS ENS"),
}


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


def _details(dataset_id: str, reformatter_url: str) -> str:
    return _load_prose(f"datasets/{dataset_id}.md", reformatter_url=reformatter_url)


CATALOG_ITEMS: list[CatalogItem] = [
    CatalogItem(
        id="noaa-gfs-analysis",
        icechunk_href="s3://dynamical-noaa-gfs/noaa-gfs-analysis/v0.1.0.icechunk/",
        icechunk_region="us-west-2",
        model_id="noaa-gfs",
        description_summary=(
            "This analysis dataset is an archive of the model's best estimate "
            "of past weather. It is created by concatenating the first few "
            "hours of each historical forecast to provide a dataset with "
            "dimensions time, latitude, and longitude."
        ),
        description_details=_details(
            "noaa-gfs-analysis",
            "https://github.com/dynamical-org/reformatters/blob/main/src/reformatters/noaa/gfs/analysis/template_config.py",
        ),
        examples=(
            DatasetExample(
                title="Temperature at a specific place and time",
                code=(
                    'import xarray as xr  # xarray>=2025.1.2 and zarr>=3.0.8 for zarr v3 support\n\n'
                    'ds = xr.open_zarr("https://data.dynamical.org/noaa/gfs/analysis/latest.zarr")\n'
                    'ds["temperature_2m"].sel(time="2026-01-01T00", latitude=0, longitude=0).compute()'
                ),
            ),
        ),
    ),
    CatalogItem(
        id="noaa-gfs-forecast",
        icechunk_href="s3://dynamical-noaa-gfs/noaa-gfs-forecast/v0.2.7.icechunk/",
        icechunk_region="us-west-2",
        model_id="noaa-gfs",
        description_summary=(
            "This dataset is an archive of past and present GFS forecasts. "
            "Forecasts are identified by an initialization time (`init_time`) "
            "denoting the start time of the model run. Each forecast steps "
            "forward in time along the `lead_time` dimension."
        ),
        description_details=_details(
            "noaa-gfs-forecast",
            "https://github.com/dynamical-org/reformatters/blob/main/src/reformatters/noaa/gfs/forecast/template_config.py",
        ),
        examples=(
            DatasetExample(
                title="Maximum temperature in a forecast",
                code=(
                    'import xarray as xr  # xarray>=2025.1.2 and zarr>=3.0.8 for zarr v3 support\n\n'
                    'ds = xr.open_zarr("https://data.dynamical.org/noaa/gfs/forecast/latest.zarr")\n'
                    'ds["temperature_2m"].sel(init_time="2025-01-01T00", latitude=0, longitude=0).max().compute()'
                ),
            ),
        ),
    ),
    CatalogItem(
        id="noaa-gefs-forecast-35-day",
        icechunk_href="s3://dynamical-noaa-gefs/noaa-gefs-forecast-35-day/v0.2.0.icechunk/",
        icechunk_region="us-west-2",
        model_id="noaa-gefs",
        description_summary=(
            "This dataset is an archive of past and present GEFS forecasts. "
            "Forecasts are identified by an initialization time (`init_time`) "
            "denoting the start time of the model run as well as by the "
            "`ensemble_member`. Each forecast has a 3 hourly forecast step "
            "along the `lead_time` dimension. This dataset contains only the "
            "00 hour UTC initialization times which produce the full length, "
            "35 day forecast."
        ),
        description_details=_details(
            "noaa-gefs-forecast-35-day",
            "https://github.com/dynamical-org/reformatters/blob/main/src/reformatters/noaa/gefs/common_gefs_template_config.py",
        ),
        examples=(
            DatasetExample(
                title="Maximum temperature in ensemble forecast",
                code=(
                    'import xarray as xr  # xarray>=2025.1.2 and zarr>=3.0.8 for zarr v3 support\n\n'
                    'ds = xr.open_zarr("https://data.dynamical.org/noaa/gefs/forecast-35-day/latest.zarr")\n'
                    'ds["temperature_2m"].sel(init_time="2025-01-01T00", latitude=0, longitude=0).max().compute()'
                ),
            ),
        ),
    ),
    CatalogItem(
        id="noaa-gefs-analysis",
        icechunk_href="s3://dynamical-noaa-gefs/noaa-gefs-analysis/v0.1.2.icechunk/",
        icechunk_region="us-west-2",
        model_id="noaa-gefs",
        description_summary=(
            "This analysis dataset is an archive of the model's best estimate "
            "of past weather. It is created by concatenating the first few "
            "hours of each historical forecast to provide a dataset with "
            "dimensions time, latitude, and longitude."
        ),
        description_details=_details(
            "noaa-gefs-analysis",
            "https://github.com/dynamical-org/reformatters/blob/main/src/reformatters/noaa/gefs/common_gefs_template_config.py",
        ),
        examples=(
            DatasetExample(
                title="Temperature at a specific place and time",
                code=(
                    'import xarray as xr  # xarray>=2025.1.2 and zarr>=3.0.8 for zarr v3 support\n\n'
                    'ds = xr.open_zarr("https://data.dynamical.org/noaa/gefs/analysis/latest.zarr")\n'
                    'ds["temperature_2m"].sel(time="2025-01-01T00", latitude=0, longitude=0).compute()'
                ),
            ),
        ),
    ),
    CatalogItem(
        id="noaa-hrrr-forecast-48-hour",
        icechunk_href="s3://dynamical-noaa-hrrr/noaa-hrrr-forecast-48-hour/v0.1.0.icechunk/",
        icechunk_region="us-west-2",
        model_id="noaa-hrrr",
        description_summary=(
            "This dataset is an archive of past and present HRRR forecasts. "
            "Forecasts are identified by an initialization time (`init_time`) "
            "denoting the start time of the model run. Each forecast has an "
            "hourly forecast step along the `lead_time` dimension. This "
            "dataset contains only the 00, 06, 12, and 18 hour UTC "
            "initialization times which produce the full length, 48 hour "
            "forecast.\n\nThis dataset uses the native HRRR Lambert Conformal "
            "Conic projection, with spatial indexing along the `x` and `y` "
            "dimensions. The example notebook shows how to use the embedded "
            "spatial reference to select geographic areas of interest."
        ),
        description_details=_details(
            "noaa-hrrr-forecast-48-hour",
            "https://github.com/dynamical-org/reformatters/",
        ),
        examples=(
            DatasetExample(
                title="Maximum temperature in a forecast",
                code=(
                    'import xarray as xr  # xarray>=2025.1.2 and zarr>=3.0.8 for zarr v3 support\n\n'
                    'ds = xr.open_zarr("https://data.dynamical.org/noaa/hrrr/forecast-48-hour/latest.zarr")\n'
                    'ds["temperature_2m"].sel(init_time="2025-01-01T00", x=0, y=0, method="nearest").max().compute()'
                ),
            ),
        ),
    ),
    CatalogItem(
        id="noaa-hrrr-analysis",
        icechunk_href="s3://dynamical-noaa-hrrr/noaa-hrrr-analysis/v0.2.0.icechunk/",
        icechunk_region="us-west-2",
        model_id="noaa-hrrr",
        description_summary=(
            "This analysis dataset is an archive of the model's best estimate "
            "of past weather. It is created by concatenating the first hour "
            "of each historical forecast to provide a dataset with dimensions "
            "time, x, and y.\n\nThis dataset uses the native HRRR Lambert "
            "Conformal Conic projection, with spatial indexing along the `x` "
            "and `y` dimensions. The example notebook shows how to use the "
            "embedded spatial reference to select geographic areas of "
            "interest."
        ),
        description_details=_details(
            "noaa-hrrr-analysis",
            "https://github.com/dynamical-org/reformatters/",
        ),
        examples=(
            DatasetExample(
                title="Temperature at a specific place and time",
                code=(
                    'import xarray as xr  # xarray>=2025.1.2 and zarr>=3.0.8 for zarr v3 support\n\n'
                    'ds = xr.open_zarr("https://data.dynamical.org/noaa/hrrr/analysis/latest.zarr")\n'
                    'ds["temperature_2m"].sel(time="2025-01-01T00", x=0, y=0, method="nearest").compute()'
                ),
            ),
        ),
    ),
    CatalogItem(
        id="noaa-mrms-conus-analysis-hourly",
        icechunk_href="s3://dynamical-noaa-mrms/noaa-mrms-conus-analysis-hourly/v0.3.0.icechunk/",
        icechunk_region="us-west-2",
        model_id="noaa-mrms",
        description_summary=(
            "This analysis dataset is an archive of MRMS radar and "
            "multi-sensor precipitation and weather analyses over the "
            "contiguous United States (CONUS)."
        ),
        description_details=_details(
            "noaa-mrms-conus-analysis-hourly",
            "https://github.com/dynamical-org/reformatters/",
        ),
        examples=(
            DatasetExample(
                title="Precipitation at a place and time",
                code=(
                    'import xarray as xr  # xarray>=2025.1.2 and zarr>=3.0.8 for zarr v3 support\n\n'
                    'ds = xr.open_zarr("https://data.dynamical.org/noaa/mrms/conus-analysis-hourly/latest.zarr")\n'
                    'ds["precipitation_surface"].sel(time="2026-01-01T00", latitude=40, longitude=-90, method="nearest").compute()'
                ),
            ),
        ),
    ),
    CatalogItem(
        id="ecmwf-aifs-single-forecast",
        icechunk_href="s3://dynamical-ecmwf-aifs-single/ecmwf-aifs-single-forecast/v0.1.0.icechunk/",
        icechunk_region="us-west-2",
        model_id="ecmwf-aifs-single",
        description_summary=(
            "This dataset is an archive of past and present ECMWF AIFS Single "
            "forecasts. Forecasts are identified by an initialization time "
            "(`init_time`) denoting the start time of the model run. Each "
            "forecast steps forward in time along the `lead_time` dimension, "
            "from 0 to 360 hours (15 days) at a 6 hourly step."
        ),
        description_details=_details(
            "ecmwf-aifs-single-forecast",
            "https://github.com/dynamical-org/reformatters/blob/main/src/reformatters/ecmwf/aifs_single/forecast/template_config.py",
        ),
        examples=(
            DatasetExample(
                title="Maximum temperature in a forecast",
                code=(
                    'import xarray as xr  # xarray>=2025.1.2 and zarr>=3.0.8 for zarr v3 support\n\n'
                    'ds = xr.open_zarr("https://data.dynamical.org/ecmwf/aifs-single/forecast/latest.zarr")\n'
                    'ds["temperature_2m"].sel(init_time="2025-01-01T00", latitude=0, longitude=0).max().compute()'
                ),
            ),
        ),
        additional_terms=ECMWF_TERMS,
    ),
    CatalogItem(
        id="ecmwf-ifs-ens-forecast-15-day-0-25-degree",
        icechunk_href="s3://dynamical-ecmwf-ifs-ens/ecmwf-ifs-ens-forecast-15-day-0-25-degree/v0.1.0.icechunk/",
        icechunk_region="us-west-2",
        model_id="ecmwf-ifs-ens",
        description_summary=(
            "This dataset is an archive of past and present ECMWF IFS ENS "
            "forecasts. Forecasts are identified by an initialization time "
            "(`init_time`) denoting the start time of the model run, as well "
            "as by the `ensemble_member`. Along the `lead_time` dimension, "
            "each forecast begins at a 3 hourly forecast step (0-144 hours) "
            "and switches to a 6 hourly step for days 6 through 15 of the "
            "forecast (hours 144-360). This dataset contains the 00 UTC "
            "initialization times only."
        ),
        description_details=_details(
            "ecmwf-ifs-ens-forecast-15-day-0-25-degree",
            "https://github.com/dynamical-org/reformatters/blob/main/src/reformatters/ecmwf/ifs_ens/forecast_15_day_0_25_degree/template_config.py",
        ),
        examples=(
            DatasetExample(
                title="Maximum temperature in ensemble",
                code=(
                    'import xarray as xr  # xarray>=2025.1.2 and zarr>=3.0.8 for zarr v3 support\n\n'
                    'ds = xr.open_zarr("https://data.dynamical.org/ecmwf/ifs-ens/forecast-15-day-0-25-degree/latest.zarr")\n'
                    'ds["temperature_2m"].sel(init_time="2025-01-01T00", latitude=0, longitude=0).max().compute()'
                ),
            ),
        ),
        additional_terms=ECMWF_TERMS,
    ),
]


_COLLECTION_IDS = [item.id for item in CATALOG_ITEMS]
