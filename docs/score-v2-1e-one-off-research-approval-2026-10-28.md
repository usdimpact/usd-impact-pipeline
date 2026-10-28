# Score v2.1E one-off private research approval — 2026-10-28

Status: **HISTORICALLY APPROVED / EXECUTION CONSUMED / BLOCKED after H.15 preflight**. The original one-off owner approval is preserved, but no further research execution is permitted under it.

## Approval evidence

Issue: https://github.com/usdimpact/usd-impact-pipeline/issues/209

Approval comment ID: `6477834394`

Approval timestamp: `2026-10-28T18:55:48Z`

Approved wording:

> I explicitly approve the one-off private Score v2.1E real-data research run under Issue #209, for 2013-01-01 through 2026-10-23, under the stated ephemeral-only, official Board/BLS-only, no-Production scope.

## Authorized scope

- methodology: `2.1E-design-candidate`;
- one-off private research only;
- exact data window: 2013-01-01 through 2026-10-23;
- exact eight series already frozen by the design/preregistration;
- direct official Federal Reserve Board and BLS endpoints only;
- raw responses and source values ephemeral only;
- temporary workspace isolated and non-public.

## Still forbidden

- Production;
- public Score replacement;
- research-ledger mutation;
- paid data;
- source-contract acceptance;
- durable raw/component storage;
- publication of source/component values;
- methodology activation.

Issue #155 remains HOLD.

A successful research run does not itself authorize any public, methodological or Production change.

## Closeout after the authorized preflight

The full candidate was not run. Pipeline [Issue #218](https://github.com/usdimpact/usd-impact-pipeline/issues/218) records the H.15 release-time vintage failure: the dated Board archive for 2020-01-06 returned HTTP 404. Current revised data cannot be substituted, and the original approval cannot be used for a seventh retry, third-party source, new series, changed weighting or Production.

The original approved receipt is preserved verbatim in `governance/score-v2-1e-real-data-research-authorization-historical-approved-2026-10-28.json`. The **executable** path `governance/score-v2-1e-real-data-research-authorization.json` now contains a HOLD/non-executable receipt with every authorization flag false. The execution contract and `scripts/validate_score_v2_1e_research_authorization.py` enforce the consumed state; the preflight runner refuses before any network call.

Closeout record: `governance/score-v2-1e-preflight-closeout-2026-10-28.json`. Future independent candidate research requires a new methodology version, new preregistration and separate source/research authorization. Issue #155 remains HOLD.
