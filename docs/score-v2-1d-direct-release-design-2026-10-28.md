# Score v2.1D direct-release zero-budget alternative — 2026-10-28

Status: **design only**.

## Objective

Remove the two remaining composite-index rights blockers from v2.1C without reintroducing paid/proprietary market feeds.

v2.1D uses direct Board/EIA statistical releases only.

## Eight slots

| Slot | Direct release | Transformation | Weight |
|---|---|---|---:|
| USD | H.10 broad dollar index | level | +0.125 |
| Energy | EIA WTI Cushing spot | log level | -0.125 |
| Financial conditions | H.8 Bank Credit, all commercial banks | negative 13-week log change | +0.125 |
| Financial stress | H.4.1 Primary Credit outstanding | log1p level | +0.125 |
| Liquidity | H.4.1 Total Assets | 13-week log change | -0.125 |
| Real yield | H.15 10Y TIPS yield | level | +0.125 |
| 2Y | H.15 2Y Treasury | level | +0.125 |
| 10Y | H.15 10Y Treasury | level | +0.125 |

## Financial-conditions replacement: H.8 Bank Credit

H.8 is a direct Board weekly statistical release.

The proposed first-study transformation is:

`-log(BankCredit_t / BankCredit_t-13w)`

so a contraction in bank credit becomes a positive tightening signal.

Why it is attractive:
- direct Board release;
- weekly frequency;
- long history;
- conceptually related to availability/expansion of bank balance-sheet credit.

Why it is imperfect:
- bank credit reflects both supply and borrower demand;
- H.8 is estimated from reporting panels and Call Reports;
- historical releases can be revised, benchmarked and reclassified;
- it is not a broad market financial-conditions index.

Any real study must use historical release vintages rather than today's revised history where feasible.

## Financial-stress replacement: H.4.1 Primary Credit

The Board states that Primary Credit outstanding is reported in table 1 of H.4.1.

The proposed transform is:

`log1p(primary_credit_level)`

This handles zero/near-zero periods while retaining large crisis spikes.

Why it is attractive:
- direct Board release;
- weekly Wednesday level, normally published Thursday;
- economically interpretable as use of the Federal Reserve discount window.

Why it is imperfect:
- discount-window stigma can suppress usage;
- some crises use special facilities instead;
- long quiet periods can make the standardized distribution sparse;
- crisis-time Primary Credit may correlate with Federal Reserve balance-sheet expansion.

Those are research questions, not reasons to optimize the transform after seeing results.

## Rights posture

The candidate relies on:
- seven direct Board statistical-release inputs;
- one EIA-published spot-price input.

The Board's public-domain default and EIA's explicit reuse statement make this a materially cleaner architecture than the composite-index candidates.

However:
- no source is approved by this design;
- each exact Board item still needs an exception check;
- EIA release-history timing must be pinned;
- no legal conclusion is made.

## Timing

Point-in-time rules remain mandatory.

- H.10: previous business week's daily observations become available Monday at 4:15 p.m. ET.
- H.8: released Friday, generally 4:15 p.m. ET; historical release contents must be used as published.
- H.4.1: Thursday, generally 4:30 p.m. ET.
- H.15: Monday-Friday, 4:15 p.m. ET.
- EIA WTI: use explicit EIA release dates rather than market observation date.

## Candidate status

v2.1D is currently the cleanest **conceptual** zero-budget architecture from a source-rights perspective because it avoids required composite indexes built from proprietary feeds.

It is not yet a validated methodology.

Next safe work is limited to:
1. pin exact H.8/H.4.1 item identifiers;
2. document release/vintage handling;
3. build synthetic-only timing and transform tests;
4. preregister research thresholds.

No real-data research is authorized.
