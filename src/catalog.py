from __future__ import annotations

import pathlib
from enum import StrEnum
from urllib.parse import urlparse

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, model_validator

_DESCRIPTIONS_DIR = pathlib.Path(__file__).parent / "descriptions"


def _load_description(item_id: str) -> str:
    path = _DESCRIPTIONS_DIR / f"{item_id}.md"
    return path.read_text(encoding="utf-8").strip()


class DatasetLicense(StrEnum):
    CC_BY_4_0 = "CC-BY-4.0"


class AdditionalTerms(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    href: HttpUrl
    title: str = Field(min_length=1)


class CatalogItem(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str = Field(min_length=1)
    model_id: str = Field(min_length=1)
    description: str = Field(min_length=1)
    icechunk_href: str = Field(pattern=r"^s3://[^/]+/.+$")
    icechunk_region: str = Field(min_length=1)
    # TODO(temporary): drop once all dynamical-catalog consumers are on the
    # icechunk-only release. See dynamical-stac PR that reintroduced this.
    zarr_href: HttpUrl
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


ECMWF_TERMS = AdditionalTerms(
    href="https://apps.ecmwf.int/datasets/licences/general/",  # type: ignore[arg-type]
    title="ECMWF Terms of Use (additional terms)",
)


CATALOG_ITEMS: list[CatalogItem] = [
    CatalogItem(
        id="noaa-gfs-analysis",
        model_id="noaa-gfs",
        description=_load_description("noaa-gfs-analysis"),
        icechunk_href="s3://dynamical-noaa-gfs/noaa-gfs-analysis/v0.1.0.icechunk/",
        icechunk_region="us-west-2",
        zarr_href="https://data.dynamical.org/noaa/gfs/analysis/latest.zarr",  # type: ignore[arg-type]
    ),
    CatalogItem(
        id="noaa-gfs-forecast",
        model_id="noaa-gfs",
        description=_load_description("noaa-gfs-forecast"),
        icechunk_href="s3://dynamical-noaa-gfs/noaa-gfs-forecast/v0.2.7.icechunk/",
        icechunk_region="us-west-2",
        zarr_href="https://data.dynamical.org/noaa/gfs/forecast/latest.zarr",  # type: ignore[arg-type]
    ),
    CatalogItem(
        id="noaa-gefs-forecast-35-day",
        model_id="noaa-gefs",
        description=_load_description("noaa-gefs-forecast-35-day"),
        icechunk_href="s3://dynamical-noaa-gefs/noaa-gefs-forecast-35-day/v0.2.0.icechunk/",
        icechunk_region="us-west-2",
        zarr_href="https://data.dynamical.org/noaa/gefs/forecast-35-day/latest.zarr",  # type: ignore[arg-type]
    ),
    CatalogItem(
        id="noaa-gefs-analysis",
        model_id="noaa-gefs",
        description=_load_description("noaa-gefs-analysis"),
        icechunk_href="s3://dynamical-noaa-gefs/noaa-gefs-analysis/v0.1.2.icechunk/",
        icechunk_region="us-west-2",
        zarr_href="https://data.dynamical.org/noaa/gefs/analysis/latest.zarr",  # type: ignore[arg-type]
    ),
    CatalogItem(
        id="noaa-hrrr-forecast-48-hour",
        model_id="noaa-hrrr",
        description=_load_description("noaa-hrrr-forecast-48-hour"),
        icechunk_href="s3://dynamical-noaa-hrrr/noaa-hrrr-forecast-48-hour/v0.1.0.icechunk/",
        icechunk_region="us-west-2",
        zarr_href="https://data.dynamical.org/noaa/hrrr/forecast-48-hour/latest.zarr",  # type: ignore[arg-type]
    ),
    CatalogItem(
        id="noaa-hrrr-analysis",
        model_id="noaa-hrrr",
        description=_load_description("noaa-hrrr-analysis"),
        icechunk_href="s3://dynamical-noaa-hrrr/noaa-hrrr-analysis/v0.2.0.icechunk/",
        icechunk_region="us-west-2",
        zarr_href="https://data.dynamical.org/noaa/hrrr/analysis/latest.zarr",  # type: ignore[arg-type]
    ),
    CatalogItem(
        id="noaa-mrms-conus-analysis-hourly",
        model_id="noaa-mrms",
        description=_load_description("noaa-mrms-conus-analysis-hourly"),
        icechunk_href="s3://dynamical-noaa-mrms/noaa-mrms-conus-analysis-hourly/v0.3.0.icechunk/",
        icechunk_region="us-west-2",
        zarr_href="https://data.dynamical.org/noaa/mrms/conus-analysis-hourly/latest.zarr",  # type: ignore[arg-type]
    ),
    CatalogItem(
        id="ecmwf-aifs-single-forecast",
        model_id="ecmwf-aifs-single",
        description=_load_description("ecmwf-aifs-single-forecast"),
        icechunk_href="s3://dynamical-ecmwf-aifs-single/ecmwf-aifs-single-forecast/v0.1.0.icechunk/",
        icechunk_region="us-west-2",
        zarr_href="https://data.dynamical.org/ecmwf/aifs-single/forecast/latest.zarr",  # type: ignore[arg-type]
        additional_terms=ECMWF_TERMS,
    ),
    CatalogItem(
        id="ecmwf-ifs-ens-forecast-15-day-0-25-degree",
        model_id="ecmwf-ifs-ens",
        description=_load_description("ecmwf-ifs-ens-forecast-15-day-0-25-degree"),
        icechunk_href="s3://dynamical-ecmwf-ifs-ens/ecmwf-ifs-ens-forecast-15-day-0-25-degree/v0.1.0.icechunk/",
        icechunk_region="us-west-2",
        zarr_href="https://data.dynamical.org/ecmwf/ifs-ens/forecast-15-day-0-25-degree/latest.zarr",  # type: ignore[arg-type]
        additional_terms=ECMWF_TERMS,
    ),
]


_COLLECTION_IDS = [item.id for item in CATALOG_ITEMS]
