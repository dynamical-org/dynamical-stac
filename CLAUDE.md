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
  `id` (enforced by `CatalogItem._quickstart_slug_matches_id`). Production
  items must declare at least one notebook (enforced by
  `CatalogItem._production_items_have_notebooks`); only staging items may
  leave `notebooks` empty.
- Regenerated `stac/` output (see above).

## Staging datasets

Set `staging=True` on a `CatalogItem` to publish it only to the staging catalog
(`stac-staging.dynamical.org`), not production. Staging items are excluded from
`generate()` by default and from the committed `stac/` tree; they're included
only when `STAC_INCLUDE_STAGING=1` (set by `upload-stac-staging.yml`, which runs
on every push to `main` and uploads to the `stac-staging` bucket). Flip the flag
to `False` and merge to release the dataset to production.

A staging dataset still needs its prose file, but its notebook is optional: a
staging item may omit `notebooks` entirely (its collection then carries no
`example` links) until the notebook is written. Any notebook it *does* declare
is still HEADed for a 200 by `test_notebook_url_exists`, and flipping
`staging=False` fails validation until at least one notebook is present.
Because staging items aren't in the committed `stac/`, regenerating locally
with `./scripts/generate` won't show them — use
`STAC_INCLUDE_STAGING=1 ./scripts/generate` to preview the staging catalog.

dynamical.org Cloudflare PR previews build against `stac-staging`, so a staging
dataset appears in website previews while staying hidden from the live site.

## Test datasets

There is a third catalog tier above staging: `stac-test.dynamical.org` (R2
bucket `stac-test`). It is a superset of staging — production + staging + every
`CatalogItem` with `test=True`. Test items are synthetic fixtures that exist so
[dynamical-catalog](https://github.com/dynamical-org/dynamical-catalog)'s
integration tests can read real generator output; they are not weather data.

Set `test=True` (mutually exclusive with `staging=True`) to publish a dataset
only to the test catalog. Test items never reach staging or production: they're
excluded from the committed `stac/` tree, from `stac-staging`, and from
`catalog._COLLECTION_IDS` (so this repo's own read/browse integration tests
skip them). They're included only when `STAC_INCLUDE_TEST=1`, set by
`upload-stac-test.yml` (which also sets `STAC_INCLUDE_STAGING=1`) — that
workflow runs on every push to `main` and uploads to the `stac-test` bucket.
Preview it locally with
`STAC_INCLUDE_STAGING=1 STAC_INCLUDE_TEST=1 ./scripts/generate` — but don't
commit the result, the committed tree is production-only.

Like staging items, a test item may omit `notebooks`. Unlike them it also has
no validation report, so its prose omits that section.

Repositories and virtual chunk containers may be `s3://`, `gs://`, `az://` or
`https://` (a repository or container served anonymously over plain HTTPS, e.g.
from an R2 custom domain). For `az://` the URL's netloc is the blob
*container*, not a bucket. `icechunk_region` is required for `s3://` (it goes
in the store's HTTPS domain and in the reader's storage options) and must be
omitted for `gs://`, `az://` and `https://`, which have no region.
`icechunk_account` is the mirror image: required for `az://` (Azure's storage
account is absent from the URL but needed for both the HTTPS domain and the
reader's storage options) and must be omitted otherwise. The generator
dispatches on the scheme in `generate._storage` /
`generate._container_credentials`, and the rendered collection carries
`xarray:storage_options` of `{"anon": true, "client_kwargs": {...}}` for S3,
`{"token": "anon"}` for GCS and `{"account_name": ..., "anon": true}` for
Azure, and none at all for HTTPS (`icechunk.http_storage` takes no region or
anon config). Container `credentials` are `{"type": "s3"|"gcs"|"azure",
"anonymous": true}` for object stores and `{"type": "http"}` for HTTPS. An
`https://` repository's `icechunk-https` asset is its href with any trailing
slash removed. Reading a `gs://`, `az://` or `https://` dataset needs
dynamical-catalog >= 1.0.0 (the previous release, 0.8.0, reads S3 only); the
example snippets of those items pass `min_version="1.0.0"` to `_example` so
the rendered import comment says so.

## Client compatibility matrix

`scripts/compat_matrix.py` discovers every non-yanked stable
`dynamical-catalog` release on PyPI at or above `MIN_VERSION`, currently
0.4.0. CI tests each release against every production collection in the root
catalog the edge serves it (see "Legacy client roots" below), including
reading one value per collection. The exception is 0.4.0, which predates
virtual chunk container support: it must open every virtual dataset but isn't
asked to read one. These checks block merges through the required
`compat-required` job.

The `main` client branch is a non-blocking canary against the staging-inclusive
catalog. Pre-releases are excluded from the supported-release matrix.

Raising `MIN_VERSION` changes the support policy. Make that change in a
separate PR with the catalog owner's approval (Alden today) and a reason for
dropping older clients. Never raise the floor in the catalog PR whose
compatibility failure it would silence. A dataset requiring a newer client
either stays in staging, or is kept out of the older clients' root catalog
with `exclude_from`.

## Legacy client roots

dynamical-catalog releases through 1.0.1 parse every collection in the root
catalog before opening any dataset, so one collection a release can't read
(a `gs://` virtual chunk container, say) breaks every dataset for it. To
publish such a collection without breaking installed clients, those clients
are served their own root.

`LEGACY_CLIENT_RANGES` in `src/catalog.py` names each range of releases, e.g.
`0.4.0-0.8.0`, with the User-Agent prefix that identifies them
(`dynamical-catalog/0.`). `generate()` writes `catalog-{range}.json` beside
`catalog.json` in every tier: the same root minus the items that list the
range in `CatalogItem.exclude_from`. Collections are shared, not copied. At
the edge, a Cloudflare URL rewrite serves that file in place of `/catalog.json`
to requests whose User-Agent starts with the prefix; every other client gets
`catalog.json`. CI picks each release's root with the same prefix test
(`catalog.root_filename_for_client`), but it only models the rule: nothing here
reads the deployed one, so a wrong host, path, prefix or target at the edge
still passes this suite. Verify the live rule whenever it or a range changes.

- Set `exclude_from=("0.4.0-0.8.0",)` on an item those releases can't parse.
  For `s3_only` ranges validation requires it on any item whose repository or
  virtual chunk containers aren't `s3://`.
- Adding a range to an item those clients can already read takes the dataset
  away from them. Treat it like raising `MIN_VERSION`: its own PR, with the
  catalog owner's approval.
- A legacy root protects nobody until its file is published **and** the edge
  rule is live. Before promoting an excluded item, check that
  `curl -A dynamical-catalog/0.8.0 https://stac.dynamical.org/catalog.json`
  returns the legacy root. After such an item is in production the rule must
  stay on. To back out, move the item back to staging, wait for the production
  upload to succeed, and confirm the live `catalog.json` is readable by the
  old clients again; only then may the rule be turned off.
- The range name is a label, not parsed; it is in a published file name and
  in the edge rule, so don't rename one.
- Shared collection documents must stay parseable and openable by every range
  that links them; the compat matrix is what checks that. It also reads one
  value per collection, except that 0.4.0 can't read virtual datasets at all
  (see above), whatever their storage.
