# Score public-safe artifact prototype — 2026-10-27

Status: **review-only / not wired to production**.

Related: issue #155 and design PR #156.

This prototype proves a narrow technical point: the public Score product can retain its aggregate weekly Score and regime history without exposing the existing per-driver provider-derived z-scores, contributions, source provenance, weekly source levels or normalization moments.

## Files

- `scripts/build_score_public_safe_artifact.py`
- `tests/test_score_public_safe_artifact.py`

The converter reads the existing Score v2 JSON but emits a new aggregate-only schema containing:

- schema version;
- pipeline generation metadata;
- fixed methodology weights;
- latest week / Score / regime;
- week-over-week and four-week aggregate Score changes;
- full aggregate Score/regime history;
- SHA-256 fingerprint of the aggregate history.

The CSV output contains only:

```text
date,score,regime
```

## Explicit non-goals

This branch does not:

- alter `usd_impact_score_v2.py`;
- alter Score drivers, weights, formula, normalization or regime bands;
- replace any existing public file;
- change Cloudflare/Pages routing;
- modify weekly publication workflow;
- migrate Score v3 or predictive readers;
- delete historical artifacts;
- deploy anything.

## Guard

The prototype rejects public-safe output containing keys such as:

- `weekly_level`;
- `z`, `z_unclipped`, `z_clipped`;
- `contribution`;
- provider/source provenance;
- normalization mean/std.

Tests also assert that known Yahoo ticker strings and Yahoo provider labels are absent from the generated aggregate artifact.

## Next dependency

Before this can replace current public Score artifacts, Score v3/predictive readers must be migrated to an approved non-public evidence path and provider/counsel treatment must be decided. Until then, this prototype remains isolated review evidence only.
