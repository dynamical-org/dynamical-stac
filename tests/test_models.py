from __future__ import annotations

import datetime as dt

import pydantic
import pytest

from catalog import DatasetLicense
from models import CollectionInput, CubeDimension, CubeVariable


def _valid_input(**overrides: object) -> CollectionInput:
    defaults: dict[str, object] = dict(
        id="test-dataset",
        name="Test Dataset",
        description="A test dataset",
        license="CC-BY-4.0",
        bbox=(-180.0, -90.0, 180.0, 90.0),
        temporal_start=dt.datetime(2020, 1, 1, tzinfo=dt.timezone.utc),
        cube_dimensions={
            "latitude": CubeDimension(
                type="spatial", axis="y", extent=[-90.0, 90.0], unit="degree_north", size=721
            ),
        },
        cube_variables={
            "temp": CubeVariable(dimensions=["latitude"], unit="K"),
        },
        zarr_href="https://data.example.com/test.zarr",
        icechunk_bucket="test-bucket",
        icechunk_prefix="test-prefix/",
        icechunk_region="us-west-2",
    )
    defaults.update(overrides)
    return CollectionInput(**defaults)  # type: ignore[arg-type]


def test_colab_url_is_derived_from_github_url() -> None:
    c = _valid_input(id="my-dataset")
    assert (
        c.github_notebook_url
        == "https://github.com/dynamical-org/notebooks/blob/main/my-dataset.ipynb"
    )
    assert (
        c.colab_notebook_url
        == "https://colab.research.google.com/github/dynamical-org/notebooks/blob/main/my-dataset.ipynb"
    )
    assert c.colab_notebook_url == c.github_notebook_url.replace(
        "https://github.com/", "https://colab.research.google.com/github/"
    )


def test_about_and_icechunk_urls() -> None:
    c = _valid_input(id="ds", icechunk_bucket="b", icechunk_prefix="p/")
    assert c.about_url == "https://dynamical.org/catalog/ds/"
    assert c.icechunk_s3_href == "s3://b/p/"


def test_bbox_validation_rejects_out_of_range() -> None:
    with pytest.raises(pydantic.ValidationError):
        _valid_input(bbox=(-181.0, -90.0, 180.0, 90.0))
    with pytest.raises(pydantic.ValidationError):
        _valid_input(bbox=(0.0, 90.0, 0.0, -90.0))


def test_temporal_start_rejects_naive_datetime() -> None:
    with pytest.raises(pydantic.ValidationError):
        _valid_input(temporal_start=dt.datetime(2020, 1, 1))


def test_temporal_start_normalizes_to_utc() -> None:
    tz = dt.timezone(dt.timedelta(hours=5))
    c = _valid_input(temporal_start=dt.datetime(2020, 1, 1, 12, tzinfo=tz))
    assert c.temporal_start.tzinfo is dt.timezone.utc
    assert c.temporal_start.hour == 7


def test_model_is_frozen() -> None:
    c = _valid_input()
    with pytest.raises(pydantic.ValidationError):
        c.id = "changed"  # type: ignore[misc]


def test_license_accepts_enum_and_string() -> None:
    assert _valid_input(license=DatasetLicense.CC_BY_4_0).license == "CC-BY-4.0"
    assert _valid_input(license="CC-BY-4.0").license == DatasetLicense.CC_BY_4_0


def test_license_rejects_unknown_value() -> None:
    with pytest.raises(pydantic.ValidationError):
        _valid_input(license="MIT")
