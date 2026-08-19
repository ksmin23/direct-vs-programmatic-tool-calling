from __future__ import annotations

import json
from types import SimpleNamespace

from ptc_benchmark.incident import build_incident_scenario
from ptc_benchmark.runner import RunConfig, ToolCallingRunner


class _CompletedResponses:
    def __init__(self, result: dict[str, object]) -> None:
        self.result = result
        self.calls: list[dict[str, object]] = []

    def create(self, **request: object) -> SimpleNamespace:
        self.calls.append(request)
        return SimpleNamespace(
            id="response-1",
            status="completed",
            output=[{"type": "message"}],
            usage=None,
            output_text=f"RESULT_JSON: {json.dumps(self.result)}\nEXPLANATION: fixture",
        )


def test_incident_runner_preserves_scenario_and_request_contract() -> None:
    scenario = build_incident_scenario("database-pool-exhaustion")
    responses = _CompletedResponses(scenario.expected_result())

    run = ToolCallingRunner(SimpleNamespace(responses=responses)).run(
        arm="direct",
        scenario=scenario,
        config=RunConfig(model="test", max_requests=1),
        run_id="incident-test",
    )

    assert run.scenario == "incident"
    assert run.case_id == "database-pool-exhaustion"
    assert run.parsed_final_result == scenario.expected_result()
    assert responses.calls[0]["parallel_tool_calls"] is True
