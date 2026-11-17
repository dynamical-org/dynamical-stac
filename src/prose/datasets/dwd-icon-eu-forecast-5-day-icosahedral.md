### Native grid

This dataset keeps the triangular cells ICON-EU computes on, rather than
interpolating them to a regular latitude/longitude grid. A single spatial
dimension, `cell`, indexes the triangles in DWD's order. The `latitude` and
`longitude` coordinates give each cell's centre and `cell_area` its area in
square metres. The triangles themselves are described, following the
[UGRID conventions](https://ugrid-conventions.github.io/ugrid-conventions/),
in the store's separate `mesh` group.

To read a location, select the cell whose centre is nearest, as the example
does. Load `latitude` and `longitude` once and keep them in memory: each spans
every cell, and leaving them lazy fetches them again with every point read. The
nearest centre is returned even for a point outside the model domain.

For a quick map, scatter the cell centres from the dataset (a single variable's
`plot.scatter` does not colour by value):

```python
field = ds[["temperature_2m"]].sel(init_time="2026-11-01T00", lead_time="24h").load()
field.plot.scatter(
    x="longitude", y="latitude", hue="temperature_2m", s=0.1, edgecolors="none"
)
```

To draw the cells themselves, add the `mesh` group:

```python
import matplotlib.pyplot as plt

mesh = dynamical_catalog.open(
    "dwd-icon-eu-forecast-5-day-icosahedral", group="mesh", chunks=None
)
plt.tripcolor(
    mesh.node_longitude,
    mesh.node_latitude,
    mesh.face_node_connectivity,
    facecolors=field["temperature_2m"],
)
```

The same two groups open in the unstructured-grid libraries
[UXarray](https://uxarray.readthedocs.io/) and
[xugrid](https://deltares.github.io/xugrid/), for regridding, regional means
and mesh-aware plotting:

```python
import uxarray as ux
import xugrid as xu

uxds = ux.open_dataset(mesh, ds)  # UXarray renames `cell` to `n_face`
uds = xu.UgridDataset(xr.merge([ds, mesh]))
```

### Source

The source grib files this archive is constructed from are provided by
[DWD Open Data](https://www.dwd.de/EN/ourservices/opendata/opendata.html)
and the [dynamical.org DWD ICON grib archive](https://source.coop/dynamical/dwd-icon-grib)
on [Source Cooperative](https://source.coop/).

### Storage

Icechunk storage generously provided by [AWS Open Data](https://aws.amazon.com/opendata/).
Storage for the dynamical.org DWD ICON-EU grib archive is generously provided by
[Source Cooperative](https://source.coop/), a [Radiant Earth](https://radiant.earth/) initiative.

### Chunks and shards

{{ chunking }}

### Validation report

{{ validation_report }}

### Compression

{{ compression }}
