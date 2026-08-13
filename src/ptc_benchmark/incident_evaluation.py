from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

from .incident import IncidentScenario, collect_evidence_ids
from .runner import ToolCallingRun


@dataclass(frozen=True)
class IncidentEvaluation:
    passed: bool
    execution_result_passed: bool
    final_result_passed: bool
    explanation_passed: bool
    evidence_grounding_passed: bool
    adaptive_start_passed: bool
    no_duplicate_calls_passed: bool
    caller_linkage_passed: bool
    failures: tuple[str, ...]


def evaluate_incident_run(
    run: ToolCallingRun,
    scenario: IncidentScenario,
) -> IncidentEvaluation:
    expected = scenario.expected_result()
    failures: list[str] = []
    if run.arm == "programmatic":
        execution_result = run.program_outputs[-1] if run.program_outputs else None
    else:
        execution_result = run.parsed_final_result
    execution_result = _normalized_result(execution_result)
    final_result = _normalized_result(run.parsed_final_result)

    execution_result_passed = execution_result == expected
    if not execution_result_passed:
        failures.append("The structured execution result does not match the incident oracle.")

    final_result_passed = final_result == expected
    if not final_result_passed:
        failures.append("RESULT_JSON does not match the incident oracle.")

    explanation = _explanation(run.final_output)
    required_explanation_values = (
        expected["root_cause"],
        expected["affected_service"],
        expected["recommended_action"],
        *expected["evidence_ids"],
    )
    explanation_passed = bool(explanation) and all(
        value in explanation for value in required_explanation_values
    )
    if not explanation_passed:
        failures.append("EXPLANATION omits the diagnosis, action, service, or required evidence IDs.")

    observed_evidence: set[str] = set()
    for call in run.tool_calls:
        observed_evidence.update(collect_evidence_ids(call.output))
    evidence_grounding_passed = set(expected["evidence_ids"]).issubset(observed_evidence)
    if not evidence_grounding_passed:
        failures.append("The final diagnosis cites evidence that was not fully retrieved by tools.")

    first_request_calls = {
        (call.name, call.arguments.get("service"), call.arguments.get("metric"))
        for call in run.tool_calls
        if call.request_index == min((item.request_index for item in run.tool_calls), default=-1)
    }
    adaptive_start_passed = (
        len(first_request_calls) == 2
        and
        ("search_logs", scenario.entry_service, None) in first_request_calls
        and ("get_service_metrics", scenario.entry_service, "error_rate") in first_request_calls
    )
    if not adaptive_start_passed:
        failures.append("The investigation did not begin with the two required entry observations.")

    signatures = [
        (call.name, json.dumps(call.arguments, sort_keys=True, separators=(",", ":")))
        for call in run.tool_calls
    ]
    no_duplicate_calls_passed = len(signatures) == len(set(signatures))
    if not no_duplicate_calls_passed:
        failures.append("The investigation repeated an identical tool call.")

    if run.arm == "programmatic":
        caller_linkage_passed = bool(run.tool_calls) and all(
            call.caller is not None
            and call.caller.get("type") == "program"
            and bool(call.caller.get("caller_id"))
            for call in run.tool_calls
        )
    else:
        caller_linkage_passed = all(call.caller is None for call in run.tool_calls)
    if not caller_linkage_passed:
        failures.append("Function-call caller linkage does not match the selected arm.")

    passed = all(
        (
            execution_result_passed,
            final_result_passed,
            explanation_passed,
            evidence_grounding_passed,
            adaptive_start_passed,
            no_duplicate_calls_passed,
            caller_linkage_passed,
        )
    )
    return IncidentEvaluation(
        passed=passed,
        execution_result_passed=execution_result_passed,
        final_result_passed=final_result_passed,
        explanation_passed=explanation_passed,
        evidence_grounding_passed=evidence_grounding_passed,
        adaptive_start_passed=adaptive_start_passed,
        no_duplicate_calls_passed=no_duplicate_calls_passed,
        caller_linkage_passed=caller_linkage_passed,
        failures=tuple(failures),
    )


def _normalized_result(value: dict[str, Any] | None) -> dict[str, Any] | None:
    if not isinstance(value, dict):
        return None
    normalized = dict(value)
    evidence_ids = normalized.get("evidence_ids")
    if isinstance(evidence_ids, list) and all(isinstance(item, str) for item in evidence_ids):
        normalized["evidence_ids"] = sorted(evidence_ids)
    return normalized


def _explanation(text: str) -> str:
    marker = "EXPLANATION:"
    index = text.find(marker)
    return text[index + len(marker) :].strip() if index >= 0 else ""
