from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, HttpUrl


class DatasetLicense(StrEnum):
    CC_BY_4_0 = "CC-BY-4.0"


class CatalogItem(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str = Field(min_length=1)
    zarr_href: HttpUrl
    icechunk_bucket: str = Field(min_length=1)
    icechunk_prefix: str = Field(min_length=1)
    license: DatasetLicense = DatasetLicense.CC_BY_4_0
    icechunk_region: str = Field(min_length=1, default="us-west-2")
    additional_terms_href: HttpUrl | None = None
    additional_terms_title: str | None = None


ECMWF_TERMS = dict(
    additional_terms_href="https://apps.ecmwf.int/datasets/licences/general/",
    additional_terms_title="ECMWF Terms of Use (additional terms)",
)


CATALOG_ITEMS: list[CatalogItem] = [
    CatalogItem(
        id="noaa-gfs-analysis",
        zarr_href="https://data.dynamical.org/noaa/gfs/analysis/latest.zarr",
        icechunk_bucket="dynamical-noaa-gfs",
        icechunk_prefix="noaa-gfs-analysis/v0.1.0.icechunk/",
    ),
    CatalogItem(
        id="noaa-gfs-forecast",
        zarr_href="https://data.dynamical.org/noaa/gfs/forecast/latest.zarr",
        icechunk_bucket="dynamical-noaa-gfs",
        icechunk_prefix="noaa-gfs-forecast/v0.2.7.icechunk/",
    ),
    CatalogItem(
        id="noaa-gefs-forecast-35-day",
        zarr_href="https://data.dynamical.org/noaa/gefs/forecast-35-day/latest.zarr",
        icechunk_bucket="dynamical-noaa-gefs",
        icechunk_prefix="noaa-gefs-forecast-35-day/v0.2.0.icechunk/",
    ),
    CatalogItem(
        id="noaa-gefs-analysis",
        zarr_href="https://data.dynamical.org/noaa/gefs/analysis/latest.zarr",
        icechunk_bucket="dynamical-noaa-gefs",
        icechunk_prefix="noaa-gefs-analysis/v0.1.2.icechunk/",
    ),
    CatalogItem(
        id="noaa-hrrr-forecast-48-hour",
        zarr_href="https://data.dynamical.org/noaa/hrrr/forecast-48-hour/latest.zarr",
        icechunk_bucket="dynamical-noaa-hrrr",
        icechunk_prefix="noaa-hrrr-forecast-48-hour/v0.1.0.icechunk/",
    ),
    CatalogItem(
        id="noaa-hrrr-analysis",
        zarr_href="https://data.dynamical.org/noaa/hrrr/analysis/latest.zarr",
        icechunk_bucket="dynamical-noaa-hrrr",
        icechunk_prefix="noaa-hrrr-analysis/v0.2.0.icechunk/",
    ),
    CatalogItem(
        id="noaa-mrms-conus-analysis-hourly",
        zarr_href="https://data.dynamical.org/noaa/mrms/conus-analysis-hourly/latest.zarr",
        icechunk_bucket="dynamical-noaa-mrms",
        icechunk_prefix="noaa-mrms-conus-analysis-hourly/v0.3.0.icechunk/",
    ),
    CatalogItem(
        id="ecmwf-aifs-single-forecast",
        zarr_href="https://data.dynamical.org/ecmwf/aifs-single/forecast/latest.zarr",
        icechunk_bucket="dynamical-ecmwf-aifs-single",
        icechunk_prefix="ecmwf-aifs-single-forecast/v0.1.0.icechunk/",
        **ECMWF_TERMS,
    ),
    CatalogItem(
        id="ecmwf-ifs-ens-forecast-15-day-0-25-degree",
        zarr_href="https://data.dynamical.org/ecmwf/ifs-ens/forecast-15-day-0-25-degree/latest.zarr",
        icechunk_bucket="dynamical-ecmwf-ifs-ens",
        icechunk_prefix="ecmwf-ifs-ens-forecast-15-day-0-25-degree/v0.1.0.icechunk/",
        **ECMWF_TERMS,
    ),
]


_COLLECTION_IDS = [item.id for item in CATALOG_ITEMS]
