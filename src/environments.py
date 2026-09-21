from __future__ import annotations

from packaging.version import Version
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class ClientVersionRange(BaseModel):
    """Inclusive client version bounds; names are derived, never parsed."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    min_version: str
    max_version: str

    @field_validator("min_version", "max_version")
    @classmethod
    def _valid_version(cls, value: str) -> str:
        return str(Version(value))

    @model_validator(mode="after")
    def _ordered_bounds(self) -> ClientVersionRange:
        if Version(self.min_version) > Version(self.max_version):
            raise ValueError("min_version must not exceed max_version")
        return self

    @property
    def name(self) -> str:
        return f"{self.min_version}-{self.max_version}"

    def contains(self, client_version: str) -> bool:
        return (
            Version(self.min_version)
            <= Version(client_version)
            <= Version(self.max_version)
        )


class StacEnvironment(BaseModel):
    """A catalog publication, optionally restricted to a client version range."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    name: str = Field(min_length=1)
    directory: str
    root_href: str
    description: str = Field(min_length=1)
    client_versions: ClientVersionRange | None = None

    @model_validator(mode="after")
    def _range_names_match(self) -> StacEnvironment:
        if self.client_versions is not None and self.name != self.client_versions.name:
            raise ValueError("versioned environment name must match its version bounds")
        return self

    @property
    def root_filename(self) -> str:
        if self.client_versions is not None:
            return f"catalog_{self.client_versions.name}.json"
        return "catalog.json"

    @property
    def catalog_url(self) -> str:
        return f"{self.root_href}/{self.root_filename}"

    def for_client_range(
        self, *, min_version: str, max_version: str, description: str
    ) -> StacEnvironment:
        versions = ClientVersionRange(min_version=min_version, max_version=max_version)
        return StacEnvironment(
            name=versions.name,
            directory=self.directory,
            root_href=self.root_href,
            description=description,
            client_versions=versions,
        )


PRODUCTION = StacEnvironment(
    name="production",
    directory="stac",
    root_href="https://stac.dynamical.org",
    description="Released datasets supported by current dynamical-catalog clients.",
)

# Membership is always explicit on CatalogItem. Capability descriptions guide
# authors; the compatibility matrix enforces what each client can actually read.
STAC_ENVIRONMENTS = (
    PRODUCTION,
    StacEnvironment(
        name="staging",
        directory="stac-staging",
        root_href="https://stac-staging.dynamical.org",
        description="Released and unreleased datasets exercised by the main client canary.",
    ),
    StacEnvironment(
        name="test",
        directory="stac-test",
        root_href="https://stac-test.dynamical.org",
        description="Weather datasets and synthetic fixtures for integration tests.",
    ),
    PRODUCTION.for_client_range(
        min_version="0.4.0",
        max_version="0.4.0",
        description="Only S3 Icechunk repositories. Virtual Icechunk Zarr datasets are not supported.",
    ),
    PRODUCTION.for_client_range(
        min_version="0.5.0",
        max_version="0.8.0",
        description="Only S3 Icechunk repositories. Virtual datasets are supported only when all source files are on S3.",
    ),
)


def _check_environments(environments: tuple[StacEnvironment, ...]) -> None:
    names = [environment.name for environment in environments]
    outputs = [
        (environment.directory, environment.root_filename)
        for environment in environments
    ]
    if len(names) != len(set(names)) or len(outputs) != len(set(outputs)):
        raise ValueError("STAC environments must have unique names and output paths")
    ranges = [
        environment.client_versions
        for environment in environments
        if environment.client_versions is not None
    ]
    for i, first in enumerate(ranges):
        for second in ranges[i + 1 :]:
            if max(Version(first.min_version), Version(second.min_version)) <= min(
                Version(first.max_version), Version(second.max_version)
            ):
                raise ValueError(
                    f"overlapping client ranges: {first.name} and {second.name}"
                )


_check_environments(STAC_ENVIRONMENTS)


def stac_environment(name: str) -> StacEnvironment:
    for environment in STAC_ENVIRONMENTS:
        if environment.name == name:
            return environment
    raise ValueError(f"Unknown STAC environment: {name!r}")


def environment_for_client(client_version: str) -> StacEnvironment:
    version = str(Version(client_version))
    for environment in STAC_ENVIRONMENTS:
        if (
            environment.client_versions is not None
            and environment.client_versions.contains(version)
        ):
            return environment
    return PRODUCTION
