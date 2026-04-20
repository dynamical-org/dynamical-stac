# Plan: dynamical-stac (issue #73)

## Context

The STAC catalog lives as manually authored JSON files in `dynamical.org/docs/stac/`, served at `https://dynamical.org/stac/catalog.json`. Issue #73 asks to:
1. Move STAC generation to its own repo (`dynamical-stac`) using proper libraries (pystac)
2. Host the generated catalog on the existing R2 bucket at `https://stac.dynamical.org/` (canonical URL: `stac.dynamical.org/catalog.json`)
3. Update `dynamical-catalog` to fetch from the new URL
4. Keep old `dynamical.org/stac/` files in place as frozen backward-compat copies (GitHub Pages can't do server-side JSON redirects)

All work on branch `icechunk-2`. Three PRs cross-referencing each other.

---

## Repo 1: dynamical-stac (new)

**Currently empty.** Initialize as a uv Python project.

### Project structure
```
dynamical-stac/
  pyproject.toml
  src/
    __main__.py     # CLI: generate | upload | generate-and-upload
    collections.py  # pystac.Collection definitions for all 10 datasets
    generate.py     # build catalog + validate + write JSON to output dir
    upload.py       # upload to R2 stac.dynamical.org bucket
```

### Dependencies
```
pystac[validation] >= 1.10.0
boto3
```

### collections.py
Port all 10 existing collection.json files from `dynamical.org/docs/stac/` to Python pystac.Collection objects, preserving:
- `cube:dimensions` and `cube:variables` (as `extra_fields`)
- `stac_extensions` list
- `extent` (spatial bbox + temporal interval)
- `assets` (zarr + icechunk, with `icechunk:storage` extra fields)
- `links` (about, example notebook links — pointing to dynamical.org/catalog/)

Datasets to include (matching current `catalog.json`):
1. noaa-gfs-analysis
2. noaa-gfs-forecast
3. noaa-gefs-forecast-35-day
4. noaa-gefs-analysis
5. noaa-hrrr-forecast-48-hour
6. noaa-hrrr-analysis
7. noaa-mrms-conus-analysis-hourly
8. ecmwf-aifs-single-forecast
9. ecmwf-ifs-ens-forecast-15-day-0-25-degree
10. noaa-gfs-analysis-hourly (deprecated, zarr v2 only — no icechunk asset)

### generate.py
```python
ROOT_HREF = "https://stac.dynamical.org"

def generate(output_dir: Path) -> None:
    catalog = pystac.Catalog(id="dynamical-org", description="...")
    catalog.add_children([all collections...])
    catalog.normalize_and_save(
        root_href=ROOT_HREF,
        catalog_type=pystac.CatalogType.ABSOLUTE_PUBLISHED,
        dest_href=str(output_dir),
    )
    catalog.validate_all()
```

Writes `output_dir/catalog.json` + `output_dir/<dataset-id>/collection.json` with all `self`/`root`/`parent` links pointing to `stac.dynamical.org`.

### upload.py
```python
def upload(stac_dir: Path) -> None:
    s3 = boto3.client("s3",
        endpoint_url=os.environ["R2_ENDPOINT_URL"],
        aws_access_key_id=os.environ["R2_ACCESS_KEY_ID"],
        aws_secret_access_key=os.environ["R2_SECRET_ACCESS_KEY"],
    )
    for file in sorted(stac_dir.rglob("*.json")):
        key = str(file.relative_to(stac_dir))
        s3.upload_file(str(file), "stac-dynamical-org", key,
            ExtraArgs={"ContentType": "application/json"})
```

(Bucket name `stac-dynamical-org` — confirm at implementation time from Cloudflare R2 dashboard or op item fields.)

### __main__.py
```python
match sys.argv[1:]:
    case ["generate", "--output", out]:
        generate(Path(out))
    case ["upload", stac_dir]:
        upload(Path(stac_dir))
    case ["generate-and-upload"]:
        with tempfile.TemporaryDirectory() as tmp:
            generate(Path(tmp))
            upload(Path(tmp))
```

Run as: `uv run python src/__main__.py generate-and-upload`

### R2 credentials
Use `r2-stac-rw` from 1Password (Dynamical vault):
```bash
op run --env-file=<(cat <<'EOF'
R2_ENDPOINT_URL=op://Dynamical/r2-stac-rw/endpoint_url
R2_ACCESS_KEY_ID=op://Dynamical/r2-stac-rw/access_key_id
R2_SECRET_ACCESS_KEY=op://Dynamical/r2-stac-rw/password
EOF
) -- uv run python src/__main__.py generate-and-upload
```
(Field names may need adjustment — confirm 1Password field labels at implementation time.)

---

## Repo 2: dynamical-catalog

**One-line change:**

File: `src/dynamical_catalog/_stac.py:13`

```python
# Before
STAC_CATALOG_URL = "https://dynamical.org/stac/catalog.json"
# After
STAC_CATALOG_URL = "https://stac.dynamical.org/catalog.json"
```

---

## Repo 3: dynamical.org

**Minimal — keep old files for backward compat.**

The 11ty site is hosted on GitHub Pages (CNAME = `dynamical.org`), which does not support server-side redirects for JSON files. The existing JSON files in `docs/stac/` remain in place as a frozen backward-compat copy. No code changes needed.

---

## Verification

1. `uv run python src/__main__.py generate --output /tmp/stac-test`
   → produces `catalog.json` + 10 `collection.json` files
   → all `self` links point to `stac.dynamical.org`

2. pystac `validate_all()` passes during generate step

3. Run `op run ... -- uv run python src/__main__.py generate-and-upload`
   → `https://stac.dynamical.org/catalog.json` returns valid JSON

4. In `dynamical-catalog`: `uv run pytest`
   → passes after URL switch

---

## Critical Files

- Source collections: `/Users/marsh/workspace/dynamical-org/dynamical.org/docs/stac/*/collection.json` (10 files)
- Catalog root: `/Users/marsh/workspace/dynamical-org/dynamical.org/docs/stac/catalog.json`
- URL to update: `/Users/marsh/workspace/dynamical-org/dynamical-catalog/src/dynamical_catalog/_stac.py:13`
- New repo root: `/Users/marsh/workspace/dynamical-org/dynamical-stac/`

---

### 2026-04-20 — Remaining todo items from meta#73

Working through the open checkboxes from the meta issue. Completed below are landed on this branch.

#### Done

- **Integration test: `dynamical-catalog` reads a value.** `tests/test_catalog_read.py` generates the catalog to a tmpdir, serves it over a local HTTP server (root_href override), monkey-patches `dynamical_catalog._stac.STAC_CATALOG_URL`, opens `noaa_gfs_forecast` via icechunk, and reads one scalar from `temperature_2m`. Marked `@pytest.mark.integration`.
- **Integration test: standard STAC browser.** `tests/test_stac_browse.py` uses `pystac-client` against the same served catalog to assert collection set matches `_COLLECTION_IDS` and that each has title/description/extents/zarr asset. Independent of any dynamical code.
- **Test wiring.** `generate.generate()` now takes `root_href` (defaults to `ROOT_HREF`), so tests can point at localhost. `tests/conftest.py` has a `served_catalog` fixture shared by both integration tests. `pyproject.toml` gained an `integration` dependency group (`pystac-client`, `dynamical-catalog` via git source on `icechunk-2` until merge + PyPI release) and an `integration` pytest marker.
- **Reformatters-triggered rebuild (STAC side).** `test.yml` now accepts `repository_dispatch: [reformatters-main-push]` and `workflow_dispatch`. Tests run in two stages (unit, then integration). A `notify-on-failure` job opens a GitHub issue when the dispatch-triggered run fails, including the reformatters SHA/ref from `client_payload`.

#### Reformatters side — separate PR needed

Add this workflow to `reformatters` (requires `STAC_DISPATCH_TOKEN` secret — a fine-grained PAT scoped to `dynamical-org/dynamical-stac` with `Actions: write` + `Contents: read`):

```yaml
# .github/workflows/notify-stac.yml
name: Notify dynamical-stac on main push

on:
  push:
    branches: [main]
    paths:
      - 'src/reformatters/**/template_config.py'

permissions:
  contents: read

jobs:
  dispatch:
    runs-on: ubuntu-latest
    steps:
      - name: Dispatch to dynamical-stac
        env:
          GH_TOKEN: ${{ secrets.STAC_DISPATCH_TOKEN }}
          SHA: ${{ github.sha }}
          REF: ${{ github.ref }}
        run: |
          gh api repos/dynamical-org/dynamical-stac/dispatches \
            -f event_type=reformatters-main-push \
            -F "client_payload[sha]=${SHA}" \
            -F "client_payload[ref]=${REF}"
```

#### Multi-icechunk schema (Alden's comment)

Context: today each collection has a single `assets.icechunk` object with one `icechunk:storage` block (cloud, bucket, prefix, region). Alden asked how this extends when a dataset is mirrored to a second cloud (e.g. R2 in addition to S3).

Options considered:

1. **Multiple keyed assets** (`icechunk-s3`, `icechunk-r2`). STAC-idiomatic, explicit, easy to browse. Breaks `dynamical-catalog`'s `assets.get("icechunk")` — needs a client-side "preferred cloud" concept or fallback iteration.
2. **STAC `alternate-assets` extension.** One primary `icechunk` asset with `alternate: {r2: {href, icechunk:storage}}` siblings. `dynamical-catalog` keeps working unchanged (it reads the primary). Matches the "mirror" framing well. This is the standard STAC answer for this exact problem.
3. **Array of storages inside one asset.** Simple schema evolution but breaks the `icechunk:storage` single-object contract and dynamical-catalog with it.
4. **Sibling collections per cloud.** Duplicates everything; wrong abstraction.

**Recommendation: Option 2 (`alternate-assets`).**

- Primary asset stays the canonical cloud location (whichever is fastest/cheapest for most users — likely the existing S3/public bucket).
- Additional clouds live under `alternate` as siblings with their own `href` + `icechunk:storage`.
- Zero changes needed in `dynamical-catalog` until/unless we want client-side cloud selection, at which point it's a small addition (e.g. `entry.open(cloud="r2")` inspects `assets["icechunk"]["alternate"]`).
- In `dynamical-stac`, the change is additive in `src/data/*.json` and requires adding `"https://stac-extensions.github.io/alternate-assets/v1.2.0/schema.json"` to `stac_extensions` on affected collections. `validate_all()` will enforce the schema.

Action: no code change until we actually have a second cloud to mirror to. When that happens, follow option 2 and add an integration test case that reads the same value via both primary and alternate storage.

#### User-action items (cannot complete autonomously)

- **R2 bucket versioning on `stac-dynamical-org`.** Cloudflare dashboard → R2 → bucket → Settings → Object versioning: Enable. Or with `wrangler` (`wrangler r2 bucket update stac-dynamical-org --versioning enable` — verify current syntax).
- **Branch rulesets** on `dynamical-catalog` and `dynamical-stac` (both private; Free-tier private repos can't use rulesets via REST). Either upgrade plan, make public, or set via UI: Settings → Rules → Rulesets → New → require PR + 1 approval + passing `test` status check on `main`.
- **PyPI 2FA.** pypi.org account settings → two-factor authentication. Account-scoped, user-only.
