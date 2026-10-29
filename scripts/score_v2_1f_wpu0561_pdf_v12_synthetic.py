#!/usr/bin/env python3
"""Synthetic-PDF parser exercise only; cannot accept a PDF path or URL.

This is deliberately NOT a general-purpose BLS PDF parser or a live preflight.
Only in-process PDFs generated below are scanned. A real PDF necessarily exposes
its content stream to pypdf and requires a new owner/security/rights decision.
"""

from __future__ import annotations

from io import BytesIO
import json
import re
from typing import Any

from pypdf import PdfReader, PdfWriter
from pypdf.generic import DecodedStreamObject, DictionaryObject, NameObject


FIXTURE_MARKER = "USDIMPACT-SCORE-WPU0561-V12-SYNTHETIC-ONLY"
TITLE = "Table 9. Producer price indexes for commodity and service groupings and individual items"
HEADER = "Commodity code | Item | Unadjusted index"
DIRECT_SCOPE = "Unprocessed nonfood materials"
TARGET = "Crude petroleum"
MONTH = "April 2026"
BANNER = "USD Impact synthetic PDF fixture only"
MAX_FIXTURE_PDF_BYTES = 65536
MAX_FIXTURE_STREAM_BYTES = 32768
MAX_FIXTURE_TEXT_CHARS = 4096
ALLOWED_LINES = frozenset((TITLE, HEADER, DIRECT_SCOPE, TARGET, MONTH, BANNER))

# The set is finite so this executable cannot be used to route arbitrary file,
# URL or economic-value payloads into a PDF parser.
CASES = frozenset({
    "nominal", "percent_only", "wrong_month", "wrong_table",
    "two_tables", "wrong_context", "domestic_variant", "duplicate_target",
    "no_target", "duplicate_header", "wrong_marker", "numeric_text",
    "too_many_pages", "text_overflow", "invalid_magic", "unknown_extra",
})


def _pdf_escape(value: str) -> str:
    if not isinstance(value, str) or not value.isascii():
        raise ValueError("fixture lines must be plain ASCII")
    return value.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def _fixture_lines(case: str) -> list[str]:
    if case not in CASES:
        raise ValueError("only enumerated synthetic cases are supported")
    lines = [BANNER, TITLE, HEADER, DIRECT_SCOPE, TARGET, MONTH]
    if case == "percent_only":
        lines[2] = "Commodity code | Item | Percent change"
    elif case == "wrong_month":
        lines[5] = "May 2026"
    elif case == "wrong_table":
        lines[1] = "Table 7. Other PPI data"
    elif case == "two_tables":
        lines.insert(2, TITLE)
    elif case == "wrong_context":
        lines[3] = "Stage 4 intermediate demand"
    elif case == "domestic_variant":
        lines[4] = "Crude Petroleum (Domestic Production)"
    elif case == "duplicate_target":
        lines.insert(5, TARGET)
    elif case == "no_target":
        lines.pop(4)
    elif case == "duplicate_header":
        lines.insert(3, HEADER)
    elif case == "numeric_text":
        lines.append("Index level 123.45")  # Invented synthetic token: never output value
    elif case == "text_overflow":
        lines.append("Z" * 8000)
    elif case == "unknown_extra":
        lines.append("Unregistered extra column")
    return lines


def _build_synthetic_pdf(case: str) -> bytes:
    if case == "invalid_magic":
        return b"NOT A PDF - SYNTHETIC NEGATIVE CASE"
    writer = PdfWriter()
    page = writer.add_blank_page(width=612, height=792)
    font = writer._add_object(DictionaryObject({
        NameObject("/Type"): NameObject("/Font"),
        NameObject("/Subtype"): NameObject("/Type1"),
        NameObject("/BaseFont"): NameObject("/Helvetica"),
    }))
    page[NameObject("/Resources")] = DictionaryObject({
        NameObject("/Font"): DictionaryObject({NameObject("/F1"): font})
    })
    lines = _fixture_lines(case)
    ops = []
    for i, line in enumerate(lines):
        ops.append(f"BT /F1 10 Tf 20 {760 - 22 * i} Td ({_pdf_escape(line)}) Tj ET")
    stream = DecodedStreamObject()
    stream.set_data("\n".join(ops).encode("ascii"))
    page[NameObject("/Contents")] = writer._add_object(stream)
    if case == "too_many_pages":
        writer.add_blank_page(width=612, height=792)
    writer.add_metadata({
        "/USDImpactFixture": "INVALID" if case == "wrong_marker" else FIXTURE_MARKER
    })
    output = BytesIO()
    writer.write(output)
    return output.getvalue()


