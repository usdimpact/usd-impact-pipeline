# Score historical public archive rights inventory and treatment matrix — 2026-10-28

Status: **read-only inventory / no deletion, rewrite, purge or Production change authorized**.

Related: issue #155, PRs #156–#159.

## Superseding current-Git-tree checkpoint (2026-10-29; metadata only)

The original October 28 "24 Score vintages" figure below was derived from the **23-date EN/ES historical index plus the current October 23 edition**, not an exhaustive list of the repository's dated archive directories. Subsequent full current-tree `contents` enumeration found **27** dated directories, including the three unindexed prior dates `2026-05-02`, `2026-05-09` and `2026-05-16`. The current edition `2026-10-23` is not in the prior-history index by design of that snapshot; do not conflate the three unindexed older dates with it.

The current Git tree includes **27** dated `score.json`, **14** dated `weekly_input.json` and **9** dated `repro_bundle.json` (**50 dated Class C files**), plus **4** latest-root Class C data files. The Git-only `data/weekly_input_*.json` family has **15** files. These are path/size metadata counts, not assertions about which underlying observations or copyrighted fields each file contains.

The updated current-tree manifest, offline path-only regression and lawful preservation gates are in `governance/score-current-tree-exposure-inventory-2026-10-29.json`, `tests/test_score_current_tree_exposure_inventory.py` and `docs/score-public-archive-metadata-preservation-2026-10-29.md`. The latter also records a complete **1,921-record** metadata listing of Cloudflare Pages deployments; **no implication that every deployment serves a publicly accessible provider-data file**.

**Preserve the original October 28 index-based snapshot below as historical evidence.** Do not delete, reindex, rewrite Git history, change Pages routing or copy provider data based on this census. Provider/counsel and Production authorizations under Issue #155 remain absent.

## Purpose

Document the currently public historical Score surfaces that would require treatment if provider/counsel review concludes that public component-level Score evidence must be removed or narrowed.

This document does not decide that removal is legally required.

## Snapshot

The public archive index currently exposes **23 prior weekly editions** from 2026-04-10 through 2026-10-16.

The current 2026-10-23 edition also exists in the dated archive and is duplicated at the current public paths.

Therefore the current served tree represents **24 Score vintages**.

## Exposure classes

### 1. Archived/current Score JSON

All 23 indexed prior editions contain:

- `public/archive/YYYY-MM-DD/score.json`;
- weekly rows with per-driver fields for DXY, WTI, SPX, VIX, BTC, GOLD, UST_2Y and UST_10Y;
- aggregate Score and regime.

The current 2026-10-23 edition has the same component-row structure at:

- `public/archive/2026-10-23/score.json`;
- `public/data/usd_impact_score_v2.json`.

Recent Score JSON also includes source-provenance metadata.

Inventory:
- **24 unique weekly vintages** with component-level Score JSON;
- **25 currently served file paths** when the current-vintage duplicate is included.

### 2. Weekly input JSON

`weekly_input.json` exists for 13 prior indexed editions from 2026-07-24 through 2026-10-16.

The current 2026-10-23 edition exists at:
- `public/archive/2026-10-23/weekly_input.json`;
- `public/data/weekly_input_latest.json`.

Each inspected weekly-input driver entry contains:
- driver name;
- z value;
- weight;
- contribution.

From 2026-08-14 onward the inspected weekly-input artifacts also contain source-provenance metadata.

Inventory:
- **14 unique weekly vintages** with public driver-level weekly-input JSON;
- **15 currently served file paths** including the current duplicate.

### 3. Strict reproduction bundles

Strict `repro_bundle.json` files are present for the prior indexed weeks:

- 2026-08-28;
- 2026-09-04;
- 2026-09-11;
- 2026-09-18;
- 2026-09-25;
- 2026-10-02;
- 2026-10-09;
- 2026-10-16.

The current 2026-10-23 strict bundle is present at:
- `public/archive/2026-10-23/repro_bundle.json`;
- `public/data/score_repro_bundle_latest.json`.

The strict bundle contains component weekly levels, frozen normalization data, provenance/fingerprint material and the published/reproduced aggregate result.

Inventory:
- **9 unique strict-bundle vintages**;
- **10 currently served strict-bundle file paths** including the current duplicate.

No strict reproduction bundle was found in the indexed archive for 2026-08-21 or earlier.

### 4. Rendered HTML

Each indexed prior edition has English and Spanish archive HTML files in the repository. The current edition also has dated English/Spanish HTML plus current English/Spanish dashboard files.

Repository-file inspection confirms those HTML files contain driver-level analytical presentation.

However, a fresh read-only origin check on 2026-10-28 found that both approved public Score origins currently return **HTTP 403** for:
- current `/en/` and `/es/` dashboard paths;
- dated `/archive/2026-10-23/en.html` and `/archive/2026-10-23/es.html`;
- archive index HTML paths.

Therefore these HTML files are **present in the public Git repository but are not currently served anonymously by the Score Pages perimeter**.

Inventory:
- **24 dated weekly vintages × 2 languages = 48 archive HTML files in the public repository tree**;
- plus the two current language HTML files;
- **50 repository HTML files**, but the tested current/archive HTML routes are currently denied with 403 at both branded and legacy origins.

This distinction matters: HTML remains part of repository/history rights review, but the verified live anonymous serving exposure is currently the machine-readable JSON surface, not the protected dashboard HTML.

### 5. Git history

The repository is public.

Removing a file from the current branch would stop that path from existing in the new tree after deployment, but it would **not** erase:
- prior Git commits;
- old blob objects reachable through public history;
- external clones/forks;
- previously downloaded copies;
- third-party caches.

Historical Git treatment is a separate decision from current-tree/site treatment.

