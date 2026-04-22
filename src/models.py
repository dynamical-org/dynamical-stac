from __future__ import annotations

import datetime as dt
from typing import Any, Literal

import pandas as pd
import pydantic
import pystac
import xarray as xr
from pydantic import BaseModel, ConfigDict, Field, computed_field, field_validator

from catalog import CatalogItem, DatasetLicense

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
    extent: list[Any] = Field(min_length=2, max_length=2)
    axis: str | None = None
    unit: str | None = None
    size: int = Field(ge=0)


class CubeVariable(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    dimensions: list[str] = Field(min_length=1)
    type: Literal["data"] = "data"
    unit: str | None = None
    description: str | None = None
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
    return CubeDimension(type="other", extent=[None, None], unit=units or None, size=size)


def _iso(value: Any) -> str:
    ts = pd.Timestamp(value)
    if ts.tzinfo is None:
        ts = ts.tz_localize("UTC")
    return ts.strftime("%Y-%m-%dT%H:%M:%SZ")


def _td_seconds(value: Any) -> int:
    return int(pd.Timedelta(value).total_seconds())


def _time_dim(ds: xr.Dataset) -> str:
    for candidate in ("init_time", "time"):
        if candidate in ds.dims:
            return candidate
    raise ValueError(f"No time dimension found in dims {list(ds.dims)}")


def _bbox(ds: xr.Dataset) -> tuple[float, float, float, float]:
    if "latitude" not in ds.coords or "longitude" not in ds.coords:
        raise ValueError(f"Dataset missing latitude/longitude coords; has {list(ds.coords)}")
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
    zarr_href: pydantic.HttpUrl
    icechunk_bucket: str = Field(min_length=1)
    icechunk_prefix: str = Field(min_length=1)
    icechunk_region: str = Field(min_length=1)
    attribution: str | None = None
    version: str | None = None
    summaries: dict[str, str] = Field(default_factory=dict)
    additional_terms_href: pydantic.HttpUrl | None = None
    additional_terms_title: str | None = None

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
        return v.astimezone(dt.timezone.utc)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def github_notebook_url(self) -> str:
        return f"https://github.com/dynamical-org/notebooks/blob/main/{self.id}.ipynb"

    @computed_field  # type: ignore[prop-decorator]
    @property
    def github_icechunk_notebook_url(self) -> str:
        return f"https://github.com/dynamical-org/notebooks/blob/main/{self.id}-icechunk.ipynb"

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

    @computed_field  # type: ignore[prop-decorator]
    @property
    def icechunk_s3_href(self) -> str:
        return f"s3://{self.icechunk_bucket}/{self.icechunk_prefix}"

    @classmethod
    def from_dataset(cls, item: CatalogItem, ds: xr.Dataset) -> CollectionInput:
        ds_id = ds.attrs.get("dataset_id")
        if ds_id != item.id:
            raise ValueError(
                f"CatalogItem id {item.id!r} does not match store dataset_id {ds_id!r}"
                f" (bucket={item.icechunk_bucket}, prefix={item.icechunk_prefix})"
            )
        time_dim = _time_dim(ds)
        t0 = pd.Timestamp(ds[time_dim].values.min()).to_pydatetime()
        if t0.tzinfo is None:
            t0 = t0.replace(tzinfo=dt.timezone.utc)
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
                description=_str_or_none(
                    da.attrs.get("long_name") or da.attrs.get("standard_name")
                ),
                short_name=_str_or_none(da.attrs.get("short_name")),
                comment=_str_or_none(da.attrs.get("comment")),
            )
        return cls(
            id=item.id,
            name=ds.attrs["name"],
            description=ds.attrs["description"],
            license=item.license,
            bbox=_bbox(ds),
            temporal_start=t0,
            cube_dimensions=dims,
            cube_variables=variables,
            zarr_href=item.zarr_href,
            icechunk_bucket=item.icechunk_bucket,
            icechunk_prefix=item.icechunk_prefix,
            icechunk_region=item.icechunk_region,
            attribution=ds.attrs.get("attribution"),
            version=ds.attrs.get("dataset_version"),
            summaries={k: ds.attrs[k] for k in _SUMMARY_ATTRS if k in ds.attrs},
            additional_terms_href=item.additional_terms_href,
            additional_terms_title=item.additional_terms_title,
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
        if self.attribution:
            collection.extra_fields["attribution"] = self.attribution
        if self.version:
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
            "zarr",
            pystac.Asset(
                href=str(self.zarr_href),
                media_type="application/x-zarr",
                title="Zarr v3 store",
                roles=["data"],
                extra_fields={"xarray:open_kwargs": {"engine": "zarr"}},
            ),
        )
        collection.add_asset(
            "icechunk",
            pystac.Asset(
                href=self.icechunk_s3_href,
                media_type="application/x-icechunk",
                title="Icechunk v2 repository",
                roles=["data"],
                extra_fields={
                    "icechunk:storage": {
                        "bucket": self.icechunk_bucket,
                        "prefix": self.icechunk_prefix,
                        "region": self.icechunk_region,
                    },
                    "xarray:open_kwargs": {"engine": "zarr", "chunks": None},
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
        if self.additional_terms_href and self.additional_terms_title:
            collection.add_link(
                pystac.Link(
                    rel="license",
                    target=str(self.additional_terms_href),
                    media_type="text/html",
                    title=self.additional_terms_title,
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
        collection.add_link(
            pystac.Link(
                rel="example",
                target=self.github_icechunk_notebook_url,
                media_type="application/x-ipynb+json",
                title="Icechunk example notebook (GitHub)",
            )
        )
        return collection


def _str_or_none(value: Any) -> str | None:
    if value is None:
        return None
    s = str(value)
    return s if s else None
