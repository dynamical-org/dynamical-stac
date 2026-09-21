# dynamical-stac

## Regenerating the committed catalogs after catalog changes

Every published environment is committed, so a change to any of them shows up as a
diff in review and each upload workflow ships exactly the tree that was merged:

| directory | host | contains |
|---|---|---|
| `stac/` | stac.dynamical.org | items listing `production` |
| `stac-staging/` | stac-staging.dynamical.org | items listing `staging` |
| `stac-test/` | stac-test.dynamical.org | items listing `test` |

Any edit to `src/catalog.py` or `src/prose/**` that changes the rendered STAC
(new `CatalogItem`, description/prose edits, model metadata, etc.) requires
regenerating them:

```
./scripts/generate
```

then commit the resulting changes under `stac/`, `stac-staging/` and
`stac-test/`. `tests/test_stac_drift.py` (integration mark) fails in CI if any
of them is stale, and names the environment.

Regeneration opens every dataset's Icechunk store once (production, staging and
the GCS/Azure test fixtures), so it needs network access and takes ~20s. The
trees are built aside and swapped in together: if any store fails to open, none
of them changes. It ignores `STAC_ROOT_HREF`. To build one environment elsewhere,
use `uv run python src/__main__.py generate --output DIR --environment staging`
(production by default). Single-environment generation honours `STAC_ROOT_HREF`
as an optional host override. The old `STAC_INCLUDE_STAGING` / `STAC_INCLUDE_TEST`
flags have been replaced by `--environment`.

`STAC_ENVIRONMENTS` in `src/environments.py` defines each publication's name,
directory and host using the Pydantic `StacEnvironment` model. Each `CatalogItem`
must declare a nonempty `environments` list of registered environment names; unknown and duplicate names are
rejected. Pydantic stores it as a tuple to preserve the model's immutability. No environment implies membership in another. Released datasets
explicitly list `production`, `staging`, and `test`, plus each supported legacy
environment (see below). A separate test
checks both item definitions and committed roots, requiring production
collections to appear in staging and staging collections to appear in test; this publication policy does not add implicit membership.

**Always run `./scripts/generate` before every commit that touches anything
under `src/`, then `git add stac/ stac-staging/ stac-test/` before
committing.** Skipping this step ships a stale catalog and breaks
`test_stac_drift.py` in CI.

The trees describe the catalogs we publish, not everything in the buckets:
uploads never delete, so a collection removed from an environment stays in R2,
unlinked, until someone deletes it.

## Adding a new `CatalogItem`

Adding a new dataset typically requires all of:

- A `CatalogItem` entry in `src/catalog.py` with an explicit `environments` list.
- A matching `Model` entry in `MODELS` (if the `model_id` is new).
- A prose file at `src/prose/datasets/{id}.md` — `description_details` loads
  this lazily, so omissions won't trip validation but will 500 at render time.
- A matching notebook at
  `https://github.com/dynamical-org/notebooks/blob/main/{slug}.ipynb` for each
  `DatasetNotebook.slug` on the item — `tests/test_catalog_read.py::test_notebook_url_exists`
  asserts HTTP 200. The Quickstart notebook's slug must equal the dataset
  `id` (enforced by `CatalogItem._quickstart_slug_matches_id`). Production
  items must declare at least one notebook (enforced by
  `CatalogItem._production_items_have_notebooks`); only items outside production may
  leave `notebooks` empty.
- Regenerated `stac/` output (see above).

## Staging datasets

Set `environments=["staging", "test"]` on an unreleased `CatalogItem` to publish
it to staging and test. It stays out of production and the committed `stac/`
tree. Include `"test"` explicitly to satisfy the publication membership policy.
`upload-stac-staging.yml` uploads the committed `stac-staging/` tree to the
`stac-staging` bucket whenever it changes on `main`; it does not regenerate, so
a staging store's new metadata reaches the staging catalog only through a
committed regeneration. Add `"production"` to the list and merge to release the
dataset to production.

