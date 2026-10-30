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


## Follow-up — closed internal JSON wire shape (2026-10-30)

The evaluator's **direct Python dataclass checks remain authoritative for synthetic-fixture logic**. A consumer serializing a SyntheticContextPanel into JSON otherwise lacked a versioned, machine-readable *wire format*. The [internal invented-preview JSON Schema](../schemas/independent_macro_context_synthetic_preview.schema.json) closes that additional boundary without adding an HTTP route, deployment artifact, input feed or public data contract.

- **Internal-only identity:** the schema uses an internal URN identifier, not a publishable HTTPS endpoint, and requires the existing exact independent synthetic panel ID and SYNTHETIC_DO_NOT_PUBLISH fixture marker.
- **No rights escalation:** exactly the existing eleven dataclass fields are required, root extras are forbidden and four flags (rights_cleared, real_data_fetch_authorized, publish_authorized, production_authorized) must be literal booleans false.
- **Closed states and label order:** SYNTHETIC_ONLY_COMPLETE requires the same four ordered source-category/qualitative-label pairs with no blockers. SYNTHETIC_ONLY_HOLD requires zero labels and at least one bounded synthetic blocker. Arbitrary prices, new regimes, URL fields and BUY/SELL claims are not permitted.
- **Invented-only period syntax:** the schema accepts only four-digit 2099 or later year tokens for source-reference dates, and closed synthetic error codes. It deliberately **does not authenticate** a source release or independently verify that a date is a real **Friday**, the previous Friday is seven days earlier, a blocker refers to one of those Fridays, the blocker list is sorted, or exact source-first-seen chronology was followed. Those semantic checks remain in the pure Python dataclass/evaluator and would need separate implementation in a future consumer. A matching 2099 JSON document can still be wholly fabricated; the schema is **not a public** market-data schema or a commercial-rights grant.
- **No additional runtime dependency:** the new standard-library tests pin the schema properties, both status conditions, exact dial enumeration, invented-period syntax, all-false rights policy and Python dataclass field parity. If jsonschema happens to be installed, an *additional optional* Draft 2020-12 validator exercise checks successful invented COMPLETE/HOLD documents and malicious mutations; its presence is not needed for the pinned CI test boundary.

The closed schema deliberately avoids a published route, live feed, current-year market dates, values, provider URLs, a composite Score, a member plan, real-data retention or Source/FRED substitutions. The independent panel's **56/56 source permissions and 14/14 external authority gates remain false**, as do original Score publication rights. Any future *real* output schema, publisher receipts, access method and source-specific legal permissions require separate counsel and owner decisions; this internal artifact cannot be relabeled or activated.

**Scope:** one new internal schema, one new offline test module and this appended explanation only. Preserve Draft website [PR #998](https://github.com/usdimpact/usd-impact-site/pull/998) unmerged and unpublished; its sitemap/access issues remain separate and unresolved. No Production deployment or live observation access.
