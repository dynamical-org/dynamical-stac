from __future__ import annotations

import datetime as dt
from typing import Literal

import numpy as np
import pandas as pd
import pystac
import xarray as xr
from pydantic import BaseModel, ConfigDict, Field, computed_field, field_validator

from catalog import AdditionalTerms, CatalogItem, DatasetLicense

LICENSE_URLS: dict[DatasetLicense, str] = {
    DatasetLicense.CC_BY_4_0: "https://creativecommons.org/licenses/by/4.0/",
}

STAC_EXTENSIONS = [
    "https://stac-extensions.github.io/xarray-assets/v1.0.0/schema.json",
    "https://stac-extensions.github.io/datacube/v2.2.0/schema.json",
]

_SUMMARY_ATTRS = (
    "spatial_domain",
    "spatial_resolution",
    "time_domain",
    "time_resolution",
    "forecast_domain",
    "forecast_resolution",
)


class CubeDimension(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    type: Literal["spatial", "temporal", "other"]
    extent: list[str] | list[float] | list[int] | list[None] = Field(
        min_length=2, max_length=2
    )
    axis: str | None = None
    unit: str | None = None
    size: int = Field(ge=0)


class CubeVariable(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    dimensions: list[str] = Field(min_length=1)
    type: Literal["data"] = "data"
    unit: str | None = None
    long_name: str = Field(min_length=1)
    standard_name: str | None = None
    short_name: str | None = None
    comment: str | None = None


def _dim_entry(name: str, coord: xr.DataArray) -> CubeDimension:
    values = coord.values
    size = int(coord.size)
    units = str(coord.attrs.get("units", ""))
    standard_name = coord.attrs.get("standard_name", "")

    if name == "latitude" or standard_name == "latitude":
        return CubeDimension(
            type="spatial",
            axis="y",
            extent=[float(values.min()), float(values.max())],
            unit=units or "degree_north",
            size=size,
        )
    if name == "longitude" or standard_name == "longitude":
        return CubeDimension(
            type="spatial",
            axis="x",
            extent=[float(values.min()), float(values.max())],
            unit=units or "degree_east",
            size=size,
        )
    if name in ("x", "y"):
        return CubeDimension(
            type="spatial",
            axis=name,
            extent=[float(values.min()), float(values.max())],
            unit=units or "m",
            size=size,
        )
    if coord.dtype.kind == "M":
        return CubeDimension(
            type="temporal",
            extent=[_iso(values.min()), _iso(values.max())],
            unit="seconds since 1970-01-01",
            size=size,
        )
    if coord.dtype.kind == "m":  # numpy timedelta64 (e.g. forecast lead_time)
        return CubeDimension(
            type="other",
            extent=[_td_seconds(values.min()), _td_seconds(values.max())],
            unit="seconds",
            size=size,
        )
    return CubeDimension(
        type="other", extent=[None, None], unit=units or None, size=size
    )


def _iso(value: np.datetime64) -> str:
    ts = pd.Timestamp(value)
    if ts.tzinfo is None:
        ts = ts.tz_localize("UTC")
    return ts.strftime("%Y-%m-%dT%H:%M:%SZ")


def _td_seconds(value: np.timedelta64) -> int:
    return int(pd.Timedelta(value).total_seconds())


def _time_dim(ds: xr.Dataset) -> str:
    for candidate in ("init_time", "time"):
        if candidate in ds.dims:
            return candidate
    raise ValueError(f"No time dimension found in dims {list(ds.dims)}")


def _bbox(ds: xr.Dataset) -> tuple[float, float, float, float]:
    if "latitude" not in ds.coords or "longitude" not in ds.coords:
        raise ValueError(
            f"Dataset missing latitude/longitude coords; has {list(ds.coords)}"
        )
    lat, lon = ds.latitude, ds.longitude
    return (float(lon.min()), float(lat.min()), float(lon.max()), float(lat.max()))


class CollectionInput(BaseModel):
    """Typed, validated input used to construct a STAC Collection."""

    model_config = ConfigDict(frozen=True, arbitrary_types_allowed=True)

    id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    description: str = Field(min_length=1)
    license: DatasetLicense
    bbox: tuple[float, float, float, float]
    temporal_start: dt.datetime
    cube_dimensions: dict[str, CubeDimension]
    cube_variables: dict[str, CubeVariable]
    icechunk_href: str = Field(pattern=r"^s3://[^/]+/.+$")
    icechunk_region: str = Field(min_length=1)
    attribution: str = Field(min_length=1)
    version: str = Field(min_length=1)
    summaries: dict[str, str] = Field(default_factory=dict)
    additional_terms: AdditionalTerms | None = None

    @field_validator("bbox")
    @classmethod
    def _check_bbox(
        cls, v: tuple[float, float, float, float]
    ) -> tuple[float, float, float, float]:
        lon_min, lat_min, lon_max, lat_max = v
        if not -180.0 <= lon_min <= lon_max <= 180.0:
            raise ValueError(f"bbox longitude out of range: {v}")
        if not -90.0 <= lat_min <= lat_max <= 90.0:
            raise ValueError(f"bbox latitude out of range: {v}")
        return v

    @field_validator("temporal_start")
    @classmethod
    def _utc_aware(cls, v: dt.datetime) -> dt.datetime:
        if v.tzinfo is None:
            raise ValueError("temporal_start must be timezone-aware")
        return v.astimezone(dt.UTC)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def github_notebook_url(self) -> str:
        return f"https://github.com/dynamical-org/notebooks/blob/main/{self.id}.ipynb"

    @computed_field  # type: ignore[prop-decorator]
    @property
    def colab_notebook_url(self) -> str:
        return self.github_notebook_url.replace(
            "https://github.com/", "https://colab.research.google.com/github/"
        )

    @computed_field  # type: ignore[prop-decorator]
    @property
    def about_url(self) -> str:
        return f"https://dynamical.org/catalog/{self.id}/"

    @classmethod
    def from_dataset(cls, item: CatalogItem, ds: xr.Dataset) -> CollectionInput:
        ds_id = ds.attrs["dataset_id"]
        if ds_id != item.id:
            raise ValueError(
                f"CatalogItem id {item.id!r} does not match store dataset_id {ds_id!r}"
                f" (icechunk_href={item.icechunk_href})"
            )
        time_dim = _time_dim(ds)
        t0 = pd.Timestamp(ds[time_dim].values.min()).to_pydatetime()
        if t0.tzinfo is None:
            t0 = t0.replace(tzinfo=dt.UTC)
        dims = {
            name: _dim_entry(name, ds[name])
            for name in sorted(ds.dims)
            if name in ds.coords
        }
        variables: dict[str, CubeVariable] = {}
        for name, da in ds.data_vars.items():
            variables[str(name)] = CubeVariable(
                dimensions=list(da.dims),
                unit=_str_or_none(da.attrs.get("units") or da.attrs.get("unit")),
                long_name=da.attrs["long_name"],
                standard_name=_str_or_none(da.attrs.get("standard_name")),
                short_name=_str_or_none(da.attrs.get("short_name")),
                comment=_str_or_none(da.attrs.get("comment")),
            )
        return cls(
            id=item.id,
            name=ds.attrs["name"],
            description=ds.attrs["description"],
            license=ds.attrs["license"],
            bbox=_bbox(ds),
            temporal_start=t0,
            cube_dimensions=dims,
            cube_variables=variables,
            icechunk_href=item.icechunk_href,
            icechunk_region=item.icechunk_region,
            attribution=ds.attrs["attribution"],
            version=ds.attrs["dataset_version"],
            summaries={k: ds.attrs[k] for k in _SUMMARY_ATTRS if k in ds.attrs},
            additional_terms=item.additional_terms,
        )

    def to_pystac_collection(self) -> pystac.Collection:
        extent = pystac.Extent(
            spatial=pystac.SpatialExtent([list(self.bbox)]),
            temporal=pystac.TemporalExtent([[self.temporal_start, None]]),
        )
        collection = pystac.Collection(
            id=self.id,
            title=self.name,
            description=self.description,
            license=self.license,
            extent=extent,
        )
        collection.stac_extensions = list(STAC_EXTENSIONS)
        collection.extra_fields["attribution"] = self.attribution
        collection.extra_fields["version"] = self.version

        summaries: dict[str, list[str]] = {k: [v] for k, v in self.summaries.items()}
        summaries["cube:variables"] = sorted(self.cube_variables)
        collection.summaries = pystac.Summaries(summaries)

        collection.extra_fields["cube:dimensions"] = {
            k: v.model_dump(exclude_none=True) for k, v in self.cube_dimensions.items()
        }
        collection.extra_fields["cube:variables"] = {
            k: v.model_dump(exclude_none=True) for k, v in self.cube_variables.items()
        }

        collection.add_asset(
            "icechunk",
            pystac.Asset(
                href=self.icechunk_href,
                media_type="application/x-icechunk",
                title="Icechunk v2 repository",
                roles=["data"],
                extra_fields={
                    "xarray:open_kwargs": {"engine": "zarr"},
                    "xarray:storage_options": {
                        "anon": True,
                        "client_kwargs": {"region_name": self.icechunk_region},
                    },
                },
            ),
        )

        collection.add_link(
            pystac.Link(
                rel="license",
                target=LICENSE_URLS[self.license],
                media_type="text/html",
                title=self.license.value,
            )
        )
        if self.additional_terms:
            collection.add_link(
                pystac.Link(
                    rel="license",
                    target=str(self.additional_terms.href),
                    media_type="text/html",
                    title=self.additional_terms.title,
                )
            )
        collection.add_link(
            pystac.Link(
                rel="about",
                target=self.about_url,
                media_type="text/html",
                title="Dataset documentation",
            )
        )
        collection.add_link(
            pystac.Link(
                rel="example",
                target=self.github_notebook_url,
                media_type="application/x-ipynb+json",
                title="Example notebook (GitHub)",
            )
        )
        collection.add_link(
            pystac.Link(
                rel="example",
                target=self.colab_notebook_url,
                media_type="text/html",
                title="Example notebook (Colab)",
            )
        )
        return collection


def _str_or_none(value: object) -> str | None:
    if value is None:
        return None
    s = str(value)
    return s if s else None
