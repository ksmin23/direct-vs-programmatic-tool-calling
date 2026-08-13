from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .refund import RefundApprovalScenario, RefundSelectionScenario, collect_refund_evidence_ids
from .runner import ToolCallingRun


@dataclass(frozen=True)
class RefundSelectionEvaluation:
    passed: bool
    execution_result_passed: bool
    final_result_passed: bool
    explanation_passed: bool
    evidence_grounding_passed: bool
    tool_coverage_passed: bool
    caller_linkage_passed: bool
    failures: tuple[str, ...]


@dataclass(frozen=True)
class RefundApprovalEvaluation:
    passed: bool
    final_result_passed: bool
    explanation_passed: bool
    action_sequence_passed: bool
    caller_linkage_passed: bool
    failures: tuple[str, ...]


@dataclass(frozen=True)
class RefundWorkflowEvaluation:
    passed: bool
    selection_passed: bool
    approval_passed: bool
    safety_boundary_passed: bool
    failures: tuple[str, ...]


def evaluate_refund_selection(
    run: ToolCallingRun,
    scenario: RefundSelectionScenario,
) -> RefundSelectionEvaluation:
    expected = scenario.expected_selection()
    failures: list[str] = []
    execution_result = (
        run.program_outputs[-1] if run.arm == "programmatic" and run.program_outputs else run.parsed_final_result
    )
    execution_result_passed = _normalize_selection(execution_result) == expected
    if not execution_result_passed:
        failures.append("The structured selection result does not match the refund oracle.")

    final_result_passed = _normalize_selection(run.parsed_final_result) == expected
    if not final_result_passed:
        failures.append("RESULT_JSON does not match the refund-selection oracle.")

    explanation = _explanation(run.final_output)
    explanation_passed = bool(explanation)
    for candidate in expected["candidates"]:
        required = (
            candidate["order_id"],
            str(candidate["delay_hours"]),
            str(candidate["refund_amount_cents"]),
            candidate["reason"],
            *candidate["evidence_ids"],
        )
        if not all(value in explanation for value in required):
            explanation_passed = False
            break
    if not explanation_passed:
        failures.append("EXPLANATION omits a candidate value or required evidence ID.")

    observed_evidence: set[str] = set()
    for call in run.tool_calls:
        observed_evidence.update(collect_refund_evidence_ids(call.output))
    cited_evidence = {
        evidence_id
        for candidate in expected["candidates"]
        for evidence_id in candidate["evidence_ids"]
    }
    evidence_grounding_passed = cited_evidence.issubset(observed_evidence)
    if not evidence_grounding_passed:
        failures.append("The selection cites evidence that was not retrieved by tools.")

    expected_calls = [("list_delayed_orders", None)]
    for order_id in scenario.order_ids:
        expected_calls.extend(
            (name, order_id)
            for name in (
                "get_order",
                "get_delivery_events",
                "get_refund_history",
                "get_refund_policy",
            )
        )
    actual_calls = [(call.name, call.arguments.get("order_id")) for call in run.tool_calls]
    tool_coverage_passed = len(actual_calls) == len(expected_calls) and set(actual_calls) == set(expected_calls)
    if not tool_coverage_passed:
        failures.append("Read calls do not cover the list and four detail tools exactly once per order.")

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
        failures.append("Selection caller linkage does not match the selected arm.")

    passed = all(
        (
            execution_result_passed,
            final_result_passed,
            explanation_passed,
            evidence_grounding_passed,
            tool_coverage_passed,
            caller_linkage_passed,
        )
    )
    return RefundSelectionEvaluation(
        passed=passed,
        execution_result_passed=execution_result_passed,
        final_result_passed=final_result_passed,
        explanation_passed=explanation_passed,
        evidence_grounding_passed=evidence_grounding_passed,
        tool_coverage_passed=tool_coverage_passed,
        caller_linkage_passed=caller_linkage_passed,
        failures=tuple(failures),
    )


def evaluate_refund_approval(
    run: ToolCallingRun,
    scenario: RefundApprovalScenario,
) -> RefundApprovalEvaluation:
    expected = scenario.expected_result()
    failures: list[str] = []
    final_result_passed = run.parsed_final_result == expected
    if not final_result_passed:
        failures.append("Approval RESULT_JSON does not match the action oracle.")

    explanation = _explanation(run.final_output)
    required: list[str] = []
    for approval in expected["approvals"]:
        required.extend((approval["order_id"], approval["decision"], approval["rationale"]))
    for refund in expected["refunds"]:
        required.extend(
            (
                refund["order_id"],
                refund["approval_id"],
                refund["refund_transaction_id"],
                str(refund["refund_amount_cents"]),
            )
        )
    explanation_passed = bool(explanation) and all(value in explanation for value in required)
    if not explanation_passed:
        failures.append("Approval EXPLANATION omits a decision or issued-refund detail.")

    candidates = {row["order_id"]: row for row in scenario.candidate_plan["candidates"]}
    approved = {
        row["order_id"]: row for row in expected["approvals"] if row["decision"] == "approved"
    }
    approval_calls = [call for call in run.tool_calls if call.name == "request_refund_approval"]
    issue_calls = [call for call in run.tool_calls if call.name == "issue_refund"]
    action_sequence_passed = (
        len(approval_calls) == len(candidates)
        and {call.arguments.get("order_id") for call in approval_calls} == set(candidates)
        and len(issue_calls) == len(approved)
        and {call.arguments.get("order_id") for call in issue_calls} == set(approved)
        and all(
            call.arguments.get("approval_id") == approved[call.arguments["order_id"]]["approval_id"]
            and call.arguments.get("amount_cents") == candidates[call.arguments["order_id"]]["refund_amount_cents"]
            for call in issue_calls
        )
    )
    if not action_sequence_passed:
        failures.append("Approval or issue-refund calls violate the expected approval boundary.")

    caller_linkage_passed = run.arm == "direct" and all(call.caller is None for call in run.tool_calls)
    if not caller_linkage_passed:
        failures.append("Approval and refund actions must use Direct Tool Calling only.")

    passed = all(
        (final_result_passed, explanation_passed, action_sequence_passed, caller_linkage_passed)
    )
    return RefundApprovalEvaluation(
        passed=passed,
        final_result_passed=final_result_passed,
        explanation_passed=explanation_passed,
        action_sequence_passed=action_sequence_passed,
        caller_linkage_passed=caller_linkage_passed,
        failures=tuple(failures),
    )


def _normalize_selection(value: dict[str, Any] | None) -> dict[str, Any] | None:
    if not isinstance(value, dict):
        return None
    normalized = dict(value)
    candidates = normalized.get("candidates")
    if not isinstance(candidates, list):
        return normalized
    normalized_candidates = []
    for candidate in candidates:
        if not isinstance(candidate, dict):
            normalized_candidates.append(candidate)
            continue
        item = dict(candidate)
        if isinstance(item.get("evidence_ids"), list):
            item["evidence_ids"] = sorted(item["evidence_ids"])
        normalized_candidates.append(item)
    normalized["candidates"] = sorted(
        normalized_candidates,
        key=lambda row: row.get("order_id", "") if isinstance(row, dict) else "",
    )
    return normalized


def _explanation(text: str) -> str:
    marker = "EXPLANATION:"
    index = text.find(marker)
    return text[index + len(marker) :].strip() if index >= 0 else ""
