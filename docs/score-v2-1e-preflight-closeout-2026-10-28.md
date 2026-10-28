# Score v2.1E one-off research execution closeout — 2026-10-28

**Disposition:** BLOCKED / FAIL CLOSED. This is an execution safety closure, not a legal opinion or a modification of the underlying historical owner decision.

## What happened

The owner-approved one-off study (Issue #209, comment 6477834394) was limited to official Board/BLS data between 2013-01-01 and 2026-10-23, with ephemeral source/raw values and no Production/public release. The authorized historical-vintage feasibility preflight [run 40755916179](https://github.com/usdimpact/usd-impact-pipeline/actions/runs/40755916179) passed fixed early/middle/late H.10, H.8 and H.4.1 historical archive samples but encountered **HTTP 404** for `www.federalreserve.gov/releases/h15/20200106/default.htm`. [Issue #218](https://github.com/usdimpact/usd-impact-pipeline/issues/218) records the independent vintage-reconstruction blocker.

The v2.1E preregistration does not permit current revised values to stand in for missing release-time vintages. No complete candidate Score was calculated. No rights to publish provider-derived data or production Score replacement were granted.

## Safety closure implemented

- Historical **approved** JSON receipt preserved verbatim as `governance/score-v2-1e-real-data-research-authorization-historical-approved-2026-10-28.json`; its original owner and timestamp remain audit evidence.
- Original **executable** path `governance/score-v2-1e-real-data-research-authorization.json` now contains an explicit `hold` receipt with zero active permissions and null approval identity/window; it points to the archived history through a non-authorizing note.
- Execution contract is `one_off_private_research_blocked`, active receipt path null, active receipt expected false, and every current authorization flag false.
- Immutable metadata-only fail-closed marker: `governance/score-v2-1e-preflight-closeout-2026-10-28.json`, pins issue #218, the failed workflow run, H.15 date/path/HTTP status and negative release flags; it includes no source/component data.
- Authorization validator checks both the original historical approval evidence and the inactive execution state. Even if someone changes the contract to active again without a new version, validation rejects it.
- Preflight workflow requires active authorization explicitly and stops before any external request. The preflight runner itself independently refuses after the validation reports blocked state.
- Non-network unit tests prove denied fetch, denial of tampered closeout, denial of old authorization reactivation, and preservation of the exact audit record.

## Remaining gates

There is no approval to retry v2.1E under the old eight-series method, broaden from Board/BLS to FRED/ALFRED/Treasury/Wayback, use paid sources or contracts, substitute current revisions, drop/reweight H.15, publish public/member-derived data, or deploy a new Score.

A new candidate needs its own identifier and frozen preregistration **before** observing new data, separate vintage-feasibility and rights approval, and a fresh explicit owner decision. Existing v2 public rights [Issue #155](https://github.com/usdimpact/usd-impact-pipeline/issues/155) remains open and unchanged.

No public Score artifact, research ledger, service configuration, account, subscription, payment, entitlement, or Production deployment is modified by this closeout.
