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

# Prepended to every example snippet so users see the required package version.
# `_example` takes a higher floor for datasets whose storage the 0.8.0 reader
# can't open (gs://, az:// and https:// repositories need 1.0.0).
_DEFAULT_MIN_DYNAMICAL_CATALOG = "0.8.0"


def _dynamical_catalog_import(min_version: str) -> str:
    return f"import dynamical_catalog  # dynamical-catalog>={min_version}"


# Storage schemes a repository (or a virtual chunk container) may use: the
# object stores `s3`, `gs` and `az`, plus `https` for a repository or container
# served anonymously over plain HTTPS. All are readable anonymously by the
# generator and by dynamical-catalog.
StorageScheme = Literal["s3", "gs", "az", "https"]

_STORAGE_SCHEMES: tuple[StorageScheme, ...] = ("s3", "gs", "az", "https")


def url_scheme(href: str) -> StorageScheme:
    """Scheme of a supported storage URL, i.e. ``s3``, ``gs``, ``az`` or ``https``."""
    scheme = href.split("://", 1)[0]
    for supported in _STORAGE_SCHEMES:
        if scheme == supported:
            return supported
    expected = ", ".join(f"{s}://" for s in _STORAGE_SCHEMES)
    raise ValueError(f"unsupported storage URL {href!r}: expected {expected}")


def s3_to_https_url(s3_href: str, region: str) -> str:
    """Convert an ``s3://bucket/key`` URL to a virtual-hosted-style HTTPS URL
    with the AWS region in the domain, e.g.

        s3://dynamical-noaa-gefs/noaa-gefs-forecast-35-day/v0.2.0.icechunk/
        -> https://dynamical-noaa-gefs.s3.us-west-2.amazonaws.com/noaa-gefs-forecast-35-day/v0.2.0.icechunk

    Any trailing slash is stripped: ``icechunk.http_storage`` rejects a
    ``base_url`` ending in ``/`` ("the repository doesn't exist").
    """
    parsed = urlparse(s3_href)
    key = parsed.path.strip("/")
    return f"https://{parsed.netloc}.s3.{region}.amazonaws.com/{key}"


def gs_to_https_url(gs_href: str) -> str:
    """Convert a ``gs://bucket/key`` URL to its public HTTPS URL, e.g.

        gs://dynamical-icechunk-gcs-demo/test-gcs-virtual/v0.1.0.icechunk/
        -> https://storage.googleapis.com/dynamical-icechunk-gcs-demo/test-gcs-virtual/v0.1.0.icechunk

    Any trailing slash is stripped for the same reason as
    :func:`s3_to_https_url`: ``icechunk.http_storage`` rejects a ``base_url``
    ending in ``/`` ("the repository doesn't exist").
    """
    parsed = urlparse(gs_href)
    key = parsed.path.strip("/")
    return f"https://storage.googleapis.com/{parsed.netloc}/{key}"


def az_to_https_url(az_href: str, account: str) -> str:
    """Convert an ``az://container/key`` URL to its public HTTPS URL, e.g.

        az://dynamical-icechunk-azure-demo/test-azure-virtual/v0.1.0.icechunk/
        -> https://dynamicalicechunktest.blob.core.windows.net/dynamical-icechunk-azure-demo/test-azure-virtual/v0.1.0.icechunk

    The storage account is not part of the ``az://`` URL, so it is passed
    separately (see ``CatalogItem.icechunk_account``). Any trailing slash is
    stripped for the same reason as :func:`s3_to_https_url`:
    ``icechunk.http_storage`` rejects a ``base_url`` ending in ``/`` ("the
    repository doesn't exist").
    """
    parsed = urlparse(az_href)
    key = parsed.path.strip("/")
    return f"https://{account}.blob.core.windows.net/{parsed.netloc}/{key}"


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