A staging dataset still needs its prose file, but its notebook is optional: a
staging item may omit `notebooks` entirely (its collection then carries no
`example` links) until the notebook is written. Any notebook it *does* declare
is still HEADed for a 200 by `test_notebook_url_exists`, and adding
`"production"` to `environments` fails validation until at least one notebook is present.
`./scripts/generate` writes them into `stac-staging/`, where the diff shows
exactly what the staging catalog will serve.

dynamical.org Cloudflare PR previews build against `stac-staging`, so a staging
dataset appears in website previews while staying hidden from the live site —
once its PR here has merged and uploaded; a preview built before that needs
rebuilding.

## Test datasets

The test environment is published at `stac-test.dynamical.org` (R2
bucket `stac-test`). Its current membership includes all weather datasets plus
synthetic fixtures because each explicitly lists `"test"`. The fixtures exist so
[dynamical-catalog](https://github.com/dynamical-org/dynamical-catalog)'s
integration tests can read real generator output; they are not weather data.

Set `environments=["test"]` to publish a dataset only to the test catalog.
These items never reach staging or production: they're
left out of `stac/`, `stac-staging/` and `catalog._COLLECTION_IDS` (so this
repo's own read/browse integration tests skip them) and appear only in the
committed `stac-test/` tree, which `upload-stac-test.yml` uploads to the
`stac-test` bucket whenever it changes on `main`.

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
0.4.0. CI tests each release against every collection explicitly assigned to its
production environment, including
reading one value per collection. These checks block merges through the
required `compat-required` job.

The `main` client branch is a non-blocking canary against the staging-inclusive
catalog. Pre-releases are excluded from the supported-release matrix.

Raising `MIN_VERSION` changes the support policy. Make that change in a
separate PR with the catalog owner's approval (Alden today) and a reason for
dropping older clients. Never raise the floor in the catalog PR whose
compatibility failure it would silence. A dataset requiring a newer client
stays in staging until the floor is raised separately or the store is made
readable by the oldest supported release.


## Legacy client environments

The same `STAC_ENVIRONMENTS` registry includes two production-only publications:

| environment | root on stac.dynamical.org | capability guidance |
|---|---|---|
| `0.4.0-0.4.0` | `catalog_0.4.0-0.4.0.json` | S3 repositories; no virtual Icechunk Zarr datasets |
| `0.5.0-0.8.0` | `catalog_0.5.0-0.8.0.json` | S3 repositories; virtual source files must all be on S3 |

`ClientVersionRange` has explicit inclusive `min_version` and `max_version`
bounds, normalized and compared with `packaging.version.Version`. Its name and
root filename are generated from those bounds. Overlapping ranges and duplicate
publication names/paths are rejected. Capability descriptions guide authors and
agents; they do not infer membership or enforce storage restrictions. The
compatibility matrix installs each supported client and opens and reads every
collection in its selected environment, including 0.4.0 (no open-only exception).

Add the appropriate range name explicitly to each supported production item's
`environments` list. The legacy environments must be subsets of production;
staging-only and fixture datasets must not be included. Current 0.4.0 membership
excludes virtual datasets; current 0.5.0–0.8.0 membership includes all 19 production
collections. Adding a new production dataset does not add it to either legacy
root automatically.

These are extra top-level roots in `stac/`, sharing the existing production
collection documents. No versioned roots are generated in `stac-staging/` or
`stac-test/`. The normal roots and collection JSON remain unchanged. The uploader
writes collection documents before any top-level root so a new root never
links to a collection that has not been uploaded yet.

`generate --output DIR --environment 0.4.0-0.4.0` writes just that root, linking
canonical production collections. All-environment generation loads stores once
and swaps each publication directory only once, even when multiple environments
share it.

No edge routing is changed here. Serving an old client's request for
`/catalog.json` from its versioned root still requires a separate routing change.
The compatibility matrix models the intended numeric routing; it does not
validate the live edge. Confirm the published roots and routing before promoting
a collection older clients cannot parse. Removing a collection from a supported
legacy environment changes its compatibility contract and needs the same review
as raising the client support floor.
