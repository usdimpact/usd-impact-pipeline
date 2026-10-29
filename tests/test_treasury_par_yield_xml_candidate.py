"""Synthetic-only tests for the Treasury par-yield XML candidate.

Fixtures below are fabricated future observations, not provider observations.
No test may call Treasury, FRED, H.15 or any other network endpoint.
"""

from __future__ import annotations

import json
import unittest
from pathlib import Path
from datetime import date, timedelta
from decimal import Decimal

from scripts.treasury_par_yield_xml_candidate import (
    MAX_ENTRIES_PER_PAGE,
    MAX_XML_BYTES,
    TreasuryXMLContractError,
    parse_treasury_par_yield_atom,
)


def _fixture(rows: list[tuple[str, str, str]]) -> str:
    entries = []
    for day, two, ten in rows:
        entries.append(
            "<entry><content type='application/xml'><m:properties>"
            f"<d:NEW_DATE>{day}</d:NEW_DATE>"
            f"<d:BC_2YEAR>{two}</d:BC_2YEAR>"
            f"<d:BC_10YEAR>{ten}</d:BC_10YEAR>"
            "<d:BC_1MONTH>0.99</d:BC_1MONTH>"
            "</m:properties></content></entry>"
        )
    return (
        "<feed xmlns='http://www.w3.org/2005/Atom'"
        " xmlns:m='http://schemas.microsoft.com/ado/2007/08/dataservices/metadata'"
        " xmlns:d='http://schemas.microsoft.com/ado/2007/08/dataservices'>"
        + "".join(entries)
        + "</feed>"
    )


def _valid() -> str:
    return _fixture(
        [
            ("2099-01-06T00:00:00", "1.50", "2.75"),
            ("2099-01-05T00:00:00", "1.25", "2.50"),
        ]
    )



def _parse(xml_payload: bytes | str, *, period: str = "2099"):
    """Exercise the explicitly scoped synthetic 2099 selection."""
    return parse_treasury_par_yield_atom(xml_payload, selected_period=period)


