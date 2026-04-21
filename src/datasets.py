from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, kw_only=True)
class Profile:
    id: str
    zarr_href: str
    icechunk_bucket: str
    icechunk_prefix: str
    license: str = "CC-BY-4.0"
    icechunk_region: str = "us-west-2"


PROFILES: list[Profile] = [
    Profile(
        id="noaa-gfs-analysis",
        zarr_href="https://data.dynamical.org/noaa/gfs/analysis/latest.zarr",
        icechunk_bucket="dynamical-noaa-gfs",
        icechunk_prefix="noaa-gfs-analysis/v0.1.0.icechunk/",
    ),
    Profile(
        id="noaa-gfs-forecast",
        zarr_href="https://data.dynamical.org/noaa/gfs/forecast/latest.zarr",
        icechunk_bucket="dynamical-noaa-gfs",
        icechunk_prefix="noaa-gfs-forecast/v0.2.7.icechunk/",
    ),
    Profile(
        id="noaa-gefs-forecast-35-day",
        zarr_href="https://data.dynamical.org/noaa/gefs/forecast-35-day/latest.zarr",
        icechunk_bucket="dynamical-noaa-gefs",
        icechunk_prefix="noaa-gefs-forecast-35-day/v0.2.0.icechunk/",
    ),
    Profile(
        id="noaa-gefs-analysis",
        zarr_href="https://data.dynamical.org/noaa/gefs/analysis/latest.zarr",
        icechunk_bucket="dynamical-noaa-gefs",
        icechunk_prefix="noaa-gefs-analysis/v0.1.2.icechunk/",
    ),
    Profile(
        id="noaa-hrrr-forecast-48-hour",
        zarr_href="https://data.dynamical.org/noaa/hrrr/forecast-48-hour/latest.zarr",
        icechunk_bucket="dynamical-noaa-hrrr",
        icechunk_prefix="noaa-hrrr-forecast-48-hour/v0.1.0.icechunk/",
    ),
    Profile(
        id="noaa-hrrr-analysis",
        zarr_href="https://data.dynamical.org/noaa/hrrr/analysis/latest.zarr",
        icechunk_bucket="dynamical-noaa-hrrr",
        icechunk_prefix="noaa-hrrr-analysis/v0.2.0.icechunk/",
    ),
    Profile(
        id="noaa-mrms-conus-analysis-hourly",
        zarr_href="https://data.dynamical.org/noaa/mrms/conus-analysis-hourly/latest.zarr",
        icechunk_bucket="dynamical-noaa-mrms",
        icechunk_prefix="noaa-mrms-conus-analysis-hourly/v0.3.0.icechunk/",
    ),
    Profile(
        id="ecmwf-aifs-single-forecast",
        zarr_href="https://data.dynamical.org/ecmwf/aifs-single/forecast/latest.zarr",
        icechunk_bucket="dynamical-ecmwf-aifs-single",
        icechunk_prefix="ecmwf-aifs-single-forecast/v0.1.0.icechunk/",
    ),
    Profile(
        id="ecmwf-ifs-ens-forecast-15-day-0-25-degree",
        zarr_href="https://data.dynamical.org/ecmwf/ifs-ens/forecast-15-day-0-25-degree/latest.zarr",
        icechunk_bucket="dynamical-ecmwf-ifs-ens",
        icechunk_prefix="ecmwf-ifs-ens-forecast-15-day-0-25-degree/v0.1.0.icechunk/",
    ),
]


_COLLECTION_IDS = [p.id for p in PROFILES]
