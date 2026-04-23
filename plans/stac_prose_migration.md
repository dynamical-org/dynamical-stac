# Move catalog prose into STAC

## Context

Today the dynamical.org 11ty site (`_data/catalog.js`) is the source of truth for the marketing prose that the catalog page renders: per-dataset description summaries, the Construction/Source/Storage/Compression/Deprecated sections, the "opening" Python code snippet, per-dataset licensing blurb, and the model-level paragraph that introduces GFS/GEFS/HRRR/IFS. STAC currently provides only structural metadata (dimensions, variables, spatial/temporal extents, attribution, summaries).

We want STAC to contain **all** information needed to render the catalog, so consumers who talk to `stac.dynamical.org` (LLMs, other clients) see the same story the website tells. This PR moves the prose and the code-snippet example into STAC as structured fields, adds a `model_id` on each Collection so datasets group naturally, and leaves the 11ty build output byte-compatible (modulo unavoidable whitespace) with what it produces today.

Scope boundary: dataset `status`, the `CC_BY_4` rendered license blurb, and the rendered `url` (https Zarr endpoint) stay in 11ty for this change — they are visual/rendering-specific or already trivially derivable. **Glyphs are removed entirely** — not moved to STAC, not kept in 11ty, no SVG icon appears next to model names on the catalog list or detail pages. The STAC `description` field stays sourced from `ds.attrs["description"]` (unchanged) — this avoids creating a second source of truth that would diverge from the Icechunk/AWS/Earthmover artifacts. Only *new* fields — which Icechunk never carried — are authored in `dynamical-stac`.

## Affected repos

- `~/workspace/dynamical-org/dynamical-stac` — author new fields, emit them on every Collection JSON
- `~/workspace/dynamical-org/dynamical.org` — consume new fields in `_data/catalog.js`; three downstream 11ty consumers all read from this same data:
  1. The website catalog pages (`content/catalog.njk`, `content/catalog-pages.njk`) → HTML at `dynamical.org/catalog/...`
  2. The Earthmover README generator (`content/earthmover-readmes.njk`) → markdown at `earthmover/{dataset_id}.md` (published to the Earthmover / Arraylake catalog)
  3. The AWS Open Data Registry generator (`content/aws-open-data-registry.njk`) → YAML at `aws/dynamical-{model_id}.yaml` (submitted as PRs to `awslabs/open-data-registry`)

All three consumers share one data plane (`_data/catalog.js`), which is now fully fed by STAC. A STAC field change propagates to all three outputs in one build.

Two PRs, landed in order: STAC first (deployed to `stac.dynamical.org`), then 11ty.

## Target field inventory (STAC Collection JSON)

New top-level extra fields emitted by `to_pystac_collection`:

| Field | Type | Source |
|---|---|---|
| `model_id` | string (`"noaa-gfs"`, `"noaa-gefs"`, `"noaa-hrrr"`, `"noaa-mrms"`, `"ecmwf-aifs-single"`, `"ecmwf-ifs-ens"`) | `CatalogItem.model_id` |
| `model_name` | string (e.g. `"NOAA GFS"`) | `MODELS[item.model_id].name` |
| `description_summary` | markdown string | `CatalogItem.description_summary` |
| `description_details` | markdown string (with `### Construction`, `### Source`, `### Storage`, `### Compression`, `### Related dataset` sections) | `CatalogItem.description_details` |
| `description_model` | markdown string | `MODELS[item.model_id].description` |
| `examples` | `[{title: string, code: string, language: "python"}]` | `CatalogItem.examples` |

The existing `description` field on the Collection is unchanged — it continues to come from `ds.attrs["description"]`, so the Icechunk store, STAC Collection, and any consumer reading via xarray all see the same canonical description string. No new authoring path for `description`.

All new fields are snake_case, matching STAC's existing style (`cube:dimensions`, `cube:variables`, and the existing `attribution`, `version` extras). No camelCase.

## Implementation — dynamical-stac

**`src/catalog.py`** — `CatalogItem` gains prose fields and a `model_id`.

```python
class DatasetExample(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")
    title: str = Field(min_length=1)
    code: str = Field(min_length=1)
    language: Literal["python"] = "python"

class CatalogItem(BaseModel):
    # existing fields: id, icechunk_href, icechunk_region, additional_terms
    model_id: str = Field(min_length=1)                  # NEW
    description_summary: str = Field(min_length=1)       # NEW, markdown
    description_details: str = Field(min_length=1)       # NEW, markdown
    examples: tuple[DatasetExample, ...] = Field(min_length=1)  # NEW
```