class TreasuryXMLCandidateTests(unittest.TestCase):
    def test_explicit_year_or_month_selection_required(self) -> None:
        with self.assertRaisesRegex(TreasuryXMLContractError, "explicit"):
            parse_treasury_par_yield_atom(_valid())
        for period in ("all", "", "2099-01", "2099x", None, "209900", "209913"):
            with self.subTest(period=period):
                with self.assertRaises(TreasuryXMLContractError):
                    parse_treasury_par_yield_atom(_valid(), selected_period=period)
        self.assertEqual(len(_parse(_valid(), period="2099")), 2)
        self.assertEqual(len(_parse(_valid(), period="209901")), 2)

    def test_rejects_rows_outside_explicit_request_period(self) -> None:
        with self.assertRaisesRegex(TreasuryXMLContractError, "outside explicit period"):
            _parse(_valid(), period="209902")
        adjacent_year = _valid().replace("2099-01-06", "2098-01-06")
        with self.assertRaisesRegex(TreasuryXMLContractError, "outside explicit period"):
            _parse(adjacent_year, period="2099")

    def test_rejects_next_page_links_and_uri_next_relations(self) -> None:
        for relation in (
            "next",
            "http://schemas.microsoft.com/ado/2007/08/dataservices/next",
            "https://example.invalid/feed#next",
            "NEXT",
        ):
            with self.subTest(rel=relation):
                payload = _valid().replace(
                    "</feed>",
                    f"<link rel='{relation}' href='https://example.invalid/page2'/></feed>",
                )
                with self.assertRaisesRegex(TreasuryXMLContractError, "paginated"):
                    _parse(payload)
        self.assertEqual(
            len(_parse(_valid().replace(
                "</feed>", "<link rel='self' href='https://example.invalid/current'/></feed>",
            ))),
            2,
        )

    def test_inline_odata_count_cannot_hide_missing_pages(self) -> None:
        good = _valid().replace("</feed>", "<m:count>2</m:count></feed>")
        self.assertEqual(len(_parse(good)), 2)
        for suffix in (
            "<m:count>3</m:count>",
            "<m:count>0</m:count>",
            "<m:count>NaN</m:count>",
            "<m:count>2</m:count><m:count>2</m:count>",
        ):
            with self.subTest(marker=suffix):
                payload = _valid().replace("</feed>", suffix + "</feed>")
                with self.assertRaises(TreasuryXMLContractError):
                    _parse(payload)

    def test_yearly_or_monthly_coverage_is_not_claimed_without_evidence(self) -> None:
        # A one-page subset with no continuation marker is accepted as rows,
        # but the parser deliberately returns no coverage/completeness proof.
        one_row = _fixture([("2099-01-05T00:00:00", "1.25", "2.50")])
        observations = _parse(one_row, period="209901")
        self.assertEqual(len(observations), 1)
        self.assertNotIn("coverage_verified", observations[0].__dataclass_fields__)


    def test_governance_contract_remains_fail_closed(self) -> None:
        root = Path(__file__).resolve().parents[1]
        contract = json.loads(
            (root / "governance/treasury-par-yield-xml-candidate-2026-10-29.json")
            .read_text(encoding="utf-8")
        )
        self.assertEqual(contract["status"], "synthetic_only_unapproved")
        self.assertEqual(
            contract["go_no_go"],
            "NO_GO_PENDING_RIGHTS_TIMING_PARITY_AND_OWNER_RELEASE_AUTHORIZATION",
        )
        self.assertEqual(contract["dataset_parameter"], "daily_treasury_yield_curve")
        self.assertEqual(
            contract["data_fields"],
            {
                "observation_date": "NEW_DATE",
                "ust_2y_percent": "BC_2YEAR",
                "ust_10y_percent": "BC_10YEAR",
            },
        )
        for key, approved in contract["safety"].items():
            with self.subTest(control=key):
                self.assertIs(approved, False)
        pagination = contract["pagination_scope"]
        self.assertEqual(pagination["required_selection"], "YYYY or YYYYMM")
        for key in (
            "all_time_page_traversal_supported",
            "explicit_next_links_accepted",
            "inline_count_mismatch_accepted",
            "full_coverage_verified",
        ):
            with self.subTest(pagination_control=key):
                self.assertIs(pagination[key], False)

    def test_valid_synthetic_atom_page_maps_and_sorts_only_target_fields(self) -> None:
        observations = _parse(_valid().encode("utf-8"))
        self.assertEqual(len(observations), 2)
        self.assertEqual(
            [str(item.observation_date) for item in observations],
            ["2099-01-05", "2099-01-06"],
        )
        self.assertEqual(observations[0].ust_2y_percent, Decimal("1.25"))
        self.assertEqual(observations[0].ust_10y_percent, Decimal("2.50"))
        self.assertEqual(observations[1].ust_2y_percent, Decimal("1.50"))

    def test_candidate_values_are_not_a_release_timestamp(self) -> None:
        fields = set(_parse(_valid())[0].__dataclass_fields__)
        self.assertEqual(
            fields,
            {"observation_date", "ust_2y_percent", "ust_10y_percent"},
        )
        self.assertNotIn("published_at", fields)

    def test_synthetic_equivalence_can_be_checked_without_retrieval(self) -> None:
        # This only shows a fixture-level source-parity contract, not real parity.
        expected_board_h15_synthetic = {
            date(2099, 1, 5): (Decimal("1.25"), Decimal("2.50")),
            date(2099, 1, 6): (Decimal("1.50"), Decimal("2.75")),
        }
        actual = {
            obs.observation_date: (obs.ust_2y_percent, obs.ust_10y_percent)
            for obs in _parse(_valid())
        }
        self.assertEqual(actual, expected_board_h15_synthetic)

    def test_rejects_empty_feed_and_wrong_root(self) -> None:
        for payload in (
            _fixture([]),
            "<root/>",
        ):
            with self.subTest(payload=payload[:30]):
                with self.assertRaises(TreasuryXMLContractError):
                    _parse(payload)

    def test_rejects_duplicate_dates(self) -> None:
        duplicate = _fixture(
            [
                ("2099-01-05T00:00:00", "1.25", "2.50"),
                ("2099-01-05T00:00:00", "1.50", "2.75"),
            ]
        )
        with self.assertRaisesRegex(TreasuryXMLContractError, "duplicate"):
            _parse(duplicate)

    def test_rejects_missing_or_explicit_null_values(self) -> None:
        missing = _valid().replace("<d:BC_2YEAR>1.50</d:BC_2YEAR>", "")
        null = _valid().replace(
            "<d:BC_2YEAR>1.50</d:BC_2YEAR>",
            "<d:BC_2YEAR m:null='true'/>",
        )
        for payload in (missing, null):
            with self.subTest(fragment=payload[:25]):
                with self.assertRaises(TreasuryXMLContractError):
                    _parse(payload)

    def test_rejects_invalid_values(self) -> None:
        for value in ("NaN", "Inf", "1e12", "10,000", "101", ""):
            payload = _valid().replace(
                "<d:BC_10YEAR>2.75</d:BC_10YEAR>",
                f"<d:BC_10YEAR>{value}</d:BC_10YEAR>",
            )
            with self.subTest(value=value):
                with self.assertRaises(TreasuryXMLContractError):
                    _parse(payload)

    def test_negative_yield_values_are_valid_decimal_data(self) -> None:
        payload = _valid().replace(
            "<d:BC_2YEAR>1.50</d:BC_2YEAR>",
            "<d:BC_2YEAR>-0.25</d:BC_2YEAR>",
        )
        self.assertEqual(
            _parse(payload)[1].ust_2y_percent,
            Decimal("-0.25"),
        )

    def test_rejects_bad_or_nonmidnight_dates(self) -> None:
        for invalid_date in (
            "2099-99-05T00:00:00",
            "2099-01-05",
            "2099-01-05T16:15:00",
        ):
            payload = _valid().replace("2099-01-05T00:00:00", invalid_date)
            with self.subTest(date=invalid_date):
                with self.assertRaises(TreasuryXMLContractError):
                    _parse(payload)

    def test_rejects_malformed_and_unsafe_xml(self) -> None:
        for payload in (
            b"<broken",
            b"<!DOCTYPE feed [<!ENTITY x 'payload'>]>" + _valid().encode(),
            b"<!ENTITY x 'payload'>" + _valid().encode(),
        ):
            with self.subTest(length=len(payload)):
                with self.assertRaises(TreasuryXMLContractError):
                    _parse(payload)

    def test_rejects_oversize_payload_or_excessive_page(self) -> None:
        with self.assertRaises(TreasuryXMLContractError):
            _parse(b"x" * (MAX_XML_BYTES + 1))
        start = date(2099, 1, 1)
        rows = [
            ((start + timedelta(days=i)).isoformat() + "T00:00:00", "1.0", "2.0")
            for i in range(MAX_ENTRIES_PER_PAGE + 1)
        ]
        with self.assertRaisesRegex(TreasuryXMLContractError, "entry count"):
            _parse(_fixture(rows))

    def test_rejects_duplicate_target_field_and_absent_properties(self) -> None:
        duplicated = _valid().replace(
            "<d:BC_2YEAR>1.50</d:BC_2YEAR>",
            "<d:BC_2YEAR>1.50</d:BC_2YEAR><d:BC_2YEAR>9</d:BC_2YEAR>",
        )
        wrong_namespace = _valid().replace(
            "http://schemas.microsoft.com/ado/2007/08/dataservices/metadata",
            "urn:incorrect:metadata",
        )
        for payload in (duplicated, wrong_namespace):
            with self.assertRaises(TreasuryXMLContractError):
                _parse(payload)


if __name__ == "__main__":
    unittest.main()
