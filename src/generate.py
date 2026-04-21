from __future__ import annotations

import datetime as dt
import pathlib
import urllib.error
import urllib.request
from typing import Any

import icechunk
import pandas as pd
import pystac
import xarray as xr

from datasets import PROFILES, Profile

ROOT_HREF = "https://stac.dynamical.org"

_STAC_EXTENSIONS = [
    "https://stac-extensions.github.io/xarray-assets/v1.0.0/schema.json",
    "https://stac-extensions.github.io/datacube/v2.2.0/schema.json",
]


def _open_icechunk(profile: Profile) -> xr.Dataset:
    storage = icechunk.s3_storage(
        bucket=profile.icechunk_bucket,
        prefix=profile.icechunk_prefix,
        region=profile.icechunk_region,
        anonymous=True,
    )
    repo = icechunk.Repository.open(storage)
    session = repo.readonly_session("main")
    return xr.open_zarr(session.store, consolidated=False, decode_timedelta=True)


def _verify_zarr_url(url: str) -> None:
    manifest_url = url.rstrip("/") + "/zarr.json"
    req = urllib.request.Request(
        manifest_url,
        method="HEAD",
        headers={"User-Agent": "dynamical-stac-generate/0.1"},
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            if resp.status >= 400:
                raise RuntimeError(f"{manifest_url} returned HTTP {resp.status}")
    except urllib.error.URLError as e:
        raise RuntimeError(f"Failed to reach zarr URL {manifest_url}: {e}") from e


def _verify_read(ds: xr.Dataset) -> None:
    first_var = next(iter(ds.data_vars))
    sel = {name: 0 for name in ds[first_var].dims}
    value = ds[first_var].isel(sel).load().values
    assert value.size == 1, f"Expected scalar from {first_var}, got shape {value.shape}"


def _time_dim(ds: xr.Dataset) -> str:
    for candidate in ("init_time", "time"):
        if candidate in ds.dims:
            return candidate
    raise ValueError(f"No time dimension found in dims {list(ds.dims)}")


def _bbox(ds: xr.Dataset) -> list[float]:
    if "latitude" not in ds.coords or "longitude" not in ds.coords:
        raise ValueError(f"Dataset missing latitude/longitude coords; has {list(ds.coords)}")
    lat, lon = ds.latitude, ds.longitude
    return [float(lon.min()), float(lat.min()), float(lon.max()), float(lat.max())]


def _dim_entry(name: str, coord: xr.DataArray) -> dict[str, Any]:
    values = coord.values
    size = int(coord.size)
    units = str(coord.attrs.get("units", ""))
    standard_name = coord.attrs.get("standard_name", "")

    if name == "latitude" or standard_name == "latitude":
        return {
            "type": "spatial",
            "axis": "y",
            "extent": [float(values.min()), float(values.max())],
            "unit": units or "degree_north",
            "size": size,
        }
    if name == "longitude" or standard_name == "longitude":
        return {
            "type": "spatial",
            "axis": "x",
            "extent": [float(values.min()), float(values.max())],
            "unit": units or "degree_east",
            "size": size,
        }
    if name in ("x", "y"):
        return {
            "type": "spatial",
            "axis": name,
            "extent": [float(values.min()), float(values.max())],
            "unit": units or "m",
            "size": size,
        }
    if coord.dtype.kind == "M":
        return {
            "type": "temporal",
            "extent": [_iso(values.min()), None],
            "unit": "seconds since 1970-01-01",
            "size": size,
        }
    if coord.dtype.kind == "m":
        return {
            "type": "other",
            "extent": [None, None],
            "unit": "seconds",
            "size": size,
        }
    return {
        "type": "other",
        "extent": [None, None],
        "unit": units,
        "size": size,
    }


def _cube_dimensions(ds: xr.Dataset) -> dict[str, dict[str, Any]]:
    out: dict[str, dict[str, Any]] = {}
    for name in sorted(ds.dims):
        if name in ds.coords:
            out[name] = _dim_entry(name, ds[name])
    return out


def _cube_variables(ds: xr.Dataset) -> dict[str, dict[str, Any]]:
    out: dict[str, dict[str, Any]] = {}
    for name, da in ds.data_vars.items():
        entry: dict[str, Any] = {
            "dimensions": list(da.dims),
            "type": "data",
        }
        unit = da.attrs.get("units") or da.attrs.get("unit")
        if unit is not None:
            entry["unit"] = str(unit)
        description = da.attrs.get("long_name") or da.attrs.get("standard_name")
        if description:
            entry["description"] = str(description)
        out[str(name)] = entry
    return out


def _iso(value: Any) -> str:
    ts = pd.Timestamp(value)
    if ts.tzinfo is None:
        ts = ts.tz_localize("UTC")
    return ts.strftime("%Y-%m-%dT%H:%M:%SZ")


_SUMMARY_ATTRS = (
    "spatial_domain",
    "spatial_resolution",
    "time_domain",
    "time_resolution",
    "forecast_domain",
    "forecast_resolution",
)


def _build_collection(profile: Profile, ds: xr.Dataset) -> pystac.Collection:
    ds_id = ds.attrs.get("dataset_id")
    if ds_id != profile.id:
        raise ValueError(
            f"Profile id {profile.id!r} does not match store dataset_id {ds_id!r}"
            f" (bucket={profile.icechunk_bucket}, prefix={profile.icechunk_prefix})"
        )

    time_dim = _time_dim(ds)
    t0 = pd.Timestamp(ds[time_dim].values.min()).to_pydatetime()
    if t0.tzinfo is None:
        t0 = t0.replace(tzinfo=dt.timezone.utc)

    extent = pystac.Extent(
        spatial=pystac.SpatialExtent([_bbox(ds)]),
        temporal=pystac.TemporalExtent([[t0, None]]),
    )

    collection = pystac.Collection(
        id=profile.id,
        title=ds.attrs["name"],
        description=ds.attrs["description"],
        license=profile.license,
        extent=extent,
    )
    collection.stac_extensions = list(_STAC_EXTENSIONS)
    if "attribution" in ds.attrs:
        collection.extra_fields["attribution"] = ds.attrs["attribution"]
    if "dataset_version" in ds.attrs:
        collection.extra_fields["version"] = ds.attrs["dataset_version"]
    summaries = {k: [ds.attrs[k]] for k in _SUMMARY_ATTRS if k in ds.attrs}
    if summaries:
        collection.summaries = pystac.Summaries(summaries)
    collection.extra_fields["cube:dimensions"] = _cube_dimensions(ds)
    collection.extra_fields["cube:variables"] = _cube_variables(ds)

    collection.add_asset(
        "zarr",
        pystac.Asset(
            href=profile.zarr_href,
            media_type="application/x-zarr",
            title="Zarr v3 store",
            roles=["data"],
            extra_fields={"xarray:open_kwargs": {"engine": "zarr"}},
        ),
    )
    collection.add_asset(
        "icechunk",
        pystac.Asset(
            href=f"s3://{profile.icechunk_bucket}/{profile.icechunk_prefix}",
            media_type="application/x-icechunk",
            title="Icechunk repository",
            roles=["data"],
            extra_fields={
                "icechunk:storage": {
                    "bucket": profile.icechunk_bucket,
                    "prefix": profile.icechunk_prefix,
                    "region": profile.icechunk_region,
                },
                "xarray:open_kwargs": {"engine": "zarr", "chunks": None},
            },
        ),
    )

    collection.add_link(
        pystac.Link(
            rel="about",
            target=f"https://dynamical.org/catalog/{profile.id}/",
            media_type="text/html",
            title="Dataset documentation",
        )
    )
    collection.add_link(
        pystac.Link(
            rel="example",
            target=f"https://github.com/dynamical-org/notebooks/blob/main/{profile.id}.ipynb",
            media_type="application/x-ipynb+json",
            title="Example notebook (GitHub)",
        )
    )
    collection.add_link(
        pystac.Link(
            rel="example",
            target=f"https://colab.research.google.com/github/dynamical-org/notebooks/blob/main/{profile.id}.ipynb",
            media_type="text/html",
            title="Example notebook (Colab)",
        )
    )
    collection.add_link(
        pystac.Link(
            rel="example",
            target=f"https://github.com/dynamical-org/notebooks/blob/main/{profile.id}-icechunk.ipynb",
            media_type="application/x-ipynb+json",
            title="Icechunk example notebook (GitHub)",
        )
    )

    return collection


def generate(output_dir: pathlib.Path, root_href: str = ROOT_HREF) -> None:
    catalog = pystac.Catalog(
        id="dynamical-org",
        description="Cloud-optimized weather and climate datasets from dynamical.org",
    )
    for profile in PROFILES:
        print(f"{profile.id}: opening icechunk store")
        ds = _open_icechunk(profile)
        _verify_read(ds)
        print(f"{profile.id}: verifying zarr URL")
        _verify_zarr_url(profile.zarr_href)
        catalog.add_child(_build_collection(profile, ds))

    catalog.normalize_hrefs(root_href)
    catalog.validate_all()
    catalog.save(
        catalog_type=pystac.CatalogType.ABSOLUTE_PUBLISHED,
        dest_href=str(output_dir),
    )