**`src/models.py`** — add a Model registry.

```python
class Model(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")
    id: str = Field(min_length=1)           # "noaa-gfs"
    name: str = Field(min_length=1)         # "NOAA GFS"
    description: str = Field(min_length=1)  # markdown, canonical prose

MODELS: dict[str, Model] = {
    "noaa-gfs":          Model(id="noaa-gfs",  name="NOAA GFS",          description="..."),
    "noaa-gefs":         Model(id="noaa-gefs", name="NOAA GEFS",         description="..."),
    "noaa-hrrr":         Model(id="noaa-hrrr", name="NOAA HRRR",         description="..."),
    "noaa-mrms":         Model(id="noaa-mrms", name="NOAA MRMS",         description="..."),
    "ecmwf-aifs-single": Model(id="ecmwf-aifs-single", name="ECMWF AIFS single",
                               description="..."),
    "ecmwf-ifs-ens":     Model(id="ecmwf-ifs-ens",     name="ECMWF IFS ensemble",
                               description="..."),
}
```

Validator on `CatalogItem`: `model_id` must be a key in `MODELS`.

**`src/models.py` — `CollectionInput`:**

- Add fields: `model_id`, `model_name`, `description_summary`, `description_details`, `description_model`, `examples`.
- `description` stays unchanged — still `ds.attrs["description"]`. Attribution, license, version, summary attrs also unchanged.
- In `from_dataset(item, ds)`: populate the new fields from `item` and `MODELS[item.model_id]` (name, description).
- In `to_pystac_collection`: add
  ```python
  collection.extra_fields["model_id"] = self.model_id
  collection.extra_fields["model_name"] = self.model_name
  collection.extra_fields["description_summary"] = self.description_summary
  collection.extra_fields["description_details"] = self.description_details
  collection.extra_fields["description_model"] = self.description_model
  collection.extra_fields["examples"] = [e.model_dump() for e in self.examples]
  ```

**Data entry** — populate prose for all 9 existing `CATALOG_ITEMS` (`catalog.py` lines 53-101) by porting from `dynamical.org/_data/catalog.js`:

- `description_summary`: port `entry.description_summary`, convert the HTML-with-`<p>`/`<code>` to markdown. The paragraphs are 1-3 sentences each; hand-convert rather than relying on a regex — sections are short and there are only 9.
- `description_details`: port `entry.description_details`, map `<h3>Construction</h3>` → `### Construction`, etc. Keep `###` so markdown-it emits `<h3>` matching the current output.
- `examples`: port `entry.examples` (title + code string) directly.
- `model_id`: port `entry.modelId`.

Model-level descriptions: port the 6 `<p>…</p>` blocks from `models` dict in `_data/catalog.js` (lines 126-228 area) to markdown.

**Verification (STAC side):**

```bash
cd ~/workspace/dynamical-org/dynamical-stac
uv run ruff check . && uv run ruff format --check .
uv run pytest                                    # if tests exist for CollectionInput
uv run stac-cli generate --output /tmp/stac      # or whatever the entry point is
jq '.model_id,.description_summary,.description_details,.description_model,.examples[0]' \
   /tmp/stac/noaa-gfs-analysis/collection.json
```

Expect all 5 new fields present and rendering as expected markdown/structured data. Run `catalog.validate_all()` via the generator — already does this.

## Implementation — dynamical.org

**Add a markdown filter.** No markdown→HTML renderer exists in the repo today (`htmlToMarkdown` in `_data/catalog.js` only goes the other direction). Add `markdown-it` to `package.json` dependencies and register in `.eleventy.js`:

```js
const md = require("markdown-it")({ html: true });  // html: true so inline <a>/<code> authored in markdown passes through
eleventyConfig.addFilter("markdown", (s) => s ? md.render(s) : "");
```

**`_data/catalog.js` — strip everything model-specific.** Delete:

- `pixelArt()` helper + all `GLYPH_*` constants (lines 9-123).
- `models` dict (lines 126-228 area — every model definition block). **No JS-side model registry remains.** Model name and description now arrive on each `entry` from STAC (`entry.model_name`, `entry.description_model`, `entry.model_id`); glyphs are gone entirely.
- Per-entry fields: `modelId`, `description_summary`, `description_details`, `examples`. Keep: `url`, `status`, `license`, `hide`.
- `htmlToMarkdown` function + the `entries.forEach(entry => { ... description_detailsMd ... })` pre-processing (lines 970-1026). Now redundant — STAC serves markdown directly.

