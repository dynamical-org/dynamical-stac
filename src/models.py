from __future__ import annotations

import datetime as dt
import re
from typing import Literal
from urllib.parse import quote

import numpy as np
import pandas as pd
import pystac
import xarray as xr
from pydantic import BaseModel, ConfigDict, Field, computed_field, field_validator

from catalog import (
    MODELS,
    AdditionalTerms,
    CatalogItem,
    DatasetExample,
    DatasetLicense,
    DatasetNotebook,
)

NOTEBOOKS_REPO_BASE = "https://github.com/dynamical-org/notebooks/blob/main"


def _github_notebook_url(slug: str) -> str:
    # Percent-encode the slug. Colab's URL parser decodes a literal ``+`` in the
    # path as a space (query-string rule applied to the path), so e.g.
    # ``noaa-gfs+ecmwf-aifs-hdd.ipynb`` gets fetched as
    # ``noaa-gfs ecmwf-aifs-hdd.ipynb`` and 404s. ``%2B`` sidesteps it on both
    # github.com and colab.
    return f"{NOTEBOOKS_REPO_BASE}/{quote(slug, safe='')}.ipynb"


def _colab_notebook_url(slug: str) -> str:
    return _github_notebook_url(slug).replace(
        "https://github.com/", "https://colab.research.google.com/github/"
    )


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

# Published catalog URL baked into the pystac open snippet. Reading the
# ``icechunk-https`` asset href from here (rather than hardcoding the store URL)
# is what lets us relocate a dataset to any public-HTTPS object store without
# users changing their code.
STAC_CATALOG_URL = "https://stac.dynamical.org/catalog.json"

# Labels for the two open-snippet variants rendered as tabs on dataset pages.
_CATALOG_VARIANT_LABEL = "dynamical-catalog"
_PYSTAC_VARIANT_LABEL = "pystac + icechunk"

# Matches an authored dynamical-catalog open line, e.g.
#   ds = dynamical_catalog.open("noaa-gfs-analysis", chunks=None)
#   ds_pressure = dynamical_catalog.open("id", group="pressure_level", chunks=None)
_CATALOG_OPEN_RE = re.compile(
    r"^(?P<var>\w+) = dynamical_catalog\.open\("
    r'"(?P<id>[^"]+)"'
    r'(?:, group="(?P<group>[^"]+)")?'
    r", chunks=None\)$"
)


def _pystac_preamble(collection_id: str, virtual_prefixes: tuple[str, ...]) -> str:
    """Imports + STAC lookup + icechunk session for the pystac open variant.

    Virtual datasets additionally authorize anonymous S3 reads of their GRIB
    chunk containers (icechunk only opens the repo over HTTPS; the referenced
    source chunks still live in public S3 buckets).
    """
    lines = [
        "import icechunk",
        "import pystac",
        "import xarray as xr",
        "",
        f'catalog = pystac.Catalog.from_file("{STAC_CATALOG_URL}")',
        f'collection = catalog.get_child("{collection_id}")',
        'asset = collection.assets["icechunk-https"]',
        "",
    ]
    if virtual_prefixes:
        entries = ", ".join(
            f'"{prefix}": icechunk.s3_anonymous_credentials()'
            for prefix in virtual_prefixes
        )
        lines += [
            f"authorize = icechunk.containers_credentials({{{entries}}})",
            "repo = icechunk.Repository.open(",
            "    icechunk.http_storage(asset.href),",
            "    authorize_virtual_chunk_access=authorize,",
            ")",
        ]
    else:
        lines.append(
            "repo = icechunk.Repository.open(icechunk.http_storage(asset.href))"
        )
    lines.append('session = repo.readonly_session("main")')
    return "\n".join(lines)


