from __future__ import annotations

import copy
from dataclasses import dataclass
from typing import Any, Literal

from .inventory import InventoryDataset, InventoryScale, build_inventory_dataset

InventoryToolSearchArm = Literal[
    "direct_eager",
    "programmatic_eager",
    "programmatic_tool_search",
]

CATALOG_SIZES = (20, 50, 100, 200)
TOOLS_PER_NAMESPACE = 5
REQUIRED_INVENTORY_TOOLS = (
    "get_inventory",
    "get_weekly_demand",
    "get_inbound_shipments",
)

_SYNTHETIC_DOMAINS = (
    "billing", "payments", "promotions", "pricing", "tax", "fraud",
    "procurement", "suppliers", "catalog", "reviews", "subscriptions",
    "warranties", "marketing", "campaigns", "analytics", "forecasting",
    "compliance", "audit", "workforce", "scheduling", "facilities", "fleet",
    "repairs", "quality", "localization", "content", "recommendations",
    "experiments", "loyalty", "gift_cards", "marketplace", "merchants",
    "settlements", "contracts", "risk", "reporting", "legal", "finance",
    "communications",
)
_SYNTHETIC_ACTIONS = ("get", "list", "validate", "estimate", "summarize")


@dataclass(frozen=True)
class InventoryToolSearchScenario:
    dataset: InventoryDataset
    catalog_size: int
    namespaces: tuple[dict[str, Any], ...]

    @property
    def scenario_name(self) -> str:
        return "inventory_tool_search"

    @property
    def case_id(self) -> str:
        return f"inventory-tool-search-{self.dataset.scale}-{self.catalog_size}"

    @property
    def function_count(self) -> int:
        return sum(len(namespace["tools"]) for namespace in self.namespaces)

    def tool_definitions(self, arm: InventoryToolSearchArm) -> list[dict[str, Any]]:
        if arm not in {
            "direct_eager",
            "programmatic_eager",
            "programmatic_tool_search",
        }:
            raise ValueError(f"Unsupported arm: {arm}")

        allowed_callers = ["direct"] if arm == "direct_eager" else ["programmatic"]
        definitions = copy.deepcopy(list(self.namespaces))
        for namespace in definitions:
            for function in namespace["tools"]:
                function["allowed_callers"] = allowed_callers
                if arm == "programmatic_tool_search":
                    function["defer_loading"] = True

        if arm == "programmatic_tool_search":
            definitions.extend(
                [{"type": "tool_search"}, {"type": "programmatic_tool_calling"}]
            )
        elif arm == "programmatic_eager":
            definitions.append({"type": "programmatic_tool_calling"})
        return definitions

    def prompt(self, arm: InventoryToolSearchArm) -> tuple[str, str]:
        base_instructions, user = self.dataset.prompt(
            "direct" if arm == "direct_eager" else "programmatic"
        )
        if arm == "programmatic_tool_search":
            orchestration = """
Before creating a Programmatic Tool Calling program, use hosted Tool Search to load
only the inventory tools needed by the task. Do not load or use an unrelated
namespace. After Tool Search returns the definitions, create one program that calls
the three required inventory tools for every SKU and performs the calculations.
Tool Search is a top-level hosted tool: never try to invoke it from inside JavaScript.
""".strip()
            base_instructions = (
                f"{base_instructions}\n\n<tool_search_contract>\n"
                f"{orchestration}\n</tool_search_contract>"
            )
        return base_instructions, user

    def execute(
        self,
        namespace: str,
        tool_name: str,
        arguments: dict[str, Any],
    ) -> dict[str, Any]:
        if namespace != "inventory" or tool_name not in REQUIRED_INVENTORY_TOOLS:
            raise ValueError(f"Tool is not executable in this benchmark: {namespace}.{tool_name}")
        return self.dataset.execute(tool_name, arguments)

    def expected_plan(self) -> dict[str, Any]:
        return self.dataset.expected_plan()


def build_inventory_tool_search_scenario(
    *,
    catalog_size: int = 100,
    inventory_scale: InventoryScale = "small",
) -> InventoryToolSearchScenario:
    if catalog_size not in CATALOG_SIZES:
        raise ValueError(f"catalog_size must be one of {CATALOG_SIZES}")

    dataset = build_inventory_dataset(inventory_scale)
    inventory_functions = [
        copy.deepcopy(tool)
        for tool in dataset.tool_definitions("programmatic")
        if tool["type"] == "function"
    ]
    for function in inventory_functions:
        function.pop("allowed_callers", None)
    inventory_functions.extend(_inventory_helper_tools())

    namespaces: list[dict[str, Any]] = [
        {
            "type": "namespace",
            "name": "inventory",
            "description": (
                "Inventory replenishment data: warehouse availability, weekly demand, "
                "inbound shipments, safety-stock policy, and dataset metadata."
            ),
            "tools": inventory_functions,
        }
    ]
    distractor_count = catalog_size // TOOLS_PER_NAMESPACE - 1
    for ordinal, domain in enumerate(_SYNTHETIC_DOMAINS[:distractor_count], start=1):
        namespaces.append(_synthetic_namespace(domain, ordinal))

    scenario = InventoryToolSearchScenario(
        dataset=dataset,
        catalog_size=catalog_size,
        namespaces=tuple(namespaces),
    )
    if scenario.function_count != catalog_size:
        raise AssertionError("Generated catalog size does not match the requested size")
    return scenario


def _inventory_helper_tools() -> list[dict[str, Any]]:
    return [
        _read_tool(
            "get_safety_stock_policy",
            "Return the read-only safety-stock policy metadata for an inventory dataset.",
        ),
        _read_tool(
            "get_inventory_dataset_metadata",
            "Return read-only provenance and freshness metadata for an inventory dataset.",
        ),
    ]


def _synthetic_namespace(domain: str, ordinal: int) -> dict[str, Any]:
    namespace_name = f"domain_{ordinal:02d}_{domain}"
    tools = []
    for tool_index, action in enumerate(_SYNTHETIC_ACTIONS, start=1):
        entity = f"{domain}_record_{tool_index:02d}"
        tools.append(
            _read_tool(
                f"{action}_{entity}",
                f"{action.title()} read-only {domain.replace('_', ' ')} data for {entity}.",
            )
        )
    return {
        "type": "namespace",
        "name": namespace_name,
        "description": (
            f"Read-only {domain.replace('_', ' ')} records, policies, and metrics. "
            "This namespace is unrelated to inventory replenishment."
        ),
        "tools": tools,
    }


def _read_tool(name: str, description: str) -> dict[str, Any]:
    return {
        "type": "function",
        "name": name,
        "description": description,
        "parameters": {
            "type": "object",
            "properties": {
                "resource_id": {"type": "string", "description": "Opaque resource ID."}
            },
            "required": ["resource_id"],
            "additionalProperties": False,
        },
        "output_schema": {
            "type": "object",
            "properties": {
                "resource_id": {"type": "string"},
                "status": {"type": "string"},
            },
            "required": ["resource_id", "status"],
            "additionalProperties": False,
        },
        "strict": True,
    }
