# Consolidated Score v2 public-exposure and FRED retention audit — October 30, 2026

**STATUS: REVIEW-ONLY / ORIGINAL SCORE PUBLICATION HOLD.** This is a metadata and source-code audit for Issues [#155](https://github.com/usdimpact/usd-impact-pipeline/issues/155) and [#282](https://github.com/usdimpact/usd-impact-pipeline/issues/282). It adds no data license, production rights, private storage grant, source switch, public schema approval, historical cleanup or new numerical observation. Baseline is protected USD Impact pipeline main **5ece72247e75defc69b9e9c72f81817276b68e54** (October 30).

This is an **incremental delta** to the already extensive [FRED retention inventory](issue-282-fred-retention-inventory-2026-10-29.md), [source-retention policy](source-retention-policy.md), [archive-preservation inventory](score-public-archive-metadata-preservation-2026-10-29.md), [public surface taxonomy](../governance/score-public-rights-surface.json), and [source-rights evidence](score-v2-provider-rights-evidence-matrix-2026-10-28.md). Findings are separated into *verified source code*, *verified connected-service metadata*, *previous independently recorded endpoint observation*, and *not verified*. No provider numeric file bodies, production data API responses, underlying storage object, workflow logs or new market-data feeds were fetched in this audit.

## 1. Exposure census from current protected Git tree

The complete Git trees API returned **695 entries / 634 blobs**, without truncation. Path-and-size metadata (not file contents) confirms the same Class C counts reported on October 29:

| Path family | Files | Substance / rights review | Current visibility |
| --- | ---: | --- | --- |
| public/archive/YYYY-MM-DD/score.json | **27** | Per-driver multiweek Score component history, including transformed Treasury z-scores, per existing verified historical audit | Public Git blob; dated route specifically allowlisted by Pages |
| public/archive/YYYY-MM-DD/weekly_input.json | **14** | Driver-level release-week z-score, weight, contribution and provenance by historical schema | Public Git blob; Pages dated route allowlisted |
| public/archive/YYYY-MM-DD/repro_bundle.json | **9** | Release-week exact levels, normalization moments, transformed values and fingerprint/provenance fields | Public Git blob; Pages dated route allowlisted |
| public/data/usd_impact_score_v2.csv and .json | **2** | Current full Score row/component history, not merely aggregate regime | Public Git blobs; Pages static allowlist |
| public/data/weekly_input_latest.json | **1** | Current driver breakdown | Public Git blob; Pages static allowlist |
| public/data/score_repro_bundle_latest.json | **1** | Current strict weekly reproduction layer | Public Git blob; Pages static allowlist |
| **Total Class C current-tree** | **54** | **50 dated + 4 current** | **Subject to source-specific derived-output rights review** |
| data/weekly_input_YYYY-MM-DD.json | **15** | Git-root weekly bridge copies, distinct from Pages allowlist | Public Git repository despite not being Pages URL routes |
| public/archive/YYYY-MM-DD/en.html and es.html | **54** | Historic premium HTML copies | Public Git blobs, even though Pages middleware denies public HTML routes |
| public/data/research | **6 metadata-visible files** | One B protocol, one D point-in-time JSON, one E robustness JSON and three F vintage JSON/CSV/HTML | Current Git tree; D/E/F web routes have explicit allowlist entries |

There are **27 dated** archive directories from 2026-04-10 through 2026-10-23. Two additional language index directories exist under public/archive and must not be counted as dates. Earlier English/Spanish archive indexes omitted three dated older releases (2026-05-02, 2026-05-09 and 2026-05-16). This is evidence of historical index differences, **not** authorization to reindex or republish them. The previous inventory already documents these omissions.

**Count limitations:** 54 is a count of candidate Class C artifacts in **the current Git tree**, not an exhaustive count of historical Git blobs, source-provider values, people, legal violations, old deployment versions, Cloudflare cached responses, forks or mirrors. No market-data file bodies were reopened to restate or recompute contents.

## 2. FRED/Treasury ingestion-to-persistence map (current code)

| Stage | Verified code | Storage / access implication | Classification |
| --- | --- | --- | --- |
| Origin / delivery | usd_impact_score_v2.py:79-94 configures **UST_2Y = FRED DGS2; UST_10Y = FRED DGS10**; 265-280 fetches FRED graph CSV. Board H.15 republishes original Treasury nominal constant-maturity series; FRED is operated by FRB St. Louis | Distinguish Treasury originating rates, Board republication, FRED delivery and exact graph-CSV transport terms | **Source-level verified, rights unresolved** |
| In-memory daily computation | usd_impact_score_v2.py:529-555 joins FRED and Yahoo series into a daily matrix; 614-615 derives normalization moments | Mixed-source computation can produce transformed information or indirectly reconstructible intermediates even without retaining raw HTTP response bytes | **Source-level verified** |
| Runner-local weekly work | .github/workflows/weekly.yml:105-118 writes full weekly-level CSV and provider fingerprint/evidence JSON into RUNNER_TEMP for same-run reproduction | Temporary intended lifetime; OS cleanup, runner snapshots, CI log retention and cloud backups remain separate questions | **Writer confirmed; disposal unverified** |
| Non-web local cache | usd_impact_score_v2.py:1391-1432 may write **_daily_cache.parquet** outside web mode; test mode may read it | Git ignore does not establish deletion or rights to cache data; inspect developer/CI copies only under a later approved preservation protocol | **Potential local persistence path** |
| File/console logs | usd_impact_score_v2.py:166-182 configures file + stdout logging; 691-708 emits some normalization statistics | Derived numerical terms may reach local logs and Actions log retention. This audit did not read historical logs or enumerate all runs | **Writer confirmed, retained copies unverified** |
| Current Score export | usd_impact_score_v2.py:733 and 821; .github/workflows/weekly.yml:105-159 | Current public CSV/JSON with component history; weekly commentary bridge and strict reproduction bundle | **Publisher-derived public output path** |
| Strict reproduction builder | scripts/build_score_repro_bundle.py:235-355 serializes release-week levels, normalized values, mean/std, contributions, source metadata, plus hash-only *daily fingerprint* | Hash-only daily subset **does not** make entire weekly bundle hash-only | **Public Class C** |
| Weekly bridge | scripts/generate_weekly_commentary.py:239-242 writes root data/weekly_input_* and public/data/weekly_input_latest.json | Two distinct Git persistence contexts, one Pages allowlisted | **Git/public evidence** |
| Dated publication | .github/workflows/weekly.yml:152-160 archives Score, weekly bridge and reproduction bundle; 184 stages public, commentary and data for PR | Human Git merge, Git history and Pages production deployments can duplicate historical public evidence | **Source-level verified** |
| Rights fail closed | .github/workflows/weekly.yml:40-78 and .github/workflows/repro-rehearsal.yml:47-77 require explicit hold == 'false' before live execution; score-v2-predictive, score-v3-shadow, research-validation, weekly-health and weekly-recovery also have rights checks | Operational HOLD prevents those inventoried normal workflow paths from new provider ingestion; a manual CLI, untracked external automation or historical run is **not proved impossible** | **Gated code verified; execution universe incomplete** |
| Read-only attestation | .github/workflows/repro-attestation.yml reads previously committed artifacts for consistency; no live provider fetch call in inspected workflow | Reading previously published restricted evidence is a separate rights/retention question; no new observations fetched by the audit | **Code verified** |

The FRED web terms currently distinguish allowed attributed uses for qualifying public-domain-tagged series from restrictions on **Services storage, caching, archiving, derivative works, AI/ML, and API-specific conditions**. The actual production source code shown above uses a graph CSV URL, **not** a FRED API-key call; counsel must map the correct FRED Services/transport terms and the separately labeled API provisions, not casually assign the API clause to every CSV request. See [FRED terms](https://fred.stlouisfed.org/legal/terms/) and existing [clause crosswalk](../governance/fred-terms-clause-crosswalk-2026-10-29.json). The private provider reply described in the retention policy is not a universal retention license and is not quoted here.

No direct Board H.15 or Treasury XML observations were downloaded or compared. A Board-owned H.15 page and its XML label show a **candidate publisher transport**, not equivalence of released vintages, permitted commercial storage or permission to change the live original Score data source.

## 3. Connected deployment and access configuration (read-only)

**Cloudflare Pages:** Project usd-impact-pipeline uses GitHub main and public/ as the published directory. Confirmed production origins: **score.usd-impact.com** and **usd-impact-pipeline.pages.dev**. The newest successful production build **among the returned current first-page production records** corresponds to commit **4fa72d2e147de2e98c59690b6a24019f25be41f2** (2026-10-29); subsequent research merge entries including 5ece722 are **idle**, not successful new builds.

On October 30 the API reported **268 production and 1,863 preview deployment records** (combined **2,131 records**). This is newer than the October 29 snapshot of 243 production + 1,678 preview and **not** a count of distinct live public data disclosures. Counts are independent paginated metadata queries; no promise of atomic historical enumeration. Existing successful deployment URLs, Git repository blobs, edge/CDN caches and old forks require separate inventories and approved preservation instructions.

**Cloudflare Access:** One account-level application covers wildcard **\*.usd-impact-pipeline.pages.dev** with one **allow** policy. That wildcard does not, by itself, protect the production root hostname or score.usd-impact.com. Current Pages middleware explicitly allows /data/usd_impact_score_v2.csv, /data/usd_impact_score_v2.json, /data/weekly_input_latest.json, /data/score_repro_bundle_latest.json, associated research files and dated /archive/YYYY-MM-DD/(score|weekly_input|repro_bundle).json. Earlier October 29 anonymous tests recorded these roots serving JSON, while preview subdomains required Access authentication. **No new anonymous endpoint GET or HEAD occurred during this audit.** Anonymous status for all historic preview builds and caches remains unverified.

**Website consumer:** The protected website main (usdimpact/usd-impact-site, sha **438d3294319a7cbb8a60d4fedcc6a1672719ea06**) still routes /score/member/* to its account API via apps/web/vercel.json:168-169. The member handler uses a private/no-store response and checks session/entitlement; that is independent of the Score pipeline's public data allowlist. The landing page advertises links to current aggregate/research and member content; [consumer impact map](score-v2-public-consumer-impact-2026-10-27.md) identifies migration dependencies. This code check is **not** a fresh user-entitlement or live member E2E test.

## 4. Dedicated private-evidence Supabase boundary

Read-only metadata against only the two **dedicated publication-guard** projects:

| Project | Buckets | Objects | Edge Functions | Verified additional detail |
| --- | ---: | ---: | ---: | --- |
| usd-impact-publication-guard-development | **1** | **1** | **1 ACTIVE broker** | Bucket score-private-evidence is nonpublic. One JSON object (1,748 bytes) matches exact documented 2099 synthetic rehearsal path, with **zero** non-rehearsal objects |
| usd-impact-publication-guard-production | **0** | **0** | **0** | No configured score evidence bucket/function or current objects in this project |

Development bucket/object timestamps match the [approved 2026-10-28 synthetic rehearsal](score-private-evidence-development-rehearsal-result-2026-10-28.md); hence the preceding 2026-10-28 **planning** snapshot saying zero buckets was superseded by that same day's explicitly authorized synthetic rehearsal. This is **not a discovered real-FRED storage incident**. The broker is configured with Supabase platform verify_jwt=false and implements GitHub OIDC validation in code; the prior test report reviewed the actual broker. Current production source-code parity and authenticated runtime behavior were **not** retested, and the private object **was not read**.

**Scope caution:** This query covered only dedicated publication-guard projects, **not** the website's general Production/Development member, account or operational data stores. Do not infer that no FRED content exists anywhere else in the organization, backup system or third-party app. The Development rehearsal authorization does not permit real-provider writes, replication or future observation archiving.

## 5. GitHub Actions retained-evidence limitations

Metadata-only checks show **zero downloadable Actions artifacts** for the sampled pre-HOLD Friday release run [#40044029286](https://github.com/usdimpact/usd-impact-pipeline/actions/runs/40044029286) and the separate [synthetic write rehearsal #40617195348](https://github.com/usdimpact/usd-impact-pipeline/actions/runs/40617195348). This **does not prove** zero historical CI caches, uploaded artifacts in unsampled runs, Actions log persistence, temporary runner snapshots or third-party mirrors. Pre-HOLD execution retrieved FRED/yfinance data according to the prior [Issue 282 source inventory](issue-282-fred-retention-inventory-2026-10-29.md); no workflow was re-run and no old logs, files or payloads were downloaded now.

Source inspection confirms rights gates in the principal weekly generation, reproduction rehearsal, research-validation, predictive/shadow, health and recovery workflows. The report **does not certify** every manual script invocation, every one-off/research workflow, external scheduler, developer checkout, saved Actions cache or other connected service. Comprehensively proving historical absence of retained provider data will require legally scoped metadata/log/access review, with no expansion of provider ingestion.

## 6. Classification: questions to counsel, not conclusions of illegality

| Data/derived evidence class | Existing surface | Question that must be decided |
| --- | --- | --- |
| Raw response / direct observation | Transient FRED graph CSV, Yahoo source fetch and development cache | May ingestion, transient use, storage, caching or archiving occur under each exact originating owner plus delivery-service terms? |
| Daily/weekly intermediary matrix | Runner temporary CSV, non-web parquet, reproduction inputs | Does material constitute FRED content/derivative; may it be temporarily written to disk, GitHub logs or backups? |
| Release-week numeric evidence | Weekly strict reproduction bundle and bridge | Can exact provider levels, normalization moments, z-scores and contributions be retained privately and displayed publicly? |
| Multiweek per-driver transformed history | Score CSV/JSON and dated archive JSON | Can public component-derived histories be displayed and historically redistributed commercially? |
| Aggregate Score/regime and historical sequence | Current and historical Score summary/research aggregate | Is nonreversible aggregate display and aggregation history authorized even when individual components are not? |
| Version hashes, code fingerprints and metadata | Daily fingerprint hashes, process/source identifiers, commit/time stamps | What is permissible persistence and provenance without reconstructibility, and what naming/attribution obligations attach? |
| Class D/E/F research diagnostics | Public research JSON/CSV/HTML | Which component-correlations, vintage comparisons or provider attribution must be removed/redacted before licensed review? |
| Old deployments, Git forks, caches | Git history, 2,131 Pages records, Actions and external consumers | How should historic copies be preserved, restricted, erased or allowed under source-rights counsel's instructions? |
| AI/ML | Potential downstream research/automation consumers, **not assessed by scanning user data or model training systems** | Whether any FRED-delivered content was used for prohibited AI/ML development/training; no affirmative evidence of such use in this audit |

The US Treasury government-publication status and the Board's general public-domain statement do **not** automatically cancel FRED delivery terms or third-party restrictions. Equally, a public exposure is a **rights risk**, not itself proof of infringement. S&P, ICE, CME, Cboe, Yahoo/BTC origin and FRED require their own exact rights/transport/product decisions. Do not open duplicate sales conversations or buy licenses under the existing zero-budget plan.

## 7. Ordered decisions and safe remediation sequence

1. **Keep HOLD.** Maintain current original Score publication gate, seven/eight-provider rights records and independent four-source research HOLD; do not fetch numerical observations, publish, switch data feeds or create new real-provider evidence.
2. **Obtain written scope-specific rights review** for FRED Services (including retention/disposal/derived commercial output), original Treasury/Board, Yahoo-delivered upstream products and every existing output/retention class. Resolve historical treatment explicitly; do not infer ALLOW from a public-domain label or pre-HOLD release.
3. **Map residual metadata-only persistence** of prior Git versions, Cloudflare successful preview/production deployments, old root URLs, Actions logs/caches/artifacts, code/log copies, backups, local developer output, forks and consumer mirrors. Approval may be needed before sensitive logs or cached content can be inspected or copied.
4. **Approve lawful retention and preservation first**: choose explicit private evidence store, allowed data fields, retention/disposal, encryption and least privilege before copying any old provider-derived evidence. Development's synthetic fixture cannot simply be repurposed.
5. **Finalize a public aggregate-only candidate** with versioned schema and synthetic tests. Existing prototypes are technical tools, not legal publication rights. Test current website links, member gateway, research readers, historical indexes and reproducibility/attestation consumers before proposing a destructive migration.
6. **Separate non-Production approval**, reversible migration and measured anonymous route audit; review CDN invalidation and Git history independently. Do not break premium member access while narrowing Class C/E/F public output.
7. **Only after independent counsel and owner authorization**, run protected exact-head checks and deployment, confirm origin/root/previews/caches and member/anonymous routes, record a legally safe rollback that does **not** republish previously restricted material.
8. **Maintain historical restoration and incident discipline**. No retroactive history rewrite, purge, private mirroring, paid license, provider correspondence, source substitution, SQL mutation or Production change is authorized by this audit.

## 8. Acceptance and unresolved evidence

**Verified:** current Git tree exposure path counts; current code FRED/yfinance source-to-sink graph; existing rights-gated principal workflows; publicly allowlisted Pages route contract; current Cloudflare project/deployment/preview Access metadata; dedicated publication-guard Supabase bucket/function/object counts; synthetic Development object metadata; two sampled run artifact listings; original Score and four-source governance HOLD.

**Existing dated observation, not freshly repeated:** October 29 anonymous endpoint checks and older pre-HOLD provider fetch execution evidence.

**Not verified:** complete Git object/fork/backup inventory; all GitHub Actions logs and dependency caches; all historical Pages hashes/edge caches; all external developer machines and other services; real-provider storage elsewhere; complete codebase's manual/external run paths; current live website member positive E2E; scope of historical FRED storage rights; commercial public derived-output rights; private preservation permission; direct-source H.15/Treasury parity.

**Disposition: HIGH-PRIORITY RIGHTS CONTAINMENT REVIEW, NOT AUTOMATIC UNPUBLISHING.** The website is not declared unlawful. The 54 Class C current-tree paths and the distinct D/E/F, Git-only bridge and storage surfaces require precise counsel decisions, then a separately authorized deployment plan. This research-only report leaves all runtime data, legal gates, public artifacts and Production unchanged.