def _pystac_variant_code(
    catalog_code: str, collection_id: str, virtual_prefixes: tuple[str, ...]
) -> str:
    """Derive the pystac + icechunk-HTTPS snippet from the dynamical-catalog one.

    The two variants share their operations verbatim and differ only in how the
    dataset is opened: each ``dynamical_catalog.open(...)`` line becomes an
    ``xr.open_zarr(session.store, ...)`` line against the session built by
    :func:`_pystac_preamble`. Raises if an open line doesn't match the expected
    shape, so a malformed snippet fails at generation time rather than shipping
    a broken example.
    """
    body: list[str] = []
    saw_open = False
    for line in catalog_code.splitlines():
        if line.startswith("import dynamical_catalog"):
            continue
        match = _CATALOG_OPEN_RE.match(line)
        if match:
            saw_open = True
            group_arg = f', group="{match["group"]}"' if match["group"] else ""
            body.append(
                f"{match['var']} = xr.open_zarr(session.store{group_arg}, chunks=None)"
            )
        elif "dynamical_catalog.open(" in line:
            raise ValueError(f"unrecognized dynamical_catalog.open line: {line!r}")
        else:
            body.append(line)
    if not saw_open:
        raise ValueError(
            f"example for {collection_id!r} has no dynamical_catalog.open(...) call"
        )
    # Drop the blank line the import preamble left behind so the first open sits
    # directly under our own preamble.
    while body and not body[0].strip():
        body.pop(0)
    preamble = _pystac_preamble(collection_id, virtual_prefixes)
    return f"{preamble}\n\n" + "\n".join(body)


