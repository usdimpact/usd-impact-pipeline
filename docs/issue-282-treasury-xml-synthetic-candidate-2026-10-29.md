# Issue #282 — Direct Treasury par-yield XML parser, synthetic-only (2026-10-29)

**Status:** review-only, no real data, no source switch, no paid access, no publication authorization, and no Production change. Issue #155 rights HOLD remains controlling.

## Why this specific component

The Score v2 pipeline currently fetches FRED **DGS2** and **DGS10** and includes provider-derived Treasury components in multiple historical public artifacts. [Issue #282](https://github.com/usdimpact/usd-impact-pipeline/issues/282) is auditing retention and commercial derived-output rights.

The U.S. Treasury directly publishes the nominal Daily Treasury Par Yield Curve Rates. The [official Treasury feed documentation](https://home.treasury.gov/treasury-daily-interest-rate-xml-feed) describes a year/month-based Atom/OData XML endpoint, and the [Treasury developer notice](https://home.treasury.gov/developer-notice-xml-changes) describes the current pagination model. [Federal Reserve H.15](https://www.federalreserve.gov/releases/h15/) identifies Treasury as the source of its nominal constant-maturity yield series.

**Do not misread this as clearance**: the owner, republisher, and transport are separate. Neither the Treasury source nor the H.15/FRB/FRED user-facing rights have been resolved for the whole Score product. Nominal published yield curves are also derived from upstream dealer-market quotations; those raw inputs are *not* in scope.

## New files

- `scripts/treasury_par_yield_xml_candidate.py` — pure Python, in-memory parsing of one candidate Atom/OData XML page; NO HTTP client and NO persistence.
- `tests/test_treasury_par_yield_xml_candidate.py` — invented future-date observations only, including positive and fail-closed cases.
- `governance/treasury-par-yield-xml-candidate-2026-10-29.json` — exact candidate scope and negative authorization flags.

The parser maps the *assumed, unverified live-compatible* Treasury XML data fields:

| Treasury field | Internal candidate | Meaning |
|---|---|---|
| `NEW_DATE` | `observation_date` | Observation date, **not** verified release timestamp |
| `BC_2YEAR` | `ust_2y_percent` | Nominal 2-year par yield (percentage-point unit) |
| `BC_10YEAR` | `ust_10y_percent` | Nominal 10-year par yield (percentage-point unit) |

The schema expectation is based on Treasury XML/OData documentation and conventional field names, **not a fresh live XML fetch or parsed verified provider sample**. If the schema differs, the parser must fail closed pending review, rather than heuristically reinterpret records.

## Safety and parsing checks

The parser rejects malformed XML, unsafe XML DOCTYPE/ENTITY declarations, missing properties, absent/blank/null target values, non-finite or non-decimal yields, duplicate dates, non-midnight/unexpected date formats, empty feeds, unusually large payloads, and excessive record counts. It accepts extra unrelated market-maturity fields but does not import them.

The tests use invented observations in 2099. They demonstrate that a *synthetic* H.15-shaped comparison can match after normalizing fields, but prove **nothing** about live series parity. No synthetic run should access real endpoints.

## Non-equivalence and timing risks

The existing [synthetic provider-neutral adapter](score-source-adapter-synthetic-parity-2026-10-28.md) already verifies that simple column mappings and unit conversions can preserve Score v2 arithmetic. This parser only prepares the direct Treasury feed for similar later review. It does not replace or bypass that framework and is **not** a new v2.1E methodology selection.

Before any permitted real-data comparison, the owner must approve the exact access, retention and derivation rights; the protocol then must compare:

1. Treasury 2Y/10Y daily yield *levels*, units, corrections and missing values to Board H.15 and current FRED DGS2/DGS10 across the frozen historical windows.
2. Friday cutoff semantics: which observations were **published and accessible** by the actual cutoff, not merely stamped with that observation date.
3. H.15 4:15 p.m. ET release, Treasury publication delay and timezones; holiday/early-close/revision/vintage edge cases.
4. Historical normalization, full 8-driver alignment, `ffill(limit=3)`, weekly resample, component z-scores, aggregate Score and regime in the existing offline parity harness.
5. Source-owner notices, commercial reuse and historical retention, third-party input exclusions and authorization for **public aggregates**.
6. API schema changes, per-year availability, pagination, downstream backup/log/CDN storage and disaster recovery.
7. Release rollback and the historical-FRED data remediation plan; do not erase reproducibility evidence before a separately approved preservation plan.

## Exact go/no-go

**NO-GO** until: source/transport rights are individually documented, legally relevant retention and public-derived use are approved, one-off real research is separately authorized, release-time/parity testing is independently reviewed, existing data-copy remediation is planned, and Issue #155's protected gate receives separate written release authorization.

No PR from this work should change `usd_impact_score_v2.py`, Score v2 weights/formula, the private evidence broker, Cloudflare Pages routing, Vercel, Supabase, payments, memberships, or live artifacts.

## References

- [U.S. Treasury — Daily Interest Rate XML Feed](https://home.treasury.gov/treasury-daily-interest-rate-xml-feed)
- [U.S. Treasury — XML Developer Notice](https://home.treasury.gov/developer-notice-xml-changes)
- [U.S. Treasury — Treasury Yield Curve Methodology](https://home.treasury.gov/policy-issues/financing-the-government/interest-rate-statistics/treasury-yield-curve-methodology)
- [Federal Reserve Board — H.15 release](https://www.federalreserve.gov/releases/h15/)
- [FRED — legal and data series terms](https://fred.stlouisfed.org/legal/terms/)
