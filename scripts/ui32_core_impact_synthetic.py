"""UI-32 standalone, synthetic-only PIT research contract. No provider or Score imports.

All inputs are invented, timestamped in 2099+, and explicitly non-publishable.
This module has no filesystem, environment, database or network side effects.
Passing a test never grants real-data/source rights, economic validity, or release.
"""
from __future__ import annotations

import calendar
import hashlib
import json
import math
import re
from dataclasses import asdict, dataclass, field
from datetime import date, datetime, time, timezone
from typing import Iterable
from zoneinfo import ZoneInfo

MARKER = "SYNTHETIC_DO_NOT_PUBLISH"
PREFIX = "SYNTHETIC:UI32:"
PROTOCOL = "UI32-R2-SYNTHETIC-V0-DRAFT"
AREAS = frozenset(("US", "EA", "UK", "JP", "CA", "CH", "SE", "CN"))
FAMILIES = frozenset(("CPI", "PCE", "HICP", "POLICY", "GUIDANCE", "EXPECTED_PATH",
                      "NOMINAL_YIELD", "REAL_YIELD", "FX", "LIQUIDITY", "ASSET", "CONSENSUS"))
MEASURES = frozenset(("HEADLINE", "CORE", "CURRENT", "EXPECTED", "LEVEL", "CHANGE"))
FREQUENCIES = frozenset(("D", "M", "Q"))
ADJUSTMENTS = frozenset(("SA", "NSA", "NOT_APPLICABLE"))
STOP_CODES = frozenset((
    "FUTURE_RELEASE", "FUTURE_FIRST_SEEN", "UNAVAILABLE_VINTAGE",
    "SOURCE_RIGHTS_UNKNOWN", "RIGHTS_RESTRICTED", "MIXED_MEASURES",
    "MIXED_FREQUENCY", "INVALID_UNIT", "AMBIGUOUS_TIMESTAMP",
    "MALFORMED_LINEAGE", "NO_CONSENSUS", "INSUFFICIENT_HISTORY",
    "NORMALIZATION_LEAKAGE", "SCORE_V2_SOURCE_BOUNDARY",
    "UNAUTHORIZED_NETWORK", "INSUFFICIENT_DATA", "REVERSE_CAUSALITY",
    "MANIFEST_MISMATCH", "REQUIRED_SOURCE_MISSING", "UNDECLARED_SOURCE",
))
_HEX = re.compile(r"[0-9a-f]{64}\Z")
_DECISION_ISSUER = object()


class SyntheticStop(ValueError):
    def __init__(self, code: str) -> None:
        if code not in STOP_CODES:
            raise ValueError("unknown synthetic STOP code")
        self.code = code
        super().__init__(code)


def _clock(value: datetime | None) -> datetime:
    if not isinstance(value, datetime) or value.tzinfo is None or value.utcoffset() is None:
        raise SyntheticStop("AMBIGUOUS_TIMESTAMP")
    result = value.astimezone(timezone.utc)
    if result.year < 2099:
        raise SyntheticStop("AMBIGUOUS_TIMESTAMP")
    return result


def _id(value: str) -> bool:
    return type(value) is str and value.startswith(PREFIX) and 8 < len(value) <= 144 and not any(
        char.isspace() or ord(char) < 33 or ord(char) > 126 for char in value
    )


