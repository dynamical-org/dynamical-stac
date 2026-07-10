from __future__ import annotations

import pathlib
from enum import StrEnum
from typing import Literal
from urllib.parse import urlparse

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, model_validator

PROSE_DIR = pathlib.Path(__file__).parent / "prose"

REFORMATTERS_ROOT = (
    "https://github.com/dynamical-org/reformatters/blob/main/src/reformatters"
)
REFORMATTERS_REPO = "https://github.com/dynamical-org/reformatters/"

# Prepended to every example snippet so users see the required package versions.
_DYNAMICAL_CATALOG_IMPORT = "import dynamical_catalog  # dynamical-catalog>=0.5.0"


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


_QUICKSTART_TITLE = "Quickstart"


class DatasetNotebook(BaseModel):
    """A Jupyter notebook hosted under dynamical-org/notebooks.

    ``slug`` is the notebook filename (without the ``.ipynb`` suffix), used to
    build the GitHub and Colab URLs. ``title`` is the human label shown next
    to the link on dataset pages.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    slug: str = Field(min_length=1, pattern=r"^[A-Za-z0-9._+\-]+$")
    title: str = Field(min_length=1)


def _example(title: str, body: str) -> DatasetExample:
    """Build an example, prepending the standard dynamical_catalog import preamble."""
    return DatasetExample(title=title, code=f"{_DYNAMICAL_CATALOG_IMPORT}\n\n{body}")


# Shared prose fragments, substituted into markdown files via {{ name }} tokens.
# Each value is inlined here (rather than a named module-level constant) because
# the markdown files are the only consumers.
FRAGMENTS: dict[str, str] = {
    "storage": (
        "Storage for this dataset is generously provided by "
        "[Source Cooperative](https://source.coop/), "
        "a [Radiant Earth](https://radiant.earth/) initiative. "
        "Icechunk storage generously provided by [AWS Open Data](https://aws.amazon.com/opendata/)."
    ),
    "storage_aws_open_data": (
        "Storage for this dataset is generously provided by "
        "[AWS Open Data](https://aws.amazon.com/opendata/)."
    ),
    "nodd_source_gfs": (
        "The source grib files this archive is constructed from are provided by "
        "[NOAA Open Data Dissemination (NODD)](https://www.noaa.gov/information-technology/open-data-dissemination) "
        "and accessed from the [AWS Open Data Registry](https://registry.opendata.aws/noaa-gfs-bdp-pds/). "
        "Operational data is additionally accessed from [NOAA NOMADS](https://nomads.ncep.noaa.gov/)."
    ),
    "nodd_source_hrrr": (
        "The source grib files this archive is constructed from are provided by "
        "[NOAA Open Data Dissemination (NODD)](https://www.noaa.gov/information-technology/open-data-dissemination) "
        "and accessed from the [AWS Open Data Registry](https://registry.opendata.aws/noaa-hrrr-pds/). "
        "Operational data is additionally accessed from [NOAA NOMADS](https://nomads.ncep.noaa.gov/)."
    ),
    "ecmwf_source": (
        "The source grib files this archive is constructed from are provided by "
        "[ECMWF Open Data](https://www.ecmwf.int/en/forecasts/datasets/open-data) "
        "and accessed from the [AWS Open Data Registry](https://registry.opendata.aws/ecmwf-forecasts/).\n\n"
        "ECMWF does not provide user support for the free & open datasets. Users should refer to the public "
        "[User Forum](https://forum.ecmwf.int/) for any questions related to the source material."
    ),
    "chunking": (
        "This dataset is stored in [Zarr](https://zarr.dev/) format, which "
        "splits each variable into a grid of **chunks** — the smallest "
        "unit read from storage. Chunks are grouped into larger **shards** (the objects actually "
        "written to storage), which keeps the object count manageable for "
        "long-archive datasets. When possible, aligning your reads with this "
        "dataset's chunk grid can significantly improve data access speed.\n\n"
        "The element count and coordinate span of this dataset:\n\n"
        "{{ chunking_table }}\n\n"
        "The same values are published in the `dynamical-org:chunking` field of "
        "this dataset's [STAC collection metadata](https://stac.dynamical.org/catalog.json)."
    ),
    # References {{ reformatter_url }} — supplied per-dataset at load time.
    "compression": (
        "The data values in this dataset have been rounded in their binary "
        "floating point representation to improve compression. See "
        "[Klöwer et al. 2021](https://www.nature.com/articles/s43588-021-00156-2) "
        "for more information on this approach. The exact number of rounded bits "
        "can be found in our [reformatting code]({{ reformatter_url }})."
    ),
}


def _load_prose(path: str, **extra: str) -> str:
    """Read a prose file and expand ``{{ name }}`` tokens.

    Fragments are expanded first; any ``{{ name }}`` tokens introduced by the
    fragment text (e.g. ``{{ reformatter_url }}`` inside ``{{ compression }}``)
    are then expanded from ``extra`` in a second pass.
    """
    text = (PROSE_DIR / path).read_text().strip()
    for name, value in FRAGMENTS.items():
        text = text.replace(f"{{{{ {name} }}}}", value)
    for name, value in extra.items():
        text = text.replace(f"{{{{ {name} }}}}", value)
    return text


MODELS: dict[str, Model] = {
    "noaa-gfs": Model(
        id="noaa-gfs",
        name="NOAA GFS",
        description=(
            "The Global Forecast System (GFS) is a National Oceanic and Atmospheric Administration "
            "(NOAA) National Centers for Environmental Prediction (NCEP) weather forecast model that "
            "generates data for dozens of atmospheric and land-soil variables, including temperatures, "
            "winds, precipitation, soil moisture, and atmospheric ozone concentration. The system "
            "couples four separate models (atmosphere, ocean model, land/soil model, and sea ice) that "
            "work together to depict weather conditions."
        ),
    ),
    "noaa-gefs": Model(
        id="noaa-gefs",
        name="NOAA GEFS",
        description=(
            "The Global Ensemble Forecast System (GEFS) is a National Oceanic and Atmospheric "
            "Administration (NOAA) National Centers for Environmental Prediction (NCEP) weather "
            "forecast model. GEFS creates 31 separate forecasts (ensemble members) to describe the "
            "range of forecast uncertainty."
        ),
    ),
    "noaa-hrrr": Model(
        id="noaa-hrrr",
        name="NOAA HRRR",
        description=(
            "The High-Resolution Rapid Refresh (HRRR) is a NOAA real-time 3-km resolution, hourly "
            "updated, cloud-resolving, convection-allowing atmospheric model, initialized by 3km grids "
            "with 3km radar assimilation. Radar data is assimilated in the HRRR every 15 min over a "
            "1-h period adding further detail to that provided by the hourly data assimilation from "
            "the 13km radar-enhanced Rapid Refresh."
        ),
    ),
    "noaa-mrms": Model(
        id="noaa-mrms",
        name="NOAA MRMS",
        description=(
            "The NOAA Multi-Radar/Multi-Sensor System (MRMS) integrates data from multiple radars "
            "and radar networks, surface observations, numerical weather prediction (NWP) models, and "
            "climatology to generate seamless, high spatio-temporal resolution mosaics at low latency "
            "focused on hail, wind, tornado, quantitative precipitation estimations, convection, "
            "icing, and turbulence."
        ),
    ),
    "ecmwf-aifs-single": Model(
        id="ecmwf-aifs-single",
        name="ECMWF AIFS Single",
        description=(
            "The Artificial Intelligence Forecasting System (AIFS) is a data driven forecast model "
            "developed by the European Centre for Medium-Range Weather Forecasts (ECMWF). This is the "
            "non-ensemble configuration of AIFS that produces a single forecast trace. AIFS is trained "
            "on ECMWF's ERA5 re-analysis and ECMWF's operational numerical weather prediction (NWP) "
            "analyses."
        ),
    ),
    "ecmwf-aifs-ens": Model(
        id="ecmwf-aifs-ens",
        name="ECMWF AIFS ENS",
        description=(
            "The Artificial Intelligence Forecasting System (AIFS) is a data driven forecast model "
            "developed by the European Centre for Medium-Range Weather Forecasts (ECMWF). AIFS ENS is "
            "the ensemble configuration of AIFS, containing 51 ensemble members. AIFS is trained on "
            "ECMWF's ERA5 re-analysis and ECMWF's operational numerical weather prediction (NWP) "
            "analyses."
        ),
    ),
    "ecmwf-ifs-ens": Model(
        id="ecmwf-ifs-ens",
        name="ECMWF IFS ENS",
        description=(
            "The Integrated Forecasting System (IFS) is a global forecast model developed by ECMWF. "
            "ENS is an ensemble configuration of IFS, containing 51 ensemble members. IFS consists of "
            "a numerical model of the Earth system, which includes an atmospheric model at its heart, "
            "coupled with models of other Earth system components such as the ocean. The data "
            "assimilation system combines the latest weather observations with a recent forecast to "
            "obtain the best possible estimate of the current state of the Earth system."
        ),
    ),
    "dwd-icon-eu": Model(
        id="dwd-icon-eu",
        name="DWD ICON-EU",
        description=(
            "ICON-EU is a regional weather forecast model operated by Deutscher Wetterdienst (DWD), "
            "Germany's national meteorological service. ICON-EU is a nested configuration of DWD's global "
            "ICON (Icosahedral Non-hydrostatic) model that provides high-resolution forecasts over Europe."
        ),
    ),
}


class CatalogItem(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str = Field(min_length=1)
    icechunk_href: str = Field(pattern=r"^s3://[^/]+/.+$")
    icechunk_region: Literal["us-west-2"]  # add additional as needed
    # Virtual datasets reference GRIB bytes in public source buckets; readers must
    # be told which container prefixes to authorize anonymously to resolve them.
    virtual_chunk_container_prefixes: tuple[str, ...] = ()
    model_id: str = Field(min_length=1)
    description_summary: str = Field(min_length=1)
    reformatter_url: str = Field(min_length=1)
    examples: tuple[DatasetExample, ...] = Field(min_length=1)
    notebooks: tuple[DatasetNotebook, ...] = Field(min_length=1)
    additional_terms: AdditionalTerms | None = None
    # Unreleased dataset: excluded from the production catalog, published only to
    # stac-staging so it can be previewed before going live. See generate.py.
    staging: bool = False

    @property
    def icechunk_bucket(self) -> str:
        return urlparse(self.icechunk_href).netloc

    @property
    def icechunk_prefix(self) -> str:
        return urlparse(self.icechunk_href).path.lstrip("/")

    def description_details(self, chunking_table: str | None = None) -> str:
        """Long-form prose from ``prose/datasets/{id}.md``.

        ``chunking_table`` is the rendered per-dataset chunk/shard table. If the
        prose references it (every dataset does) but none was computed — the
        store lacks chunk/shard encoding — this raises rather than shipping a
        dataset page with a dangling table.
        """
        text = _load_prose(
            f"datasets/{self.id}.md", reformatter_url=self.reformatter_url
        )
        if "{{ chunking_table }}" in text:
            if chunking_table is None:
                raise ValueError(
                    f"{self.id} prose references the chunk/shard table but the "
                    f"store has no chunk/shard encoding to render it"
                )
            text = text.replace("{{ chunking_table }}", chunking_table)
        return text

    @model_validator(mode="after")
    def _quickstart_slug_matches_id(self) -> CatalogItem:
        for notebook in self.notebooks:
            if notebook.title == _QUICKSTART_TITLE and notebook.slug != self.id:
                raise ValueError(
                    f"Quickstart notebook slug {notebook.slug!r} must equal "
                    f"CatalogItem id {self.id!r}"
                )
        return self

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
    def _virtual_chunk_container_prefixes_are_s3(self) -> CatalogItem:
        for prefix in self.virtual_chunk_container_prefixes:
            if not prefix.startswith("s3://"):
                raise ValueError(
                    f"{self.id} virtual chunk container {prefix!r} must be an "
                    f"s3:// URL: dynamical-catalog only authorizes anonymous S3 "
                    f"virtual chunk access, so a non-S3 source can be advertised "
                    f"but never read. icechunk supports other backends (GCS, "
                    f"Azure, HTTP); extend dynamical-catalog's reader first to "
                    f"use one here."
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

# Cross-model notebook referenced by multiple datasets.
_GFS_AIFS_HDD_NOTEBOOK = DatasetNotebook(
    slug="noaa-gfs+ecmwf-aifs-hdd",
    title="Heating degree days: GFS vs AIFS",
)


def _quickstart_notebook(slug: str) -> DatasetNotebook:
    """Build the default per-dataset ``{id}.ipynb`` notebook.

    ``CatalogItem._quickstart_slug_matches_id`` enforces that the slug passed
    here matches the owning ``CatalogItem.id``.
    """
    return DatasetNotebook(slug=slug, title=_QUICKSTART_TITLE)


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
        reformatter_url=f"{REFORMATTERS_ROOT}/noaa/gfs/analysis/template_config.py",
        examples=(
            _example(
                "Temperature at a specific place and time",
                'ds = dynamical_catalog.open("noaa-gfs-analysis")\n'
                'ds["temperature_2m"].sel(time="2026-01-01T00", latitude=0, longitude=0).compute()',
            ),
        ),
        notebooks=(_quickstart_notebook("noaa-gfs-analysis"),),
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
        reformatter_url=f"{REFORMATTERS_ROOT}/noaa/gfs/forecast/template_config.py",
        examples=(
            _example(
                "Maximum temperature in a forecast",
                'ds = dynamical_catalog.open("noaa-gfs-forecast")\n'
                'ds["temperature_2m"].sel(init_time="2025-01-01T00", latitude=0, longitude=0).max().compute()',
            ),
        ),
        notebooks=(
            _quickstart_notebook("noaa-gfs-forecast"),
            _GFS_AIFS_HDD_NOTEBOOK,
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
        reformatter_url=f"{REFORMATTERS_ROOT}/noaa/gefs/common_gefs_template_config.py",
        examples=(
            _example(
                "Maximum temperature in ensemble forecast",
                'ds = dynamical_catalog.open("noaa-gefs-forecast-35-day")\n'
                'ds["temperature_2m"].sel(init_time="2025-01-01T00", latitude=0, longitude=0).max().compute()',
            ),
        ),
        notebooks=(_quickstart_notebook("noaa-gefs-forecast-35-day"),),
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
        reformatter_url=f"{REFORMATTERS_ROOT}/noaa/gefs/common_gefs_template_config.py",
        examples=(
            _example(
                "Temperature at a specific place and time",
                'ds = dynamical_catalog.open("noaa-gefs-analysis")\n'
                'ds["temperature_2m"].sel(time="2025-01-01T00", latitude=0, longitude=0).compute()',
            ),
        ),
        notebooks=(_quickstart_notebook("noaa-gefs-analysis"),),
    ),
    CatalogItem(
        id="noaa-gefs-forecast-10-day-spatial-dev",
        icechunk_href="s3://dynamical-noaa-gefs/noaa-gefs-forecast-10-day-spatial-dev/v0.1.0.icechunk/",
        icechunk_region="us-west-2",
        virtual_chunk_container_prefixes=("s3://noaa-gefs-pds/",),
        model_id="noaa-gefs",
        description_summary=(
            "This dataset is an archive of past and present GEFS forecasts, "
            "optimized for spatial (map) access patterns. Forecasts are "
            "identified by an initialization time (`init_time`) denoting the "
            "start time of the model run, as well as by the `ensemble_member`. "
            "Each forecast has a 3 hourly forecast step along the `lead_time` "
            "dimension, out to 10 days (240 hours).\n\nThis is a virtual "
            "dataset: each chunk references a single GRIB message in NOAA's "
            "source archive, decoded at read time, so the data is served on the "
            "native GEFS 0.25 degree grid with longitudes running 0 to 360 "
            "degrees east. It is an experimental dataset and its structure is "
            "not yet settled."
        ),
        reformatter_url=f"{REFORMATTERS_ROOT}/noaa/gefs/forecast_10_day_spatial/template_config.py",
        examples=(
            _example(
                "A temperature map at one forecast step",
                'ds = dynamical_catalog.open("noaa-gefs-forecast-10-day-spatial-dev")\n'
                'ds["temperature_2m"].sel(init_time="2025-01-01T00", ensemble_member=0, lead_time="24h").compute()',
            ),
        ),
        # Placeholder until a dedicated notebook exists: reuse the GEFS 35-day
        # notebook. A non-"Quickstart" title sidesteps _quickstart_slug_matches_id.
        notebooks=(
            DatasetNotebook(
                slug="noaa-gefs-forecast-35-day",
                title="Example notebook (GEFS 35-day forecast)",
            ),
        ),
        staging=True,
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
        reformatter_url=REFORMATTERS_REPO,
        examples=(
            _example(
                "Maximum temperature in a forecast",
                'ds = dynamical_catalog.open("noaa-hrrr-forecast-48-hour")\n'
                'ds["temperature_2m"].sel(init_time="2025-01-01T00", x=0, y=0, method="nearest").max().compute()',
            ),
        ),
        notebooks=(_quickstart_notebook("noaa-hrrr-forecast-48-hour"),),
    ),
    CatalogItem(
        id="noaa-hrrr-forecast-48-hour-spatial",
        icechunk_href="s3://dynamical-noaa-hrrr/noaa-hrrr-forecast-48-hour-spatial/v0.5.0.icechunk/",
        icechunk_region="us-west-2",
        virtual_chunk_container_prefixes=("s3://noaa-hrrr-bdp-pds/",),
        model_id="noaa-hrrr",
        description_summary=(
            "This dataset is an archive of past and present HRRR forecasts, "
            "optimized for spatial (map) access patterns. Forecasts are "
            "identified by an initialization time (`init_time`) denoting the "
            "start time of the model run, and step forward hourly along the "
            "`lead_time` dimension out to 48 hours. This dataset contains only "
            "the 00, 06, 12, and 18 hour UTC initialization times which produce "
            "the full length, 48 hour forecast.\n\nThis is a virtual dataset: "
            "each chunk references a single GRIB message in NOAA's source "
            "archive, decoded at read time, and served on the native HRRR 3 km "
            "Lambert Conformal Conic grid with spatial indexing along the `x` "
            "and `y` dimensions. Alongside the surface and single-level "
            "variables it includes `pressure_level` and `model_level` groups "
            "holding the full vertical profiles. It is an experimental dataset "
            "and its structure is not yet settled."
        ),
        reformatter_url=f"{REFORMATTERS_ROOT}/noaa/hrrr/forecast_48_hour_spatial/template_config.py",
        examples=(
            _example(
                "A temperature map at one forecast step",
                'ds = dynamical_catalog.open("noaa-hrrr-forecast-48-hour-spatial")\n'
                'ds["temperature_2m"].sel(init_time="2025-01-01T00", lead_time="24h").compute()',
            ),
        ),
        # Placeholder until a dedicated notebook exists: reuse the materialized
        # HRRR 48-hour notebook. A non-"Quickstart" title sidesteps
        # _quickstart_slug_matches_id.
        notebooks=(
            DatasetNotebook(
                slug="noaa-hrrr-forecast-48-hour",
                title="Example notebook (HRRR 48-hour forecast)",
            ),
        ),
        staging=True,
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
        reformatter_url=REFORMATTERS_REPO,
        examples=(
            _example(
                "Temperature at a specific place and time",
                'ds = dynamical_catalog.open("noaa-hrrr-analysis")\n'
                'ds["temperature_2m"].sel(time="2025-01-01T00", x=0, y=0, method="nearest").compute()',
            ),
        ),
        notebooks=(_quickstart_notebook("noaa-hrrr-analysis"),),
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
        reformatter_url=REFORMATTERS_REPO,
        examples=(
            _example(
                "Precipitation at a place and time",
                'ds = dynamical_catalog.open("noaa-mrms-conus-analysis-hourly")\n'
                'ds["precipitation_surface"].sel(time="2026-01-01T00", latitude=40, longitude=-90, method="nearest").compute()',
            ),
        ),
        notebooks=(_quickstart_notebook("noaa-mrms-conus-analysis-hourly"),),
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
        reformatter_url=f"{REFORMATTERS_ROOT}/ecmwf/aifs_single/forecast/template_config.py",
        examples=(
            _example(
                "Maximum temperature in a forecast",
                'ds = dynamical_catalog.open("ecmwf-aifs-single-forecast")\n'
                'ds["temperature_2m"].sel(init_time="2025-01-01T00", latitude=0, longitude=0).max().compute()',
            ),
        ),
        notebooks=(
            _quickstart_notebook("ecmwf-aifs-single-forecast"),
            _GFS_AIFS_HDD_NOTEBOOK,
        ),
        additional_terms=ECMWF_TERMS,
    ),
    CatalogItem(
        id="ecmwf-aifs-ens-forecast",
        icechunk_href="s3://dynamical-ecmwf-aifs-ens/ecmwf-aifs-ens-forecast/v0.1.0.icechunk/",
        icechunk_region="us-west-2",
        model_id="ecmwf-aifs-ens",
        description_summary=(
            "This dataset is an archive of past and present ECMWF AIFS ENS "
            "forecasts. Forecasts are identified by an initialization time "
            "(`init_time`) denoting the start time of the model run, as well "
            "as by the `ensemble_member`. Each forecast steps forward in time "
            "along the `lead_time` dimension."
        ),
        reformatter_url=f"{REFORMATTERS_ROOT}/ecmwf/aifs_ens/forecast/template_config.py",
        examples=(
            _example(
                "Maximum temperature in ensemble",
                'ds = dynamical_catalog.open("ecmwf-aifs-ens-forecast")\n'
                'ds["temperature_2m"].sel(init_time="2025-08-01T00", latitude=0, longitude=0).max().compute()',
            ),
        ),
        notebooks=(_quickstart_notebook("ecmwf-aifs-ens-forecast"),),
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
        reformatter_url=f"{REFORMATTERS_ROOT}/ecmwf/ifs_ens/forecast_15_day_0_25_degree/template_config.py",
        examples=(
            _example(
                "Maximum temperature in ensemble",
                'ds = dynamical_catalog.open("ecmwf-ifs-ens-forecast-15-day-0-25-degree")\n'
                'ds["temperature_2m"].sel(init_time="2025-01-01T00", latitude=0, longitude=0).max().compute()',
            ),
        ),
        notebooks=(_quickstart_notebook("ecmwf-ifs-ens-forecast-15-day-0-25-degree"),),
        additional_terms=ECMWF_TERMS,
    ),
    CatalogItem(
        id="dwd-icon-eu-forecast-5-day",
        icechunk_href="s3://dynamical-dwd-icon-eu/dwd-icon-eu-forecast-5-day/v0.2.0.icechunk/",
        icechunk_region="us-west-2",
        model_id="dwd-icon-eu",
        description_summary=(
            "This dataset is an archive of past and present ICON-EU forecasts. "
            "Forecasts are identified by an initialization time (`init_time`) "
            "denoting the start time of the model run and step forward in time "
            "along the `lead_time` dimension. This dataset contains only the "
            "00, 06, 12, and 18 hour UTC initialization times which produce "
            "the full length, 5 day forecast."
        ),
        reformatter_url=f"{REFORMATTERS_ROOT}/dwd/icon_eu/forecast_5_day/template_config.py",
        examples=(
            _example(
                "Maximum temperature in a forecast",
                'ds = dynamical_catalog.open("dwd-icon-eu-forecast-5-day")\n'
                'ds["temperature_2m"].sel(init_time="2026-04-01T00", latitude=50, longitude=10).max().compute()',
            ),
        ),
        notebooks=(_quickstart_notebook("dwd-icon-eu-forecast-5-day"),),
    ),
]


_COLLECTION_IDS = [item.id for item in CATALOG_ITEMS]
