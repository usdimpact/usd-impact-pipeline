# Original Score provider entrypoints — direct-use rights HOLD safeguard

**Date:** October 30, 2026  
**Status:** Engineering fail-closed safeguard only / ORIGINAL SCORE PUBLICATION HOLD / zero additional data-license budget.  
**Issues:** [#155 — public redistribution](https://github.com/usdimpact/usd-impact-pipeline/issues/155) and [#282 — FRED retention](https://github.com/usdimpact/usd-impact-pipeline/issues/282).  
**Originating finding:** [Consolidated October 30 read-only audit, section 9](score-155-282-readonly-exposure-retention-delta-2026-10-30.md).

## Problem

GitHub Actions ordinarily calls `scripts.score_publication_rights_gate` before weekly Score or reproduction work. A developer invoking `python usd_impact_score_v2.py` directly, or `python -m scripts.build_score_repro_bundle ... --live-refetch`, does not inherit an Actions job condition. These two CLI paths could reach the existing FRED DGS2/DGS10 and Yahoo-delivered data independently of those workflow-level checks. A shared Python `fetch_all_inputs` caller was likewise reachable. This is **source-code reachability**, not evidence of any unauthorized post-HOLD execution.

## Implemented code boundaries

1. `scripts/score_publication_rights_gate.py`: reusable `require_score_provider_rights()` checks the **canonical repo-anchored** rights policy, independent of working directory, environment flags or a caller-supplied policy pathname. The reviewed v1 rights interlock still rejects every `allow` claim; a signed-looking GitHub URL is not sufficient. Missing, damaged and invalid-UTF-8 policy files fail closed.
2. `usd_impact_score_v2.py:main()`: after parsing flags but **before** creating a `.pipeline_cache` directory, setting up logs, opening provider-history parquet, fetching either source, computing or writing outputs, requires the canonical gate. Under HOLD it prints a bounded Issue #155 diagnostic to stderr and exits **3** without creating any output.
3. `usd_impact_score_v2.py:fetch_all_inputs()`: a second check before the first Yahoo/FRED provider client protects other Python callers that use this shared source function, including the existing one-off research/robustness code paths. It changes no economic formula or source mappings.
4. `scripts/build_score_repro_bundle.py:main()`: `--live-refetch` is denied **before even reading** the supplied Score JSON and before output writing; the directly callable `_live_weekly()` is guarded too, and the shared fetch has a further check.

The new tests use only **invented values, mocks and temporary files**. They assert no calls to provider transports, parquet reads, Score JSON reads, logging setup, directory creation, evidence writes or production/publishing routines while HOLD. They also test a fake working-directory policy, a syntactically plausible but unapproved v1 allow receipt, malformed/missing/invalid-text policy and unaffected pure scoring helpers.

## Deliberate scope boundaries

- The existing 8-driver weights, Score formula, current public artifacts, existing historical archives, approved premium member routes, YAML workflow gates and Cloudflare configuration are unchanged.
- Pure offline computation and fixture-based `--weekly-levels` reproduction are **not licensed commercial operations** by this patch. In particular, this patch does **not** certify that reading an old real-provider weekly input file is lawful. Review that retention question under Issue #282 before inspecting, copying or regenerating old derived evidence.
- Lower-level functions `fetch_yahoo()` and `fetch_fred()` are still Python-callable directly, without going through `fetch_all_inputs()`. The guard closes the identified Score CLI, reproduction live CLI and shared fetch paths, **not an arbitrary hostile Python caller**. Python imports and code in a local process are not a security perimeter; a comprehensive source-adapter/transport permission boundary is a separately scoped engineering follow-up.
- Separate federal research preflights, old deployments, historical Git blobs, GitHub Actions logs, external backups, local developer caches and third-party mirrors are **not altered**. No provider observations were accessed to develop or test this patch.
- No false v1 release path was introduced. Source-specific legal/counsel decisions, approved public schema, lawful private retention, a future reviewed v2 rights contract and separate Production authorization remain necessary for any restart.

## Offline verification and acceptance (no provider requests)

Run from a trusted checkout of the reviewed exact PR head, with Python test dependencies already installed:

```sh
python -m unittest tests/test_score_provider_cli_rights_hold.py -v
python -m unittest tests/test_score_publication_rights_gate.py -v
python -m unittest tests/test_score_rights_v1_release_interlock.py -v
```

The code-quality workflow also validates release tests, rights guards and frozen research. **Never test with a live provider request.** A manual invocation of either Score CLI under HOLD should exit 3 without output; the unit tests mock all provider work and are the recommended verification.

## Mandatory human decisions before any real-data usage or release

These are **not required to merge this fail-closed guard**, but are mandatory for clearing HOLD or changing the public/historical data treatment:

1. **Source-rights review and written scope:** In [Issue #155](https://github.com/usdimpact/usd-impact-pipeline/issues/155), review [the provider/counsel decision pack](score-provider-counsel-rights-decision-package-2026-10-28.md) and [provider follow-up queue](../governance/score-provider-rights-followup-queue-2026-10-29.json). Obtain provider/counsel decisions for exact data owners, FRED/Yahoo transports, commercial internal computation, aggregate display, component values and required citations. **No new paid agreement or repeated S&P/Cboe case is authorized.** Keep private correspondence in a suitable private system; record only non-sensitive references/decisions in GitHub.
2. **Lawful historical preservation/disposal:** In [Issue #282](https://github.com/usdimpact/usd-impact-pipeline/issues/282), review [the consolidated retention audit](score-155-282-readonly-exposure-retention-delta-2026-10-30.md) and specify which Git/Pages/runner/log/cache/backup artifacts can legally remain, be restricted, or must eventually be removed. **Do not delete archives, purge caches or copy real provider data without a separately approved preservation plan.**
3. **Owner release choice:** Decide whether USD Impact should proceed with a no-cost, non-reversible aggregate-only Score or keep the original project paused. Only after necessary rights clearance should a distinct release PR establish a verifiable v2 rights/release contract, public schema, member/research compatibility tests, signed owner decision and controlled non-Production preview. The separate Macro Context Panel in [Issue #313](https://github.com/usdimpact/usd-impact-pipeline/issues/313) has independent rights and methodology gates.

**No manual action is required now to preserve the HOLD:** the safer defaults remain in force. Do not edit the v1 gate from `hold` to `allow` as a shortcut; the v1 validator rejects such a change.

## Release note

This patch is security/rights containment, **not** a Score content update. Use the existing `[CF-Pages-Skip]` documentation/non-public-code merge convention, verify the exact-head CI and confirm the merge did not trigger a newly successful Production deployment. A merge is not a legal license.
