"""Independent federal-source Macro Context Panel: synthetic-only experiment.

THIS IS NOT USD IMPACT SCORE v2. Invented year-2099+ values only.
No provider retrieval, file I/O, paid market-data transport, real observations,
publishing, trading signal, model approval, rights grant or production access.

Uses the existing Phase-B synthetic point-in-time receipts to prevent revisions
and late-release data from leaking into a historical cutoff.
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from typing import Iterable

from scripts.score_public_source_phase_b_synthetic import (
    MIN_SYNTHETIC_YEAR,
    REQUIRED_IDS,
    SYNTHETIC_ID_PREFIX,
    SYNTHETIC_MARKER,
    SyntheticReceipt,
    evaluate_synthetic_asof,
)

PANEL_ID = "INDEPENDENT_FEDERAL_MACRO_CONTEXT_V0_SYNTHETIC_ONLY"
DIALS = ("dollar_breadth", "crude_inventory", "treasury_curve_level",
         "treasury_curve_direction")
# Exact invented result vocabulary. This is a formatting/safety contract, not
# evidence of an approved methodology, source rights or a publication license.
DIAL_LABEL_VALUES = {
    "dollar_breadth": frozenset({"UP", "DOWN", "UNCHANGED"}),
    "crude_inventory": frozenset({"BUILD", "DRAW", "UNCHANGED"}),
    "treasury_curve_level": frozenset({"POSITIVE", "FLAT", "INVERTED"}),
    "treasury_curve_direction": frozenset({"STEEPENING", "FLATTENING", "UNCHANGED"}),
}
SOURCE_BLOCKER_CODES = frozenset({
    "MISSING_SYNTHETIC_RECEIPT",
    "NOT_FIRST_SEEN_BY_CUTOFF",
    "NO_MATCHING_VISIBLE_SYNTHETIC_VALUE",
})
WEEK_BLOCKER_CODES = frozenset({
    "INCOMPLETE_FOUR_SOURCE_SET",
    "TREASURY_CURVE_SNAPSHOT_MISMATCH",
    "TREASURY_CURVE_REVISION_MISMATCH",
    "TREASURY_CURVE_INITIAL_RELEASE_MISMATCH",
    "TREASURY_CURVE_VERSION_PUBLICATION_MISMATCH",
    "TREASURY_CURVE_FIRST_SEEN_MISMATCH",
})


def _canonical_synthetic_friday(value: str) -> date:
    """Require a strict ISO Friday in 2099+, never a historical source date."""
    if type(value) is not str:
        raise ValueError("synthetic preview week must be a canonical ISO date")
    try:
        week = date.fromisoformat(value)
    except ValueError as exc:
        raise ValueError("synthetic preview week must be a canonical ISO date") from exc
    if (
        week.isoformat() != value
        or week.year < MIN_SYNTHETIC_YEAR
        or week.weekday() != 4
    ):
        raise ValueError("synthetic preview requires canonical 2099+ Fridays")
    return week


def _valid_panel_blocker(value: str, weeks: frozenset[str]) -> bool:
    """Only the offline evaluator's bounded, contextual HOLD reasons are valid."""
    if type(value) is not str or len(value) > 180:
        return False
    week, sep, detail = value.partition(":")
    if not sep or week not in weeks:
        return False
    if detail in WEEK_BLOCKER_CODES:
        return True
    source_id, sep, code = detail.partition(":")
    return bool(sep and source_id in REQUIRED_IDS and code in SOURCE_BLOCKER_CODES)


SOURCE_UNITS = {
    "fed_h10_nominal_broad": "index",
    "eia_crude_stocks_weekly": "thousand_barrels",
    "treasury_direct_2yr_par": "yield_percent",
    "treasury_direct_10yr_par": "yield_percent",
}

# Local CANDIDATE scope tags prevent invented source observations with
# incompatible measurement definitions from silently entering the panel.
# They do NOT establish the exact live feed, historic vintage or legal rights.
SOURCE_BASIS_IDS = {
    "fed_h10_nominal_broad":
        "CANDIDATE:H10_NOMINAL_BROAD_POST_2019_GOODS_SERVICES_REBASED",
    "eia_crude_stocks_weekly":
        "CANDIDATE:EIA_WCESTUS1_CRUDE_ENDING_STOCKS_EX_SPR_UNRECONCILED",
    "treasury_direct_2yr_par":
        "CANDIDATE:TREASURY_NOMINAL_PAR_CURVE_2YR_ILLUSTRATIVE_FIELD",
    "treasury_direct_10yr_par":
        "CANDIDATE:TREASURY_NOMINAL_PAR_CURVE_10YR_ILLUSTRATIVE_FIELD",
}


@dataclass(frozen=True)
class SyntheticObservation:
    """Invented scalar tied to the metadata of one source snapshot/version.

    No exact provider series, price history, or actual observation can be passed
    because the reference period must be an invented Friday in year 2099+.
    """

    source_id: str
    reference_week: date
    snapshot_id: str
    value: float
    unit: str
    basis_id: str
    fixture_marker: str = SYNTHETIC_MARKER


