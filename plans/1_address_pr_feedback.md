# Address PR #1 review comments — dynamical-stac

## Context

PR #1 (https://github.com/dynamical-org/dynamical-stac/pull/1) initializes the dynamical-stac repo. It was approved by @samn and contains a mix of @samn's review comments (all already addressed in commits `903ba99`/`db61f9a`) and @mrshll's own self-review comments (still open).

This plan covers the still-open items — @mrshll's self-review notes on commit `db61f9a` — plus a live add: a Pydantic model validator on `CatalogItem` enforcing that `id` matches the first path fragment of `icechunk_href`.

### Already addressed (no action needed)

- `.github/workflows/*.yml` — action SHAs pinned + `uv run --locked` — done in `f064f30`/`903ba99`.
- `src/catalog.py` — Pydantic `BaseModel` already used for `CatalogItem` / `AdditionalTerms`.
- `src/models.py` timedelta64 branch — clarifying comment already added in `903ba99`.
- Icechunk asset title is already `"Icechunk v2 repository"`.
- `src/upload.py:8` — bucket is already `"stac"`.
- `about_url` may not exist at build time — note only; no change.

## Changes

### 1. `src/generate.py` — lowercase catalog title

`CATALOG_TITLE = "Dynamical.org STAC Catalog"` → `"dynamical.org STAC Catalog"`.

### 2. `src/models.py` — tighten required attrs and drop icechunk-specific notebook

- `CollectionInput.attribution` / `.version` now required (`str = Field(min_length=1)`).
- `from_dataset` now reads `dataset_id`, `attribution`, `dataset_version`, `license`, `long_name` with `ds.attrs["..."]` (was `.get(...)` for several).
- Removed `github_icechunk_notebook_url` computed field and its `"Icechunk example notebook (GitHub)"` `pystac.Link`.
- `CubeVariable.description` split into `long_name: str = Field(min_length=1)` and `standard_name: str | None = None`.
- Removed `"chunks": None` from the icechunk asset's `xarray:open_kwargs`.

### 3. `src/catalog.py` — `id` must match icechunk_href path fragment (new)

Added `@model_validator(mode="after")` on `CatalogItem`: `id` must equal `icechunk_prefix.split("/", 1)[0]`. Catches typos that silently mismatch the bucket layout.

### 4. `tests/test_from_dataset.py`

- Default synthetic dataset now sets `"attribution"` + `"dataset_version"` (required by `from_dataset`).
- Replaced the long_name→standard_name fallback test with:
  - `test_from_dataset_populates_long_name_and_standard_name`
  - `test_from_dataset_standard_name_is_optional`
  - `test_from_dataset_requires_long_name`
- Added `test_from_dataset_requires_attribution` and `test_from_dataset_requires_dataset_version`.

### 5. `tests/test_catalog_read.py`

- Parametrized `test_every_icechunk_opens_and_reads` over `_COLLECTION_IDS`: opens each collection via `dynamical_catalog.open(...)`, reads a scalar from the first data_var.
- Kept a stricter `test_noaa_gfs_forecast_temperature_2m_reads` smoke case.
- New `test_notebook_url_exists` parametrized over `_COLLECTION_IDS`: HTTP HEAD against `https://github.com/dynamical-org/notebooks/blob/main/{id}.ipynb`, asserts 200.

All new network-touching tests are `@pytest.mark.integration`.

### 6. Pivot: commit generated STAC JSON; CI uploads on push to main

Mid-PR direction change from @mrshll: stop generating in CI; treat the generated JSON as source of truth checked into the repo, and have CI only publish.

- Generated `stac/` directory committed (1 catalog.json + 9 collection.json).
- Workflow renamed `.github/workflows/generate-and-upload.yml` → `upload-stac.yml`. Triggers: `push: branches: [main], paths: [stac/**]` and `workflow_dispatch`. Runs `upload stac`.
- Local flow: `uv run python src/__main__.py generate --output stac` → commit → merge → CI uploads.
- `generate-and-upload` CLI subcommand kept for local one-shot runs but is no longer used in CI.

Follow-ups (not in this PR): CI drift check that regenerates into a tmp dir and diffs against `stac/` so humans can't forget to regenerate.

## Verification

1. `uv run ruff check && uv run ruff format --check`
2. `uv run pytest tests/ -m "not integration"` — fast suite.
3. `uv run pytest tests/ -m integration` — all icechunks open & read; notebook URLs 200.
4. Inspect `stac/catalog.json` + `stac/*/collection.json` for `attribution`, `version`, split `long_name`/`standard_name`, no `chunks: null`, no icechunk-notebook example link.

### 2026-04-22 — PR feedback session

- Addressed @mrshll self-review comments on `db61f9a` and landed the CatalogItem href/id validator requested mid-session.
- Pivoted to committed-JSON flow: `stac/` is now source of truth; CI uploads on push to `main`.
- `test_from_dataset.py`: added attribution/dataset_version required-attr tests and split long_name/standard_name tests.
- `test_catalog_read.py`: parametrized integration test over all 9 collections + notebook-URL HEAD check.
