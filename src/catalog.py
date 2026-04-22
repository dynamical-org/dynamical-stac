from __future__ import annotations

from enum import StrEnum
from urllib.parse import urlparse

from pydantic import BaseModel, ConfigDict, Field, HttpUrl


class DatasetLicense(StrEnum):
    CC_BY_4_0 = "CC-BY-4.0"


class CatalogItem(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str = Field(min_length=1)
    zarr_href: HttpUrl
    icechunk_href: str = Field(pattern=r"^s3://[^/]+/.+$")
    icechunk_region: str = Field(min_length=1)
    license: DatasetLicense
    additional_terms_href: HttpUrl | None = None
    additional_terms_title: str | None = None

    @property
    def icechunk_bucket(self) -> str:
        return urlparse(self.icechunk_href).netloc

    @property
    def icechunk_prefix(self) -> str:
        return urlparse(self.icechunk_href).path.lstrip("/")


ECMWF_TERMS = dict(
    additional_terms_href="https://apps.ecmwf.int/datasets/licences/general/",
    additional_terms_title="ECMWF Terms of Use (additional terms)",
)


CATALOG_ITEMS: list[CatalogItem] = [
    CatalogItem(
        id="noaa-gfs-analysis",
        zarr_href="https://data.dynamical.org/noaa/gfs/analysis/latest.zarr",
        icechunk_href="s3://dynamical-noaa-gfs/noaa-gfs-analysis/v0.1.0.icechunk/",
        icechunk_region="us-west-2",
        license=DatasetLicense.CC_BY_4_0,
    ),
    CatalogItem(
        id="noaa-gfs-forecast",
        zarr_href="https://data.dynamical.org/noaa/gfs/forecast/latest.zarr",
        icechunk_href="s3://dynamical-noaa-gfs/noaa-gfs-forecast/v0.2.7.icechunk/",
        icechunk_region="us-west-2",
        license=DatasetLicense.CC_BY_4_0,
    ),
    CatalogItem(
        id="noaa-gefs-forecast-35-day",
        zarr_href="https://data.dynamical.org/noaa/gefs/forecast-35-day/latest.zarr",
        icechunk_href="s3://dynamical-noaa-gefs/noaa-gefs-forecast-35-day/v0.2.0.icechunk/",
        icechunk_region="us-west-2",
        license=DatasetLicense.CC_BY_4_0,
    ),
    CatalogItem(
        id="noaa-gefs-analysis",
        zarr_href="https://data.dynamical.org/noaa/gefs/analysis/latest.zarr",
        icechunk_href="s3://dynamical-noaa-gefs/noaa-gefs-analysis/v0.1.2.icechunk/",
        icechunk_region="us-west-2",
        license=DatasetLicense.CC_BY_4_0,
    ),
    CatalogItem(
        id="noaa-hrrr-forecast-48-hour",
        zarr_href="https://data.dynamical.org/noaa/hrrr/forecast-48-hour/latest.zarr",
        icechunk_href="s3://dynamical-noaa-hrrr/noaa-hrrr-forecast-48-hour/v0.1.0.icechunk/",
        icechunk_region="us-west-2",
        license=DatasetLicense.CC_BY_4_0,
    ),
    CatalogItem(
        id="noaa-hrrr-analysis",
        zarr_href="https://data.dynamical.org/noaa/hrrr/analysis/latest.zarr",
        icechunk_href="s3://dynamical-noaa-hrrr/noaa-hrrr-analysis/v0.2.0.icechunk/",
        icechunk_region="us-west-2",
        license=DatasetLicense.CC_BY_4_0,
    ),
    CatalogItem(
        id="noaa-mrms-conus-analysis-hourly",
        zarr_href="https://data.dynamical.org/noaa/mrms/conus-analysis-hourly/latest.zarr",
        icechunk_href="s3://dynamical-noaa-mrms/noaa-mrms-conus-analysis-hourly/v0.3.0.icechunk/",
        icechunk_region="us-west-2",
        license=DatasetLicense.CC_BY_4_0,
    ),
    CatalogItem(
        id="ecmwf-aifs-single-forecast",
        zarr_href="https://data.dynamical.org/ecmwf/aifs-single/forecast/latest.zarr",
        icechunk_href="s3://dynamical-ecmwf-aifs-single/ecmwf-aifs-single-forecast/v0.1.0.icechunk/",
        icechunk_region="us-west-2",
        license=DatasetLicense.CC_BY_4_0,
        **ECMWF_TERMS,
    ),
    CatalogItem(
        id="ecmwf-ifs-ens-forecast-15-day-0-25-degree",
        zarr_href="https://data.dynamical.org/ecmwf/ifs-ens/forecast-15-day-0-25-degree/latest.zarr",
        icechunk_href="s3://dynamical-ecmwf-ifs-ens/ecmwf-ifs-ens-forecast-15-day-0-25-degree/v0.1.0.icechunk/",
        icechunk_region="us-west-2",
        license=DatasetLicense.CC_BY_4_0,
        **ECMWF_TERMS,
    ),
]


_COLLECTION_IDS = [item.id for item in CATALOG_ITEMS]
