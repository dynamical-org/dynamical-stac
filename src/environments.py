from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict

StacEnvironmentName = Literal["production", "staging", "test"]


class StacEnvironment(BaseModel):
    """A published catalog's name, committed directory (also its R2 bucket), and host."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    name: StacEnvironmentName
    directory: str
    root_href: str


# Publication membership is declared explicitly on each CatalogItem.
STAC_ENVIRONMENTS = (
    StacEnvironment(
        name="production", directory="stac", root_href="https://stac.dynamical.org"
    ),
    StacEnvironment(
        name="staging",
        directory="stac-staging",
        root_href="https://stac-staging.dynamical.org",
    ),
    StacEnvironment(
        name="test", directory="stac-test", root_href="https://stac-test.dynamical.org"
    ),
)


def stac_environment(name: StacEnvironmentName) -> StacEnvironment:
    for environment in STAC_ENVIRONMENTS:
        if environment.name == name:
            return environment
    raise ValueError(f"Unknown STAC environment: {name!r}")
