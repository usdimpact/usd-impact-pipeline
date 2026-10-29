#!/usr/bin/env python3
"""Restricted BLS PPI PDF structural gate.

Reads a single PDF through stdin ONLY inside a network-isolated resource-limited
process. Never prints extracted text, numeric identifiers, economic values,
full dates, freeform PDF metadata, or line excerpts. Reports only finite
structural status booleans. No source selection beyond this one PDF.

Security caveat: PDF bytes and decoded page text are transiently in process
memory; a cgroup memory bound protects against extreme decompression expansion.
No untrusted real PDF may be parsed without a *separately activated* one-off run.
"""

from __future__ import annotations

from io import BytesIO
import json
import re
import sys
from typing import Any

from pypdf import PdfReader


MAX_WIRE_BYTES = 10 * 1024 * 1024
MAX_PAGES = 200
MAX_PAGE_CONTENT_BYTES = 256 * 1024
MAX_TOTAL_CONTENT_BYTES = 4 * 1024 * 1024
MAX_PAGE_TEXT_CHARS = 16384
MAX_OUTPUT_BYTES = 4096
ALLOWED_CODES = frozenset({
    "unexpected_pdf_magic", "pdf_size_bound", "pdf_load_failed", "encrypted_document",
    "invalid_page_count", "page_content_bound", "total_content_bound", "page_text_bound",
    "parser_failure", "missing_table9_title", "missing_index_level_header",
    "missing_commodity_header", "missing_exact_crude_label", "missing_direct_scope",
    "ambiguous_repeated_title", "target_label_variant", "no_first_release_vintage_proof",
    "unexpected_status",
})


def result(reason_codes: set[str], *, flags: dict[str, bool] | None = None, page_count: int | None = None) -> dict[str, Any]:
    f = flags or {}
    output = {
        "status": "fail_closed" if reason_codes - {"no_first_release_vintage_proof"} else "structural_metadata_only_hold",
        "reason_codes": sorted(reason_codes),
        "page_count_band": "unknown" if page_count is None else ("1_to_50" if page_count <= 50 else "51_to_200"),
        "table9_title_seen": f.get("table9", False),
        "unadjusted_index_role_seen": f.get("index", False),
        "percent_change_role_seen": f.get("percent_change", False),
        "target_label_seen": f.get("label", False),
        "target_scope_seen": f.get("scope", False),
        "ambiguous_layout": f.get("ambiguous", True),
        "vintage_proven": False,
        "identifier_values_retained": False,
        "economic_values_retained": False,
        "network_requests": 0,
    }
    assert set(output["reason_codes"]) <= ALLOWED_CODES
    assert len(json.dumps(output)) < MAX_OUTPUT_BYTES
    return output


def inspect_bytes(blob: bytes) -> dict[str, Any]:
    if not blob.startswith(b"%PDF-"):
        return result({"unexpected_pdf_magic"})
    if len(blob) > MAX_WIRE_BYTES:
        return result({"pdf_size_bound"})
    try:
        pdf = PdfReader(BytesIO(blob), strict=True)
        if pdf.is_encrypted:
            return result({"encrypted_document"})
        count = len(pdf.pages)
        if count < 1 or count > MAX_PAGES:
            return result({"invalid_page_count"})
    except Exception:
        return result({"pdf_load_failed"})
    title_pages: list[int] = []
    target_page_matches = 0
    content_total = 0
    flags = {"table9": False, "index": False, "percent_change": False, "label": False, "scope": False, "ambiguous": False}
    try:
        in_table9 = False
        for i, page in enumerate(pdf.pages):
            stream = page.get_contents()
            if stream is None:
                continue
            # This untrusted decompression happens ONLY inside networkless,
            # read-only, memory/pid/CPU-bounded container. get_data() itself can
            # expand before length check; memory cgroup limit is essential.
            data = stream.get_data()
            if len(data) > MAX_PAGE_CONTENT_BYTES:
                return result({"page_content_bound"}, flags=flags, page_count=count)
            content_total += len(data)
            if content_total > MAX_TOTAL_CONTENT_BYTES:
                return result({"total_content_bound"}, flags=flags, page_count=count)
            del data
            raw = page.extract_text(extraction_mode="plain") or ""
            if len(raw) > MAX_PAGE_TEXT_CHARS:
                return result({"page_text_bound"}, flags=flags, page_count=count)
            # Classify only structural phrases; do not record or print raw text.
            # A text extractor necessarily decoded source numeric characters;
            # this was separately owner-approved for transient private preflight.
            if re.search(r"\btable\s*9\b", raw, flags=re.IGNORECASE):
                in_table9 = True
                title_pages.append(i)
                flags["table9"] = True
            if in_table9 and re.search(r"\btable\s*10\b", raw, flags=re.IGNORECASE):
                in_table9 = False
            if not in_table9:
                continue
            safe = re.sub(r"\d+(?:[\.,]\d+)?", "<num>", raw.lower())
            if "unadjusted index" in " ".join(safe.split()):
                flags["index"] = True
            if "percent change" in " ".join(safe.split()):
                flags["percent_change"] = True
            if "commodity code" in " ".join(safe.split()):
                flags["commodity"] = True
            if "unprocessed nonfood materials" in " ".join(safe.split()):
                flags["scope"] = True
            for line in safe.splitlines():
                normalized = " ".join(line.split())
                if re.search(r"\bcrude petroleum\s*\(domestic production\)", normalized):
                    flags["ambiguous"] = True
                elif "crude petroleum" in normalized:
                    # Require exact lexical label and reject variants; numeric
                    # indexes on the row are already removed.
                    if re.search(r"(?<![a-z])crude petroleum(?![a-z(])", normalized):
                        flags["label"] = True
                        target_page_matches += 1
            del raw, safe
    except (MemoryError, Exception):
        return result({"parser_failure"}, flags=flags, page_count=count)
    flags["ambiguous"] = flags["ambiguous"] or len(title_pages) > 1 or target_page_matches > 1
    codes: set[str] = {"no_first_release_vintage_proof"}
    if not flags["table9"]:
        codes.add("missing_table9_title")
    if not flags["index"]:
        codes.add("missing_index_level_header")
    if not flags.get("commodity", False):
        codes.add("missing_commodity_header")
    if not flags["label"]:
        codes.add("missing_exact_crude_label")
    if not flags["scope"]:
        codes.add("missing_direct_scope")
    if len(title_pages) > 1 or target_page_matches > 1:
        codes.add("ambiguous_repeated_title")
    if flags["ambiguous"] and "ambiguous_repeated_title" not in codes:
        codes.add("target_label_variant")
    # Even a compatible structural result stays HOLD: PDF vintage, revisions,
    # basis and exact identifier must be proven independently.
    return result(codes, flags=flags, page_count=count)


def main() -> int:
    try:
        data = sys.stdin.buffer.read(MAX_WIRE_BYTES + 1)
        print(json.dumps(inspect_bytes(data), sort_keys=True))
        return 0
    except Exception:
        print(json.dumps(result({"parser_failure"}), sort_keys=True))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
