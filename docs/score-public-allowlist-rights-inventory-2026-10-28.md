# Score public allowlist rights inventory — 2026-10-28

Status: **read-only classification / no route, file, deployment or Production change authorized**.

Related: issue #155, PRs #156–#159.

## Purpose

Classify every explicit public path in the Cloudflare Pages Score perimeter by the kind of information it exposes, so future rights containment can be targeted rather than removing all transparency material indiscriminately.

This is an engineering inventory, not a legal conclusion.

## Current perimeter

`security/score-public-paths.mjs` explicitly allowlists individual public paths and one dated JSON pattern:

`/archive/YYYY-MM-DD/(score|weekly_input|repro_bundle).json`

All other Score Pages paths are denied unless separately allowlisted.

A fresh anonymous origin check on 2026-10-28 confirmed that the current component/research paths identified below are actually reachable on the branded Score origin. The current Score JSON is also reachable on the legacy `pages.dev` origin.

## Classification

### Class A — aggregate / operational public material

These files do not contain the reviewed provider/component observation fields:

- `/member-required`
- `/member-required.html`
- `/robots.txt`
- `/favicon.ico`
- `/data/backtest_results.json`

Current repository inspection of `backtest_results.json` found no driver names, provider/source metadata, weekly levels, z-score fields or component contributions.

Engineering default: **retain unless counsel identifies a separate issue**.

### Class B — methodology/source-contract transparency, no provider observation series

These paths describe methodology, retrieval/source mappings, schemas or replication rules rather than publishing current/historical provider observations:

- `/data/score_v2_data_semantics.json`
- `/data/score_v2_data_semantics.schema.json`
- `/data/score_v2_methodology.json`
- `/data/score_v2_methodology.schema.json`
- `/data/research/independent_replication_protocol.json`

Observed content includes:
- USD Impact driver names and weights;
- provider/series/source URL mappings in methodology/semantics;
- normalization and missing-data rules;
- rights/retention references;
- replication workflow requirements.

The independent-replication protocol contains rules/paths/tolerances, not component observations.

Engineering default: **review wording/source-attribution separately, but do not treat these files as equivalent to provider-derived numerical redistribution**.

If strict reproduction evidence becomes private, the independent-replication claim must be narrowed because its current workflow assumes public strict evidence.

### Class C — direct component-derived public release evidence

These are the highest-priority machine-readable rights surfaces:

- `/data/usd_impact_score_v2.csv`
- `/data/usd_impact_score_v2.json`
- `/data/weekly_input_latest.json`
- `/data/score_repro_bundle_latest.json`
- dated `/archive/YYYY-MM-DD/score.json`
- dated `/archive/YYYY-MM-DD/weekly_input.json`
- dated `/archive/YYYY-MM-DD/repro_bundle.json`

Observed structure:

**Score CSV/JSON**
- full historical rows with driver-specific normalized values;
- aggregate Score/regime;
- recent JSON provenance/source metadata.

**Weekly input**
- driver name;
- z value;
- methodology weight;
- contribution;
- recent source-provenance metadata.

**Strict reproduction bundle**
- component weekly level;
- z-score and contribution fields;
- frozen normalization moments;
- source/provenance fields;
- provider/input-history fingerprints;
- aggregate published/reproduced result.

Fresh anonymous checks confirmed current and dated examples are reachable from the branded origin.

Engineering default under aggregate-only containment: **migrate strict evidence first, then replace/remove these public component fields**.

### Class D — aggregate research with provider provenance

`/data/research/score_v2_point_in_time_latest.json`

Observed structure:
- aggregate point-in-time vs full-sample Score/regime histories;
- aggregate differences and anchor-window statistics;
- current provider/source-provenance metadata by driver;
- no direct per-driver weekly observation series in the reviewed payload shape.

This is less exposed than Class C, but still carries provider/source metadata and is generated from the component histories.

Engineering default: **rights-review separately; if conservative containment is selected, retain aggregate study results but remove/narrow provider provenance unless specifically approved**.

### Class E — component-derived diagnostic research

`/data/research/score_v2_robustness_latest.json`

Observed component-derived structures include:
- leave-one-driver-out diagnostics;
- sign-sensitivity diagnostics;
- driver-pair correlation concentration;
- rolling component correlations;
- contribution concentration;
- dominant-driver/contribution statistics;
- current source provenance.

These are transformed diagnostics rather than raw levels, but they are explicitly driver/component-derived.

Engineering default: **do not assume aggregate-safe treatment; include in provider/counsel derived-data decision**.

### Class F — component revision research

- `/data/research/score_v2_vintage_comparison_latest.csv`
- `/data/research/score_v2_vintage_comparison_latest.json`
- `/data/research/score_v2_vintage_comparison_latest.html`
- clean URL `/data/research/score_v2_vintage_comparison_latest`

Observed structures include:
- per-driver z-score differences/revisions;
- largest component revision;
- component revision summaries;
- aggregate vintage Score/regime differences.

Fresh anonymous checks confirmed the CSV, JSON and HTML/clean-URL presentation are reachable.

Engineering default: **treat as component-derived evidence requiring the same derived-data review as Class E**.

## Live anonymous verification

Fresh 2026-10-28 anonymous requests succeeded for:

- current Score CSV/JSON;
- current weekly-input JSON;
- current strict reproduction bundle;
- current point-in-time research JSON;
- current robustness research JSON;
- vintage-comparison CSV/JSON/HTML;
- methodology JSON;
- data-semantics JSON;
- dated 2026-10-23 Score/weekly-input/reproduction JSON.

By contrast, current and dated EN/ES dashboard/archive HTML routes returned HTTP 403 at both branded and legacy origins. Those protected HTML files are therefore a repository/history review concern, not the verified current anonymous serving surface.

## Proposed containment priority

If aggregate-only public treatment is approved:

1. **Class C first** — direct component release evidence.
2. **Class E/F next** — component-derived research diagnostics/revision outputs.
3. **Class D** — preserve aggregate research where feasible, remove/narrow provenance if required.
4. **Class B** — preserve methodology transparency unless provider/counsel specifically requires narrower provider/source naming.
5. **Class A** — retain.

This sequence avoids an overbroad “delete everything Score-related” response.

## Required dependency review before changing Class E/F

Research outputs are generated from current/public component histories and archived vintages.

Before removing them:
- identify generation scripts and tests;
- decide whether the research itself remains publishable in aggregate form;
- migrate any required strict/private evidence inputs;
- revise independent-replication statements;
- preserve frozen/preregistered research semantics;
- run exact-head research and quality checks.

Do not silently stop or rewrite preregistered research because of a delivery-layer rights migration.

## No-action record

This inventory used:
- the current public-path allowlist;
- repository file structures;
- fresh anonymous origin fetches.

No allowlist, route, data file, research output, archive, cache, deployment, credential or Production configuration was changed.