@dataclass(frozen=True, slots=True)
class Receipt:
    economy: str
    source_registry_id: str
    series_id: str
    indicator_family: str
    measure: str
    frequency: str
    period_start: date
    period_end: date
    unit: str
    adjustment: str
    release_id: str
    revision: int
    initial_release_at: datetime
    version_published_at: datetime
    revision_effective_at: datetime
    first_seen_at: datetime
    ingested_at: datetime
    snapshot_id: str
    content_digest: str
    previous_digest: str | None = None
    value: float | None = None
    missing_reason: str | None = None
    local_published_at: datetime | None = None
    local_zone: str | None = None
    target_series_id: str | None = None
    fixture_marker: str = MARKER
    synthetic_only: bool = True
    rights_cleared: bool = False
    real_data_retrieval_authorized: bool = False
    publish_authorized: bool = False
    production_authorized: bool = False
    schema_migration_authorized: bool = False

    def __post_init__(self) -> None:
        if self.fixture_marker != MARKER or self.synthetic_only is not True:
            raise ValueError("UI-32 synthetic-only marker required")
        if any(x is not False for x in (self.rights_cleared,
            self.real_data_retrieval_authorized, self.publish_authorized,
            self.production_authorized, self.schema_migration_authorized)):
            raise ValueError("UI-32 cannot grant operational authority")
        if self.economy not in AREAS or self.indicator_family not in FAMILIES or self.measure not in MEASURES:
            raise SyntheticStop("MIXED_MEASURES")
        if self.frequency not in FREQUENCIES or self.adjustment not in ADJUSTMENTS:
            raise SyntheticStop("MIXED_FREQUENCY")
        if type(self.unit) is not str or self.unit not in {"pct", "index", "bp", "ratio", "units"}:
            raise SyntheticStop("INVALID_UNIT")
        # Mock consensus and path receipts must name the exact fictional
        # series they forecast. Same economy/unit alone is not evidence.
        if self.indicator_family in {"CONSENSUS", "EXPECTED_PATH"}:
            if not _id(self.target_series_id) or self.target_series_id == self.series_id:
                raise SyntheticStop("MIXED_MEASURES")
        elif self.target_series_id is not None:
            raise SyntheticStop("MIXED_MEASURES")
        for value in (self.source_registry_id, self.series_id, self.release_id, self.snapshot_id):
            if not _id(value):
                raise SyntheticStop("SCORE_V2_SOURCE_BOUNDARY")
        if type(self.revision) is not int or not 0 <= self.revision <= 999:
            raise SyntheticStop("MALFORMED_LINEAGE")
        if not _HEX.fullmatch(self.content_digest) or (self.previous_digest is not None and
            not _HEX.fullmatch(self.previous_digest)):
            raise SyntheticStop("MALFORMED_LINEAGE")
        if (type(self.period_start) is not date or type(self.period_end) is not date
                or self.period_start.year < 2099 or self.period_end < self.period_start):
            raise SyntheticStop("AMBIGUOUS_TIMESTAMP")
        # An invented monthly CPI/PCE/HICP record must still represent a real
        # calendar month, never an arbitrary Friday mislabeled as monthly.
        if self.frequency == "M" and not (
            self.period_start == date(self.period_end.year, self.period_end.month, 1)
            and self.period_end.day == calendar.monthrange(self.period_end.year, self.period_end.month)[1]
        ):
            raise SyntheticStop("MIXED_FREQUENCY")
        if self.frequency == "D" and self.period_start != self.period_end:
            raise SyntheticStop("MIXED_FREQUENCY")
        if self.frequency == "Q" and not (
            self.period_start.month in (1, 4, 7, 10) and self.period_start.day == 1
            and self.period_end.month == self.period_start.month + 2
            and self.period_end.year == self.period_start.year
            and self.period_end.day == calendar.monthrange(self.period_end.year, self.period_end.month)[1]
        ):
            raise SyntheticStop("MIXED_FREQUENCY")
        initial, published, effective, seen, ingested = (_clock(x) for x in (
            self.initial_release_at, self.version_published_at, self.revision_effective_at,
            self.first_seen_at, self.ingested_at))
        if not initial <= published <= effective <= seen <= ingested:
            raise SyntheticStop("MALFORMED_LINEAGE")
        # Full monthly/quarterly reference periods cannot be known
        # before their last UTC calendar day is complete. A daily period
        # may publish on its own date. This is a candidate logical floor,
        # never a statement of actual publisher schedules or rights.
        if (initial.date() < self.period_end if self.frequency == "D"
                else initial.date() <= self.period_end):
            raise SyntheticStop("AMBIGUOUS_TIMESTAMP")
        if self.local_published_at is not None or self.local_zone is not None:
            if not isinstance(self.local_zone, str) or self.local_published_at is None:
                raise SyntheticStop("AMBIGUOUS_TIMESTAMP")
            try:
                zone = ZoneInfo(self.local_zone)
                local = self.local_published_at
                if not isinstance(local.tzinfo, ZoneInfo) or local.tzinfo.key != zone.key:
                    raise SyntheticStop("AMBIGUOUS_TIMESTAMP")
                if local.astimezone(timezone.utc).astimezone(zone).replace(fold=local.fold) != local:
                    raise SyntheticStop("AMBIGUOUS_TIMESTAMP")
                if _clock(local) != published:
                    raise SyntheticStop("AMBIGUOUS_TIMESTAMP")
            except (KeyError, TypeError, AttributeError) as exc:
                raise SyntheticStop("AMBIGUOUS_TIMESTAMP") from exc
        if self.value is None:
            if self.missing_reason not in {"NO_CONSENSUS", "INSUFFICIENT_DATA"}:
                raise SyntheticStop("INSUFFICIENT_DATA")
        elif (type(self.value) not in (float, int) or not math.isfinite(self.value)
              or self.missing_reason is not None):
            raise SyntheticStop("INVALID_UNIT")

    @property
    def identity(self) -> tuple[object, ...]:
        return (self.source_registry_id, self.series_id, self.period_start.isoformat(),
                self.period_end.isoformat(), self.release_id, self.revision)


