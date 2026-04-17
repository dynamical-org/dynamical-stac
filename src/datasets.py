from __future__ import annotations

import json
import pathlib

import pystac

_DATA_DIR = pathlib.Path(__file__).parent / "data"

_COLLECTION_IDS = [
    "noaa-gfs-analysis",
    "noaa-gfs-forecast",
    "noaa-gefs-forecast-35-day",
    "noaa-gefs-analysis",
    "noaa-hrrr-forecast-48-hour",
    "noaa-hrrr-analysis",
    "noaa-mrms-conus-analysis-hourly",
    "ecmwf-aifs-single-forecast",
    "ecmwf-ifs-ens-forecast-15-day-0-25-degree",
]


def load_collections() -> list[pystac.Collection]:
    collections = []
    for cid in _COLLECTION_IDS:
        d = json.loads((_DATA_DIR / f"{cid}.json").read_text())
        collections.append(pystac.Collection.from_dict(d))
    return collections
