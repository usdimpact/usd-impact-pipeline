# Score public-safe research prototype — 2026-10-28

Status: **review-only / not wired into Production, research generation, or public routing**.

Related: issue #155, PRs #156 and #157.

## Goal

Prove that the existing Score research engines can remain unchanged while a separate publication transformer emits narrower aggregate-only research artifacts.

The transformer consumes research results **after** the frozen/preregistered calculations complete. It does not:
- refetch provider data;
- alter research inputs;
- change methodology;
- change preregistration;
- change workflow triggers;
- rewrite historical research records.

## Prototype

`scripts/build_score_public_safe_research.py`

It emits review-only replacements for three current public research families.

### Point-in-time study

Preserved:
- aggregate point-in-time/full-sample Score and regime history;
- aggregate differences;
- anchor-window aggregate statistics;
- study metadata/limitations.

Removed:
- current driver/provider source-provenance object.

### Robustness study

Preserved aggregate diagnostics:
- point-in-time normalization;
- rolling normalization;
- regime-threshold sensitivity;
- aggregate Score distribution;
- regime duration;
- subperiod stability;
- top-level aggregate Score/regime metadata.

Removed component-derived diagnostics:
- leave-one-driver-out;
- sign-sensitivity by driver;
- component/pair correlation concentration;
- rolling component correlations;
- contribution concentration/dominant-driver outputs;
- provider source provenance.

This intentionally favors a conservative aggregate publication surface over maximum diagnostic transparency.

### Vintage comparison

Preserved:
- aggregate as-published vs current Score;
- aggregate Score difference;
- aggregate regimes and regime/sign agreement;
- archive/week/timestamp identifiers;
- aggregate revision summary.

Removed:
- per-driver z-score revision summaries;
- per-vintage component z-score revisions;
- largest-revision driver/component fields;
- source archive paths.

The prototype also renders aggregate-only CSV and HTML forms so all currently allowlisted vintage-comparison formats have a rights-safe candidate.

## Guard

`assert_aggregate_safe()` rejects reintroduction of keys including:
- provider/source provenance;
- driver/component containers;
- weekly levels;
- z/contribution fields;
- omitted/flipped/dominant driver fields;
- component revision structures;
- source archive paths.

Tests use the current research outputs as fixtures and prove the transformer does not change the number of aggregate study/vintage rows.

## Important limitation

“Aggregate-only” is an engineering containment label, not a legal conclusion.

Provider/counsel review still decides whether:
- aggregate Score histories;
- aggregate research statistics;
- transformed diagnostics;
- provider/source naming in separate methodology documents

may remain public.

## Migration sequence if approved

1. rights disposition;
2. private strict-evidence boundary;
3. prove frozen research output equivalence;
4. generate aggregate-safe research outputs in review;
5. compare aggregate values/row counts to existing research;
6. update public-path allowlist and links only in a separate reviewed change;
7. exact-head quality/security review;
8. separate Production authorization.

The transformer must never be wired as a shortcut around issue #155.

## No-action record

No research engine, preregistration, workflow, allowlist, public file, archive, deployment or Production configuration was changed by this prototype.
