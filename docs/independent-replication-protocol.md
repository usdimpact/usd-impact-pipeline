# USD Impact Score v2 — independent replication protocol

**Status:** prepared, not executed  
**As of:** 2026-08-26  
**First eligible release:** 2026-08-28 or later

This document defines how an external reviewer can test one strict, as-published USD Impact Score v2 release. Publishing this protocol does **not** mean an independent review has occurred.

The machine-readable source of truth for this protocol is [`public/data/research/independent_replication_protocol.json`](../public/data/research/independent_replication_protocol.json).

## What this can establish

A successful external reproduction can support a narrow claim that the reviewed strict release is reproducible from the frozen public calculation artifacts and that the published methodology was clear enough for an independent implementation.

It cannot establish:

- predictive power;
- future returns;
- economic usefulness;
- a trading edge;
- institutional endorsement;
- a complete reconstruction from original Yahoo/FRED transport bytes; or
- that every historical release is independently reproduced.

Predictive testing remains governed by the separately preregistered prospective Score v2 protocol.

## Why the review cannot use the 2026-08-21 release

Releases through 2026-08-21 are explicit reproduction-bundle legacy artifacts. The strict publication boundary starts with 2026-08-28. From that point, publication requires a frozen latest bundle and matching dated archive bundle, independent arithmetic validation inside the repository, dependency-lock binding, and a post-merge reproduction attestation.

An external review must therefore select a release dated **2026-08-28 or later** that has also passed the `main_post_merge` attestation.

## Independence requirements

The reviewer must not have designed the Score, selected its production variables/signs/weights/thresholds, or implemented the production pipeline. The primary recomputation must run in an environment controlled by the reviewer.

Paid work is not automatically disqualifying, but compensation and other material conflicts must be disclosed. Material clarification from USD Impact must be retained with the final report. The reviewer must be free to publish negative, ambiguous, or not-testable findings without USD Impact rewriting the substantive conclusion.

USD Impact's own CI, rehearsal, strict validator, and post-merge attestation remain **first-party controls** and cannot be relabeled as independent evidence.

## Frozen review materials

The selected release must bind the reviewer to one exact merged production commit. At minimum, retain and hash:

- `public/data/score_v2_methodology.json`;
- `public/data/score_v2_data_semantics.json`;
- `public/data/score_repro_bundle_latest.json`;
- `public/archive/<week>/score_repro_bundle.json`;
- `public/data/usd_impact_score_v2.json`;
- `public/data/weekly_input_latest.json`;
- `requirements.lock`; and
- the exact release commit identifier.

The repository reference validator, `scripts/validate_weekly_release.py`, may be used only as a **secondary** cross-check after the reviewer has completed an independent implementation.

## Primary test

1. Record the selected week, exact merged commit, artifact URLs and local SHA-256 hashes.
2. Confirm the latest and dated strict bundles are byte-identical.
3. Confirm the bundle's dependency-lock hash equals the reviewed `requirements.lock` hash.
4. Do not import `usd_impact_score_v2.py` for the primary calculation.
5. Independently implement the arithmetic described by the public methodology.
6. For each of the eight drivers, recompute the z-score from the frozen level, mean and sample standard deviation.
7. Apply the published ±3.5 clipping rule.
8. Apply the fixed signed weight and recompute contribution.
9. Sum the eight contributions and independently classify the regime using the published thresholds.
10. Compare all per-driver and total values with the frozen bundle and published latest-week output at absolute tolerance `1e-9`.
11. Review `score_v2_data_semantics.json` for any material ambiguity about source field, alignment, resampling, forward fill, futures continuity, timestamps or retention boundaries.
12. Only after completing the independent implementation, optionally run `python scripts/validate_weekly_release.py --root .` as a secondary first-party cross-check.

## Required finding classes

Every material check must be classified as one of:

- **MATCH** — independent result agrees within the declared tolerance and no material ambiguity blocks the check.
- **MISMATCH** — result differs outside tolerance; retain both values and the smallest identified divergence.
- **AMBIGUOUS** — the public specification permits materially different reasonable implementations.
- **NOT_TESTABLE** — the public/frozen evidence is insufficient; identify the missing evidence explicitly.

A report must not convert `AMBIGUOUS` or `NOT_TESTABLE` into a pass.

## Minimum report contents

The final external report should include reviewer identity/qualification, independence statement, compensation/conflict disclosure, environment, exact release commit, artifact hashes, all material clarifications, the eight per-driver calculations, total score/regime comparison, provenance review, methodology/data-semantics clarity findings, and the known raw-data-retention limitation.

## Claim policy

Until such a report exists, the strongest permitted public wording is **“independent replication protocol prepared”** or equivalent.

After a report exists, USD Impact should describe only what that report actually tested. Even a complete MATCH for one release does not establish predictive power or future performance.
