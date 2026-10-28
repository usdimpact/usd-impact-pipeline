#!/usr/bin/env python3
"""Pure structural helpers for Issue #258 ambiguity-diagnostics design.

This module performs no network I/O and has no file-writing path. It exists to
prove the candidate-local scoping rules on synthetic rows before any future
owner-authorized live diagnostic.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

IDENTIFIER_HEADERS = ("commodity code", "series code", "series id", "item code")
DESCRIPTION_HEADERS = ("commodity", "item", "description")
REVISION_CONTEXT_TERMS = ("preliminary", "final", "revised", "corrected")


def normalize_header(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip().lower()


def header_role(value: str) -> str | None:
    normalized = normalize_header(value)
    identifier = any(term in normalized for term in IDENTIFIER_HEADERS)
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
    compact = re.sub(r"\s+", "", value).upper()
    if compact == "WPU0561":
        return "0561"
    if compact in {"05-61", "0561", "561"}:
        return "0561"
    return None


def is_blank_row(row: list[str]) -> bool:
    return not any(cell.strip() for cell in row)


@dataclass(frozen=True)
class LocalBlock:
    header_row: int
    start_row: int
    end_row: int
    roles: dict[int, str]
    revision_context_labels: tuple[str, ...]
    mapped_candidate_rows: tuple[int, ...]
    reason_code: str


def _roles_for_header(row: list[str]) -> dict[int, str]:
    roles: dict[int, str] = {}
    for column, text in enumerate(row, start=1):
        role = header_role(text)
        if role is not None:
            roles[column] = role
    return roles


def _is_header_anchor(row: list[str]) -> bool:
    roles = set(_roles_for_header(row).values())
    return "description" in roles and "identifier" in roles


def find_header_anchors(rows: list[list[str]]) -> list[int]:
    return [
        row_number
        for row_number, row in enumerate(rows, start=1)
        if _is_header_anchor(row)
    ]


def _local_revision_labels(rows: list[list[str]], header_row: int, prior_anchor: int | None) -> tuple[str, ...]:
    labels: set[str] = set()
    lower_bound = max(1, header_row - 5)
    if prior_anchor is not None:
        lower_bound = max(lower_bound, prior_anchor + 1)

    for row_number in range(header_row - 1, lower_bound - 1, -1):
        row = rows[row_number - 1]
        if is_blank_row(row):
            break
        if _is_header_anchor(row):
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
    start_row: int,
    end_row: int,
    roles: dict[int, str],
) -> tuple[int, ...]:
    identifier_columns = [column for column, role in roles.items() if role == "identifier"]
    if len(identifier_columns) != 1:
        return ()
    identifier_column = identifier_columns[0]

    output: list[int] = []
    for row_number in range(start_row + 1, end_row + 1):
        row = rows[row_number - 1]
        if not any(re.search(r"\bCrude\s+petroleum\b", cell, re.IGNORECASE) for cell in row):
            continue
        if identifier_column <= len(row):
            if normalize_identifier(row[identifier_column - 1]) == "0561":
                output.append(row_number)
    return tuple(output)


def diagnose_local_blocks(
    rows: list[list[str]],
    *,
    source_context: str,
) -> list[LocalBlock]:
    anchors = find_header_anchors(rows)
    blocks: list[LocalBlock] = []

    for index, header_row in enumerate(anchors):
        next_anchor = anchors[index + 1] if index + 1 < len(anchors) else None
        end_row = (next_anchor - 1) if next_anchor is not None else len(rows)
        prior_anchor = anchors[index - 1] if index > 0 else None
        roles = _roles_for_header(rows[header_row - 1])
        revision_labels = (
            ("archived_release_path",)
            if source_context == "archived_original_release"
            else _local_revision_labels(rows, header_row, prior_anchor)
        )
        mapped = _candidate_rows(
            rows,
            start_row=header_row,
            end_row=end_row,
            roles=roles,
        )

        identifier_count = sum(1 for role in roles.values() if role == "identifier")
        index_count = sum(1 for role in roles.values() if role == "index_level")
        ambiguous_count = sum(1 for role in roles.values() if role == "ambiguous")

        if identifier_count != 1:
            reason = "identifier_column_not_proven"
        elif ambiguous_count:
            reason = "ambiguous_local_column_semantics"
        elif len(mapped) == 0:
            reason = "mapped_row_count_zero"
        elif len(mapped) > 1:
            reason = "mapped_row_count_multiple"
        elif index_count == 0:
            reason = "index_level_column_count_zero"
        elif index_count > 1:
            reason = "index_level_column_count_multiple"
        elif source_context == "detailed_report" and len(revision_labels) == 0:
            reason = "revision_context_missing"
        elif source_context == "detailed_report" and len(revision_labels) > 1:
            reason = "revision_context_conflicting"
        else:
            reason = "candidate_block_unique"

        blocks.append(
            LocalBlock(
                header_row=header_row,
                start_row=header_row,
                end_row=end_row,
                roles=roles,
                revision_context_labels=revision_labels,
                mapped_candidate_rows=mapped,
                reason_code=reason,
            )
        )

    return blocks


def resource_reason_summary(blocks: list[LocalBlock]) -> dict[str, int]:
    summary: dict[str, int] = {}
    for block in blocks:
        summary[block.reason_code] = summary.get(block.reason_code, 0) + 1
    if not blocks:
        summary["no_local_header_anchor"] = 1
    if sum(1 for block in blocks if block.reason_code == "candidate_block_unique") > 1:
        summary["multiple_candidate_blocks"] = 1
    return summary