def _normalized_lines(text: str) -> list[str]:
    return [" ".join(line.split()).casefold() for line in text.splitlines() if line.strip()]


def _inspect_generated_synthetic_bytes(blob: bytes) -> dict[str, Any]:
    reasons: set[str] = set()
    if not blob.startswith(b"%PDF-"):
        reasons.add("invalid_pdf_magic")
    if len(blob) > MAX_FIXTURE_PDF_BYTES:
        reasons.add("fixture_pdf_oversized")
    if reasons:
        return _result(reasons)
    try:
        reader = PdfReader(BytesIO(blob), strict=True)
        if reader.is_encrypted:
            return _result({"encrypted_pdf"})
        if len(reader.pages) != 1:
            return _result({"unexpected_page_count"})
        if reader.metadata is None or reader.metadata.get("/USDImpactFixture") != FIXTURE_MARKER:
            return _result({"wrong_fixture_marker"})
        page = reader.pages[0]
        content = page.get_contents()
        if content is None:
            return _result({"missing_content_stream"})
        # For generated synthetic data ONLY. On arbitrary PDFs, get_data() can
        # already trigger a decompression bomb; this is NOT a live security gate.
        if len(content.get_data()) > MAX_FIXTURE_STREAM_BYTES:
            return _result({"synthetic_content_stream_oversized"})
        text = page.extract_text(extraction_mode="plain") or ""
    except Exception:
        # No exception contents, decoded stream fragments, file paths or bytes
        # are returned or logged.
        return _result({"parser_failure"})
    if len(text) > MAX_FIXTURE_TEXT_CHARS:
        return _result({"synthetic_text_oversized"})

    lines = _normalized_lines(text)
    title = TITLE.casefold()
    if lines.count(title) != 1:
        reasons.add("table9_missing_or_not_unique")
    if lines.count(HEADER.casefold()) != 1:
        reasons.add("unadjusted_index_header_missing_or_not_unique")
    if lines.count(DIRECT_SCOPE.casefold()) != 1:
        reasons.add("direct_commodity_context_missing")
    if lines.count(TARGET.casefold()) != 1:
        reasons.add("exact_target_missing_or_not_unique")
    if lines.count(MONTH.casefold()) != 1:
        reasons.add("april_month_missing_or_not_unique")
    if lines.count(BANNER.casefold()) != 1:
        reasons.add("not_signed_synthetic_fixture")
    allow = frozenset(s.casefold() for s in ALLOWED_LINES)
    if any(line not in allow for line in lines):
        reasons.add("unexpected_fixture_text")
    if re.search(r"(?<![A-Za-z0-9])\d+[.,]\d+(?![A-Za-z0-9])", text):
        reasons.add("numeric_economic_token_in_fixture")
    return _result(reasons)


def _result(reasons: set[str]) -> dict[str, Any]:
    return {
        "status": "synthetic_format_compatible_not_live" if not reasons else "hold",
        "reason_codes": sorted(reasons),
        "pdf_source": "generated_in_process_synthetic_only",
        "live_pdf_fetched": False,
        "actual_bls_pdf_parsed": False,
        "numeric_identifier_value_retained": False,
        "economic_value_retained": False,
        "source_approved": False,
        "production_changed": False,
        "network_requests": 0,
    }


def run_synthetic_case(case: str) -> dict[str, Any]:
    """Only public entrypoint: construct fixture in memory and inspect it."""
    if case not in CASES:
        raise ValueError("Only fixed synthetic cases are allowed")
    return _inspect_generated_synthetic_bytes(_build_synthetic_pdf(case))


if __name__ == "__main__":
    print(json.dumps(run_synthetic_case("nominal"), indent=2, sort_keys=True))
