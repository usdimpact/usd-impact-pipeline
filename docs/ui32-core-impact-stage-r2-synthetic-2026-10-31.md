# UI-32 Stage R2 — standalone synthetic-only PIT contract

**31 October 2026 — owner-authorized Stage R2 engineering; Draft review only.** This is not adopted economic methodology, a calibrated model, a public data contract, a licensed market source, an implementation of Score v2, the Macro Context Panel, or permission to publish. Governed by [UI-32 Issue #333](https://github.com/usdimpact/usd-impact-pipeline/issues/333) and the [research completion proposal](https://docs.google.com/document/d/18nYaDx0lAYxpfvUR4XQT2QLX7DrmHGz-XRLts_jpcr8/edit).

## Four-file scope

1. `scripts/ui32_core_impact_synthetic.py`: purely in-memory, standard-library-only validator; no provider SDK, network, database, environment, file system or site/Score dependency.
2. `tests/test_ui32_core_impact_synthetic.py`: **25 named T01–T25** cases plus additional positive/negative regression methods, all invented dates and numbers in year 2099+.
3. `.github/workflows/ui32-core-impact-synthetic.yml`: read-only exact-PR-head Actions test, only paths above; Python 3.11, no `pip`, no artifacts, no uploads and no privileged secrets. GitHub checkout/setup inherently contact GitHub; this is not a general OS-level network sandbox.
4. This research audit note. No existing production file is modified.

## Frozen synthetic boundary

- `SYNTHETIC_DO_NOT_PUBLISH` and `SYNTHETIC:UI32:` mandatory; eight mock economies (`US`, `EA`, `UK`, `JP`, `CA`, `CH`, `SE`, `CN`) without actual source identifiers. The experimental owner proposal still lists Australia and New Zealand as optional future extensions.
- Every reference period and timestamp is **2099+**. The June/July/August fictional monthly CPI records have true calendar month-end boundaries; source calendars, Friday clocks, economic source numbers and original publication times are **not** inferred.
- Chronology for synthetic receipts: `initial_release <= version_published <= revision_effective <= first_seen <= ingestion` (UTC). Eligibility also requires all publication, correction-effective and first-seen clocks at or before the fictional as-of cutoff. A source-local timestamp is accepted only when zone, offset, UTC translation and round-trip agree.
- Immutable series/reference/release/revision keys, revision-link digests and unique snapshots reject conflicting duplicate/vintage identities. Identical retries are idempotent. Future revisions never rewrite earlier as-of results.
- Cross-economy comparison requires consistent family, headline/core, frequency, reference dates, units and adjustment; no silent CPI↔PCE/HICP conversion. Absent consensus is `NO_CONSENSUS`; current policy is not a future expected path. Short or future-trained windows fail closed.
- A direct caller cannot instantiate an apparently validated `Decision` without the evaluator's internal issuer. All rights, retrieval, publication, Production and schema flags remain **False**. This is a defensive software contract, not a cryptographic signature or a hostile-interpreter security boundary.
- Outputs contain invented snapshot identifiers and closed blocker codes; a fingerprint hashes canonical fictional record content and is explicitly `UNSIGNED`. No numeric value, forecast, -100..+100 score, trading signal or website feed is released.

## Test coverage and limitations

- `T01` future release; `T02` future revision; `T03` late first-seen; `T04` local-clock mismatch; `T05` colliding digest; `T06` frequency conflict; `T07` missing consensus; `T08` CPI/PCE and headline/core conflicts; `T09` policy path unavailable; `T10` future-trained normalization; `T11` short trend history; `T12` unknown source rights; `T13` Score boundary; `T14` idempotency; `T15` units/seasonality; `T16` forbidden mock network; `T17` missing clocks; `T18` deterministic **unsigned** fingerprint; `T19` reverse-causality; `T20` unsupported origin; `T21` noncausal publication; `T22` independent source identity; `T23` fake dates/authority; `T24` pre-period publication; `T25` retrospective normalization leakage.
- Additional regressions cover eight-area mock enumeration, comparable synthetic numerical calculation, release-chain gaps, snapshot reuse, direct decision forging, static import allowlist and mocking two standard HTTP/socket entrypoints during the evaluator call.
- Those mocked network entrypoints do **not** prove that every imaginable arbitrary future import or a malicious runner lacks egress. No network-capable imports are present in the production module; no data-adapter functions or runtime hooks are connected.
- The local synthetic test suite is **not** a validation of real publisher timing, real historical vintages, legal permissions, economic weighting, forecasting, or application security. In particular, the permitted `2099+` clock is a deliberate artificial test restriction, not a usable live-source contract.

## Remain ON HOLD

- Separate Score v2 rights HOLD [#155](https://github.com/usdimpact/usd-impact-pipeline/issues/155), Treasury/FRED transport/retention HOLD [#282](https://github.com/usdimpact/usd-impact-pipeline/issues/282), and Macro Context Panel HOLD [#313](https://github.com/usdimpact/usd-impact-pipeline/issues/313) stay untouched.
- All actual provider source×series×transport×use-case rights are **UNKNOWN / DENY**. No direct market-source fetch, licensed data copy, provider outreach, real-data storage, Supabase migration, Cloudflare/Vercel/Render change, site route, purchase, email, Score output, feature flag or public API.
- A local or GitHub CI pass is **Draft PR review evidence only**. Require exact-head review of all changed paths and an explicit **separate owner approval** before merging, production use or expanding scope to any real inputs.
