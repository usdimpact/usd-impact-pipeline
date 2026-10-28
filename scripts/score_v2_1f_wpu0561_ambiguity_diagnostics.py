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
DESCRIPTION_HEADERS = ("commodity", "item", "description")
REVISION_CONTEXT_TERMS = ("preliminary", "final", "revised", "corrected")
TRANSPORT_REASON_CODES = ("transport_dns_failure", "http_access_control")
MAX_HEADER_DEPTH = 3


def normalize_header(value: str) -> str:
    return re.sub(r"\s+", " ", unicodedata.normalize("NFKC", value)).strip().lower()


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
    normalized = unicodedata.normalize("NFKC", value).strip().upper()
    normalized = re.sub(r"[\s\-\u2010\u2011\u2012\u2013\u2014\u2015]+", "", normalized)
    if normalized.startswith("WPU"):
        normalized = normalized[3:]
    if normalized in {"0561", "561"}:
        return "0561"
    return None


def is_blank_row(row: list[str]) -> bool:
    return not any(cell.strip() for cell in row)


def _row_has_header_role(row: list[str]) -> bool:
    return any(header_role(cell) is not None for cell in row)


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
        if not _row_has_header_role(rows[end_row - 1]):
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
