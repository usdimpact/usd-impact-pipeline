# USD Impact Score v2 — independent replication reviewer packet

**Status:** commissioning packet; independent review not yet performed  
**Selected release:** 2026-09-18  
**Exact merged production release commit:** `1fda87c8eb817622a32ea85d4c496e692ce707d9`  
**Post-merge reproduction attestation:** GitHub Actions run `35454912323` — SUCCESS  
**Protocol:** `docs/independent-replication-protocol.md` and `public/data/research/independent_replication_protocol.json`

This packet freezes the release identity and review instructions for a genuinely external reviewer. It is not evidence of independent validation, audit, endorsement, predictive power, or investment performance.

## Reviewer independence declaration

Before substantive work begins, the reviewer should confirm in writing that they:

- did not design Score v2 or select its production variables, signs, weights, or regime thresholds;
- did not implement the USD Impact production pipeline;
- will perform the primary recomputation in an environment they control;
- will disclose compensation, commercial relationships, and other material conflicts;
- may report MATCH, MISMATCH, AMBIGUOUS, or NOT_TESTABLE without USD Impact editing the substantive conclusion.

## Frozen release materials

Use the files exactly as they existed at release commit `1fda87c8eb817622a32ea85d4c496e692ce707d9`:

- `public/data/score_v2_methodology.json`
- `public/data/score_v2_data_semantics.json`
- `public/data/score_repro_bundle_latest.json`
- `public/archive/2026-09-18/repro_bundle.json`
- `public/data/usd_impact_score_v2.json`
- `public/data/weekly_input_latest.json`
- `requirements.lock`
- `public/data/research/independent_replication_protocol.json`

The latest and dated reproduction bundles are the same Git blob at this release (`9a9aaf7d552138f626f87bde4af93a2f32d294e9`), providing repository-level identity evidence. The reviewer should independently compute and report local SHA-256 hashes for every retained file; Git blob IDs are not substitutes for that required report evidence.

## Primary independent recomputation

The reviewer should follow the public protocol and, for the primary calculation, must not import or call USD Impact's production Score implementation.

For each of the eight drivers:

1. Read the frozen weekly level, mean, and sample standard deviation.
2. Independently calculate the z-score using sample-standard-deviation semantics (`ddof=1`).
3. Apply the published ±3.5 clipping rule.
4. Apply the published signed weight.
5. Recompute the driver contribution.
6. Sum all eight contributions.
7. Independently classify the final score using the published regime thresholds.
8. Compare independently calculated values with the frozen release using the protocol's absolute tolerance.

The repository validator may be used only after the independent implementation as a secondary cross-check.

## Required report

Retain:

- reviewer identity, qualifications, and signed independence statement;
- compensation/conflict disclosure;
- review environment and software versions;
- exact release commit and local SHA-256 hashes;
- per-driver independent calculations;
- independent total Score and regime;
- methodology/data-semantics ambiguity findings;
- explicit acknowledgement that raw original provider transport bytes are not retained;
- each material clarification supplied by USD Impact;
- final classification for each material finding: MATCH, MISMATCH, AMBIGUOUS, or NOT_TESTABLE.

## Claim boundary

Until the completed external report is retained, public wording remains **“independent replication protocol prepared”** or equivalent.

A future full MATCH would support only a narrow reproducibility statement for the reviewed 2026-09-18 release. It would not establish predictive power, future returns, a trading edge, audit assurance, or endorsement. Predictive testing remains governed separately by the preregistered prospective study.
