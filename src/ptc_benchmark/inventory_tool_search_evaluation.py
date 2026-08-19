from __future__ import annotations

from dataclasses import dataclass

from .inventory_tool_search import REQUIRED_INVENTORY_TOOLS, InventoryToolSearchScenario
from .inventory_tool_search_runner import InventoryToolSearchRun


@dataclass(frozen=True)
class InventoryToolSearchEvaluation:
    passed: bool
    required_tools_loaded_passed: bool
    unrelated_namespace_avoided_passed: bool
    executed_tools_passed: bool
    event_order_passed: bool
    caller_linkage_passed: bool
    program_output_passed: bool
    final_result_passed: bool
    explanation_passed: bool
    warnings: tuple[str, ...]
    failures: tuple[str, ...]


def evaluate_inventory_tool_search_run(
    run: InventoryToolSearchRun,
    scenario: InventoryToolSearchScenario,
) -> InventoryToolSearchEvaluation:
    failures: list[str] = []
    warnings: list[str] = []
    expected = scenario.expected_plan()
    required_loaded = {f"inventory.{name}" for name in REQUIRED_INVENTORY_TOOLS}

    if run.arm == "programmatic_tool_search":
        required_tools_loaded_passed = required_loaded <= run.loaded_tools
        unrelated_namespace_avoided_passed = all(
            name.startswith("inventory.") for name in run.loaded_tools
        )
        extra_inventory = sorted(run.loaded_tools - required_loaded)
        if extra_inventory:
            warnings.append(
                "Tool Search loaded extra inventory tools (efficiency warning only): "
                + ", ".join(extra_inventory)
            )
    else:
        required_tools_loaded_passed = True
        unrelated_namespace_avoided_passed = True

    if not required_tools_loaded_passed:
        failures.append("Tool Search did not load every required inventory tool.")
    if not unrelated_namespace_avoided_passed:
        failures.append("Tool Search loaded at least one unrelated namespace.")

    expected_calls = {
        (f"inventory.{tool_name}", sku)
        for sku in scenario.dataset.skus
        for tool_name in REQUIRED_INVENTORY_TOOLS
    }
    actual_calls = [
        (call.qualified_name, call.arguments.get("sku")) for call in run.tool_calls
    ]
    executed_tools_passed = (
        len(actual_calls) == len(expected_calls) and set(actual_calls) == expected_calls
    )
    if not executed_tools_passed:
        failures.append("Executed tools do not match every required tool and SKU exactly once.")

    if run.arm == "programmatic_tool_search":
        event_order_passed = _combined_event_order_passed(run)
    else:
        event_order_passed = True
    if not event_order_passed:
        failures.append(
            "The semantic event order is not Tool Search, program, function calls, "
            "program output, then final message."
        )

    if run.arm == "direct_eager":
        caller_linkage_passed = all(call.caller is None for call in run.tool_calls)
    else:
        caller_linkage_passed = bool(run.tool_calls) and all(
            call.caller is not None
            and call.caller.get("type") == "program"
            and bool(call.caller.get("caller_id"))
            for call in run.tool_calls
        )
    if not caller_linkage_passed:
        failures.append("Function-call caller linkage does not match the selected arm.")

    if run.arm == "direct_eager":
        program_output_passed = True
    else:
        program_output_passed = bool(run.program_outputs) and run.program_outputs[-1] == expected
    if not program_output_passed:
        failures.append("The final program output does not match the deterministic oracle.")

    final_result_passed = run.parsed_final_result == expected
    if not final_result_passed:
        failures.append("RESULT_JSON does not match the deterministic oracle.")

    explanation = _explanation(run.final_output)
    explanation_passed = bool(explanation)
    for row in expected["recommendations"]:
        evidence = (
            row["sku"],
            str(row["available_units"]),
            str(row["forecast_units"]),
            str(row["inbound_units"]),
            str(row["reorder_units"]),
        )
        if not all(value in explanation for value in evidence):
            explanation_passed = False
            break
    if not explanation_passed:
        failures.append("EXPLANATION omits a recommended SKU or required unit evidence.")

    return InventoryToolSearchEvaluation(
        passed=not failures,
        required_tools_loaded_passed=required_tools_loaded_passed,
        unrelated_namespace_avoided_passed=unrelated_namespace_avoided_passed,
        executed_tools_passed=executed_tools_passed,
        event_order_passed=event_order_passed,
        caller_linkage_passed=caller_linkage_passed,
        program_output_passed=program_output_passed,
        final_result_passed=final_result_passed,
        explanation_passed=explanation_passed,
        warnings=tuple(warnings),
        failures=tuple(failures),
    )


def _combined_event_order_passed(run: InventoryToolSearchRun) -> bool:
    types = [event.type for event in run.events]
    try:
        search_call = types.index("tool_search_call")
        search_output = types.index("tool_search_output")
        program = types.index("program")
        program_output = types.index("program_output")
        message = types.index("message")
    except ValueError:
        return False
    function_calls = [index for index, value in enumerate(types) if value == "function_call"]
    if not function_calls:
        return False
    return (
        search_call < search_output < program
        and all(program < index < program_output for index in function_calls)
        and program_output < message
        and all(
            index < program
            for index, value in enumerate(types)
            if value in {"tool_search_call", "tool_search_output"}
        )
    )


def _explanation(text: str) -> str:
    marker = "EXPLANATION:"
    index = text.find(marker)
    return text[index + len(marker) :].strip() if index >= 0 else ""
