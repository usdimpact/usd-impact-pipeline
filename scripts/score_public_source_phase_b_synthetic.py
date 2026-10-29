"""Pure, synthetic-only point-in-time receipt validator for a future macro study.

RESEARCH ONLY: No provider observation, external API, prices, source adapters,
network calls, file writes, production engine imports, auth or rights grants.

Never use the output as permission to publish or as a complete source history.
Every input MUST be a 2099+ synthetic receipt, not a real provider record.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timezone
from typing import Iterable

SYNTHETIC_MARKER = "SYNTHETIC_DO_NOT_PUBLISH"
SYNTHETIC_ID_PREFIX = "SYNTHETIC:"
MIN_SYNTHETIC_YEAR = 2099
REQUIRED_IDS = frozenset(
    {
        "fed_h10_nominal_broad",
        "eia_crude_stocks_weekly",
        "treasury_direct_2yr_par",
        "treasury_direct_10yr_par",
    }
)
TREASURY_IDS = frozenset(
    {"treasury_direct_2yr_par", "treasury_direct_10yr_par"}
)


# Only these output reasons can be synthesized by the offline as-of
# evaluator. Directly constructed decision objects may not add free-form text,
# provider-looking errors or real source IDs to a supposed fictional preview.
ASOF_SOURCE_BLOCKER_CODES = frozenset({
    "MISSING_SYNTHETIC_RECEIPT",
    "NOT_FIRST_SEEN_BY_CUTOFF",
})
ASOF_CURVE_BLOCKER_CODES = frozenset({
    "TREASURY_CURVE_SNAPSHOT_MISMATCH",
    "TREASURY_CURVE_REVISION_MISMATCH",
    "TREASURY_CURVE_INITIAL_RELEASE_MISMATCH",
    "TREASURY_CURVE_VERSION_PUBLICATION_MISMATCH",
    "TREASURY_CURVE_FIRST_SEEN_MISMATCH",
})


def _valid_asof_blocker(value: str) -> bool:
    """Recognize only Phase B's exact synthetic source/curve HOLD codes."""
    if type(value) is not str or len(value) > 150:
        return False
    if value in ASOF_CURVE_BLOCKER_CODES:
        return True
    source_id, separator, code = value.partition(":")
    return bool(
        separator
        and source_id in REQUIRED_IDS
        and code in ASOF_SOURCE_BLOCKER_CODES
    )


@dataclass(frozen=True)
class SyntheticReceipt:
    """Availability metadata for one invented source/version, WITHOUT values.

    initial_release_at: documented first publication of this reference period
    version_published_at: when this specific version/correction was published
    first_seen_at: when our fictional observer first detected this version
    snapshot_id: invented immutable version ID, shared across Treasury tenors
    revision: monotone nonnegative integer, no implied content/hash values
    """

    source_id: str
    reference_week: date
    initial_release_at: datetime | None
    version_published_at: datetime | None
    first_seen_at: datetime | None
    revision: int
    snapshot_id: str
    record_id: str
    fixture_marker: str = SYNTHETIC_MARKER


@dataclass(frozen=True)
class SyntheticAsOfDecision:
    status: str
    selected: tuple[tuple[str, str], ...]
    blockers: tuple[str, ...]
    publish_authorized: bool = False
    real_source_retrieval_authorized: bool = False

    def __post_init__(self) -> None:
        # A frozen dataclass is still directly constructible. These guards are
        # format-only; they do NOT verify real receipts or grant rights.
        if (
            self.publish_authorized is not False
            or self.real_source_retrieval_authorized is not False
        ):
            raise ValueError("synthetic evaluation cannot grant rights")
        if type(self.status) is not str or self.status not in (
            "SYNTHETIC_ONLY_HOLD", "SYNTHETIC_ONLY_COMPLETE"
        ):
            raise ValueError("unrecognized synthetic as-of result status")
        if type(self.selected) is not tuple or len(self.selected) > len(REQUIRED_IDS):
            raise ValueError("synthetic as-of source selection must be a bounded tuple")
        if any(
            type(item) is not tuple or len(item) != 2
            or type(item[0]) is not str or item[0] not in REQUIRED_IDS
            or type(item[1]) is not str
            or not item[1].startswith(SYNTHETIC_ID_PREFIX)
            or len(item[1]) > 160
            for item in self.selected
        ):
            raise ValueError("unrecognized synthetic as-of source or snapshot ID")
        if (
            self.selected != tuple(sorted(self.selected))
            or len({source_id for source_id, _ in self.selected}) != len(self.selected)
        ):
            raise ValueError("synthetic as-of source pairs must be unique and sorted")
        if type(self.blockers) is not tuple or len(self.blockers) > 16:
            raise ValueError("synthetic as-of blockers must be bounded tuples")
        if (
            any(type(item) is not str for item in self.blockers)
            or self.blockers != tuple(sorted(set(self.blockers)))
            or not all(_valid_asof_blocker(item) for item in self.blockers)
        ):
            raise ValueError("unrecognized or duplicate synthetic as-of blocker code")
        if self.status == "SYNTHETIC_ONLY_HOLD":
            if not self.blockers:
                raise ValueError("synthetic as-of HOLD requires an explicit blocker")
            return

        # A direct caller may not declare a COMPLETE outcome with a partial
        # set or two different Treasury curve snapshots.
        if self.blockers or {source for source, _ in self.selected} != REQUIRED_IDS:
            raise ValueError("synthetic as-of COMPLETE requires four sources and no blockers")
        snapshots = dict(self.selected)
        if snapshots["treasury_direct_2yr_par"] != snapshots["treasury_direct_10yr_par"]:
            raise ValueError("synthetic as-of COMPLETE requires one Treasury curve snapshot")


