from pathlib import Path

from scripts import validate_score_v2_1e_h15_output_scope_review as validator

ROOT = Path(__file__).resolve().parents[1]

def test_h15_output_scope_review_is_fail_closed():
    result = validator.validate(ROOT)
    assert result["status"] == "passed"
    assert result["h15_slots_reviewed"] == 3
    assert result["published_government_outputs_only"] is True
    assert result["raw_upstream_quote_use"] is False
    assert result["source_approval"] is False
    assert result["real_data_research_authorized"] is False
    assert result["production_authorized"] is False
    assert result["rights_hold"] is True