@dataclass(frozen=True)
class SyntheticContextPanel:
    """Qualitative synthetic preview; contains NO source observation numbers."""

    status: str
    reference_week: str
    previous_week: str
    panel_id: str
    dial_labels: tuple[tuple[str, str], ...]
    blockers: tuple[str, ...]
    fixture_marker: str = SYNTHETIC_MARKER
    rights_cleared: bool = False
    real_data_fetch_authorized: bool = False
    publish_authorized: bool = False
    production_authorized: bool = False

    def __post_init__(self) -> None:
        # A preview may be constructed directly; no caller can turn optional
        # bool-like values into an implied rights or publication decision.
        if any(
            getattr(self, name) is not False
            for name in (
                "rights_cleared",
                "real_data_fetch_authorized",
                "publish_authorized",
                "production_authorized",
            )
        ):
            raise ValueError("synthetic context panel cannot grant real-data or publication rights")
        if self.panel_id != PANEL_ID or self.fixture_marker != SYNTHETIC_MARKER:
            raise ValueError("unrecognized synthetic panel")
        if type(self.status) is not str or self.status not in {"SYNTHETIC_ONLY_HOLD", "SYNTHETIC_ONLY_COMPLETE"}:
            raise ValueError("invalid synthetic-only state")

        current = _canonical_synthetic_friday(self.reference_week)
        previous = _canonical_synthetic_friday(self.previous_week)
        if previous != current - timedelta(days=7):
            raise ValueError("synthetic preview weeks must be consecutive Fridays")
        if type(self.dial_labels) is not tuple or any(
            type(item) is not tuple or len(item) != 2
            for item in self.dial_labels
        ):
            raise ValueError("synthetic preview labels must be immutable pairs")
        if type(self.blockers) is not tuple or len(self.blockers) > 40:
            raise ValueError("synthetic preview blockers must be bounded tuples")

        if self.status == "SYNTHETIC_ONLY_COMPLETE":
            if self.blockers or len(self.dial_labels) != len(DIALS):
                raise ValueError("complete synthetic preview requires four labels and no blockers")
            for (name, label), expected_name in zip(self.dial_labels, DIALS):
                if type(name) is not str or name != expected_name or type(label) is not str or label not in DIAL_LABEL_VALUES[expected_name]:
                    raise ValueError("unrecognized synthetic preview label or dial order")
        else:
            if self.dial_labels or not self.blockers:
                raise ValueError("synthetic HOLD must have blockers and no labels")
            allowed_weeks = frozenset((self.reference_week, self.previous_week))
            if (
                any(type(item) is not str for item in self.blockers)
                or self.blockers != tuple(sorted(set(self.blockers)))
                or not all(_valid_panel_blocker(item, allowed_weeks) for item in self.blockers)
            ):
                raise ValueError("synthetic HOLD contains invalid or unscoped blockers")


def _validate_observation(obs: SyntheticObservation, weeks: set[date]) -> None:
    if not isinstance(obs, SyntheticObservation):
        raise ValueError("only synthetic observations are accepted")
    if obs.fixture_marker != SYNTHETIC_MARKER:
        raise ValueError("synthetic observation marker missing")
    if obs.source_id not in REQUIRED_IDS:
        raise ValueError("unrecognized candidate source")
    if not isinstance(obs.unit, str) or obs.unit != SOURCE_UNITS[obs.source_id]:
        raise ValueError("synthetic source unit does not match the candidate contract")
    if not isinstance(obs.basis_id, str) or obs.basis_id != SOURCE_BASIS_IDS[obs.source_id]:
        raise ValueError(
            "synthetic source measurement basis does not match the candidate contract"
        )
    if (
        not isinstance(obs.reference_week, date)
        or isinstance(obs.reference_week, datetime)
        or obs.reference_week not in weeks
        or obs.reference_week.year < MIN_SYNTHETIC_YEAR
    ):
        raise ValueError("observation outside synthetic current/previous Fridays")
    if (
        not isinstance(obs.snapshot_id, str)
        or not obs.snapshot_id.startswith(SYNTHETIC_ID_PREFIX)
        or len(obs.snapshot_id) > 160
    ):
        raise ValueError("snapshot must have an invented synthetic identifier")
    if isinstance(obs.value, bool) or not isinstance(obs.value, (int, float)):
        raise ValueError("synthetic scalar must be numeric, not boolean")
    try:
        value = float(obs.value)
    except (OverflowError, ValueError) as exc:
        raise ValueError("synthetic scalar must be finite") from exc
    if not math.isfinite(value):
        raise ValueError("synthetic scalar must be finite")
    if obs.source_id in {"fed_h10_nominal_broad", "eia_crude_stocks_weekly"}:
        if value <= 0:
            raise ValueError("invented index and inventory levels must be positive")