def _utc(value: datetime, label: str) -> datetime:
    if not isinstance(value, datetime) or value.tzinfo is None:
        raise ValueError(f"{label}: timezone-aware datetime required")
    if value.utcoffset() is None:
        raise ValueError(f"{label}: valid timezone offset required")
    return value.astimezone(timezone.utc)


def _check_receipt(receipt: SyntheticReceipt, week: date) -> None:
    if not isinstance(receipt, SyntheticReceipt):
        raise ValueError("only synthetic receipt records are accepted")
    if receipt.fixture_marker != SYNTHETIC_MARKER:
        raise ValueError("synthetic fixture marker missing")
    if receipt.source_id not in REQUIRED_IDS:
        raise ValueError("unknown macro-study candidate source")
    if receipt.reference_week != week:
        raise ValueError("reference week mismatch")
    if not isinstance(receipt.revision, int) or isinstance(receipt.revision, bool):
        raise ValueError("revision must be an integer")
    if receipt.revision < 0:
        raise ValueError("negative revision is not permitted")
    for label, identifier in (
        ("record_id", receipt.record_id),
        ("snapshot_id", receipt.snapshot_id),
    ):
        if not isinstance(identifier, str) or not identifier.startswith(
            SYNTHETIC_ID_PREFIX
        ):
            raise ValueError(f"{label} must have a synthetic-only marker")
        if len(identifier) > 160:
            raise ValueError(f"{label}: oversized identifier")

    # Unknown publication or first-seen receipt must fail closed. We never
    # substitute the advertised calendar schedule for a genuine timestamp.
    if (
        receipt.initial_release_at is None
        or receipt.version_published_at is None
        or receipt.first_seen_at is None
    ):
        raise ValueError("unverified actual release or first-seen receipt")
    initial = _utc(receipt.initial_release_at, "initial_release_at")
    published = _utc(receipt.version_published_at, "version_published_at")
    seen = _utc(receipt.first_seen_at, "first_seen_at")
    if not (initial <= published <= seen):
        raise ValueError("non-causal publication/version/first-seen chronology")
    if min(initial.year, published.year, seen.year) < MIN_SYNTHETIC_YEAR:
        raise ValueError("live/historical provider timestamps not permitted")


