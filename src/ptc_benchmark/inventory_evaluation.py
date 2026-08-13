from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .inventory import InventoryDataset
from .runner import InventoryRun


@dataclass(frozen=True)
class InventoryEvaluation:
    passed: bool
    execution_result_passed: bool
    final_result_passed: bool
    explanation_passed: bool
    tool_coverage_passed: bool
    caller_linkage_passed: bool
    failures: tuple[str, ...]


def evaluate_inventory_run(
    run: InventoryRun,
    dataset: InventoryDataset,
) -> InventoryEvaluation:
    expected = dataset.expected_plan()
    failures: list[str] = []

    if run.arm == "programmatic":
        execution_result = run.program_outputs[-1] if run.program_outputs else None
    else:
        execution_result = run.parsed_final_result
    execution_passed = execution_result == expected
    if not execution_passed:
        failures.append("The structured execution result does not match the oracle.")

    final_passed = run.parsed_final_result == expected
    if not final_passed:
        failures.append("RESULT_JSON does not match the oracle.")

    explanation = _explanation(run.final_output)
    explanation_passed = bool(explanation)
    for row in expected["recommendations"]:
        required_values = (
            row["sku"],
            str(row["available_units"]),
            str(row["forecast_units"]),
            str(row["inbound_units"]),
            str(row["reorder_units"]),
        )
        if not all(value in explanation for value in required_values):
            explanation_passed = False
            break
    if not explanation_passed:
        failures.append("EXPLANATION omits a recommended SKU or required unit evidence.")

    expected_calls = {
        (name, sku)
        for sku in dataset.skus
        for name in ("get_inventory", "get_weekly_demand", "get_inbound_shipments")
    }
    actual_calls = [(call.name, call.arguments.get("sku")) for call in run.tool_calls]
    tool_coverage_passed = len(actual_calls) == len(expected_calls) and set(actual_calls) == expected_calls
    if not tool_coverage_passed:
        failures.append("Tool calls do not cover every required tool and SKU exactly once.")

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
            execution_passed,
            final_passed,
            explanation_passed,
            tool_coverage_passed,
            caller_linkage_passed,
        )
    )
    return InventoryEvaluation(
        passed=passed,
        execution_result_passed=execution_passed,
        final_result_passed=final_passed,
        explanation_passed=explanation_passed,
        tool_coverage_passed=tool_coverage_passed,
        caller_linkage_passed=caller_linkage_passed,
        failures=tuple(failures),
    )


def _explanation(text: str) -> str:
    marker = "EXPLANATION:"
    index = text.find(marker)
    return text[index + len(marker) :].strip() if index >= 0 else ""