@dataclass(frozen=True, slots=True)
class Decision:
    status: str
    selected: tuple[str, ...]
    blockers: tuple[str, ...]
    fixture_marker: str = MARKER
    rights_cleared: bool = False
    real_data_retrieval_authorized: bool = False
    publish_authorized: bool = False
    production_authorized: bool = False
    _issuer: object = field(default=None, repr=False, compare=False)

    def __post_init__(self) -> None:
        if self._issuer is not _DECISION_ISSUER:
            raise ValueError("direct construction cannot certify a synthetic evaluation")
        if self.fixture_marker != MARKER or any(v is not False for v in (
            self.rights_cleared, self.real_data_retrieval_authorized,
            self.publish_authorized, self.production_authorized)):
            raise ValueError("cannot construct privileged research result")
        if self.status not in {"SYNTHETIC_ONLY_HOLD", "SYNTHETIC_ONLY_COMPLETE"}:
            raise ValueError("invalid research result status")
        if (type(self.selected) is not tuple or self.selected != tuple(sorted(set(self.selected)))
                or any(not _id(x) for x in self.selected)):
            raise ValueError("invalid selected synthetic snapshots")
        if (type(self.blockers) is not tuple or self.blockers != tuple(sorted(set(self.blockers)))
                or any(x not in STOP_CODES for x in self.blockers)):
            raise ValueError("invalid synthetic blockers")
        if (self.status == "SYNTHETIC_ONLY_COMPLETE") != bool(self.selected and not self.blockers):
            raise ValueError("invalid synthetic completion assertion")
        # A blocked evaluation may describe failures but must not expose
        # partially selected IDs to a caller that ignores its HOLD status.
        if self.status == "SYNTHETIC_ONLY_HOLD" and self.selected:
            raise ValueError("synthetic HOLD cannot select snapshots")