class CubeDimension(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    type: Literal["spatial", "temporal", "other"]
    extent: list[str | None] | list[float | None] | list[int | None] = Field(
        min_length=2, max_length=2
    )
    axis: str | None = None
    unit: str | None = None
    size: int | None = Field(default=None, ge=0)


class CubeVariable(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    dimensions: list[str] = Field(min_length=1)
    type: Literal["data"] = "data"
    # Chunk/shard element counts per dimension, ordered to match ``dimensions``.
    # ``chunks`` follows the (unofficial but datacube-v2.2.0-valid) convention
    # from stac-extensions/datacube#7; ``shards`` mirrors it for zarr v3 sharding.
    chunks: list[int] | None = None
    shards: list[int] | None = None
    unit: str | None = None
    long_name: str = Field(min_length=1)
    standard_name: str | None = None
    short_name: str | None = None
    comment: str | None = None


class ChunkGrid(BaseModel):
    """One chunking grid (a chunk or a shard) for the dataset's data variables.

    ``shape`` is the element count per dimension, ordered to match
    ``dimensions``. ``lengths`` maps each dimension that has a physical extent
    (spatial/temporal) to a human-readable span covered by one chunk/shard
    (e.g. ``"30 days"``, ``"30.25°"``); dimensionless axes like
    ``ensemble_member`` are omitted.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    dimensions: list[str] = Field(min_length=1)
    shape: list[int] = Field(min_length=1)
    lengths: dict[str, str] = Field(default_factory=dict)
    uncompressed_size_bytes: int = Field(ge=0)
    uncompressed_size: str = Field(min_length=1)


class Chunking(BaseModel):
    """Collection-level chunk + shard summary, shared by all data variables.

    Emitted only when every data variable shares one
    ``(dims, chunks, shards, dtype)`` signature (the case for all current
    datasets); :func:`_build_chunking` raises otherwise so non-uniform stores
    fail loudly at generation time rather than shipping a misleading summary.

    ``shard`` is ``None`` for chunked-but-unsharded stores (e.g. virtual
    datasets whose chunks each reference a single source GRIB message); the
    rendered table and STAC field then omit the shard column entirely.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    dtype: str = Field(min_length=1)
    chunk: ChunkGrid
    shard: ChunkGrid | None = None

    def as_markdown_table(self) -> str:
        """Transposed Markdown table — one row per dimension (element count plus
        its coordinate span), then an uncompressed-size row. Includes a shard
        column only when the store is sharded. Transposed so high-dimensional
        datasets don't side-scroll on narrow screens.
        """

        def cell(grid: ChunkGrid, dim: str, n: int) -> str:
            length = grid.lengths.get(dim)
            return f"{n} ({length})" if length is not None else str(n)

        if self.shard is None:
            rows = ["| dimension | chunk |", "|---|---|"]
            for dim, c in zip(self.chunk.dimensions, self.chunk.shape, strict=True):
                rows.append(f"| {dim} | {cell(self.chunk, dim, c)} |")
            rows.append(f"| **uncompressed** | {self.chunk.uncompressed_size} |")
            return "\n".join(rows)

        rows = ["| dimension | chunk | shard |", "|---|---|---|"]
        for dim, c, s in zip(
            self.chunk.dimensions, self.chunk.shape, self.shard.shape, strict=True
        ):
            rows.append(
                f"| {dim} | {cell(self.chunk, dim, c)} | {cell(self.shard, dim, s)} |"
            )
        rows.append(
            f"| **uncompressed** | {self.chunk.uncompressed_size} "
            f"| {self.shard.uncompressed_size} |"
        )
        return "\n".join(rows)


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
        # Open-ended + no size so the catalog doesn't drift every time the
        # upstream store gets a new timestep. The collection-level temporal
        # extent carries the same [start, None] shape.
        return CubeDimension(
            type="temporal",
            extent=[_iso(values.min()), None],
            unit="seconds since 1970-01-01",
        )
    if coord.dtype.kind == "m":  # numpy timedelta64 (e.g. forecast lead_time)
        return CubeDimension(
            type="other",
            extent=[_td_seconds(values.min()), _td_seconds(values.max())],
            unit="seconds",
            size=size,
        )
    # Numeric non-spatial/temporal coords (vertical levels, ensemble member)
    # carry a meaningful min/max; report it, preserving int vs float so integer
    # level/member indices don't render as floats. Non-numeric coords, if any,
    # keep [None, None].
    kind = values.dtype.kind
    if kind in "iu":
        extent: list[int | None] | list[float | None] = [
            int(values.min()),
            int(values.max()),
        ]
    elif kind == "f":
        extent = [float(values.min()), float(values.max())]
    else:
        extent = [None, None]
    return CubeDimension(type="other", extent=extent, unit=units or None, size=size)


def _iso(value: np.datetime64) -> str:
    ts = pd.Timestamp(value)
    if ts.tzinfo is None:
        ts = ts.tz_localize("UTC")
    return ts.strftime("%Y-%m-%dT%H:%M:%SZ")


def _td_seconds(value: np.timedelta64) -> int:
    return int(pd.Timedelta(value).total_seconds())


def _num(value: float) -> str:
    """Format a number without trailing zeros (e.g. 30.25 -> '30.25', 795 -> '795')."""
    return f"{value:g}"


def _human_bytes(n: int) -> str:
    size = float(n)
    for unit in ("B", "KiB", "MiB", "GiB", "TiB"):
        if size < 1024 or unit == "TiB":
            return f"{size:.1f} {unit}"
        size /= 1024
    raise AssertionError("unreachable")


def _human_timedelta(td: pd.Timedelta) -> str:
    secs = td.total_seconds()
    if secs % 86400 == 0:
        days = int(secs // 86400)
        return f"{days} day" if days == 1 else f"{days} days"
    if secs % 3600 == 0:
        hours = int(secs // 3600)
        return f"{hours} hour" if hours == 1 else f"{hours} hours"
    minutes = int(secs // 60)
    return f"{minutes} minute" if minutes == 1 else f"{minutes} minutes"


_SPATIAL_DIMS = frozenset({"latitude", "longitude", "x", "y"})


def _human_spatial(magnitude: float, dim: str, units: str) -> str | None:
    """Format a spatial span as degrees or metres/km, or ``None`` if not spatial.

    Matches purely on ``units``; the dimension name is used only to fail loudly
    when a known spatial axis carries coordinate units we don't handle yet,
    rather than silently dropping it from the chunk/shard summary.
    """
    if units in ("degree_north", "degree_east"):
        return f"{_num(magnitude)}°"
    if units == "m":
        if magnitude >= 1000:
            return f"{_num(magnitude / 1000)} km"
        return f"{_num(magnitude)} m"
    if dim in _SPATIAL_DIMS:
        raise ValueError(f"Spatial dim {dim!r} has unhandled coord units {units!r}")
    return None


def _coord_length(ds: xr.Dataset, dim: str, n: int) -> str | None:
    """Human-readable span covered by ``n`` consecutive cells along ``dim``.

    Returns ``None`` for dimensions without a physical extent (e.g. integer
    ``ensemble_member``). The span is measured from the actual coordinate
    values, so non-uniform axes (e.g. ECMWF IFS ENS ``lead_time``, which
    switches from a 3- to a 6-hourly step) are handled correctly. When ``n``
    reaches or exceeds the dimension size the chunk spans the whole dimension.
    """
    if dim not in ds.coords:
        return None
    coord = ds[dim]
    values = coord.values
    size = values.size
    if size < 2:
        return None
    if n < size:
        span = values[n] - values[0]
        # If the last n cells cover a different span than the first n, the axis
        # is non-uniform (e.g. ECMWF IFS ENS lead_time, 3h->6h) so the single
        # reported span is only approximate.
        approx = (values[size - 1] - values[size - 1 - n]) != span
    else:  # covers the full dimension; extend by one cell width
        span = (values[-1] - values[0]) + (values[1] - values[0])
        approx = False
    prefix = "~" if approx else ""

    kind = values.dtype.kind
    if kind in ("M", "m"):  # datetime64 / timedelta64
        return prefix + _human_timedelta(pd.Timedelta(span))
    if kind == "f":
        units = str(coord.attrs.get("units", ""))
        formatted = _human_spatial(abs(float(span)), dim, units)
        return f"{prefix}{formatted}" if formatted is not None else None
    return None


def _chunk_grid(
    ds: xr.Dataset, dims: list[str], shape: tuple[int, ...], itemsize: int
) -> ChunkGrid:
    lengths = {}
    for dim, n in zip(dims, shape, strict=True):
        length = _coord_length(ds, dim, int(n))
        if length is not None:
            lengths[dim] = length
    nbytes = int(np.prod(shape)) * itemsize
    return ChunkGrid(
        dimensions=dims,
        shape=[int(n) for n in shape],
        lengths=lengths,
        uncompressed_size_bytes=nbytes,
        uncompressed_size=_human_bytes(nbytes),
    )


def _build_chunking(ds: xr.Dataset) -> Chunking | None:
    """Collection-level chunk/shard summary, or ``None`` if encoding lacks it.

    Raises if data variables don't all share one ``(dims, chunks, shards,
    dtype)`` signature, so a non-uniform store can't ship a misleading summary.
    """
    signatures: dict[
        str, tuple[tuple[str, ...], tuple[int, ...], tuple[int, ...], str]
    ] = {}
    for name in ds.data_vars:
        da = ds[name]
        chunks = da.encoding.get("chunks")
        shards = da.encoding.get("shards")
        if chunks is None:
            continue
        signatures[str(name)] = (
            tuple(str(d) for d in da.dims),
            tuple(chunks),
            tuple(shards) if shards is not None else None,
            str(da.encoding["dtype"]),
        )
    if not signatures:
        return None
    if len(set(signatures.values())) > 1:
        raise ValueError(
            f"Data variables have non-uniform chunk/shard signatures, so a "
            f"single collection-level chunking summary would be misleading: "
            f"{signatures}"
        )
    dims_t, chunks, shards, dtype = next(iter(signatures.values()))
    dims = list(dims_t)
    itemsize = np.dtype(dtype).itemsize
    return Chunking(
        dtype=dtype,
        chunk=_chunk_grid(ds, dims, chunks, itemsize),
        shard=_chunk_grid(ds, dims, shards, itemsize) if shards is not None else None,
    )


def _time_dim(ds: xr.Dataset) -> str:
    for candidate in ("init_time", "time"):
        if candidate in ds.dims:
            return candidate
    raise ValueError(f"No time dimension found in dims {list(ds.dims)}")


def _wrap_longitude(lon: xr.DataArray) -> xr.DataArray:
    """Map a 0-360 longitude axis into the STAC-required [-180, 180] range.

    Datasets on the native 0-360 grid (e.g. GEFS) would otherwise produce a
    bbox east edge of ~359.75, which ``CollectionInput._check_bbox`` rejects.
    Axes already within range are returned unchanged so the existing -180..180
    datasets don't drift.
    """
    if float(lon.min()) >= -180.0 and float(lon.max()) <= 180.0:
        return lon
    return ((lon + 180.0) % 360.0) - 180.0


def _bbox(ds: xr.Dataset) -> tuple[float, float, float, float]:
    if "latitude" not in ds.coords or "longitude" not in ds.coords:
        raise ValueError(
            f"Dataset missing latitude/longitude coords; has {list(ds.coords)}"
        )
    lat, lon = ds.latitude, _wrap_longitude(ds.longitude)
    return (float(lon.min()), float(lat.min()), float(lon.max()), float(lat.max()))


def _cube_variable(da: xr.DataArray) -> CubeVariable:
    """Build a datacube ``cube:variables`` entry from a data variable."""
    chunks = da.encoding.get("chunks")
    shards = da.encoding.get("shards")
    return CubeVariable(
        dimensions=list(da.dims),
        chunks=[int(n) for n in chunks] if chunks is not None else None,
        shards=[int(n) for n in shards] if shards is not None else None,
        unit=_str_or_none(da.attrs.get("units") or da.attrs.get("unit")),
        long_name=da.attrs["long_name"],
        standard_name=_str_or_none(da.attrs.get("standard_name")),
        short_name=_str_or_none(da.attrs.get("short_name")),
        comment=_str_or_none(da.attrs.get("comment")),
    )


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
    chunking: Chunking | None = None
    icechunk_href: str = Field(pattern=r"^s3://[^/]+/.+$")
    icechunk_region: str = Field(min_length=1)
    icechunk_https_href: str = Field(pattern=r"^https://[^/]+/.+$")
    virtual_chunk_container_prefixes: tuple[str, ...] = ()
    attribution: str = Field(min_length=1)
    version: str = Field(min_length=1)
    summaries: dict[str, str] = Field(default_factory=dict)
    additional_terms: AdditionalTerms | None = None
    model_id: str = Field(min_length=1)
    model_name: str = Field(min_length=1)
    description_summary: str = Field(min_length=1)
    description_details: str = Field(min_length=1)
    description_model: str = Field(min_length=1)
    examples: tuple[DatasetExample, ...] = Field(min_length=1)
    notebooks: tuple[DatasetNotebook, ...] = Field(min_length=1)

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
    def about_url(self) -> str:
        return f"https://dynamical.org/catalog/{self.id}/"

    @classmethod
    def from_dataset(
        cls,
        item: CatalogItem,
        ds: xr.Dataset,
        subgroups: dict[str, xr.Dataset] | None = None,
    ) -> CollectionInput:
        """Build a collection from the store's root group ``ds``.

        ``subgroups`` maps each nested zarr group name (e.g. ``pressure_level``)
        to its opened dataset. The datacube extension has no notion of a group
        hierarchy, so we flatten: the group's extra dimension is added to
        ``cube:dimensions`` and its variables are listed under ``{group}/{var}``
        keys (following GeoZarr's slash-path convention). This keeps the keys
        unique when the same variable name appears in several groups (e.g.
        ``temperature`` in both ``pressure_level`` and ``model_level``). Passing
        no subgroups reproduces the single-group output exactly.
        """
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
        # Sort by variable name so regeneration is deterministic; xarray's
        # `data_vars` iteration order depends on zarr store internals and
        # silently reshuffles across generator runs otherwise.
        variables: dict[str, CubeVariable] = {
            str(name): _cube_variable(ds.data_vars[name])
            for name in sorted(ds.data_vars)
        }
        # Fold each nested group's new dimension(s) and variables into the same
        # flat datacube maps. Iterate groups in sorted order for determinism.
        for group_name, group_ds in sorted((subgroups or {}).items()):
            for name in sorted(group_ds.dims):
                if name in group_ds.coords and name not in dims:
                    dims[name] = _dim_entry(name, group_ds[name])
            for name in sorted(group_ds.data_vars):
                variables[f"{group_name}/{name}"] = _cube_variable(
                    group_ds.data_vars[name]
                )
        model = MODELS[item.model_id]
        chunking = _build_chunking(ds)
        chunking_table = chunking.as_markdown_table() if chunking is not None else None
        return cls(
            id=item.id,
            name=ds.attrs["name"],
            description=ds.attrs["description"],
            license=ds.attrs["license"],
            bbox=_bbox(ds),
            temporal_start=t0,
            cube_dimensions=dims,
            cube_variables=variables,
            chunking=chunking,
            icechunk_href=item.icechunk_href,
            icechunk_region=item.icechunk_region,
            icechunk_https_href=item.icechunk_https_href,
            virtual_chunk_container_prefixes=item.virtual_chunk_container_prefixes,
            attribution=ds.attrs["attribution"],
            version=ds.attrs["dataset_version"],
            summaries={k: ds.attrs[k] for k in _SUMMARY_ATTRS if k in ds.attrs},
            additional_terms=item.additional_terms,
            model_id=item.model_id,
            model_name=model.name,
            description_summary=item.description_summary,
            description_details=item.description_details(chunking_table),
            description_model=model.description,
            examples=item.examples,
            notebooks=item.notebooks,
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
        collection.extra_fields["model_id"] = self.model_id
        collection.extra_fields["model_name"] = self.model_name
        collection.extra_fields["description_summary"] = self.description_summary
        collection.extra_fields["description_details"] = self.description_details
        collection.extra_fields["description_model"] = self.description_model
        # Each example carries two open-snippet variants (rendered as tabs on
        # dataset pages): the dynamical-catalog library and a library-free
        # pystac + icechunk-over-HTTPS equivalent that shares the operations.
        collection.extra_fields["examples"] = [
            {
                "title": ex.title,
                "variants": [
                    {
                        "label": _CATALOG_VARIANT_LABEL,
                        "code": ex.code,
                        "language": ex.language,
                    },
                    {
                        "label": _PYSTAC_VARIANT_LABEL,
                        "code": _pystac_variant_code(
                            ex.code, self.id, self.virtual_chunk_container_prefixes
                        ),
                        "language": ex.language,
                    },
                ],
            }
            for ex in self.examples
        ]

        # Don't mirror cube:variables into summaries. STAC Browser renders the
        # summary's flat name list in place of the top-level dict, collapsing
        # the variable table to its first entry. pystac.Summaries also silently
        # drops lists >25 items.
        summaries: dict[str, list[str]] = {k: [v] for k, v in self.summaries.items()}
        collection.summaries = pystac.Summaries(summaries)

        collection.extra_fields["cube:dimensions"] = {
            k: v.model_dump(exclude_none=True) for k, v in self.cube_dimensions.items()
        }
        collection.extra_fields["cube:variables"] = {
            k: v.model_dump(exclude_none=True) for k, v in self.cube_variables.items()
        }
        if self.chunking is not None:
            # exclude_none drops the `shard` key for chunked-but-unsharded
            # stores; sharded collections have no None fields, so their output
            # is unchanged.
            collection.extra_fields["dynamical-org:chunking"] = (
                self.chunking.model_dump(exclude_none=True)
            )

        virtual_chunk_containers = [
            {
                "url_prefix": prefix,
                "credentials": {"type": "s3", "anonymous": True},
            }
            for prefix in self.virtual_chunk_container_prefixes
        ]

        icechunk_extra_fields: dict[str, object] = {
            "xarray:open_kwargs": {"engine": "zarr"},
            "xarray:storage_options": {
                "anon": True,
                "client_kwargs": {"region_name": self.icechunk_region},
            },
        }
        if virtual_chunk_containers:
            icechunk_extra_fields["icechunk:virtual_chunk_containers"] = (
                virtual_chunk_containers
            )
        collection.add_asset(
            "icechunk",
            pystac.Asset(
                href=self.icechunk_href,
                media_type="application/x-icechunk",
                title="Icechunk v2 repository",
                roles=["data"],
                extra_fields=icechunk_extra_fields,
            ),
        )

        # Library-free access path: open with pystac + icechunk.http_storage.
        # No xarray:storage_options — http_storage takes no region/anon config.
        icechunk_https_extra_fields: dict[str, object] = {
            "xarray:open_kwargs": {"engine": "zarr"},
        }
        if virtual_chunk_containers:
            icechunk_https_extra_fields["icechunk:virtual_chunk_containers"] = (
                virtual_chunk_containers
            )
        collection.add_asset(
            "icechunk-https",
            pystac.Asset(
                href=self.icechunk_https_href,
                media_type="application/x-icechunk",
                title="Icechunk v2 repository (HTTPS)",
                roles=["data"],
                extra_fields=icechunk_https_extra_fields,
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
        for notebook in self.notebooks:
            collection.add_link(
                pystac.Link(
                    rel="example",
                    target=_github_notebook_url(notebook.slug),
                    media_type="application/x-ipynb+json",
                    title=f"{notebook.title} (GitHub)",
                )
            )
            collection.add_link(
                pystac.Link(
                    rel="example",
                    target=_colab_notebook_url(notebook.slug),
                    media_type="text/html",
                    title=f"{notebook.title} (Colab)",
                )
            )
        return collection


def _str_or_none(value: object) -> str | None:
    if value is None:
        return None
    s = str(value)
    return s or None