def evaluate_synthetic_asof(
    receipts: Iterable[SyntheticReceipt],
    reference_week: date,
    as_of_at: datetime,
) -> SyntheticAsOfDecision:
    """Choose as-of-visible *synthetic* versions; never grant publication.

    The scheduled Monday/Wednesday/18:00ET time is NOT used to infer any
    receipt. Real source data is refused through hardcoded 2099+ fixture gates.
    Revisions first published/detected AFTER the cutoff cannot leak backward.
    """

    if not isinstance(reference_week, date) or isinstance(reference_week, datetime):
        raise ValueError("reference_week must be a date")
    if reference_week.year < MIN_SYNTHETIC_YEAR or reference_week.weekday() != 4:
        raise ValueError("synthetic reference week must end Friday in 2099+")
    cutoff = _utc(as_of_at, "as_of_at")
    if cutoff.year < MIN_SYNTHETIC_YEAR:
        raise ValueError("real/historical as-of cutoffs are forbidden")

    items = tuple(receipts)
    if len(items) > 80:
        raise ValueError("too many synthetic revisions")
    seen_ids: set[str] = set()
    seen_versions: set[tuple[str, int]] = set()
    grouped: dict[str, list[SyntheticReceipt]] = {
        source_id: [] for source_id in REQUIRED_IDS
    }
    for item in items:
        _check_receipt(item, reference_week)
        if item.record_id in seen_ids:
            raise ValueError("duplicate synthetic receipt ID")
        seen_ids.add(item.record_id)
        key = (item.source_id, item.revision)
        if key in seen_versions:
            raise ValueError("duplicate source revision")
        seen_versions.add(key)
        grouped[item.source_id].append(item)

    # One source/week has one initial publication instant. A correction
    # must preserve that first-publication receipt and use a NEW immutable
    # snapshot ID. Otherwise as-of versions cannot be distinguished safely,
    # including when a later revision is not yet visible at the cutoff.
    # Compare UTC instants rather than requiring identical timezone text.
    for revisions in grouped.values():
        if len(revisions) < 2:
            continue
        # Preserve the prior out-of-order failure for contradictory revision
        # chronology before evaluating first-publication and snapshot identity.
        by_publication = sorted(
            revisions,
            key=lambda item: (
                _utc(item.version_published_at, "version_published_at"),
                item.revision,
            ),
        )
        if [item.revision for item in by_publication] != sorted(
            item.revision for item in by_publication
        ):
            raise ValueError("out-of-order synthetic revision numbering")
        first_releases = {
            _utc(item.initial_release_at, "initial_release_at")
            for item in revisions
        }
        if len(first_releases) != 1:
            raise ValueError("conflicting synthetic initial release across revisions")
        snapshots = [item.snapshot_id for item in revisions]
        if len(snapshots) != len(set(snapshots)):
            raise ValueError("synthetic snapshot ID reused across revisions")

    selected: dict[str, SyntheticReceipt] = {}
    blockers: list[str] = []
    for source_id in sorted(REQUIRED_IDS):
        versions = grouped[source_id]
        if not versions:
            blockers.append(f"{source_id}:MISSING_SYNTHETIC_RECEIPT")
            continue
        visible = [
            receipt
            for receipt in versions
            if (
                _utc(receipt.initial_release_at, "initial_release_at") <= cutoff
                and _utc(receipt.version_published_at, "version_published_at") <= cutoff
                and _utc(receipt.first_seen_at, "first_seen_at") <= cutoff
            )
        ]
        if not visible:
            blockers.append(f"{source_id}:NOT_FIRST_SEEN_BY_CUTOFF")
            continue
        winner = max(
            visible,
            key=lambda item: (
                _utc(item.version_published_at, "version_published_at"),
                item.revision,
            ),
        )
        selected[source_id] = winner

    if TREASURY_IDS.issubset(selected):
        two = selected["treasury_direct_2yr_par"]
        ten = selected["treasury_direct_10yr_par"]
        if two.snapshot_id != ten.snapshot_id:
            blockers.append("TREASURY_CURVE_SNAPSHOT_MISMATCH")
        if two.revision != ten.revision:
            blockers.append("TREASURY_CURVE_REVISION_MISMATCH")
        # Two tenor rows from a supposedly identical immutable curve version
        # must have one coherent publication and detection timeline.  Matching
        # a synthetic snapshot ID/revision alone does NOT establish that both
        # fields were first published and first seen at the same instant.
        # Compare UTC instants so different but equivalent timezone encodings
        # are accepted.  A mismatch is a HOLD, never a substitute timestamp.
        for timestamp_attr, blocker in (
            ("initial_release_at", "TREASURY_CURVE_INITIAL_RELEASE_MISMATCH"),
            ("version_published_at", "TREASURY_CURVE_VERSION_PUBLICATION_MISMATCH"),
            ("first_seen_at", "TREASURY_CURVE_FIRST_SEEN_MISMATCH"),
        ):
            if _utc(getattr(two, timestamp_attr), timestamp_attr) != _utc(
                getattr(ten, timestamp_attr), timestamp_attr
            ):
                blockers.append(blocker)

    # Never return any numeric source observation. Even a complete four-signal
    # synthetic receipt set is NOT an approved model or publication license.
    result = SyntheticAsOfDecision(
        status="SYNTHETIC_ONLY_HOLD" if blockers else "SYNTHETIC_ONLY_COMPLETE",
        selected=tuple(
            sorted((source_id, receipt.snapshot_id)
                   for source_id, receipt in selected.items())
        ),
        blockers=tuple(sorted(blockers)),
    )
    return result
