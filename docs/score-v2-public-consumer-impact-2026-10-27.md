# Score v2 public-consumer impact map — 2026-10-27

Status: **review-only companion to #155 / #156**.

## Finding

The current USD Impact website does **not** require public per-driver Score values to render the main Score product.

The main page `apps/web/src/pages/score.astro` renders educational/product copy and routes verified members to the protected member dashboard. Its public pipeline dependency is the historical vintage-audit link, not the component-level weekly bridge.

## Direct website links that would need migration

The public methodology page currently links directly to:

- `/data/weekly_input_latest.json` as "Latest decomposition JSON";
- `/data/usd_impact_score_v2.json` as "Full score JSON";
- `/data/usd_impact_score_v2.csv` as "Full score CSV";
- current robustness / point-in-time / vintage-comparison research artifacts;
- methodology / semantics artifacts.

The first three currently expose provider-derived component values or transformations and are the primary website-facing migration points for a future aggregate-only public schema.

The methodology prose also explicitly names current Yahoo tickers and explains source-treatment details. Whether that descriptive source identification may remain public is a separate provider/counsel decision from redistribution of numeric values.

## Runtime dependency result

Search of `usdimpact/usd-impact-site` found no runtime fetch of:

- `score_repro_bundle_latest.json`;
- public per-driver CSV rows;
- public component decomposition for rendering the main `/score/` page.

The helper `scorePipelineArchiveUrl()` still constructs dated `/archive/YYYY-MM-DD/weekly_input.json` URLs, but current source search finds no production call site outside its own tests. Treat it as legacy API surface to remove or repoint during the eventual containment release rather than as a current rendering dependency.

## Pipeline consumers that are not website UI

The larger dependency surface is inside `usdimpact/usd-impact-pipeline`:

- weekly preflight / release validation;
- independent-replication protocol and post-merge attestation;
- Score v2 predictive ingestion;
- Score v3 shadow ingestion;
- vintage/robustness research;
- public-path allowlists and archive generation.

Those consumers must be separated into:
1. **public aggregate product evidence**, and
2. **private/internal strict calculation evidence**.

## Future website migration checklist

Only after #155 rights/controller decisions and the internal evidence path are resolved:

1. publish a versioned aggregate-only JSON/CSV route;
2. update `/score/methodology/` artifact cards to the aggregate-safe routes;
3. accurately narrow reproduction language;
4. remove or repoint the unused `weekly_input.json` archive helper;
5. keep methodology/weights/regime-band documentation public;
6. decide whether exact provider/ticker names remain permissible descriptive attribution;
7. test that `/score/` and protected member dashboards are unchanged;
8. verify no public link exposes the private strict bundle.

No website change is authorized by this document.