@dataclass(frozen=True, slots=True)
class SourceScope:
    """Exact fictional input identity, excluding revisions and snapshot IDs."""

    source_registry_id: str
    series_id: str
    economy: str
    indicator_family: str
    measure: str
    frequency: str
    period_start: date
    period_end: date
    unit: str
    adjustment: str
    release_id: str
    target_series_id: str | None = None

    def __post_init__(self) -> None:
        if not all(_id(x) for x in (self.source_registry_id, self.series_id, self.release_id)):
            raise SyntheticStop("SCORE_V2_SOURCE_BOUNDARY")
        if self.economy not in AREAS or self.indicator_family not in FAMILIES or self.measure not in MEASURES:
            raise SyntheticStop("MIXED_MEASURES")
        if self.frequency not in FREQUENCIES or self.adjustment not in ADJUSTMENTS:
            raise SyntheticStop("MIXED_FREQUENCY")
        if type(self.unit) is not str or self.unit not in {"pct", "index", "bp", "ratio", "units"}:
            raise SyntheticStop("INVALID_UNIT")
        if (type(self.period_start) is not date or type(self.period_end) is not date
                or self.period_start.year < 2099 or self.period_end < self.period_start):
            raise SyntheticStop("AMBIGUOUS_TIMESTAMP")
        if self.frequency == "M" and not (
            self.period_start == date(self.period_end.year, self.period_end.month, 1)
            and self.period_end.day == calendar.monthrange(self.period_end.year, self.period_end.month)[1]
        ):
            raise SyntheticStop("MIXED_FREQUENCY")
        if self.frequency == "D" and self.period_start != self.period_end:
            raise SyntheticStop("MIXED_FREQUENCY")
        if self.frequency == "Q" and not (
            self.period_start.month in (1, 4, 7, 10) and self.period_start.day == 1
            and self.period_end.month == self.period_start.month + 2
            and self.period_end.year == self.period_start.year
            and self.period_end.day == calendar.monthrange(self.period_end.year, self.period_end.month)[1]
        ):
            raise SyntheticStop("MIXED_FREQUENCY")
        if self.indicator_family in {"CONSENSUS", "EXPECTED_PATH"}:
            if not _id(self.target_series_id) or self.target_series_id == self.series_id:
                raise SyntheticStop("MIXED_MEASURES")
        elif self.target_series_id is not None:
            raise SyntheticStop("MIXED_MEASURES")

    @classmethod
    def from_receipt(cls, r: Receipt) -> SourceScope:
        if type(r) is not Receipt:
            raise SyntheticStop("SCORE_V2_SOURCE_BOUNDARY")
        return cls(r.source_registry_id, r.series_id, r.economy,
                   r.indicator_family, r.measure, r.frequency,
                   r.period_start, r.period_end, r.unit, r.adjustment,
                   r.release_id, r.target_series_id)


@dataclass(frozen=True, slots=True)
class ScopeManifest:
    """Caller-supplied, immutable 2099+ test scope; NOT signed source authority."""

    version_id: str
    as_of: datetime
    valid_from: datetime
    valid_until: datetime
    required: tuple[SourceScope, ...]
    optional: tuple[SourceScope, ...] = ()
    fixture_marker: str = MARKER
    synthetic_only: bool = True
    rights_cleared: bool = False
    real_data_retrieval_authorized: bool = False
    publish_authorized: bool = False
    production_authorized: bool = False

    def __post_init__(self) -> None:
        if not _id(self.version_id) or self.fixture_marker != MARKER or self.synthetic_only is not True:
            raise ValueError("synthetic scope version and marker required")
        if any(v is not False for v in (self.rights_cleared,
                self.real_data_retrieval_authorized, self.publish_authorized,
                self.production_authorized)):
            raise ValueError("scope cannot grant source or release authority")
        start, cutoff, end = (_clock(x) for x in
                              (self.valid_from, self.as_of, self.valid_until))
        if start > cutoff or cutoff > end:
            raise SyntheticStop("MANIFEST_MISMATCH")
        if (type(self.required) is not tuple or type(self.optional) is not tuple
                or not self.required or len(self.required) + len(self.optional) > 128):
            raise SyntheticStop("MANIFEST_MISMATCH")
        entries = self.required + self.optional
        if any(type(x) is not SourceScope for x in entries) or len(set(entries)) != len(entries):
            raise SyntheticStop("MANIFEST_MISMATCH")
        # Two declared scopes cannot share one revision lineage while claiming
        # different economies, measures, adjustments or target series.
        lineage_scopes: dict[tuple[object, ...], SourceScope] = {}
        for scope in entries:
            key = (scope.source_registry_id, scope.series_id,
                   scope.period_start, scope.period_end, scope.release_id)
            if key in lineage_scopes and lineage_scopes[key] != scope:
                raise SyntheticStop("MANIFEST_MISMATCH")
            lineage_scopes[key] = scope


