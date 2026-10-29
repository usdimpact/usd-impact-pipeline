#!/usr/bin/env python3
"""Pure structural helpers for Issue #258 ambiguity-diagnostics design.

This module performs no network I/O and has no file-writing path. It exists to
prove candidate-local scoping, layered semantic status, and conservative header
interpretation on synthetic rows before any future owner-authorized live
diagnostic.
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass

IDENTIFIER_HEADERS = ("commodity code", "series code", "series id", "item code")
BARE_CODE_HEADER_RE = re.compile(r"\bcode\b")
DESCRIPTION_HEADERS = ("commodity", "item", "description")
REVISION_CONTEXT_TERMS = ("preliminary", "final", "revised", "corrected")
TRANSPORT_REASON_CODES = ("transport_dns_failure", "http_access_control")
MAX_HEADER_DEPTH = 3


def normalize_header(value: str) -> str:
    return re.sub(r"\s+", " ", unicodedata.normalize("NFKC", value)).strip().lower()


def header_role(value: str) -> str | None:
    normalized = normalize_header(value)
    identifier = any(term in normalized for term in IDENTIFIER_HEADERS) or bool(BARE_CODE_HEADER_RE.search(normalized))
    percent_change = "percent" in normalized or "%" in normalized or "change" in normalized
    index_level = "index" in normalized and not percent_change
    description = any(term in normalized for term in DESCRIPTION_HEADERS)

    if identifier and (percent_change or index_level):
        return "ambiguous"
    if identifier:
        return "identifier"
    if percent_change:
        return "percent_change"
    if index_level:
        return "index_level"
    if description:
        return "description"
    return None


def normalize_identifier(value: str) -> str | None:
    normalized = unicodedata.normalize("NFKC", value).strip().upper()
    normalized = re.sub(r"[\s\-\u2010\u2011\u2012\u2013\u2014\u2015]+", "", normalized)
    if normalized.startswith("WPU"):
        normalized = normalized[3:]
    if normalized in {"0561", "561"}:
        return "0561"
    return None


def is_blank_row(row: list[str]) -> bool:
    return not any(cell.strip() for cell in row)


def _row_header_role_count(row: list[str]) -> int:
    return sum(1 for cell in row if header_role(cell) is not None)


def _row_has_header_role(row: list[str]) -> bool:
    return _row_header_role_count(row) > 0


def _role_for_header_path(texts: tuple[str, ...]) -> str | None:
    """Resolve a local multi-row header path from leaf to parent.

    The most specific recognized child/leaf header wins. A mixed leaf such as
    "Index code" remains explicitly ambiguous. Broader parent/group labels do
    not override a recognized child role.
    """
    for text in reversed(texts):
        role = header_role(text)
        if role is not None:
            return role
    return None


def _header_stack_start(rows: list[list[str]], end_row: int) -> int:
    start_row = end_row
    while start_row > 1 and (end_row - start_row + 1) < MAX_HEADER_DEPTH:
        prior = rows[start_row - 2]
        if is_blank_row(prior) or not _row_has_header_role(prior):
            break
        start_row -= 1
    return start_row


def _header_paths_and_roles(
    rows: list[list[str]],
    *,
    start_row: int,
    end_row: int,
) -> tuple[dict[int, tuple[str, ...]], dict[int, str]]:
    max_column = max((len(rows[row_number - 1]) for row_number in range(start_row, end_row + 1)), default=0)
    paths: dict[int, tuple[str, ...]] = {}
    roles: dict[int, str] = {}

    for column in range(1, max_column + 1):
        texts = tuple(
            rows[row_number - 1][column - 1].strip()
            for row_number in range(start_row, end_row + 1)
            if column <= len(rows[row_number - 1]) and rows[row_number - 1][column - 1].strip()
        )
        if not texts:
            continue
        paths[column] = texts
        role = _role_for_header_path(texts)
        if role is not None:
            roles[column] = role

    return paths, roles


def find_header_anchors(rows: list[list[str]]) -> list[tuple[int, int, dict[int, tuple[str, ...]], dict[int, str]]]:
    anchors: list[tuple[int, int, dict[int, tuple[str, ...]], dict[int, str]]] = []
    for end_row in range(1, len(rows) + 1):
        # Data rows can legitimately contain words such as "item" or
        # "description". Requiring at least two recognized header-role cells
        # prevents those rows from becoming false header-stack terminators.
        if _row_header_role_count(rows[end_row - 1]) < 2:
            continue
        start_row = _header_stack_start(rows, end_row)
        paths, roles = _header_paths_and_roles(rows, start_row=start_row, end_row=end_row)
        role_set = set(roles.values())
        if "description" in role_set and "identifier" in role_set:
            anchors.append((start_row, end_row, paths, roles))
    return anchors


def _local_revision_labels(
    rows: list[list[str]],
    header_start_row: int,
    prior_header_end_row: int | None,
) -> tuple[str, ...]:
    labels: set[str] = set()
    lower_bound = max(1, header_start_row - 5)
    if prior_header_end_row is not None:
        lower_bound = max(lower_bound, prior_header_end_row + 1)

    for row_number in range(header_start_row - 1, lower_bound - 1, -1):
        row = rows[row_number - 1]
        if is_blank_row(row):
            break
        for cell in row:
            normalized = normalize_header(cell)
            for term in REVISION_CONTEXT_TERMS:
                if term in normalized:
                    labels.add(term)
    return tuple(sorted(labels))


def _candidate_rows(
    rows: list[list[str]],
    *,
    data_start_row: int,
    end_row: int,
    roles: dict[int, str],
) -> tuple[int, ...]:
    identifier_columns = [column for column, role in roles.items() if role == "identifier"]
    if len(identifier_columns) != 1:
        return ()
    identifier_column = identifier_columns[0]

    output: list[int] = []
    for row_number in range(data_start_row, end_row + 1):
        row = rows[row_number - 1]
        if not any(re.search(r"\bCrude\s+petroleum\b", cell, re.IGNORECASE) for cell in row):
            continue
        if identifier_column <= len(row):
            if normalize_identifier(row[identifier_column - 1]) == "0561":
                output.append(row_number)
    return tuple(output)


@dataclass(frozen=True)
class TransportDiagnostic:
    transport_status: str
    semantic_status: str
    reason_code: str


def not_evaluated_transport(reason_code: str) -> TransportDiagnostic:
    if reason_code not in TRANSPORT_REASON_CODES:
        raise ValueError("unsupported transport reason code")
    return TransportDiagnostic(
        transport_status="failed",
        semantic_status="not_evaluated",
        reason_code=reason_code,
    )


@dataclass(frozen=True)
class LocalBlock:
    header_row: int
    header_start_row: int
    header_end_row: int
    start_row: int
    end_row: int
    header_paths: dict[int, tuple[str, ...]]
    roles: dict[int, str]
    revision_context_labels: tuple[str, ...]
    mapped_candidate_rows: tuple[int, ...]
    identity_status: str
    block_status: str
    field_status: str
    release_context_status: str
    reason_codes: tuple[str, ...]
    reason_code: str


def diagnose_local_blocks(
    rows: list[list[str]],
    *,
    source_context: str,
) -> list[LocalBlock]:
    anchors = find_header_anchors(rows)
    blocks: list[LocalBlock] = []

    for index, (header_start, header_end, header_paths, roles) in enumerate(anchors):
        next_start = anchors[index + 1][0] if index + 1 < len(anchors) else None
        end_row = (next_start - 1) if next_start is not None else len(rows)
        prior_end = anchors[index - 1][1] if index > 0 else None

        revision_labels = (
            ("archived_release_path",)
            if source_context == "archived_original_release"
            else _local_revision_labels(rows, header_start, prior_end)
        )
        mapped = _candidate_rows(
            rows,
            data_start_row=header_end + 1,
            end_row=end_row,
            roles=roles,
        )

        identifier_count = sum(1 for role in roles.values() if role == "identifier")
        index_count = sum(1 for role in roles.values() if role == "index_level")
        ambiguous_count = sum(1 for role in roles.values() if role == "ambiguous")

        if identifier_count == 1 and mapped:
            identity_status = "proven"
        else:
            identity_status = "not_proven"

        if len(mapped) == 1:
            block_status = "unique"
        elif len(mapped) > 1:
            block_status = "multiple"
        else:
            block_status = "none"

        if ambiguous_count:
            field_status = "ambiguous"
        elif index_count == 1:
            field_status = "unique"
        elif index_count > 1:
            field_status = "multiple"
        else:
            field_status = "missing"

        if source_context == "archived_original_release":
            release_context_status = "archived_release_path"
        elif len(revision_labels) == 1:
            release_context_status = revision_labels[0]
        elif len(revision_labels) == 0:
            release_context_status = "missing"
        else:
            release_context_status = "conflicting"

        reasons: list[str] = []
        if identifier_count != 1:
            reasons.append("identifier_column_not_proven")
        if len(mapped) == 0:
            reasons.append("mapped_row_count_zero")
        elif len(mapped) > 1:
            reasons.append("mapped_row_count_multiple")
        if ambiguous_count:
            reasons.append("ambiguous_local_column_semantics")
        elif index_count == 0:
            reasons.append("index_level_column_count_zero")
        elif index_count > 1:
            reasons.append("index_level_column_count_multiple")
        if source_context == "detailed_report":
            if release_context_status == "missing":
                reasons.append("revision_context_missing")
            elif release_context_status == "conflicting":
                reasons.append("revision_context_conflicting")

        if not reasons:
            reasons.append("candidate_block_unique")

        blocks.append(
            LocalBlock(
                header_row=header_end,
                header_start_row=header_start,
                header_end_row=header_end,
                start_row=header_start,
                end_row=end_row,
                header_paths=header_paths,
                roles=roles,
                revision_context_labels=revision_labels,
                mapped_candidate_rows=mapped,
                identity_status=identity_status,
                block_status=block_status,
                field_status=field_status,
                release_context_status=release_context_status,
                reason_codes=tuple(reasons),
                reason_code=reasons[0],
            )
        )

    return blocks


CANDIDATE_RE = re.compile(r"\bCrude\s+petroleum\b", re.IGNORECASE)
CONTEXT_NUMERIC_TOKEN_RE = re.compile(r"(?<![A-Za-z])\d+(?:[.,]\d+)?(?![A-Za-z])")
CONTEXT_ALNUM_TOKEN_RE = re.compile(r"\b(?=\w*[A-Za-z])(?=\w*\d)\w+\b")
CONTEXT_PLACEHOLDERS = ("<num>", "<alnum-redacted>", "<numeric-redacted>", "<identifier-not-0561>")


def context_safe_text(value: str) -> str | None:
    """Return text-only diagnostic content with every numeric-bearing token removed.

    This helper is deliberately stricter than normal header normalization. It
    supports candidate-centered structural inventory only and must never expose
    identifier values or economic values.
    """
    normalized = re.sub(r"\s+", " ", unicodedata.normalize("NFKC", value)).strip()
    if not normalized:
        return None
    safe = CONTEXT_ALNUM_TOKEN_RE.sub("<alnum-redacted>", normalized)
    safe = CONTEXT_NUMERIC_TOKEN_RE.sub("<num>", safe)
    basis = safe
    for marker in CONTEXT_PLACEHOLDERS:
        basis = basis.replace(marker, "")
    if not re.search(r"[A-Za-z]", basis):
        return None
    return safe


def candidate_context_inventory(
    rows: list[list[str]],
    *,
    preceding_rows: int = 8,
    max_candidates: int = 32,
    max_cells_per_candidate: int = 64,
) -> list[dict[str, object]]:
    """Collect bounded non-numeric text context without requiring a header anchor."""
    if preceding_rows < 0 or preceding_rows > 8:
        raise ValueError("preceding_rows must be between 0 and 8")
    if max_candidates != 32:
        raise ValueError("max_candidates must remain 32")
    if max_cells_per_candidate != 64:
        raise ValueError("max_cells_per_candidate must remain 64")

    candidate_rows = [
        row_number
        for row_number, row in enumerate(rows, start=1)
        if any(CANDIDATE_RE.search(cell) for cell in row)
    ]
    if len(candidate_rows) > max_candidates:
        raise RuntimeError("candidate context count exceeds 32")

    output: list[dict[str, object]] = []
    for candidate_row in candidate_rows:
        start_row = max(1, candidate_row - preceding_rows)
        cells: list[dict[str, object]] = []
        truncated = False
        for row_number in range(start_row, candidate_row + 1):
            row = rows[row_number - 1]
            for column, raw in enumerate(row, start=1):
                safe = context_safe_text(raw)
                if safe is None:
                    continue
                if len(cells) >= max_cells_per_candidate:
                    truncated = True
                    break
                cells.append(
                    {
                        "row": row_number,
                        "column": column,
                        "text": safe,
                        "role": header_role(safe),
                    }
                )
            if truncated:
                break
        output.append(
            {
                "candidate_row": candidate_row,
                "window_start_row": start_row,
                "window_end_row": candidate_row,
                "cells": cells,
                "truncated": truncated,
            }
        )
    return output



EXACT_TARGET_LABEL_RE = re.compile(
    r"^Crude\\s+petroleum(?:\\s*\\(\\s*<num>\\s*\\))?$",
    re.IGNORECASE,
)
STAGE_INTERMEDIATE_DEMAND_RE = re.compile(
    r"\\bStage\\s+<num>\\s+intermediate\\s+demand(?:\\s+goods)?\\b",
    re.IGNORECASE,
)
UNPROCESSED_NONFOOD_RE = re.compile(
    r"\\bUnprocessed\\s+nonfood\\s+materials\\b",
    re.IGNORECASE,
)


def is_exact_target_label(value: str) -> bool:
    """Match only the numeric-redacted direct Crude petroleum label."""
    return bool(EXACT_TARGET_LABEL_RE.fullmatch(re.sub(r"\\s+", " ", value).strip()))


def exact_target_rows(rows: list[list[str]]) -> tuple[int, ...]:
    """Return rows containing the exact target label after numeric redaction."""
    return tuple(
        row_number
        for row_number, row in enumerate(rows, start=1)
        if any(is_exact_target_label(cell) for cell in row)
    )


def classify_exact_target_context(
    rows: list[list[str]],
    candidate_row: int,
    *,
    lookback_rows: int = 8,
) -> dict[str, object]:
    """Classify an exact-label candidate using only nearby sanitized text.

    Row numbers are coordinates only and must never act as selection criteria.
    The classifier deliberately distinguishes direct commodity context from
    stage/intermediate-demand context while failing closed on mixed or unknown
    context.
    """
    if lookback_rows < 0 or lookback_rows > 8:
        raise ValueError("lookback_rows must be between 0 and 8")
    if candidate_row < 1 or candidate_row > len(rows):
        raise ValueError("candidate_row is outside rows")

    row = rows[candidate_row - 1]
    exact_cells = [cell for cell in row if is_exact_target_label(cell)]
    if not exact_cells:
        return {
            "candidate_row": candidate_row,
            "exact_label": False,
            "context_status": "not_exact_target",
            "stage_intermediate_demand_context": False,
            "unprocessed_nonfood_context": False,
        }

    start_row = max(1, candidate_row - lookback_rows)
    context_cells = [
        cell
        for row_number in range(start_row, candidate_row)
        for cell in rows[row_number - 1]
        if cell.strip()
    ]
    stage_context = any(STAGE_INTERMEDIATE_DEMAND_RE.search(cell) for cell in context_cells)
    commodity_context = any(UNPROCESSED_NONFOOD_RE.search(cell) for cell in context_cells)

    if stage_context and commodity_context:
        status = "ambiguous_mixed_context"
    elif stage_context:
        status = "stage_intermediate_demand_context"
    elif commodity_context:
        status = "commodity_unprocessed_nonfood_context"
    else:
        status = "exact_label_unclassified_context"

    return {
        "candidate_row": candidate_row,
        "exact_label": True,
        "exact_label_cell_count": len(exact_cells),
        "window_start_row": start_row,
        "window_end_row": candidate_row,
        "context_status": status,
        "stage_intermediate_demand_context": stage_context,
        "unprocessed_nonfood_context": commodity_context,
    }


def classify_exact_target_candidates(
    rows: list[list[str]],
    *,
    lookback_rows: int = 8,
) -> list[dict[str, object]]:
    """Classify every exact-label candidate without reading identifiers/values."""
    return [
        classify_exact_target_context(rows, row_number, lookback_rows=lookback_rows)
        for row_number in exact_target_rows(rows)
    ]


def resource_reason_summary(blocks: list[LocalBlock]) -> dict[str, int]:
    summary: dict[str, int] = {}
    for block in blocks:
        for reason in block.reason_codes:
            summary[reason] = summary.get(reason, 0) + 1
    if not blocks:
        summary["no_local_header_anchor"] = 1
    if sum(1 for block in blocks if block.reason_codes == ("candidate_block_unique",)) > 1:
        summary["multiple_candidate_blocks"] = 1
    return summary