**Update `reshapeStacCollection`** (catalog.js line 1097) to also extract:

```js
model_id: collection.model_id,
model_name: collection.model_name,
description_summary: collection.description_summary,
description_details: collection.description_details,
description_model: collection.description_model,
examples: collection.examples,
```

The `entry.name` / `entry.dataset_id` / `entry.description` / variables / dimensions mapping is unchanged.

**Update the model-grouping pass** (catalog.js lines 1050-1077): build `modelGroups` from the STAC fields that are already on each entry — the first entry for a given `model_id` contributes `model_name` and `description_model` to the group object:

```js
const modelGroups = {};
entries.forEach((entry) => {
  if (!entry.model_id) return;
  if (!modelGroups[entry.model_id]) {
    modelGroups[entry.model_id] = {
      id: entry.model_id,
      name: entry.model_name,
      description: entry.description_model,
      datasets: [],
    };
  }
  modelGroups[entry.model_id].datasets.push(entry);
});
```

No per-model JS data is defined anywhere — 11ty is a pure renderer over STAC.

**`content/catalog-pages.njk`** — markdown renders + model-field sourcing + glyph removal:

- Line 35 (`{%- set model = catalog.models | find('id', entry.modelId) %}`): change lookup key to `entry.model_id`.
- Line 42: remove the glyph span entirely — `<h1 style="display: flex; align-items: center;">{% if model.glyph %}<span class="catalog-glyph">{{ model.glyph | safe }}</span>{% endif %}{{ entry.name }}</h1>` → `<h1>{{ entry.name }}</h1>`.
- Line 80: `{{ model.description | safe }}` → `{{ entry.description_model | markdown | safe }}`
- Line 82: `{{ entry.description_summary | safe }}` → `{{ entry.description_summary | markdown | safe }}`
- Line 194: `{{ model.name }}` — already works (model object still exposes `name`, now sourced from STAC).
- Line 198: `{{ entry.description_details | safe }}` → `{{ entry.description_details | markdown | safe }}`
- Examples block (lines 121-129): unchanged — `example.title` + `example.code | highlight('py', ...)` works identically whether examples come from 11ty or STAC.

**`content/catalog.njk`** — remove glyph span on line 31: `<span class="catalog-glyph">{{ model.glyph | safe }}</span>{{ model.name }}` → `{{ model.name }}`. Everything else unchanged (uses `model.name`, `entry.status`, `entry.spatial_resolution`, `entry.spatial_domain`, `entry.dataset_id`, `entry.name`).