def _direction(now: float, before: float, up: str, down: str) -> str:
    if math.isclose(now, before, rel_tol=1e-12, abs_tol=1e-12):
        return "UNCHANGED"
    return up if now > before else down


def evaluate_synthetic_context(
    receipts: Iterable[SyntheticReceipt],
    observations: Iterable[SyntheticObservation],
    reference_week: date,
    as_of_at: datetime,
) -> SyntheticContextPanel:
    """Return synthetic qualitative dials if BOTH weeks' versions are visible.

    This panel is intentionally never released; the actual source terms, exact
    identity and as-published vintage availability must be approved separately.
    No nominal Wednesday time can substitute for source-first-seen receipts.
    """
    if (
        not isinstance(reference_week, date)
        or isinstance(reference_week, datetime)
        or reference_week.year < MIN_SYNTHETIC_YEAR
        or reference_week.weekday() != 4
    ):
        raise ValueError("reference_week must be a synthetic Friday in 2099+")
    previous_week = reference_week - timedelta(days=7)
    if previous_week.year < MIN_SYNTHETIC_YEAR:
        raise ValueError("previous week must also be synthetic 2099+")
    if not isinstance(as_of_at, datetime) or as_of_at.tzinfo is None:
        raise ValueError("as_of_at must be timezone-aware")
    if as_of_at.utcoffset() is None or as_of_at.astimezone(timezone.utc).year < MIN_SYNTHETIC_YEAR:
        raise ValueError("as_of_at must be a valid synthetic 2099+ timestamp")

    expected_weeks = {previous_week, reference_week}
    receipts = tuple(receipts)
    observations = tuple(observations)
    if len(receipts) > 80 or len(observations) > 80:
        raise ValueError("too many synthetic receipts or observations")

    for receipt in receipts:
        if not isinstance(receipt, SyntheticReceipt):
            raise ValueError("only synthetic source receipts allowed")
        if receipt.reference_week not in expected_weeks:
            raise ValueError("source receipt references an unexpected week")

    seen: dict[tuple[date, str, str], float] = {}
    for item in observations:
        _validate_observation(item, expected_weeks)
        key = (item.reference_week, item.source_id, item.snapshot_id)
        if key in seen:
            raise ValueError("duplicate synthetic observation for one source snapshot")
        seen[key] = float(item.value)

    chosen: dict[date, dict[str, float]] = {}
    blockers: list[str] = []
    for week in (previous_week, reference_week):
        selection = evaluate_synthetic_asof(
            (item for item in receipts if item.reference_week == week),
            week, as_of_at,
        )
        if selection.blockers:
            blockers.extend(f"{week}:{reason}" for reason in selection.blockers)

        values: dict[str, float] = {}
        for source_id, snapshot in selection.selected:
            key = (week, source_id, snapshot)
            if key not in seen:
                blockers.append(f"{week}:{source_id}:NO_MATCHING_VISIBLE_SYNTHETIC_VALUE")
                continue
            values[source_id] = seen[key]
        if len(values) != len(REQUIRED_IDS):
            blockers.append(f"{week}:INCOMPLETE_FOUR_SOURCE_SET")
        chosen[week] = values

    if blockers:
        return SyntheticContextPanel(
            status="SYNTHETIC_ONLY_HOLD",
            panel_id=PANEL_ID,
            reference_week=reference_week.isoformat(),
            previous_week=previous_week.isoformat(),
            dial_labels=(),
            blockers=tuple(sorted(set(blockers))),
        )

    prior = chosen[previous_week]
    now = chosen[reference_week]

    dollar = _direction(
        now["fed_h10_nominal_broad"], prior["fed_h10_nominal_broad"],
        "UP", "DOWN",
    )
    inventory = _direction(
        now["eia_crude_stocks_weekly"], prior["eia_crude_stocks_weekly"],
        "BUILD", "DRAW",
    )
    prior_spread = prior["treasury_direct_10yr_par"] - prior["treasury_direct_2yr_par"]
    current_spread = now["treasury_direct_10yr_par"] - now["treasury_direct_2yr_par"]
    if math.isclose(current_spread, 0.0, rel_tol=1e-12, abs_tol=1e-12):
        curve_level = "FLAT"
    else:
        curve_level = "POSITIVE" if current_spread > 0 else "INVERTED"
    curve_direction = _direction(current_spread, prior_spread, "STEEPENING", "FLATTENING")

    return SyntheticContextPanel(
        status="SYNTHETIC_ONLY_COMPLETE",
        panel_id=PANEL_ID,
        reference_week=reference_week.isoformat(),
        previous_week=previous_week.isoformat(),
        dial_labels=(
            ("dollar_breadth", dollar),
            ("crude_inventory", inventory),
            ("treasury_curve_level", curve_level),
            ("treasury_curve_direction", curve_direction),
        ),
        blockers=(),
    )