## Exposure summary

| Surface | Unique vintages | Current anonymous serving state | Component/provenance exposure |
| --- | ---: | --- | --- |
| Score JSON | 24 | public; current + dated paths verified live | per-driver z fields; recent provenance |
| Weekly input JSON | 14 | public; current + dated paths verified live | driver z/weight/contribution; recent provenance |
| Strict reproduction bundle | 9 | public; current + dated paths verified live | weekly levels, normalization, fingerprints/provenance |
| EN/ES HTML | 24 | repository files exist; tested current/archive routes return 403 | rendered component analysis exists in Git tree |
| Git history | historical | public repository history | prior versions remain reachable unless rewritten |

Counts are a current-tree inventory, not a legal conclusion.

## Live-origin verification — 2026-10-28

A fresh anonymous, read-only fetch verified that the following machine-readable paths are currently reachable at the branded Score origin:

- current Score JSON;
- current weekly-input JSON;
- current strict reproduction bundle;
- dated 2026-10-23 Score JSON;
- dated 2026-10-23 weekly-input JSON;
- dated 2026-10-23 strict reproduction bundle.

The legacy `pages.dev` origin also returned the current Score JSON directly.

Structural inspection of those live responses confirmed:
- component/driver names are present;
- source-provenance metadata is present in current Score/weekly-input/reproduction responses;
- weekly-input responses contain z/contribution fields;
- strict reproduction responses contain component and contribution-level evidence.

No provider-derived numeric values are reproduced in this inventory.

By contrast, current/archive EN/ES HTML requests returned HTTP 403 at both origins, consistent with the protected dashboard perimeter.

This live check changes the risk priority: **machine-readable JSON is the verified anonymous serving surface that requires first treatment if aggregate-only containment is approved**.

## Treatment options

### H0 — prospective HOLD only

Keep historical public artifacts unchanged while #159 blocks new public/research expansion.

Advantages:
- zero destructive change;
- preserves frozen research evidence and current public history;
- no SHA/reference disruption.

Limitation:
- historical component-level material remains publicly accessible.

Use only if provider/counsel/owner accepts that treatment.

### H1 — current-tree aggregate redaction

After approved private-evidence migration:

- replace current/public Score JSON with the reviewed aggregate-only schema;
- replace dated archive `score.json` with aggregate-only date/score/regime history appropriate to each vintage;
- replace/remove public `weekly_input.json` driver/provenance fields;
- remove public strict `repro_bundle.json` files after exact private copies are verified;
- decide whether protected EN/ES repository HTML also needs source-tree redaction even though anonymous serving is currently denied;
- update independent-replication claims and tests.

Advantages:
- stops the deployed/current repository tree from serving component evidence;
- preserves Git history and locked historical commit references.

Limitation:
- old bytes remain accessible through public Git history.

### H2 — current-tree redaction plus serving/cache verification

Perform H1, then explicitly verify every formerly public **machine-readable** sensitive path returns no component data from the deployed origin/CDN, while confirming protected HTML remains denied.

If stale CDN/provider cache entries remain, perform only the narrowly required purge after separate Production authorization.

This still does not erase public Git history or external clones.

### H3 — Git-history rewrite / blob purge

Rewrite repository history to remove affected blobs and force-update rewritten refs.

Potential consequences:
- changes descendant commit SHAs;
- invalidates SHA-based attestations and reviewer evidence;
- can break frozen research/preregistration references;
- requires branch/tag/PR/reference reconciliation;
- does not revoke external clones or already downloaded copies;
- creates a large operational and audit migration.

Disposition: **do not perform unless counsel explicitly requires historical Git removal and a dedicated migration plan is approved**.

### H4 — make the repository private

Changing repository visibility could reduce future casual access to Git history, but:
- it does not erase prior public clones/caches;
- it does not itself remove deployed public assets;
- it can affect CI/deployment/public replication workflows.

It is not a substitute for H1/H2 or an actual history rewrite.

Disposition: **not a standalone archive-remediation method**.

## Required sequence if aggregate-only treatment is approved

Do not delete/redact first.

1. Keep #159 HOLD active.
2. Obtain provider/counsel disposition covering both public output and internal evidence retention.
3. Select/approve the private evidence boundary.
4. Copy/verify every strict bundle required by frozen research into the approved private boundary, preserving exact bytes and hashes.
5. Prove #158 private handoff and frozen-research equivalence.
6. Freeze a hash-only inventory of every public file to be changed.
7. Build aggregate-only replacements in a review branch.
8. Re-render EN/ES archives/current pages.
9. Update archive indexes, independent-replication language and tests.
10. Run exact-head quality/security/reproduction checks.
11. Obtain separate Production authorization.
12. Deploy the current-tree treatment.
13. Verify former sensitive URLs no longer serve component data.
14. Handle cache purge only if verification proves it necessary.
15. Decide Git-history treatment separately.

## Research preservation warning

The strict historical bundles are part of the frozen predictive/shadow research evidence chain.

Deleting them from the public tree before an approved exact-byte private migration could make the preregistered research non-reproducible or force an impermissible provider refetch/backfill.

Therefore archive containment must be **migration-first, redaction-second**.

## Do-not-act conditions

Do not remove or rewrite historical artifacts while any of the following is unresolved:

- provider/counsel treatment;
- permission for internal retention of strict evidence;
- private storage/authentication boundary;
- exact-byte migration verification;
- frozen research equivalence;
- current-tree replacement schema;
- Git-history requirement;
- Production authorization.

## No-action record

This inventory was produced through read-only inspection of the current public repository tree.

No historical file, Git ref, deployment, CDN cache, archive, Score value, storage resource or Production configuration was changed.