@dataclass(frozen=True, slots=True)
class ScopedDecision:
    """No global completeness claim; no operational or publishing authority."""

    status: str
    selected: tuple[str, ...]
    blockers: tuple[str, ...]
    manifest_id: str
    required_count: int
    fixture_marker: str = MARKER
    rights_cleared: bool = False
    real_data_retrieval_authorized: bool = False
    publish_authorized: bool = False
    production_authorized: bool = False
    _issuer: object = field(default=None, repr=False, compare=False)

    def __post_init__(self) -> None:
        if self._issuer is not _DECISION_ISSUER:
            raise ValueError("direct construction cannot certify scope coverage")
        if not _id(self.manifest_id) or type(self.required_count) is not int or self.required_count < 1:
            raise ValueError("invalid synthetic manifest reference")
        if self.fixture_marker != MARKER or any(x is not False for x in (
                self.rights_cleared, self.real_data_retrieval_authorized,
                self.publish_authorized, self.production_authorized)):
            raise ValueError("scope result cannot grant operational authority")
        if self.status not in {"SYNTHETIC_ONLY_HOLD", "SYNTHETIC_ONLY_SCOPED_COMPLETE"}:
            raise ValueError("invalid scoped status")
        if (type(self.selected) is not tuple or self.selected != tuple(sorted(set(self.selected)))
                or any(not _id(x) for x in self.selected)):
            raise ValueError("invalid scoped selected IDs")
        if (type(self.blockers) is not tuple or self.blockers != tuple(sorted(set(self.blockers)))
                or any(x not in STOP_CODES for x in self.blockers)):
            raise ValueError("invalid scoped blockers")
        if (self.status == "SYNTHETIC_ONLY_SCOPED_COMPLETE") != bool(self.selected and not self.blockers):
            raise ValueError("invalid scoped completion assertion")
        if self.status == "SYNTHETIC_ONLY_HOLD" and self.selected:
            raise ValueError("scoped HOLD must not expose partial snapshots")


def _versions(items: Iterable[Receipt]) -> tuple[Receipt, ...]:
    rows = tuple(items)
    if len(rows) > 128 or any(type(r) is not Receipt for r in rows):
        raise SyntheticStop("SCORE_V2_SOURCE_BOUNDARY")
    dedup: dict[tuple[object, ...], Receipt] = {}
    for r in rows:
        key = r.identity
        if key in dedup and dedup[key] != r:
            raise SyntheticStop("MALFORMED_LINEAGE")
        dedup[key] = r
    groups: dict[tuple[object, ...], list[Receipt]] = {}
    snapshots: dict[str, tuple[object, ...]] = {}
    for r in dedup.values():
        if r.snapshot_id in snapshots and snapshots[r.snapshot_id] != r.identity:
            raise SyntheticStop("MALFORMED_LINEAGE")
        snapshots[r.snapshot_id] = r.identity
        groups.setdefault(r.identity[:-1], []).append(r)
    for group in groups.values():
        group.sort(key=lambda r: r.revision)
        if group[0].revision != 0:
            raise SyntheticStop("UNAVAILABLE_VINTAGE")
        if group[0].previous_digest is not None:
            raise SyntheticStop("MALFORMED_LINEAGE")
        for before, after in zip(group, group[1:]):
            if (after.revision != before.revision + 1
                    or after.previous_digest != before.content_digest
                    or after.snapshot_id == before.snapshot_id
                    or _clock(after.initial_release_at) != _clock(before.initial_release_at)
                    or _clock(after.version_published_at) <= _clock(before.version_published_at)):
                raise SyntheticStop("MALFORMED_LINEAGE")
    return tuple(dedup.values())