**CSS cleanup**: the `.catalog-glyph` class is no longer rendered. Grep the CSS files and remove the dangling rule if it exists (otherwise leave — it's zero-render cost).

**`content/earthmover-readmes.njk`** (markdown output, per-dataset) — edits to match the new data shape:

- Line 10 (`{%- set model = catalog.models | find('id', entry.modelId) -%}`): change lookup to `entry.model_id`.
- Line 25 (`{{ model.description | striptags }}`): model.description is now markdown from STAC — emit as-is for markdown output. Simplify to `{{ entry.description_model }}` (no striptags needed; markdown has no tags).
- Line 27 (`{{ entry.description_summary | striptags }}`): `{{ entry.description_summary }}` (same reasoning).
- Line 63 (`{{ entry.licenseMd }}`): `licenseMd` is derived from the dropped `htmlToMarkdown(entry.license)` helper. Replace with an inline markdown string: `_Licensed under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/)._`
- Line 72 (`{{ entry.description_detailsMd }}`): `description_detailsMd` is also gone. Replace with `{{ entry.description_details }}` — STAC now serves markdown directly, which is exactly what the markdown output wants.
- Every other field (`entry.description`, `entry.spatial_domain`, dimensions, variables, attribution, `githubUrl`, `colabUrl`) is unchanged.

**`content/aws-open-data-registry.njk`** (YAML output, per-model) — edits to preserve HTML-in-YAML formatting:

- Line 12 (`{{ model.description | safe | trim }}`): `model.description` is now markdown from STAC but the ODR YAML embeds an HTML-formatted block scalar (mixed with authored `<p>` / `<ul>` below). Render markdown → HTML here: `{{ model.description | markdown | safe | trim }}`.
- Line 17 (`{{ entry.description | safe }}`): `entry.description` continues to come from `ds.attrs["description"]` (a plain string — unchanged). `| safe` remains a no-op here.
- All other fields (`model.id`, `model.name`, `model.datasets`, `entry.dataset_id`, `entry.name`, `entry.time_resolution`, `entry.githubUrl`) are unchanged.

## Output-preservation check

Source of whitespace differences to watch for:

1. markdown-it adds a trailing `\n` after `<p>…</p>` that the raw HTML in `_data/catalog.js` doesn't. Browser rendering is identical, but byte-diff will be noisy. Acceptable.
2. Section headers: current HTML uses `<h3>`; `## Section` in markdown renders as `<h2>`. **This would be a visible difference.** Fix: author `description_details` sections as `### Section` (three hashes) so markdown-it emits `<h3>` matching today. Same applies to `description_model` if it contains headers (today it doesn't — just `<p>`).
3. `<code>foo</code>` inline in summaries: port as backtick-code `` `foo` ``; markdown-it renders it back to `<code>foo</code>`. Identical.

## Files to touch

- `dynamical-stac/src/catalog.py` — add Model import/registry, extend CatalogItem, populate all 9 items with prose
- `dynamical-stac/src/models.py` — `Model` class, `CollectionInput` new fields, `from_dataset` wiring, `to_pystac_collection` emission
- `dynamical-stac/tests/` — extend existing tests (if any) for new required fields
- `dynamical.org/package.json` — add `markdown-it` dependency
- `dynamical.org/.eleventy.js` — register `markdown` filter
- `dynamical.org/_data/catalog.js` — delete `pixelArt`, `GLYPH_*`, `models` dict, per-entry prose, `htmlToMarkdown`; update `reshapeStacCollection` and model grouping
- `dynamical.org/content/catalog-pages.njk` — swap 3 `| safe` usages for `| markdown | safe`; remove glyph span; swap `modelId` → `model_id` in model lookup
- `dynamical.org/content/catalog.njk` — remove glyph span
- `dynamical.org/content/earthmover-readmes.njk` — swap `modelId` → `model_id`; use `description_details`/`description_summary`/`description_model` directly as markdown; inline license blurb
- `dynamical.org/content/aws-open-data-registry.njk` — pipe `model.description` through `markdown` filter to preserve HTML-in-YAML output

## Verification end-to-end

1. Run the STAC generator locally, save output to a scratch dir, copy one Collection JSON into a fixture and point 11ty at the local STAC (or deploy STAC first, then build 11ty against production STAC).
2. `npm run build` in `dynamical.org`. Snapshot-diff against a baseline captured before the change:
   - `docs/catalog/index.html` + each `docs/catalog/<slug>/index.html` (website pages)
   - `docs/earthmover/<slug>.md` (Earthmover readmes — one per dataset with a notebook)
   - `docs/aws/dynamical-<model_id>.yaml` (AWS ODR YAMLs — one per model)
   Expected deltas: glyph `<span>` removed, markdown-it whitespace noise (trailing newlines, normalized `<p>` indentation) on HTML; for Earthmover markdown files, content should be identical modulo the inlined license line. AWS ODR YAML should diff-clean once the `| markdown` filter is in place.
3. `npm start`, open `http://localhost:8081/catalog/` and spot-check: GFS analysis page (has Construction/Source/Storage/Compression + Related dataset), GEFS analysis page (has the most complex description_details with lists + multiple h3), HRRR forecast page (spans two paragraphs in description_summary), ECMWF IFS-ENS page (different model prose).
4. Model intro paragraph renders for each of the 6 models on their respective pages.
5. Example code block still syntax-highlights and lives inside a `.frame` container.
6. Open one generated Earthmover readme and one AWS ODR YAML; confirm they render correctly in a markdown previewer and pass a YAML linter respectively.

## Rollout ordering

1. Land STAC PR. Deploy. Verify `curl https://stac.dynamical.org/noaa-gfs-analysis/collection.json | jq .model_id` returns `"noaa-gfs"` and the prose fields are present.
2. Land 11ty PR. Cloudflare Pages rebuild against new STAC.

If the 11ty PR lands first, pages lose the description and details sections. Order matters; no feature flag needed since the STAC deploy is a strict superset.

## Plan-file location

This plan is drafted at `~/.claude/plans/we-want-the-stac-crispy-petal.md` per plan-mode requirement. On exit, per the user's `CLAUDE.md` convention, it will move to `~/workspace/dynamical-org/dynamical-stac/plans/{PR#}_stac_prose_migration.md` (STAC PR is the first-ordered work) and/or a mirrored file in `dynamical.org/plans/` for the companion PR.
