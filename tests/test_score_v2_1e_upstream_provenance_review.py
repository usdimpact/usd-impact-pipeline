from pathlib import Path
from scripts import validate_score_v2_1e_upstream_provenance_review as validator

ROOT = Path(__file__).resolve().parents[1]

def test_review_is_evidence_only_and_fail_closed():
    result = validator.validate(ROOT)
    assert result["status"] == "passed"
    assert result["slots_reviewed"] == 8
    assert result["h15_residual_slots"] == 3
    assert result["source_approval"] is False
    assert result["real_data_research_authorized"] is False
    assert result["production_authorized"] is False
    assert result["rights_hold"] is True