def visible(r: Receipt, as_of: datetime) -> bool:
    cutoff = _clock(as_of)
    # Ingestion must also be complete by the cutoff. An earlier
    # fictional first-seen receipt cannot backdate a later stored value.
    return all(_clock(x) <= cutoff for x in (r.initial_release_at, r.version_published_at,
                                           r.revision_effective_at, r.first_seen_at,
                                           r.ingested_at))


def select_asof(receipts: Iterable[Receipt], as_of: datetime) -> Decision:
    cutoff = _clock(as_of)
    rows = _versions(receipts)
    by_identity: dict[tuple[object, ...], list[Receipt]] = {}
    for r in rows:
        by_identity.setdefault(r.identity[:-1], []).append(r)
    selected: list[str] = []
    blockers: set[str] = set()
    for versions in by_identity.values():
        versions.sort(key=lambda r: r.revision)
        options = [r for r in versions if visible(r, cutoff)]
        if options:
            winner = options[-1]
            if winner.value is None:
                blockers.add("INSUFFICIENT_DATA")
            else:
                selected.append(winner.snapshot_id)
        else:
            first = versions[0]
            if (_clock(first.initial_release_at) > cutoff
                    or _clock(first.version_published_at) > cutoff):
                blockers.add("FUTURE_RELEASE")
            elif _clock(first.first_seen_at) > cutoff:
                blockers.add("FUTURE_FIRST_SEEN")
            else:
                blockers.add("UNAVAILABLE_VINTAGE")  # stored after cutoff
    blockers_tuple = tuple(sorted(blockers))
    # Fail closed atomically across all fictional sources. Any blocker means
    # NO snapshot IDs may escape a HOLD, even if some rows were eligible.
    selected_tuple = () if blockers_tuple else tuple(sorted(set(selected)))
    status = "SYNTHETIC_ONLY_COMPLETE" if selected_tuple and not blockers_tuple else "SYNTHETIC_ONLY_HOLD"
    return Decision(status, selected_tuple, blockers_tuple, _issuer=_DECISION_ISSUER)


def select_required_asof(
    receipts: Iterable[Receipt], manifest: ScopeManifest, as_of: datetime
) -> ScopedDecision:
    """Strict coverage of an explicitly declared fictional source universe.

    The regular select_asof remains generic. This wrapper does NOT certify that
    the caller's scope is economically complete, signed, licensed, or public.
    """
    if type(manifest) is not ScopeManifest:
        raise SyntheticStop("MANIFEST_MISMATCH")
    cutoff = _clock(as_of)
    if cutoff != _clock(manifest.as_of):
        return ScopedDecision("SYNTHETIC_ONLY_HOLD", (), ("MANIFEST_MISMATCH",),
                              manifest.version_id, len(manifest.required),
                              _issuer=_DECISION_ISSUER)
    rows = _versions(receipts)
    # A version chain must not silently change the economic identity of its
    # series. Otherwise one selected revision could stand in for two scopes.
    lineage_scopes: dict[tuple[object, ...], SourceScope] = {}
    for row in rows:
        key = row.identity[:-1]
        scope = SourceScope.from_receipt(row)
        if key in lineage_scopes and lineage_scopes[key] != scope:
            return ScopedDecision("SYNTHETIC_ONLY_HOLD", (), ("MALFORMED_LINEAGE",),
                                  manifest.version_id, len(manifest.required),
                                  _issuer=_DECISION_ISSUER)
        lineage_scopes[key] = scope
    actual = set(lineage_scopes.values())
    required = set(manifest.required)
    allowed = required | set(manifest.optional)
    blockers: set[str] = set()
    if required - actual:
        blockers.add("REQUIRED_SOURCE_MISSING")
    if actual - allowed:
        blockers.add("UNDECLARED_SOURCE")
    if blockers:
        return ScopedDecision("SYNTHETIC_ONLY_HOLD", (), tuple(sorted(blockers)),
                              manifest.version_id, len(manifest.required),
                              _issuer=_DECISION_ISSUER)
    # The existing R9 atomic HOLD guard still applies to every supplied row.
    result = select_asof(rows, cutoff)
    status = ("SYNTHETIC_ONLY_SCOPED_COMPLETE"
              if result.status == "SYNTHETIC_ONLY_COMPLETE" else "SYNTHETIC_ONLY_HOLD")
    return ScopedDecision(status, result.selected, result.blockers,
                          manifest.version_id, len(manifest.required),
                          _issuer=_DECISION_ISSUER)


