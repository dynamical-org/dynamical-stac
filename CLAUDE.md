# dynamical-stac

## Regenerating `stac/` after catalog changes

Any edit to `src/catalog.py` or `src/prose/**` that changes the rendered STAC
(new `CatalogItem`, description/prose edits, model metadata, etc.) requires
regenerating the committed STAC output:

```
./scripts/generate
```

then commit the resulting changes under `stac/`. `tests/test_stac_drift.py`
(integration mark) fails in CI if `stac/` is stale.

Regeneration opens each dataset's Icechunk store on S3, so it needs network
access and takes ~20s.

**Always run `./scripts/generate` before every commit that touches anything
under `src/`, then `git add stac/` before committing.** Skipping this step
ships a stale catalog and breaks `test_stac_drift.py` in CI.

## Pre-commit hook (prek)

To make it hard to forget the regeneration step, this repo ships a
`.pre-commit-config.yaml` that runs `scripts/generate` automatically when any
file under `src/` is staged. We use [prek](https://github.com/j178/prek), a
fast Rust reimplementation of `pre-commit` that consumes the same config.

Install once per clone (uv-based environment):

```
uv tool install prek
prek install
```

`uv tool install` puts the `prek` binary on your `PATH` (no Python runtime
required at the call site); `prek install` wires it into `.git/hooks/`.

After that, every `git commit` that touches `src/` will regenerate `stac/`.
If the hook produces a diff, the commit aborts so you can `git add stac/` and
re-commit. The hook is a no-op for commits that don't touch `src/`.

You still need to run `./scripts/generate` manually when committing through a
client that bypasses hooks, or when you want to inspect the diff before
staging.

## Adding a new `CatalogItem`

Adding a new dataset typically requires all of:

- A `CatalogItem` entry in `src/catalog.py`.
- A matching `Model` entry in `MODELS` (if the `model_id` is new).
- A prose file at `src/prose/datasets/{id}.md` — `description_details` loads
  this lazily, so omissions won't trip validation but will 500 at render time.
- A matching notebook at
  `https://github.com/dynamical-org/notebooks/blob/main/{slug}.ipynb` for each
  `DatasetNotebook.slug` on the item — `tests/test_catalog_read.py::test_notebook_url_exists`
  asserts HTTP 200. The Quickstart notebook's slug must equal the dataset
  `id` (enforced by `CatalogItem._quickstart_slug_matches_id`).
- Regenerated `stac/` output (see above).