def _example(
    title: str, body: str, min_version: str = _DEFAULT_MIN_DYNAMICAL_CATALOG
) -> DatasetExample:
    """Build an example, prepending the standard dynamical_catalog import preamble.

    ``min_version`` is the oldest dynamical-catalog release that can open the
    dataset; it is rendered into the import comment users copy.
    """
    return DatasetExample(
        title=title, code=f"{_dynamical_catalog_import(min_version)}\n\n{body}"
    )


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
        "{{ chunking_table }}"
    ),
    "chunking_unsharded": (
        "This dataset is stored in [Zarr](https://zarr.dev/) format, which "
        "splits each variable into a grid of **chunks** — the smallest "
        "unit read from storage. When possible, aligning your reads with this "
        "dataset's chunk grid can significantly improve data access speed.\n\n"
        "The element count and coordinate span of this dataset:\n\n"
        "{{ chunking_table }}"
    ),
    # References {{ validation_url }} — supplied per-dataset at load time.
    "validation_report": (
        "Review the [validation report]({{ validation_url }}) for variable "
        "availability, missing data, known quirks, fill values, value "
        "distributions, and sample plots."
    ),
    # References {{ reformatter_url }} — supplied per-dataset at load time.
    "compression": (
        "The data values in this dataset have been rounded in their binary "
        "floating point representation to improve compression. See "
        "[Klöwer et al. 2021](https://www.nature.com/articles/s43588-021-00156-2) "
        "for more information on this approach. The exact number of rounded bits "
        "can be found in our [reformatting code]({{ reformatter_url }})."
    ),
    # Appended after {{ compression }} in both IMERG datasets' prose.
    "compression_imerg_note": (
        "NASA distributes IMERG precipitation values already rounded to "
        "0.01 mm/hr. Our rounding is relative rather than absolute, and adds "
        "less than 0.5% error to each value."
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
    "google-weathernext2": Model(
        id="google-weathernext2",
        name="Google WeatherNext 2",
        description=(
            "WeatherNext 2 is Google's global medium-range probabilistic "
            "weather forecasting model. It produces a 64-member ensemble on "
            "a 0.25 degree grid, initialized four times daily with forecasts "
            "extending to 15 days."
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
    "nasa-imerg": Model(
        id="nasa-imerg",
        name="NASA IMERG",
        description=(
            "The Integrated Multi-satellitE Retrievals for GPM (IMERG) is a NASA algorithm that merges "
            "precipitation estimates from the constellation of passive microwave satellites in the Global "
            "Precipitation Measurement (GPM) mission with microwave-calibrated infrared estimates and "
            "monthly gauge analyses to produce a global, gridded, half-hourly precipitation "
            "record. IMERG intercalibrates, merges, and interpolates these inputs onto a 0.1 degree grid "
            "spanning the TRMM and GPM satellite eras."
        ),
    ),
    "eccc-hrdps": Model(
        id="eccc-hrdps",
        name="ECCC HRDPS",
        description=(
            "The High Resolution Deterministic Prediction System (HRDPS) is the 2.5 km limited-area "
            "weather forecast model operated by Environment and Climate Change Canada (ECCC), Canada's "
            "national meteorological service. Its continental domain covers Canada and the northern "
            "United States at a resolution that captures fine-scale weather features."
        ),
    ),
    "dynamical-test": Model(
        id="dynamical-test",
        name="dynamical.org test fixtures",
        description=(
            "These are tiny synthetic datasets used to exercise dynamical-catalog's read "
            "paths against real generator output; they are not weather data."
        ),
    ),
}


class CatalogItem(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str = Field(min_length=1)
    # The netloc is the bucket for `s3://` and `gs://`, the blob *container* for
    # `az://` (Azure's storage account lives in `icechunk_account`, not in the
    # URL), and the host for `https://` (a repository served anonymously over
    # plain HTTPS, e.g. from an R2 custom domain; advertised with its trailing
    # slash stripped, as `icechunk.http_storage` requires).
    icechunk_href: str = Field(pattern=r"^(s3|gs|az|https)://[^/]+/.+$")
    # S3 only: the region is part of the store's HTTPS domain and of the reader's
    # storage options. GCS, Azure and HTTPS have no region in either, so `gs://`,
    # `az://` and `https://` items omit it. Enforced by `_region_matches_scheme`.
    icechunk_region: Literal["us-west-2"] | None = None  # add additional as needed
    # Azure only: the storage account that owns the container. It is absent from
    # the `az://` URL but needed for both the HTTPS domain and the reader's
    # storage options. Enforced by `_account_matches_scheme`.
    icechunk_account: str | None = None
    # Virtual datasets reference chunks in public source stores; readers must be
    # told which container prefixes to authorize anonymously to resolve them.
    virtual_chunk_container_prefixes: tuple[str, ...] = ()
    model_id: str = Field(min_length=1)
    description_summary: str = Field(min_length=1)
    reformatter_url: str = Field(min_length=1)
    examples: tuple[DatasetExample, ...] = Field(min_length=1)
    # Optional only while a dataset is unreleased: a staging item may have no
    # notebook written yet. Enforced non-empty for production items by
    # `_production_items_have_notebooks`.
    notebooks: tuple[DatasetNotebook, ...] = ()
    additional_terms: AdditionalTerms | None = None
    # Unreleased dataset: excluded from the production catalog, published only to
    # stac-staging so it can be previewed before going live. See generate.py.
    staging: bool = False
    # Fixture dataset: excluded from both production and staging, published only
    # to stac-test where dynamical-catalog's integration tests read it. Mutually
    # exclusive with `staging` (see `_tier_is_unambiguous`).
    test: bool = False

    @property
    def icechunk_scheme(self) -> StorageScheme:
        return url_scheme(self.icechunk_href)

    @property
    def icechunk_bucket(self) -> str:
        """Netloc of the icechunk href: the bucket for S3/GCS, the container for Azure."""
        return urlparse(self.icechunk_href).netloc

    @property
    def icechunk_container(self) -> str:
        """Azure alias for :attr:`icechunk_bucket` (Azure names the netloc a container)."""
        return self.icechunk_bucket

    @property
    def icechunk_prefix(self) -> str:
        return urlparse(self.icechunk_href).path.lstrip("/")

    @property
    def icechunk_https_href(self) -> str:
        """Public HTTPS URL for the icechunk store.

        Advertised as the ``icechunk-https`` asset so datasets can be opened
        with only ``pystac`` + ``icechunk`` (no ``dynamical-catalog``); see
        ``icechunk.http_storage``. S3 stores put the region in the domain; GCS
        stores are served from a single ``storage.googleapis.com`` host; Azure
        stores put the storage account in the domain; an ``https://`` store is
        already public HTTPS and is advertised unchanged apart from stripping
        any trailing slash.
        """
        if self.icechunk_scheme == "https":
            return self.icechunk_href.rstrip("/")
        if self.icechunk_scheme == "gs":
            return gs_to_https_url(self.icechunk_href)
        if self.icechunk_scheme == "az":
            assert self.icechunk_account is not None  # _account_matches_scheme
            return az_to_https_url(self.icechunk_href, self.icechunk_account)
        assert self.icechunk_region is not None  # _region_matches_scheme
        return s3_to_https_url(self.icechunk_href, self.icechunk_region)

    def description_details(self, chunking_table: str | None = None) -> str:
        """Long-form prose from ``prose/datasets/{id}.md``.

        ``chunking_table`` is the rendered per-dataset chunk/shard table. If the
        prose references it (every dataset does) but none was computed — the
        store lacks chunk/shard encoding — this raises rather than shipping a
        dataset page with a dangling table.
        """
        text = _load_prose(
            f"datasets/{self.id}.md",
            reformatter_url=self.reformatter_url,
            validation_url=f"https://dynamical.org/catalog/{self.id}/validation/",
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
    def _tier_is_unambiguous(self) -> CatalogItem:
        """A dataset belongs to exactly one tier above production.

        ``staging`` publishes to stac-staging (and, as a superset, stac-test);
        ``test`` publishes only to stac-test. Setting both would make the
        intended tier ambiguous.
        """
        if self.staging and self.test:
            raise ValueError(
                f"CatalogItem {self.id!r} sets both staging=True and test=True; "
                f"pick one tier (test items are already excluded from staging)"
            )
        return self

    @model_validator(mode="after")
    def _region_matches_scheme(self) -> CatalogItem:
        """``icechunk_region`` is required for S3 stores and absent for the rest."""
        if self.icechunk_scheme == "s3" and self.icechunk_region is None:
            raise ValueError(
                f"CatalogItem {self.id!r} has an s3:// icechunk_href, so it must "
                f"set icechunk_region"
            )
        if self.icechunk_scheme != "s3" and self.icechunk_region is not None:
            raise ValueError(
                f"CatalogItem {self.id!r} has a {self.icechunk_scheme}:// "
                f"icechunk_href, which has no region; leave icechunk_region unset "
                f"(got {self.icechunk_region!r})"
            )
        return self

    @model_validator(mode="after")
    def _account_matches_scheme(self) -> CatalogItem:
        """``icechunk_account`` is required for Azure stores and absent for the rest."""
        if self.icechunk_scheme == "az" and self.icechunk_account is None:
            raise ValueError(
                f"CatalogItem {self.id!r} has an az:// icechunk_href, so it must "
                f"set icechunk_account (the Azure storage account owning the "
                f"container)"
            )
        if self.icechunk_scheme != "az" and self.icechunk_account is not None:
            raise ValueError(
                f"CatalogItem {self.id!r} has a {self.icechunk_scheme}:// "
                f"icechunk_href, which has no storage account; leave "
                f"icechunk_account unset (got {self.icechunk_account!r})"
            )
        return self

    @model_validator(mode="after")
    def _production_items_have_notebooks(self) -> CatalogItem:
        """Every dataset in the production catalog links a real notebook.

        Staging and test items are exempt: an unreleased dataset can be
        previewed on stac-staging before its notebook exists, and a test fixture
        has no notebook to write. Flipping ``staging`` to False then fails
        validation until a notebook is added.
        """
        if not (self.staging or self.test) and not self.notebooks:
            raise ValueError(
                f"CatalogItem {self.id!r} is in the production catalog, so it "
                f"must declare at least one notebook (notebooks may only be "
                f"omitted while staging=True or test=True)"
            )
        return self

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
    def _virtual_chunk_container_prefixes_are_supported(self) -> CatalogItem:
        for prefix in self.virtual_chunk_container_prefixes:
            if not prefix.startswith(("s3://", "gs://", "az://", "https://")):
                raise ValueError(
                    f"{self.id} virtual chunk container {prefix!r} must be an "
                    f"s3://, gs://, az:// or https:// URL: dynamical-catalog only "
                    f"authorizes anonymous S3, GCS, Azure and HTTPS virtual chunk "
                    f"access (gs://, az:// and https:// need dynamical-catalog "
                    f">= 1.0.0), so a source on any other backend "
                    f"can be advertised but never read. Extend dynamical-catalog's "
                    f"reader first to use one here."
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

ECCC_TERMS = AdditionalTerms(
    href="https://eccc-msc.github.io/open-data/licence/readme_en/",  # type: ignore[arg-type]
    title="ECCC Data Servers End-use Licence (additional terms)",
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
                "Temperature at a place and time",
                'ds = dynamical_catalog.open("noaa-gfs-analysis", chunks=None)\n'
                'ds["temperature_2m"].sel(time="2026-01-01T00", latitude=0, longitude=0)',
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
                "Maximum temperature",
                'ds = dynamical_catalog.open("noaa-gfs-forecast", chunks=None)\n'
                'ds["temperature_2m"].sel(init_time="2025-01-01T00", latitude=0, longitude=0).max()',
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
                "Maximum ensemble temperature",
                'ds = dynamical_catalog.open("noaa-gefs-forecast-35-day", chunks=None)\n'
                'ds["temperature_2m"].sel(init_time="2025-01-01T00", latitude=0, longitude=0).max()',
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
                "Temperature at a place and time",
                'ds = dynamical_catalog.open("noaa-gefs-analysis", chunks=None)\n'
                'ds["temperature_2m"].sel(time="2025-01-01T00", latitude=0, longitude=0)',
            ),
        ),
        notebooks=(_quickstart_notebook("noaa-gefs-analysis"),),
    ),
    CatalogItem(
        id="noaa-hrrr-forecast-18-hour-virtual",
        icechunk_href="s3://dynamical-noaa-hrrr/noaa-hrrr-forecast-18-hour-virtual/v0.1.0.icechunk/",
        icechunk_region="us-west-2",
        virtual_chunk_container_prefixes=("s3://noaa-hrrr-bdp-pds/",),
        model_id="noaa-hrrr",
        description_summary=(
            "This dataset is an archive of past and present HRRR forecasts, "
            "optimized for spatial (map) access patterns. Forecasts are "
            "identified by an initialization time (`init_time`) denoting the "
            "start time of the model run, and step forward hourly along the "
            "`lead_time` dimension out to 18 hours. A new forecast is "
            "initialized every hour.\n\n"
            "This dataset uses the native HRRR Lambert Conformal Conic "
            "projection, with spatial indexing along the `x` and `y` "
            "dimensions. The example notebook shows how to use the embedded "
            "spatial reference to select geographic areas of interest.\n\n"
            "Note: `dynamical-catalog>=0.8.0` (or `zarr>=3.2 icechunk>=2.0 "
            "gribberish>=1.5`) is required."
        ),
        reformatter_url=f"{REFORMATTERS_ROOT}/noaa/hrrr/forecast_18_hour_virtual/template_config.py",
        examples=(
            _example(
                "Temperature map",
                'ds = dynamical_catalog.open("noaa-hrrr-forecast-18-hour-virtual", chunks=None)\n'
                'ds["temperature_2m"].sel(init_time="2025-01-01T00", lead_time="12h")\n'
                "\n"
                "# Variables with a vertical dimension live in the pressure_level and model_level groups\n"
                'ds_pressure = dynamical_catalog.open("noaa-hrrr-forecast-18-hour-virtual", group="pressure_level", chunks=None)\n'
                'ds_model = dynamical_catalog.open("noaa-hrrr-forecast-18-hour-virtual", group="model_level", chunks=None)\n'
                "\n"
                'ds_pressure["temperature"].sel(pressure_level=500)',
            ),
        ),
        notebooks=(_quickstart_notebook("noaa-hrrr-forecast-18-hour-virtual"),),
        staging=False,
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
                "Maximum temperature",
                'ds = dynamical_catalog.open("noaa-hrrr-forecast-48-hour", chunks=None)\n'
                'ds["temperature_2m"].sel(init_time="2025-01-01T00", x=0, y=0, method="nearest").max()',
            ),
        ),
        notebooks=(_quickstart_notebook("noaa-hrrr-forecast-48-hour"),),
    ),
    CatalogItem(
        id="noaa-hrrr-forecast-48-hour-virtual",
        icechunk_href="s3://dynamical-noaa-hrrr/noaa-hrrr-forecast-48-hour-virtual/v0.5.0.icechunk/",
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
            "the full length, 48 hour forecast.\n\n"
            "This dataset uses the native HRRR Lambert Conformal Conic "
            "projection, with spatial indexing along the `x` and `y` "
            "dimensions. The example notebook shows how to use the embedded "
            "spatial reference to select geographic areas of interest.\n\n"
            "Note: `dynamical-catalog>=0.8.0` (or `zarr>=3.2 icechunk>=2.0 "
            "gribberish>=1.5`) is required."
        ),
        reformatter_url=f"{REFORMATTERS_ROOT}/noaa/hrrr/forecast_48_hour_virtual/template_config.py",
        examples=(
            _example(
                "Temperature map",
                'ds = dynamical_catalog.open("noaa-hrrr-forecast-48-hour-virtual", chunks=None)\n'
                'ds["temperature_2m"].sel(init_time="2025-01-01T00", lead_time="24h")\n'
                "\n"
                "# Variables with a vertical dimension live in the pressure_level and model_level groups\n"
                'ds_pressure = dynamical_catalog.open("noaa-hrrr-forecast-48-hour-virtual", group="pressure_level", chunks=None)\n'
                'ds_model = dynamical_catalog.open("noaa-hrrr-forecast-48-hour-virtual", group="model_level", chunks=None)\n'
                "\n"
                'ds_pressure["temperature"].sel(pressure_level=500)',
            ),
        ),
        notebooks=(_quickstart_notebook("noaa-hrrr-forecast-48-hour-virtual"),),
        staging=False,
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
                "Temperature at a place and time",
                'ds = dynamical_catalog.open("noaa-hrrr-analysis", chunks=None)\n'
                'ds["temperature_2m"].sel(time="2025-01-01T00", x=0, y=0, method="nearest")',
            ),
        ),
        notebooks=(_quickstart_notebook("noaa-hrrr-analysis"),),
    ),
    CatalogItem(
        id="noaa-hrrr-analysis-virtual",
        icechunk_href="s3://dynamical-noaa-hrrr/noaa-hrrr-analysis-virtual/v0.1.0.icechunk/",
        icechunk_region="us-west-2",
        virtual_chunk_container_prefixes=("s3://noaa-hrrr-bdp-pds/",),
        model_id="noaa-hrrr",
        description_summary=(
            "This analysis dataset is an archive of the model's best estimate "
            "of past weather, optimized for spatial (map) access patterns. It "
            "is created by concatenating the first hour of each historical "
            "forecast to provide a dataset with dimensions time, x, and y.\n\n"
            "This dataset uses the native HRRR Lambert Conformal Conic "
            "projection, with spatial indexing along the `x` and `y` "
            "dimensions. The example notebook shows how to use the embedded "
            "spatial reference to select geographic areas of interest.\n\n"
            "Note: `dynamical-catalog>=0.8.0` (or `zarr>=3.2 icechunk>=2.0 "
            "gribberish>=1.5`) is required."
        ),
        reformatter_url=f"{REFORMATTERS_ROOT}/noaa/hrrr/analysis_virtual/template_config.py",
        examples=(
            _example(
                "Temperature map",
                'ds = dynamical_catalog.open("noaa-hrrr-analysis-virtual", chunks=None)\n'
                'ds["temperature_2m"].sel(time="2025-01-01T00")\n'
                "\n"
                "# Variables with a vertical dimension live in the pressure_level and model_level groups\n"
                'ds_pressure = dynamical_catalog.open("noaa-hrrr-analysis-virtual", group="pressure_level", chunks=None)\n'
                'ds_model = dynamical_catalog.open("noaa-hrrr-analysis-virtual", group="model_level", chunks=None)\n'
                "\n"
                'ds_pressure["temperature"].sel(pressure_level=500)',
            ),
        ),
        notebooks=(_quickstart_notebook("noaa-hrrr-analysis-virtual"),),
        staging=False,
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
                'ds = dynamical_catalog.open("noaa-mrms-conus-analysis-hourly", chunks=None)\n'
                'ds["precipitation_surface"].sel(time="2026-01-01T00", latitude=40, longitude=-90, method="nearest")',
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
                "Maximum temperature",
                'ds = dynamical_catalog.open("ecmwf-aifs-single-forecast", chunks=None)\n'
                'ds["temperature_2m"].sel(init_time="2025-01-01T00", latitude=0, longitude=0).max()',
            ),
        ),
        notebooks=(
            _quickstart_notebook("ecmwf-aifs-single-forecast"),
            _GFS_AIFS_HDD_NOTEBOOK,
        ),
        additional_terms=ECMWF_TERMS,
    ),
    CatalogItem(
        id="ecmwf-aifs-single-forecast-virtual",
        icechunk_href="s3://dynamical-ecmwf-aifs-single/ecmwf-aifs-single-forecast-virtual/v0.1.0.icechunk/",
        icechunk_region="us-west-2",
        virtual_chunk_container_prefixes=("s3://ecmwf-forecasts/",),
        model_id="ecmwf-aifs-single",
        description_summary=(
            "This dataset is an archive of past and present ECMWF AIFS Single "
            "forecasts, optimized for spatial (map) access patterns. Forecasts "
            "are identified by an initialization time (`init_time`) denoting "
            "the start time of the model run, and step forward along the "
            "`lead_time` dimension from 0 to 360 hours (15 days) at a 6 hourly "
            "step.\n\n"
            "Chunks reference the bytes of ECMWF's original GRIB files and are "
            "decoded on read, so this archive carries every variable ECMWF "
            "publishes for AIFS Single. Surface and single-level variables are "
            "at the dataset root; variables carried on pressure levels are in "
            "the `pressure_level` group.\n\n"
            "Note: `dynamical-catalog>=0.8.0` (or `zarr>=3.2 icechunk>=2.0 "
            "gribberish>=1.5`) is required."
        ),
        reformatter_url=f"{REFORMATTERS_ROOT}/ecmwf/aifs_single/forecast_virtual/template_config.py",
        examples=(
            _example(
                "Temperature map",
                'ds = dynamical_catalog.open("ecmwf-aifs-single-forecast-virtual", chunks=None)\n'
                'ds["temperature_2m"].sel(init_time="2026-03-01T00", lead_time="24h")\n'
                "\n"
                "# Variables with a vertical dimension live in the pressure_level group\n"
                'ds_pressure = dynamical_catalog.open("ecmwf-aifs-single-forecast-virtual", group="pressure_level", chunks=None)\n'
                'ds_pressure["geopotential_height"].sel(pressure_level=500)',
            ),
        ),
        notebooks=(_quickstart_notebook("ecmwf-aifs-single-forecast-virtual"),),
        additional_terms=ECMWF_TERMS,
        staging=True,
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
                "Maximum ensemble temperature",
                'ds = dynamical_catalog.open("ecmwf-aifs-ens-forecast", chunks=None)\n'
                'ds["temperature_2m"].sel(init_time="2025-08-01T00", latitude=0, longitude=0).max()',
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
                "Maximum ensemble temperature",
                'ds = dynamical_catalog.open("ecmwf-ifs-ens-forecast-15-day-0-25-degree", chunks=None)\n'
                'ds["temperature_2m"].sel(init_time="2025-01-01T00", latitude=0, longitude=0).max()',
            ),
        ),
        notebooks=(_quickstart_notebook("ecmwf-ifs-ens-forecast-15-day-0-25-degree"),),
        additional_terms=ECMWF_TERMS,
    ),
    CatalogItem(
        id="ecmwf-ifs-ens-forecast-46-day-1-5-degree",
        icechunk_href="s3://dynamical-ecmwf-ifs-ens/ecmwf-ifs-ens-forecast-46-day-1-5-degree/v0.1.0.icechunk/",
        icechunk_region="us-west-2",
        model_id="ecmwf-ifs-ens",
        description_summary=(
            "This dataset is an archive of ECMWF IFS ENS sub-seasonal-range "
            "forecasts. Forecasts are identified by an initialization time "
            "(`init_time`) denoting the start time of the model run, as well "
            "as by the `ensemble_member`. Each forecast steps forward along "
            "the `lead_time` dimension from 0 to 1104 hours (0 to 46 days) at "
            "a 24 hourly step, and carries 101 ensemble members on a global "
            "1.5 degree grid. This dataset contains the 00 UTC initialization "
            "times only.\n\n"
            "Because the step is 24 hourly, most surface variables are daily "
            "means or rates rather than instantaneous values — hence the "
            "`average_` prefixes. Surface and single-level variables are at "
            "the dataset root; the six variables carried on pressure levels "
            "are in the `pressure_level` group.\n\n"
            "Note: ECMWF's licence holds sub-seasonal-range forecasts back for "
            "48 hours, so this is not a real-time dataset — each "
            "initialization becomes available about two days after its "
            "`init_time`."
        ),
        reformatter_url=f"{REFORMATTERS_ROOT}/ecmwf/ifs_ens/forecast_46_day_1_5_degree/template_config.py",
        examples=(
            _example(
                "Maximum ensemble temperature",
                'ds = dynamical_catalog.open("ecmwf-ifs-ens-forecast-46-day-1-5-degree", chunks=None)\n'
                'ds["average_temperature_2m"].sel(init_time="2026-08-01T00", latitude=0, longitude=0).max()',
            ),
            _example(
                "Ensemble spread of the large scale flow",
                'ds_pressure = dynamical_catalog.open("ecmwf-ifs-ens-forecast-46-day-1-5-degree", group="pressure_level", chunks=None)\n'
                'ds_pressure["geopotential_height"].sel(init_time="2026-08-01T00", lead_time="10d", pressure_level=500).std("ensemble_member")',
            ),
        ),
        # No notebook yet: dynamical-org/notebooks#52 adds the quickstart. Staging
        # items may omit it; re-add before flipping staging=False, which requires it.
        additional_terms=ECMWF_TERMS,
        staging=True,
    ),
    CatalogItem(
        id="google-weathernext2-forecast-historical-virtual",
        icechunk_href=(
            "https://google-weathernext2.r2.dynamical.org/"
            "google-weathernext2-forecast-historical-virtual/v0.1.0.icechunk/"
        ),
        virtual_chunk_container_prefixes=("https://wn.dynamical.org/chunks/",),
        model_id="google-weathernext2",
        description_summary=(
            "This dataset is the fixed 2022-2024 archive of Google "
            "WeatherNext 2 forecasts, optimized for spatial (map) access "
            "patterns. Forecasts are identified by an initialization time "
            "(`init_time`) and one of 64 `ensemble_member` values, then step "
            "forward from 6 to 360 hours (15 days) along the `lead_time` "
            "dimension at a 6 hourly interval. Surface variables are at the "
            "dataset root; variables carried on pressure levels are in the "
            "`pressure_level` group."
        ),
        reformatter_url=(
            f"{REFORMATTERS_ROOT}/google/weathernext2/"
            "forecast_historical_virtual/template_config.py"
        ),
        examples=(
            _example(
                "Hurricane Beryl ensemble pressure",
                'ds = dynamical_catalog.open("google-weathernext2-forecast-historical-virtual", chunks=None)\n'
                'ds["pressure_reduced_to_mean_sea_level"].sel(init_time="2024-07-04T00", lead_time="96h", ensemble_member=slice(0, 3), y=slice(10, 35), x=slice(255, 305))',
                min_version="1.0.0",  # https:// repository
            ),
        ),
        # notebooks#56 adds one combined historical + operational quickstart.
        # Link it after that PR merges; staging items may omit notebooks.
        staging=True,
    ),
    CatalogItem(
        id="google-weathernext2-forecast-operational-virtual",
        icechunk_href=(
            "https://google-weathernext2.r2.dynamical.org/"
            "google-weathernext2-forecast-operational-virtual/v0.1.0.icechunk/"
        ),
        virtual_chunk_container_prefixes=("https://wn.dynamical.org/chunks/",),
        model_id="google-weathernext2",
        description_summary=(
            "This dataset is the 2025-present archive of Google WeatherNext 2 "
            "forecasts, optimized for spatial (map) access patterns and "
            "updated behind a strict 48-hour publication boundary. Forecasts "
            "are identified by an initialization time (`init_time`) and one "
            "of 64 `ensemble_member` values, then step forward from 6 to 360 "
            "hours (15 days) along the `lead_time` dimension at a 6 hourly "
            "interval. Surface variables are at the dataset root; variables "
            "carried on pressure levels are in the `pressure_level` group."
        ),
        reformatter_url=(
            f"{REFORMATTERS_ROOT}/google/weathernext2/"
            "forecast_operational_virtual/template_config.py"
        ),
        examples=(
            _example(
                "Day-10 ensemble wind scenarios",
                'ds = dynamical_catalog.open("google-weathernext2-forecast-operational-virtual", chunks=None)\n'
                'latest = ds.isel(init_time=-1).sel(lead_time="240h", ensemble_member=slice(0, 3), y=slice(25, 75), x=slice(270, 359.75))\n'
                '(latest["wind_u_100m"] ** 2 + latest["wind_v_100m"] ** 2) ** 0.5',
                min_version="1.0.0",  # https:// repository
            ),
        ),
        # notebooks#56 adds one combined historical + operational quickstart.
        # Link it after that PR merges; staging items may omit notebooks.
        staging=True,
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
                "Maximum temperature",
                'ds = dynamical_catalog.open("dwd-icon-eu-forecast-5-day", chunks=None)\n'
                'ds["temperature_2m"].sel(init_time="2026-04-01T00", latitude=50, longitude=10).max()',
            ),
        ),
        notebooks=(_quickstart_notebook("dwd-icon-eu-forecast-5-day"),),
    ),
    CatalogItem(
        id="nasa-imerg-analysis-early",
        icechunk_href="s3://dynamical-nasa-imerg/nasa-imerg-analysis-early/v0.1.0.icechunk/",
        icechunk_region="us-west-2",
        model_id="nasa-imerg",
        description_summary=(
            "This analysis dataset is an archive of global half-hourly "
            "precipitation estimates from NASA GPM IMERG, version 07, on a "
            "0.1 degree grid with dimensions time, latitude, and longitude. "
            "This is the Early Run, a low-latency product published about 4 "
            "hours after observation time, suited to time-sensitive "
            "applications."
        ),
        reformatter_url=f"{REFORMATTERS_ROOT}/nasa/imerg/template_config.py",
        examples=(
            _example(
                "Precipitation at a place and time",
                'ds = dynamical_catalog.open("nasa-imerg-analysis-early", chunks=None)\n'
                'ds["precipitation_surface"].sel(time="2026-01-01T00:00", latitude=0, longitude=0, method="nearest")',
            ),
        ),
        notebooks=(_quickstart_notebook("nasa-imerg-analysis-early"),),
    ),
    CatalogItem(
        id="nasa-imerg-analysis-late",
        icechunk_href="s3://dynamical-nasa-imerg/nasa-imerg-analysis-late/v0.1.0.icechunk/",
        icechunk_region="us-west-2",
        model_id="nasa-imerg",
        description_summary=(
            "This analysis dataset is an archive of global half-hourly "
            "precipitation estimates from NASA GPM IMERG, version 07, on a "
            "0.1 degree grid with dimensions time, latitude, and longitude. "
            "This is the Late Run, which incorporates additional satellite "
            "sensor input for higher quality, published about 14 hours "
            "after observation time."
        ),
        reformatter_url=f"{REFORMATTERS_ROOT}/nasa/imerg/template_config.py",
        examples=(
            _example(
                "Precipitation at a place and time",
                'ds = dynamical_catalog.open("nasa-imerg-analysis-late", chunks=None)\n'
                'ds["precipitation_surface"].sel(time="2026-01-01T00:00", latitude=0, longitude=0, method="nearest")',
            ),
        ),
        notebooks=(_quickstart_notebook("nasa-imerg-analysis-late"),),
    ),
    CatalogItem(
        id="eccc-hrdps-forecast",
        icechunk_href="s3://dynamical-eccc-hrdps/eccc-hrdps-forecast/v0.1.0.icechunk/",
        icechunk_region="us-west-2",
        model_id="eccc-hrdps",
        description_summary=(
            "This dataset is an archive of past and present HRDPS continental "
            "forecasts. Forecasts are identified by four daily initialization "
            "times (`init_time`) denoting the start of the model run and step "
            "forward in time along the `lead_time` dimension, hourly out to "
            "48 hours."
        ),
        reformatter_url=f"{REFORMATTERS_ROOT}/eccc/hrdps/forecast/template_config.py",
        examples=(
            _example(
                "Temperature map at a time",
                'ds = dynamical_catalog.open("eccc-hrdps-forecast", chunks=None)\n'
                'ds["temperature_2m"].sel(init_time="2026-08-01T00", lead_time="12h")',
            ),
        ),
        notebooks=(_quickstart_notebook("eccc-hrdps-forecast"),),
        additional_terms=ECCC_TERMS,
    ),
    CatalogItem(
        id="test-gcs-virtual",
        icechunk_href="gs://dynamical-icechunk-gcs-demo/test-gcs-virtual/v0.1.0.icechunk/",
        virtual_chunk_container_prefixes=(
            "gs://dynamical-icechunk-gcs-demo/test-gcs-virtual/source/",
        ),
        model_id="dynamical-test",
        description_summary=(
            "A synthetic 2x3x4 `temperature_2m` array on Google Cloud Storage "
            "whose single chunk is a virtual reference into the same bucket. "
            "Published only to the test catalog so dynamical-catalog can "
            "exercise anonymous GCS repository and virtual chunk reads against "
            "real generator output."
        ),
        # No reformatter builds this fixture; point at the consumer instead so
        # the {{ compression }} fragment's link (if ever used) still resolves.
        reformatter_url="https://github.com/dynamical-org/dynamical-catalog",
        examples=(
            _example(
                "Read the array",
                'ds = dynamical_catalog.open("test-gcs-virtual", chunks=None)\n'
                'ds["temperature_2m"].isel(time=0)',
                min_version="1.0.0",  # gs:// repository
            ),
        ),
        notebooks=(),
        test=True,
    ),
    CatalogItem(
        id="test-azure-virtual",
        icechunk_href="az://dynamical-icechunk-azure-demo/test-azure-virtual/v0.1.0.icechunk/",
        icechunk_account="dynamicalicechunktest",
        virtual_chunk_container_prefixes=(
            "az://dynamical-icechunk-azure-demo/test-azure-virtual/source/",
        ),
        model_id="dynamical-test",
        description_summary=(
            "A synthetic 2x3x4 `temperature_2m` array on Azure Blob Storage "
            "whose single chunk is a virtual reference into the same container. "
            "Published only to the test catalog so dynamical-catalog can "
            "exercise anonymous Azure repository and virtual chunk reads "
            "against real generator output."
        ),
        # No reformatter builds this fixture; point at the consumer instead so
        # the {{ compression }} fragment's link (if ever used) still resolves.
        reformatter_url="https://github.com/dynamical-org/dynamical-catalog",
        examples=(
            _example(
                "Read the array",
                'ds = dynamical_catalog.open("test-azure-virtual", chunks=None)\n'
                'ds["temperature_2m"].isel(time=0)',
                min_version="1.0.0",  # az:// repository
            ),
        ),
        notebooks=(),
        test=True,
    ),
]


# Collection ids in the production and staging catalogs. Test-tier fixtures are
# left out: the integration tests here read through released dynamical-catalog
# versions and against the staging-inclusive `served_catalog` fixture, neither
# of which carries test items.
_COLLECTION_IDS = [item.id for item in CATALOG_ITEMS if not item.test]