def compare(left: Receipt, right: Receipt, as_of: datetime) -> float:
    if not (visible(left, as_of) and visible(right, as_of)):
        raise SyntheticStop("UNAVAILABLE_VINTAGE")
    if left.frequency != right.frequency or (left.period_start, left.period_end) != (right.period_start, right.period_end):
        raise SyntheticStop("MIXED_FREQUENCY")
    if (left.indicator_family, left.measure) != (right.indicator_family, right.measure):
        raise SyntheticStop("MIXED_MEASURES")
    if (left.unit, left.adjustment) != (right.unit, right.adjustment):
        raise SyntheticStop("INVALID_UNIT")
    if left.value is None or right.value is None:
        raise SyntheticStop("INSUFFICIENT_DATA")
    return left.value - right.value


def surprise(actual: Receipt, consensus: Receipt | None, as_of: datetime) -> float:
    if actual.indicator_family not in {"CPI", "PCE", "HICP"}:
        raise SyntheticStop("MIXED_MEASURES")
    if not visible(actual, as_of):
        raise SyntheticStop("UNAVAILABLE_VINTAGE")
    if consensus is None or consensus.value is None or not visible(consensus, as_of):
        raise SyntheticStop("NO_CONSENSUS")
    if (consensus.indicator_family != "CONSENSUS" or consensus.measure != actual.measure
        or consensus.target_series_id != actual.series_id
        or consensus.economy != actual.economy or consensus.frequency != actual.frequency
        or consensus.unit != actual.unit or consensus.adjustment != actual.adjustment
        or (consensus.period_start, consensus.period_end) != (actual.period_start, actual.period_end)
        or _clock(consensus.first_seen_at) > _clock(actual.initial_release_at)
        or _clock(consensus.ingested_at) > _clock(actual.initial_release_at)):
        raise SyntheticStop("NO_CONSENSUS")
    if actual.value is None:
        raise SyntheticStop("INSUFFICIENT_DATA")
    return actual.value - consensus.value


def policy_parts(current: Receipt, expected: Receipt | None, as_of: datetime) -> tuple[float, float | None]:
    if (current.indicator_family != "POLICY" or current.measure != "CURRENT"
            or not visible(current, as_of) or current.value is None):
        raise SyntheticStop("UNAVAILABLE_VINTAGE")
    future = (expected.value if expected is not None and expected.indicator_family == "EXPECTED_PATH"
              and expected.measure == "EXPECTED"
              and expected.target_series_id == current.series_id
              and expected.economy == current.economy and expected.unit == current.unit
              and expected.adjustment == current.adjustment
              and visible(expected, as_of) else None)
    return current.value, future


