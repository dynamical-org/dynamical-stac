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
