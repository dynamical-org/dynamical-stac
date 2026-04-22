from __future__ import annotations

from enum import StrEnum
from urllib.parse import urlparse

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, model_validator


class DatasetLicense(StrEnum):
    CC_BY_4_0 = "CC-BY-4.0"


class AdditionalTerms(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    href: HttpUrl
    title: str = Field(min_length=1)


class CatalogItem(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str = Field(min_length=1)
    icechunk_href: str = Field(pattern=r"^s3://[^/]+/.+$")
    icechunk_region: str = Field(min_length=1)
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
        icechunk_href="s3://dynamical-noaa-gfs/noaa-gfs-analysis/v0.1.0.icechunk/",
        icechunk_region="us-west-2",
    ),
    CatalogItem(
        id="noaa-gfs-forecast",
        icechunk_href="s3://dynamical-noaa-gfs/noaa-gfs-forecast/v0.2.7.icechunk/",
        icechunk_region="us-west-2",
    ),
    CatalogItem(
        id="noaa-gefs-forecast-35-day",
        icechunk_href="s3://dynamical-noaa-gefs/noaa-gefs-forecast-35-day/v0.2.0.icechunk/",
        icechunk_region="us-west-2",
    ),
    CatalogItem(
        id="noaa-gefs-analysis",
        icechunk_href="s3://dynamical-noaa-gefs/noaa-gefs-analysis/v0.1.2.icechunk/",
        icechunk_region="us-west-2",
    ),
    CatalogItem(
        id="noaa-hrrr-forecast-48-hour",
        icechunk_href="s3://dynamical-noaa-hrrr/noaa-hrrr-forecast-48-hour/v0.1.0.icechunk/",
        icechunk_region="us-west-2",
    ),
    CatalogItem(
        id="noaa-hrrr-analysis",
        icechunk_href="s3://dynamical-noaa-hrrr/noaa-hrrr-analysis/v0.2.0.icechunk/",
        icechunk_region="us-west-2",
    ),
    CatalogItem(
        id="noaa-mrms-conus-analysis-hourly",
        icechunk_href="s3://dynamical-noaa-mrms/noaa-mrms-conus-analysis-hourly/v0.3.0.icechunk/",
        icechunk_region="us-west-2",
    ),
    CatalogItem(
        id="ecmwf-aifs-single-forecast",
        icechunk_href="s3://dynamical-ecmwf-aifs-single/ecmwf-aifs-single-forecast/v0.1.0.icechunk/",
        icechunk_region="us-west-2",
        additional_terms=ECMWF_TERMS,
    ),
    CatalogItem(
        id="ecmwf-ifs-ens-forecast-15-day-0-25-degree",
        icechunk_href="s3://dynamical-ecmwf-ifs-ens/ecmwf-ifs-ens-forecast-15-day-0-25-degree/v0.1.0.icechunk/",
        icechunk_region="us-west-2",
        additional_terms=ECMWF_TERMS,
    ),
]


_COLLECTION_IDS = [item.id for item in CATALOG_ITEMS]
