# Independent Macro Context Panel — closed synthetic preview-result contract

**Recorded:** 2026-10-30. **Scope:** review-only, invented-source 2099+ prototype. This is not a public display schema, live data source, commercial-use grant, production approval, real source integrity proof, or replacement of the eight-driver USD Impact Score.

Controlling records: [Issue #313 — independent candidate rights and owner decisions](https://github.com/usdimpact/usd-impact-pipeline/issues/313), [Issue #155 — legacy Score derived-data HOLD](https://github.com/usdimpact/usd-impact-pipeline/issues/155), and [non-activating owner/counsel queue](../governance/independent-macro-context-owner-counsel-decision-queue-2026-10-30.json). All 56 candidate source permissions, 14 external owner/source approvals, and the original publication HOLD remain unchanged.

## Gap

The prototype's evaluator used synthetic 2099+ invented receipts, coherent Treasury release timestamps, and measurement-basis tags. However, its frozen `SyntheticContextPanel` result dataclass could be created **directly** with `status=SYNTHETIC_ONLY_COMPLETE` and arbitrary `reference_week`, labels, blockers, or weakly typed false-like flags. That bypassed normal evaluator input validation. A standalone preview or future consumer accepting direct result objects could inadvertently display unlabeled real dates, unreviewed recommendations, arbitrary provider-like strings, or a misleading COMPLETE/HOLD result.

## Hardening (non-public, pure standard library)

The dataclass now checks all result fields during construction, regardless of whether the evaluator or an external test caller created the object:

1. **No rights promotion:** all four authorization fields must be the **actual boolean `False`**, not a falsy integer, empty collection, or fake receipt. The exact synthetic-only panel identifier and fixture marker are mandatory.
2. **Synthetic dates:** reference and previous periods must be real calendar Fridays in 2099 or later, using strict four-digit ISO dates; the previous Friday must be exactly seven days earlier. This is invented-fixture protection, not a future real-data calendar rule.
3. **Closed labels:** only four reviewed descriptive fields in fixed order are permitted: `dollar_breadth`, `crude_inventory`, `treasury_curve_level`, `treasury_curve_direction`. Their labels are constrained to `UP/DOWN/UNCHANGED`, `BUILD/DRAW/UNCHANGED`, `POSITIVE/INVERTED/FLAT`, and `STEEPENING/FLATTENING/UNCHANGED` respectively. No ticker prices, forecasts, BUY/SELL terms, component data, free-form titles, URLs, or additional keys.
4. **Status logic:** `SYNTHETIC_ONLY_COMPLETE` requires exactly those four labels and zero blockers. `SYNTHETIC_ONLY_HOLD` requires zero labels and at least one blocker. There is no ambiguous partly completed state.
5. **Closed error vocabulary:** blockers must be unique, sorted and bounded; each must identify one of the two synthetic Fridays, optionally an approved synthetic source ID, and an exact known synthetic fail-closed code. Free-form text, URLs, secrets, real numbers, HTML, newlines and unreviewed provider strings are refused.

These are **output-format and disclosure safeguards only**. A caller can still fabricate a well-formed synthetic result; validity is not authenticity. The `COMPLETE` label **never** means source rights, real-data retrieval, public distribution or Production is approved.

## Tests

The existing `tests/test_independent_macro_context_synthetic.py` suite adds **16 invented-data adversarial checks** to the prior 40. Cases include direct dataclass construction with 2026 dates or invalid 2099 weeks, mismatched previous Friday, malformed/extra/duplicate/unsorted labels, unauthorized trading text, missing or leaked blockers, bogus source codes, oversize/invalid blocker values, and integer-zero authorization coercion. Positive synthetic COMPLETE and HOLD outputs are also validated. No actual price or provider values are accessed.

## Scope and next gates

Only three files change: the dormant pure-Python synthetic engine, its synthetic tests, and this document. No deployment artifact, public/members' site route, Live Score, original Score formula/data, original rights gate, real-data storage, provider API, email correspondence, source-version history or archive is altered. The review requires exact-head protected CI (quality, CodeQL, dependency and frozen research), Git recovery references, non-deploy `[CF-Pages-Skip]` merge, and final read-back.

Before any customer-facing version: resolve original source and transport rights (including upstream exceptions and legally permitted retained versions), owner methodology/naming/audience approval, actual first-publication and historical corrections, independent versioned output schema, privacy/security/compliance and separate Production authorization. None is granted here.
