from __future__ import annotations

import pytest

from ptc_benchmark.incident import INCIDENT_CASE_IDS, build_incident_scenario


@pytest.mark.parametrize("case_id", INCIDENT_CASE_IDS)
def test_incident_scenario_exposes_grounded_oracle(case_id: str) -> None:
    scenario = build_incident_scenario(case_id)
    expected = scenario.expected_result()

    assert expected["incident_id"] == case_id
    assert expected["confidence"] == "high"
    assert len(expected["evidence_ids"]) >= 3
    assert len(scenario.tool_definitions("direct")) == 4
    assert scenario.tool_definitions("programmatic")[-1] == {
        "type": "programmatic_tool_calling"
    }


def test_incident_builder_rejects_unknown_case() -> None:
    with pytest.raises(ValueError, match="Unknown incident case"):
        build_incident_scenario("missing")
