"""Independent federal-source Macro Context Panel: synthetic-only experiment.

THIS IS NOT USD IMPACT SCORE v2. Invented year-2099+ values only.
No provider retrieval, file I/O, paid market-data transport, real observations,
publishing, trading signal, model approval, rights grant or production access.

Uses the existing Phase-B synthetic point-in-time receipts to prevent revisions
and late-release data from leaking into a historical cutoff.
"""
from __future__ import annotations

import math
import re
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

# Closed internal result vocabulary. These are invented test labels only:
# never a trading signal, provider attribution, license, public schema, or
# an approved customer-facing product.
DIAL_VALUES = {
    "dollar_breadth": frozenset(("UP", "DOWN", "UNCHANGED")),
    "crude_inventory": frozenset(("BUILD", "DRAW", "UNCHANGED")),
    "treasury_curve_level": frozenset(("POSITIVE", "INVERTED", "FLAT")),
    "treasury_curve_direction": frozenset(
        ("STEEPENING", "FLATTENING", "UNCHANGED")
    ),
}
BLOCKER_CODES = frozenset((
    "MISSING_SYNTHETIC_RECEIPT",
    "NOT_FIRST_SEEN_BY_CUTOFF",
    "TREASURY_CURVE_SNAPSHOT_MISMATCH",
    "TREASURY_CURVE_REVISION_MISMATCH",
    "TREASURY_CURVE_INITIAL_RELEASE_MISMATCH",
    "TREASURY_CURVE_VERSION_PUBLICATION_MISMATCH",
    "TREASURY_CURVE_FIRST_SEEN_MISMATCH",
    "NO_MATCHING_VISIBLE_SYNTHETIC_VALUE",
    "INCOMPLETE_FOUR_SOURCE_SET",
))
_DATE_TOKEN = re.compile(r"[0-9]{4}-[0-9]{2}-[0-9]{2}")


def _synthetic_result_friday(value: object, label: str) -> date:
    if not isinstance(value, str) or _DATE_TOKEN.fullmatch(value) is None:
        raise ValueError(f"{label}: YYYY-MM-DD date required")
    try:
        parsed = date.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(f"{label}: invalid calendar date") from exc
    if parsed.year < MIN_SYNTHETIC_YEAR or parsed.weekday() != 4:
        raise ValueError(f"{label}: synthetic year-2099+ Friday required")
    return parsed


def _valid_blocker(value: object, allowed_weeks: set[str]) -> bool:
    # No arbitrary error text, numbers, URLs, markdown, escape sequences,
    # free-form evidence, market data or contact details in panel output.
    if not isinstance(value, str) or len(value) > 150:
        return False
    parts = value.split(":")
    if len(parts) not in (2, 3) or parts[0] not in allowed_weeks:
        return False
    if len(parts) == 3:
        return parts[1] in REQUIRED_IDS and parts[2] in BLOCKER_CODES
    return parts[1] in BLOCKER_CODES



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
        # A caller may instantiate a frozen dataclass directly instead of using
        # the evaluator. That MUST NOT bypass the closed synthetic-only
        # vocabulary or put free-form provider/economic text into a preview.
        for authorized in (
            self.rights_cleared,
            self.real_data_fetch_authorized,
            self.publish_authorized,
            self.production_authorized,
        ):
            if authorized is not False:
                raise ValueError(
                    "synthetic context panel cannot grant real-data or publication rights"
                )
        if self.panel_id != PANEL_ID or self.fixture_marker != SYNTHETIC_MARKER:
            raise ValueError("unrecognized synthetic panel")
        if self.status not in {"SYNTHETIC_ONLY_HOLD", "SYNTHETIC_ONLY_COMPLETE"}:
            raise ValueError("invalid synthetic-only state")

        current = _synthetic_result_friday(self.reference_week, "reference_week")
        previous = _synthetic_result_friday(self.previous_week, "previous_week")
        if previous != current - timedelta(days=7):
            raise ValueError("previous_week must precede reference_week by seven days")

        if not isinstance(self.dial_labels, tuple):
            raise ValueError("synthetic dial labels must be a tuple")
        if not isinstance(self.blockers, tuple) or len(self.blockers) > 32:
            raise ValueError("synthetic blockers must be a bounded tuple")
        if self.blockers != tuple(sorted(set(self.blockers))):
            raise ValueError("synthetic blockers must be unique and sorted")
        weeks = {self.previous_week, self.reference_week}
        if not all(_valid_blocker(item, weeks) for item in self.blockers):
            raise ValueError("unrecognized synthetic blocker code")

        if self.status == "SYNTHETIC_ONLY_HOLD":
            if self.dial_labels or not self.blockers:
                raise ValueError("synthetic HOLD must have blockers and no labels")
            return

        if self.blockers:
            raise ValueError("synthetic COMPLETE must not contain blockers")
        if len(self.dial_labels) != len(DIALS):
            raise ValueError("synthetic COMPLETE requires exactly four dial labels")
        for index, pair in enumerate(self.dial_labels):
            if (
                not isinstance(pair, tuple)
                or len(pair) != 2
                or pair[0] != DIALS[index]
                or not isinstance(pair[1], str)
                or pair[1] not in DIAL_VALUES[DIALS[index]]
            ):
                raise ValueError("unapproved synthetic dial name or label")


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
