# Frozen research residual dependency risk — fresh reassessment request (2026-11-07)

> **PENDING REVIEW / NO ACCEPTANCE / NO CHANGE TO ENFORCEMENT.** This is an evidence-index and decision request, not a security approval, published release permission, or authorization to change a frozen dependency. Prepared as an entirely separate Draft from Score publishing [PR #338](https://github.com/usdimpact/usd-impact-pipeline/pull/338).

## 1. Trigger and exact evidence

At [pipeline PR #338 head `d9c4d21697d7ad725f03c9f4bc91b4d47d00a083`](https://github.com/usdimpact/usd-impact-pipeline/pull/338), [Weekly Score quality #42383397243](https://github.com/usdimpact/usd-impact-pipeline/actions/runs/42383397243) **PASSED** with 1,041 Python tests, including all 15 new, offline, policy-mutation test methods. [Python security #42383397265](https://github.com/usdimpact/usd-impact-pipeline/actions/runs/42383397265) **FAILED** as designed. Its frozen-research job stopped at "Verify residual-risk acceptance is current and scoped", because `accepted_until = 2026-11-05` and the run date was 2026-11-07. The frozen `pip-audit` job step and upload of its fresh frozen JSON **DID NOT RUN**. Separate online dependency audit and Python CodeQL jobs **PASSED**; neither result is a review of the frozen root lock.

This failure is independent of the four-file publishing governance patch. **Do not bypass it by extending the expiration, mutating expected advisory IDs, changing branch protection, removing the security check, redefining an exit code, replacing the frozen requirements lock or claiming a now-missing audit passed.**

Baseline evidence pinned at read-only GitHub `main@e9a04b7576cbfd842cec7cbf0b18cfb2022ceb77`:
- `requirements.lock`: Git blob `ddf0049a5c294729a653302cbe9feec2316bb951`, **31 exact pins**; declared SHA-256 `a4c6fb90909a04eb267057d3e31049c7fc38b12e8a7d556e79c0141aa0d52db6` in existing runtime governance and security workflow. **The SHA-256 is an existing repository assertion; this review packet does not claim an independently recomputed local digest.**
- `docs/frozen-residual-risk-review-2026-10-26.md`: blob `9d8afa22fc9a0ed7775e302075651d8006eac041`; historical acceptance through November 5 only.
- `.github/workflows/python-security.yml`: blob `4107f7571a14a2e1b553c9bec9c40cfbebdee6ea`; fixed first-party expiry and audited finding-set gate.
- `runtime/frozen-research-wheelhouse.json`: blob `10449e6e9c8118c519e99100b310ef9f0d4c104a`; declares `network=none`, read-only root, capability-drop, no-new-privileges, non-root UID.
- `runtime/active-environment.json`: Git blob `642a9cd8753d076c34a3ef4389cd362cbc8621e8`; separate active online dependency lock, not evidence of a clean frozen lock.

Historical **October exact-match expectations** in the workflow: **43** entries: `urllib3==2.7.0` (3), `certifi==2026.7.22` (1), `pillow==12.3.0` (39). These are earlier reviewed expectations, **not** a fresh November registry scan. The existing audit tool pin was `pip-audit==2.10.1`. Any currently returned extra/changed/removed advisory or altered fix-version value requires separate review.

## 2. Unreviewed October advisory / November CVE identifier — investigate coverage gap

**`CVE-2026-112902` / `GHSA-xvh5-g6gv-559v` (Pillow libtiff encoder).** The official Pillow GHSA was already published **October 17, 2026**—before the October 26 residual-risk acceptance. The CVE identifier's formal publication followed on **November 5, 2026**, and an Ubuntu/OSV record followed on November 6. The earlier October audit's exact-match list lacks this advisory *by GHSA and by later CVE ID*. This is a potential **coverage gap in the prior accepted review**, not proof that the vulnerability originated after acceptance. The vendor description identifies exposure in Pillow versions through 12.3.0 when encoding TIFF files with crafted metadata; it may disclose process memory or crash a worker. `pillow==12.3.0` in the immutable research lock falls in the stated affected range. The October workflow's 39-entry Pillow expected list **does not explicitly contain `CVE-2026-112902`**.

Source material:
- https://github.com/python-pillow/Pillow/security/advisories/GHSA-xvh5-g6gv-559v
- https://github.com/python-pillow/Pillow/blob/main/docs/releasenotes/13.0.0.rst
- https://security-tracker.debian.org/tracker/CVE-2026-112902
- https://osv.dev/vulnerability/UBUNTU-CVE-2026-112902

**Crucial limitation:** An external advisory record appearing today does not establish that current `pip-audit` emits this identifier, rather than an alias, or that the vulnerability is exploitable through the two frozen, offline research modes. The earlier scope review says research consumes preexisting JSON rather than opening images; this negative-reachability claim must be tested against **exact current source and writable artifact paths**, including transitive image conversion, rather than merely copied into a refreshed acceptance.

The active online runtime previously moved to Pillow 13.0.0; require a newly checked pin and fresh active audit before claiming current protection. A true Pillow security fix is not an automatic license or permission to change frozen research.

## 3. Mandatory fresh review checklist — no gate modifications in this Draft

| ID | Review task and evidence | Default if unavailable |
| --- | --- | --- |
| R01 | Re-verify protected main, exact source tree, root lock bytes and independent SHA-256, Python/runtime OS and lock dependency identity. | **HOLD** |
| R02 | Re-verify **actual enforced runtime** isolation: no network, only sanctioned commands, no mount escape, read-only root, dropped capabilities, no-new-privileges, non-root UID, resource limits and controlled output export. A JSON declaration alone is insufficient. | **HOLD** |
| R03 | Perform a new **approved, read-only security advisory audit** of all 31 frozen pins in a controlled environment, recording audit tool version, UTC scan timestamp, SHA-256 digest of raw private audit JSON, version IDs and advisory-source provenance; no market-data/provider observation requests. No workflow dispatch is authorized by this document. | **HOLD** |
| R04 | Compare fresh findings with 43 October expected triples and their exact alias map. Separately evaluate `CVE-2026-112902` and any other late advisories, changed fixes, severity or exploit preconditions. Missing and added findings both require review; avoid blanket aliases. | **HOLD** |
| R05 | Trace frozen worker's actual imports and callable paths, file/format ingress, image open/save/convert and TIFF metadata propagation, attacker-controlled writes, temp mounts and output release. Prove or explicitly decline to claim Pillow and network advisory nonreachability. | **HOLD** |
| R06 | Reconfirm the online lock and independent clean audit, but keep online and frozen risk decisions separate. | **HOLD** |
| R07 | Record narrowly scoped disposition for **each** current finding: mitigate via containment, fix through separately approved research migration, or time-bounded residual risk acceptance with rationale. Do not change preregistered research outputs. | **HOLD** |
| R08 | Obtain authorized human security/owner review covering exact artifact SHA, environments, findings, evidence custody and concrete expiration. Solo-owner operation may be documented transparently, but **must not claim an independent reviewer exists**. | **HOLD** |
| R09 | Only after R01–R08 complete and explicit item-specific authorization: propose a **separate** versioned security-control change with exact-head CI, no bypass and rollback evidence. Its acceptance must not grant Score/provider data rights or a Production release. | **HOLD** |
| R10 | Preserve all existing source-rights, publication, historical archive retention and website holds. Do not merge unrelated Draft PRs under a security exception. | **HOLD** |

## 4. Pending decision receipt — not a signed document

| Required item | Value |
| --- | --- |
| Review decision | **PENDING / DENY** |
| Authorized reviewer and role | **NOT RECORDED** |
| Owner's item-specific disposition | **NOT RECORDED** |
| Exact audited frozen-lock digest | Existing asserted digest above; **fresh independent check missing** |
| New advisory scan UTC timestamp | **NOT PERFORMED** |
| New advisory raw evidence digest | **NOT AVAILABLE** |
| Current finding/alias/OSV diff | **NOT PERFORMED** |
| Actual frozen-worker isolation proof | **NOT RE-VERIFIED** |
| Scope-specific revised acceptance / expiry | **NONE** |
| Separate release authorization | **NONE** |

Keep the original expire-at-November-5 condition in force until a properly authorized replacement exists. Neither this packet, this PR, nor a future green site copy PR conveys evidence of publication rights or historical Score redistribution consent.

## 5. Parallel-work boundary

- Original eight-input Score and all historical public-derived artifacts: Issue [#155](https://github.com/usdimpact/usd-impact-pipeline/issues/155), **RIGHTS HOLD**.
- FRED delivery/retention: Issue [#282](https://github.com/usdimpact/usd-impact-pipeline/issues/282), **HOLD**.
- Separate four-source independent educational Macro Context Panel: Issue [#313](https://github.com/usdimpact/usd-impact-pipeline/issues/313), **56/56 source rights FALSE**, **14/14 authorities FALSE**, synthetic-only, no live source observations or release.
- Publishing reconciliation: [pipeline Draft #338](https://github.com/usdimpact/usd-impact-pipeline/pull/338), no deployment or merge.
- Public-facing historical status copy: [site Draft #1204](https://github.com/usdimpact/usd-impact-site/pull/1204), no deployment or merge.
- This packet changes **one documentation file only**, does not alter `requirements.lock`, the frozen wheelhouse, research hashes, workflows, CI acceptances, policies, Score components, member routes, public pages, archival datasets or cloud state.

**Final state: fresh residual-risk review required; no acceptance granted.**

## 6. 2026-11-07 independent source-only delta review (non-authorizing)

**R01 digest — partially evidenced.** Reconstructed the exact 43-line UTF-8 `requirements.lock` returned via authenticated GitHub contents and independently calculated SHA-256 with system `sha256sum`, **no installs or provider data queries**. Obtained **`a4c6fb90909a04eb267057d3e31049c7fc38b12e8a7d556e79c0141aa0d52db6`**, matching the declared freeze/hash in `runtime/frozen-research-wheelhouse.json` and the existing security workflow. The source lock has 31 pinned dependencies. This confirms this **text snapshot** matches the historical expected digest, but not that a freshly built/downloaded wheelhouse or actual executing container matches all approved properties. R01 remains **PARTIAL**, not globally PASS.

**R02 static runtime commands — partial only.** Reviewed `scripts/run_frozen_research.py` Git blob `9d434e952d4357ce4701f06979dbd4ae7b41272a`, `runtime/research-worker.Dockerfile` blob `ff8b8a16d5405d795869c8f29fef25d5e19b3e9f`, and `runtime/frozen-research-wheelhouse.json` blob `10449e6e9c8118c519e99100b310ef9f0d4c104a`. The declared Docker runtime arguments include `--network none`, `--read-only`, `--cap-drop ALL`, `--security-opt no-new-privileges`, PID/CPU/memory limits, and an explicitly bounded output mount. The Dockerfile runs non-root UID 65532. **Those source declarations and the prior green test are not independent proof of runtime enforcement or absence of dynamically reachable code**, and the host builder does separately download wheels and pull a pinned base image. No Docker build or container execution was attempted in this review; R02 remains **PARTIAL**.

**R05 static image/source call path — partial only.** The closed frozen launcher selects exactly `score-v3-shadow` or `score-v2-predictive`:
- `scripts/score_v3_shadow_ingestion.py` Git blob `6f413347221e1d2f7fe8759552855b092ed055ce` reads and verifies pre-existing JSON reproduction material. Its selected imported calls include `repro.verify_bundle()` and `freeze_v3.verify_frozen()`.
- `scripts/score_v2_predictive_ingestion.py` blob `b1dfe60665bc2c2520f2897c1f294222e1492ceb` similarly reads dated JSON reproduction evidence and invokes `repro.verify_bundle()`.
- `scripts/build_score_repro_bundle.py` blob `8b3fd26222d227dcaa97363469b21288c341dc02`, `scripts/freeze_score_v3_initialization.py` blob `b210a3f542f4b42be40ec9cd56b86887aec31e33`, and `usd_impact_score_v2.py` blob `eabeb89ca1479c73913369ad4f2c2163ca046166` are imported by research modules. **These source files contain dormant live provider-fetch functions and PNG chart-rendering helpers**, respectively. No TIFF `Image.open` + TIFF `save()` operations were found in the examined entrypoints/call paths. However, imported-module presence and search negatives are **not a full interprocedural call-graph or dynamic reachability proof**; a precise security review must establish that no reachable parser, plugin, worker export, upstream third-party library or injection path can TIFF-encode attacker-controlled image metadata. Any such possibility means retain HOLD. R05 remains **PARTIAL**.

**Advisory timeline correction.** Official project [GHSA-xvh5-g6gv-559v](https://github.com/python-pillow/Pillow/security/advisories/GHSA-xvh5-g6gv-559v) is dated **2026-10-17**, and the formal CVE ID appeared **2026-11-05**. In other words, a prior-acceptance *coverage gap* is possible even though the later automated feed began reporting the CVE in November. No currently authorized full frozen pip-audit scan has been run. Do **not** add an alias to the accepted set just because a static source scan suggested the research workers are non-image-oriented. The library is pinned to 12.3.0, while the upstream fixed version is 13.0.0.

**Unchanged decisions:** R01/R02/R05 are evidence collection only; R03 fresh scan, R04 diff, R05 complete dynamic/independent reachability, R07 scoped disposition, R08 human approval and R09 optional future control patch are still **PENDING / DENY**. No expiry, risk acceptance, protected lock, research data, source retrieval or publication gate changed.
