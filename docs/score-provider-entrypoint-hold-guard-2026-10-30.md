# Frozen Score provider access — guarded manual launcher and rights HOLD

**Date:** October 30, 2026  
**Status:** Original Score publication and provider rights **HOLD**. Engineering containment without changing immutable engine bytes, methodology, historical outputs or Production.  
**Issues:** [#155 — Score provider/public rights](https://github.com/usdimpact/usd-impact-pipeline/issues/155), [#282 — FRED and historical retention](https://github.com/usdimpact/usd-impact-pipeline/issues/282).  
**Previous audit:** [27-workflow and manual CLI exposure, section 9](score-155-282-readonly-exposure-retention-delta-2026-10-30.md).

## Verified invariant that governs this change

The release-quality job checks a [pre-holdout Score v3 engine lock](../research/score_v3_engine_lock.json) under [`verify_score_v3_engine_lock.py`](../scripts/verify_score_v3_engine_lock.py). Two files originally proposed for direct rights checks are **immutable**:

- `usd_impact_score_v2.py`
- `scripts/build_score_repro_bundle.py`

An initial draft attempted to add an early rights guard to each. **CI correctly failed** with `Score v3 engine file drifted from its pre-holdout lock: usd_impact_score_v2.py`. Both frozen files were immediately restored to their exact original Git blob SHA and remain byte-identical to their pinned engine-lock hashes. **No lock, preregistration, metric contract, weights or verifier was relaxed, rebaselined or overwritten.**

## Safe engineering addition without changing the frozen research baseline

1. `scripts/score_publication_rights_gate.py` gains `require_score_provider_rights()`, which reuses the canonical repository-anchored rights policy rather than a caller working-directory JSON or environment override. Invalid, missing, invalid-UTF-8 and syntactically convincing v1 `allow` entries are all denied; even a GitHub receipt is not a source license.
2. `scripts/score_provider_guarded_cli.py` is an **opt-in supported manual launcher**. It checks that gate before any call to the frozen Score or reproduction Python modules, source data file, local parquet cache, logger or output directory. Under the current HOLD it prints a brief Issue #155 diagnostic to stderr, exits with status **3**, and **does not start a subprocess**. If a separately approved future v2 rights contract clears this gate, the runner passes argument vectors to the frozen modules without shell interpolation.
3. `tests/test_score_provider_cli_rights_hold.py` has eight hermetic no-network checks: Score and reproduction modes refuse execution, no subprocess or output, malformed/missing/invalid-text policy denies, fake v1 authorization and cwd/env spoof fail, immutable engine and reproduction hashes remain exact, a *mocked* future command path is safely formed, and invalid command names do not start provider work.

No real FRED, Yahoo, ICE, S&P, Cboe, CME or other provider observations were fetched, compared, retained or used to develop or verify this change.

### Safe manual operational rule — required immediately for any future operator runs

**Never invoke the frozen legacy provider-facing files directly while HOLD is active.** In particular, do **not** use:

- `python usd_impact_score_v2.py` (including `--web` and `--test`)
- `python -m scripts.build_score_repro_bundle --live-refetch`
- `python -c "import usd_impact_score_v2; ...fetch_all_inputs(...)"` or equivalent lower-level direct provider calls

If an operator needs to verify the rights status, the **read-only/no-provider** command is:

```sh
python -m scripts.score_publication_rights_gate
```

For a manual execution request, the supported launcher syntax is:

```sh
python -m scripts.score_provider_guarded_cli score --web --output-dir public
python -m scripts.score_provider_guarded_cli repro --live-refetch --score-json synthetic-placeholder.json --output synthetic-output.json
```

**Do not actually run a live-data workflow during HOLD.** Both launcher examples must refuse with status 3 **before** reading any named file or making a provider request. They are syntax examples, not authorization to retrieve observations or write output. The tests in this PR are the preferred offline verification.

### Crucial limit — not a universal transport blockade

This launcher is **voluntary**. It cannot prevent a person or independent script from running the existing original frozen CLI, its `fetch_all_inputs()`, `fetch_yahoo()`, `fetch_fred()`, or unrelated scripts directly. The same code-level reachability detected in the October 30 audit therefore **remains as a residual risk**. The current eight GitHub Actions Score workflows are guarded independently and remain on HOLD. Do not treat this sidecar as evidence that all Python processes in every environment are gated or that any historic producer data is licensed.

A comprehensive **mandatory runtime boundary** requires a **separate approved architecture decision** that preserves the locked pre-holdout implementation as an unchanged research artifact while routing all supported *operational* calls through a locked-down, rights-reviewed entrypoint/source adapter. Such a change cannot be slipped into a research-only CI job or delivered by silently updating the v3 engine hash.

## Tests and reviewer acceptance (offline only)

```sh
python -m unittest discover -s tests -p 'test_score_provider_cli_rights_hold.py' -v
python -m unittest discover -s tests -p 'test_score_publication_rights_gate.py' -v
python -m unittest discover -s tests -p 'test_score_v3_engine_lock.py' -v
python -m scripts.verify_score_v3_engine_lock --filesystem-only --json
```

This PR should pass the project's protected exact-head release-quality and security checks. It changes no public artifacts, website/member files, Accounts, Supabase, Cloudflare runtime policy, workflows, frozen code or provider contracts. Use the established `[CF-Pages-Skip]` merge convention and verify no newly successful Production deployment.

## Manual mandatory steps — exact owner responsibilities

**Now, to avoid the residual direct-command risk:** Have any team/operator using this repository **stop executing the two original provider-consuming CLIs or direct provider functions** and use the reviewed launcher for manual requests instead. Confirm there are no independent local scheduled tasks or external agents calling the frozen scripts directly. GitHub Actions' original weekly release is already HOLD-gated; this is about callers **outside** those workflows. If no manual jobs exist, simply leave them disabled.

**Before restarting real-data calculation or public Score delivery:**

1. **Written source rights and derived-output scope** — open [Issue #155](https://github.com/usdimpact/usd-impact-pipeline/issues/155), review the [provider/counsel decision package](score-provider-counsel-rights-decision-package-2026-10-28.md), and obtain exact provider/counsel answers covering original owner + FRED/Yahoo transports, commercial calculation, aggregate histories, component disclosure and attribution. No budget is authorized for paid licenses or duplicate S&P/Cboe outreach. Keep correspondence private; enter only non-sensitive decision receipts in GitHub.
2. **Historical retention/disposal authorization** — open [Issue #282](https://github.com/usdimpact/usd-impact-pipeline/issues/282) and [the consolidated audit](score-155-282-readonly-exposure-retention-delta-2026-10-30.md). Decide lawful treatment of existing Class C files, Git history, old deployments, Actions caches/logs, backups and possible private storage. Do not erase, mirror or copy old provider observations first.
3. **Owner architecture/engine lock decision** — review [Score v3 locked research baseline](../research/score_v3_engine_lock.json) and this note. Approve a *new, separate operational entrypoint/source adapter* if fully enforced direct-use protection is required. The frozen Score v3 baseline, source hash history, and pre-holdout independence must remain unchanged. A mandatory enforcement migration is a future independently reviewed change, **not** a side effect of this guard PR.
4. **Separate release approval** — only after rights, archival decisions and safe operational entrypoint: approve a lawful aggregate-only schema, validate member/research consumers, review future v2 access/retention policy and authorize non-Production preview before any controlled Production change.

For the separate proposed Macro Context Panel, decisions remain under [Issue #313](https://github.com/usdimpact/usd-impact-pipeline/issues/313) and must **not** be treated as original Score permissions.

**No owner signature or paid action is required to merge this protective sidecar.** No legal approval or release will be inferred from a GitHub merge.
