#!/usr/bin/env python3
"""Strict offline parser for a synthetic Treasury par-yield OData/Atom page.

Issue #282 research only: NO network, filesystem writes, FRED fetch, live
Treasury fetch, Score production adapter, or rights authorization here.
The schema is a candidate based on the published Treasury XML feed docs;
real-feed compatibility and observation-to-release timing remain unverified.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date
from decimal import Decimal, InvalidOperation
from xml.etree import ElementTree as ET


ATOM = "{http://www.w3.org/2005/Atom}"
META = "{http://schemas.microsoft.com/ado/2007/08/dataservices/metadata}"
DATA = "{http://schemas.microsoft.com/ado/2007/08/dataservices}"
MAX_XML_BYTES = 2_000_000
MAX_ENTRIES_PER_PAGE = 400
DATE_TEXT = re.compile(r"^\d{4}-\d{2}-\d{2}T00:00:00(?:\.0+)?$")
DECIMAL_TEXT = re.compile(r"^-?\d+(?:\.\d+)?$")
FORBIDDEN_XML = re.compile(rb"<!\s*(?:DOCTYPE|ENTITY)\b", flags=re.IGNORECASE)


class TreasuryXMLContractError(ValueError):
    """The input cannot be trusted as a valid Treasury yield-curve page."""


@dataclass(frozen=True)
class TreasuryParYieldObservation:
    observation_date: date
    ust_2y_percent: Decimal
    ust_10y_percent: Decimal


def _one_field(properties: ET.Element, name: str) -> str:
    matches = properties.findall(DATA + name)
    if len(matches) != 1:
        raise TreasuryXMLContractError(f"expected one {name} field")
    node = matches[0]
    if META + "null" in node.attrib:
        raise TreasuryXMLContractError(f"{name} has an explicit null marker")
    value = (node.text or "").strip()
    if not value:
        raise TreasuryXMLContractError(f"{name} is blank")
    return value


def _percent(value: str, field: str) -> Decimal:
    if not DECIMAL_TEXT.fullmatch(value):
        raise TreasuryXMLContractError(f"invalid numeric format in {field}")
    try:
        number = Decimal(value)
    except InvalidOperation as exc:
        raise TreasuryXMLContractError(f"invalid decimal in {field}") from exc
    if not number.is_finite() or abs(number) > 100:
        raise TreasuryXMLContractError(f"invalid percentage range in {field}")
    return number


def parse_treasury_par_yield_atom(
    xml_payload: bytes | str,
) -> tuple[TreasuryParYieldObservation, ...]:
    """Parse one candidate Treasury XML response entirely in memory.

    This function accepts ONLY the documented Atom + OData namespaces and
    required NEW_DATE, BC_2YEAR and BC_10YEAR fields. It intentionally has
    no network/file I/O. Entries are sorted and dates must be unique.
    An observation date is NOT evidence of a release/availability timestamp.
    """
    if isinstance(xml_payload, str):
        payload = xml_payload.encode("utf-8")
    elif isinstance(xml_payload, bytes):
        payload = xml_payload
    else:
        raise TreasuryXMLContractError("XML input must be bytes or text")
    if not payload or len(payload) > MAX_XML_BYTES:
        raise TreasuryXMLContractError("XML payload is empty or exceeds size limit")
    if FORBIDDEN_XML.search(payload):
        raise TreasuryXMLContractError("DOCTYPE/ENTITY declarations are forbidden")
    try:
        root = ET.fromstring(payload)
    except ET.ParseError as exc:
        raise TreasuryXMLContractError("malformed XML") from exc
    if root.tag != ATOM + "feed":
        raise TreasuryXMLContractError("expected Atom feed root")

    entries = root.findall(ATOM + "entry")
    if not 1 <= len(entries) <= MAX_ENTRIES_PER_PAGE:
        raise TreasuryXMLContractError("empty page or excessive entry count")

    by_date: dict[date, TreasuryParYieldObservation] = {}
    for entry in entries:
        candidates = entry.findall(ATOM + "content/" + META + "properties")
        if len(candidates) != 1:
            raise TreasuryXMLContractError("entry lacks exactly one properties element")
        properties = candidates[0]
        raw_date = _one_field(properties, "NEW_DATE")
        if not DATE_TEXT.fullmatch(raw_date):
            raise TreasuryXMLContractError("unexpected observation timestamp format")
        try:
            observed = date.fromisoformat(raw_date[:10])
        except ValueError as exc:
            raise TreasuryXMLContractError("invalid observation date") from exc
        if observed in by_date:
            raise TreasuryXMLContractError("duplicate observation date")

        by_date[observed] = TreasuryParYieldObservation(
            observation_date=observed,
            ust_2y_percent=_percent(_one_field(properties, "BC_2YEAR"), "BC_2YEAR"),
            ust_10y_percent=_percent(_one_field(properties, "BC_10YEAR"), "BC_10YEAR"),
        )

    return tuple(by_date[day] for day in sorted(by_date))