def trend(values: Iterable[Receipt], as_of: datetime, count: int = 3) -> str:
    rows = sorted(tuple(values), key=lambda r: r.period_end)
    if count < 3 or len(rows) < count or any(not visible(r, as_of) or r.value is None for r in rows):
        raise SyntheticStop("INSUFFICIENT_HISTORY")
    if len({(r.source_registry_id, r.economy, r.series_id, r.indicator_family,
             r.measure, r.frequency, r.unit, r.adjustment) for r in rows}) != 1:
        raise SyntheticStop("MIXED_MEASURES")
    if len({r.period_end for r in rows}) != len(rows):
        raise SyntheticStop("INSUFFICIENT_HISTORY")
    if rows[-1].frequency == "M" and any(
        (after.period_end.year * 12 + after.period_end.month)
        - (before.period_end.year * 12 + before.period_end.month) != 1
        for before, after in zip(rows[-count:], rows[-count + 1:])
    ):
        raise SyntheticStop("INSUFFICIENT_HISTORY")
    # A simple candidate direction across at least three releases,
    # NOT an approved economic acceleration/second-derivative model.
    recent = rows[-count:]
    changes = [after.value - before.value for before, after in zip(recent, recent[1:])]
    if all(change > 0 for change in changes):
        return "ACCELERATING"
    if all(change < 0 for change in changes):
        return "DECELERATING"
    return "STABLE" if all(change == 0 for change in changes) else "MIXED"


def normalization(values: Iterable[Receipt], as_of: datetime) -> float:
    rows = tuple(sorted(values, key=lambda r: r.period_end))
    if any(not visible(r, as_of) for r in rows):
        raise SyntheticStop("NORMALIZATION_LEAKAGE")
    if len(rows) < 3 or any(r.value is None for r in rows):
        raise SyntheticStop("INSUFFICIENT_HISTORY")
    if len({(r.source_registry_id, r.economy, r.series_id, r.indicator_family,
             r.measure, r.unit, r.frequency, r.adjustment) for r in rows}) != 1:
        raise SyntheticStop("MIXED_MEASURES")
    if len({r.period_end for r in rows}) != len(rows):
        raise SyntheticStop("INSUFFICIENT_HISTORY")
    if rows[-1].frequency == "M" and any(
        (after.period_end.year * 12 + after.period_end.month)
        - (before.period_end.year * 12 + before.period_end.month) != 1
        for before, after in zip(rows, rows[1:])
    ):
        raise SyntheticStop("INSUFFICIENT_HISTORY")
    mean = sum(r.value for r in rows) / len(rows)
    variance = sum((r.value - mean) ** 2 for r in rows) / len(rows)
    if variance == 0:
        raise SyntheticStop("INSUFFICIENT_HISTORY")
    return (rows[-1].value - mean) / math.sqrt(variance)


def rights_mock(status: str = "UNKNOWN", *, requested_enable: bool = False) -> str:
    if requested_enable is not False:
        raise ValueError("mock rights cannot enable a source")
    return "SOURCE_RIGHTS_UNKNOWN" if status == "UNKNOWN" else "RIGHTS_RESTRICTED"


def require_offline(*_args: object, **_kwargs: object) -> None:
    raise SyntheticStop("UNAUTHORIZED_NETWORK")


def assert_upstream_causality(*, rewrite_from_asset_outcome: bool = False) -> None:
    if rewrite_from_asset_outcome is not False:
        raise SyntheticStop("REVERSE_CAUSALITY")


def assert_independent(origin: str) -> None:
    if not _id(origin):
        raise SyntheticStop("SCORE_V2_SOURCE_BOUNDARY")


def fingerprint(receipts: Iterable[Receipt], as_of: datetime) -> dict[str, object]:
    _clock(as_of)
    rows = _versions(receipts)
    # Include invented content itself, not solely a caller-supplied digest.
    # This is an integrity fingerprint, NOT an authenticated publisher receipt.
    identifiers = sorted(hashlib.sha256(json.dumps(asdict(r), sort_keys=True,
        default=str, separators=(",", ":")).encode()).hexdigest() for r in rows)
    payload = json.dumps({"protocol": PROTOCOL, "as_of": _clock(as_of).isoformat(),
                          "identifiers": identifiers}, sort_keys=True, separators=(",", ":"))
    return {"fixture_marker": MARKER, "digest": hashlib.sha256(payload.encode()).hexdigest(),
            "signature_status": "UNSIGNED", "rights_cleared": False,
            "publish_authorized": False, "production_authorized": False}
