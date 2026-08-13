from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date, timedelta
from typing import Any, Literal

InventoryScale = Literal["small", "medium", "large"]
Arm = Literal["direct", "programmatic"]

SCALE_COUNTS: dict[InventoryScale, int] = {
    "small": 3,
    "medium": 10,
    "large": 30,
}


@dataclass(frozen=True)
class InventoryDataset:
    scale: InventoryScale
    as_of_date: str
    skus: tuple[str, ...]
    inventory: dict[str, dict[str, Any]]
    demand: dict[str, dict[str, Any]]
    inbound: dict[str, dict[str, Any]]
    safety_stock: int = 5

    @property
    def scenario_name(self) -> str:
        return "inventory"

    @property
    def case_id(self) -> str:
        return f"inventory-{self.scale}"

    def execute(self, tool_name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        sku = arguments.get("sku")
        if sku not in self.skus:
            raise ValueError(f"Unknown sku: {sku!r}")
        stores = {
            "get_inventory": self.inventory,
            "get_weekly_demand": self.demand,
            "get_inbound_shipments": self.inbound,
        }
        try:
            return stores[tool_name][sku]
        except KeyError as exc:
            raise ValueError(f"Unknown tool: {tool_name}") from exc

    def expected_plan(self) -> dict[str, Any]:
        horizon_end = date.fromisoformat(self.as_of_date) + timedelta(days=7)
        recommendations: list[dict[str, Any]] = []
        for sku in self.skus:
            available_units = sum(
                row["on_hand_units"] - row["reserved_units"]
                for row in self.inventory[sku]["warehouses"]
            )
            forecast_units = sum(row["units"] for row in self.demand[sku]["daily_forecast"])
            inbound_units = sum(
                row["units"]
                for row in self.inbound[sku]["shipments"]
                if row["status"] == "scheduled"
                and date.fromisoformat(row["eta_date"]) <= horizon_end
            )
            reorder_units = max(
                forecast_units + self.safety_stock - available_units - inbound_units,
                0,
            )
            if reorder_units > 0:
                recommendations.append(
                    {
                        "sku": sku,
                        "available_units": available_units,
                        "forecast_units": forecast_units,
                        "inbound_units": inbound_units,
                        "reorder_units": reorder_units,
                    }
                )
        recommendations.sort(key=lambda row: (-row["reorder_units"], row["sku"]))
        return {
            "recommendations": recommendations,
            "total_reorder_units": sum(row["reorder_units"] for row in recommendations),
        }

    def tool_definitions(self, arm: Arm) -> list[dict[str, Any]]:
        allowed_callers = ["direct"] if arm == "direct" else ["programmatic"]
        definitions = [
            _function_tool(
                name="get_inventory",
                description=(
                    "Return warehouse-level on-hand and reserved inventory for one SKU. "
                    "Available units equal the sum of on_hand_units minus reserved_units."
                ),
                output_schema=_inventory_output_schema(),
                allowed_callers=allowed_callers,
            ),
            _function_tool(
                name="get_weekly_demand",
                description=(
                    "Return the seven daily demand forecast rows for one SKU. "
                    "Forecast units equal the sum of daily units."
                ),
                output_schema=_demand_output_schema(),
                allowed_callers=allowed_callers,
            ),
            _function_tool(
                name="get_inbound_shipments",
                description=(
                    "Return inbound shipment rows for one SKU. Count only scheduled shipments "
                    "whose eta_date is within seven days after the dataset as_of_date."
                ),
                output_schema=_inbound_output_schema(),
                allowed_callers=allowed_callers,
            ),
        ]
        if arm == "programmatic":
            definitions.append({"type": "programmatic_tool_calling"})
        return definitions

    def prompt(self, arm: Arm) -> tuple[str, str]:
        sku_list = ", ".join(self.skus)
        shared = f"""
You are preparing a deterministic inventory replenishment plan as of {self.as_of_date}.

For every SKU in this exact list, call get_inventory, get_weekly_demand, and
get_inbound_shipments exactly once: {sku_list}.

For each SKU:
1. available_units = sum(on_hand_units - reserved_units) across warehouses.
2. forecast_units = sum(units) across all seven daily_forecast rows.
3. inbound_units = sum(units) only for shipments with status "scheduled" and
   eta_date on or before {(date.fromisoformat(self.as_of_date) + timedelta(days=7)).isoformat()}.
4. reorder_units = max(forecast_units + {self.safety_stock} - available_units - inbound_units, 0).

Keep only positive reorder quantities. Sort by reorder_units descending and then
sku ascending. The structured result must be exactly one JSON object with this shape:
{{"recommendations":[{{"sku":"...","available_units":0,"forecast_units":0,
"inbound_units":0,"reorder_units":0}}],"total_reorder_units":0}}

The final assistant message must contain:
RESULT_JSON: <the exact one-line JSON object>
EXPLANATION: <a concise explanation that cites every recommended SKU and all four
source/calculated unit values for that SKU>.
Do not invent values and do not omit evidence from the explanation.
""".strip()

        if arm == "direct":
            orchestration = """
Use Direct Tool Calling. Call the functions directly and issue independent calls in
parallel when possible. Use the returned tool data to calculate the result. Do not
write or execute a programmatic_tool_calling program.
""".strip()
        else:
            orchestration = """
Use Programmatic Tool Calling for the complete lookup and calculation stage. Create
all tool-call promises before awaiting them and resolve them with Promise.all. Perform
all filtering, summation, sorting, and reduction inside the generated JavaScript.
Emit exactly the required JSON object from the program with text(JSON.stringify(result)).
After the program completes, write the required RESULT_JSON and EXPLANATION final message.
Do not call the inventory functions directly.
""".strip()

        instructions = f"<task_contract>\n{shared}\n</task_contract>\n\n<tool_orchestration>\n{orchestration}\n</tool_orchestration>"
        user = "Which products should we reorder this week, and in what quantities?"
        return instructions, user


def build_inventory_dataset(scale: InventoryScale = "medium") -> InventoryDataset:
    if scale not in SCALE_COUNTS:
        raise ValueError(f"Unsupported scale: {scale}")
    count = SCALE_COUNTS[scale]
    as_of = date(2026, 8, 10)
    skus = tuple(f"sku-{index + 1:03d}" for index in range(count))
    inventory: dict[str, dict[str, Any]] = {}
    demand: dict[str, dict[str, Any]] = {}
    inbound: dict[str, dict[str, Any]] = {}

    for index, sku in enumerate(skus):
        warehouses = []
        for warehouse_index in range(3):
            warehouses.append(
                {
                    "warehouse_id": f"wh-{warehouse_index + 1}",
                    "on_hand_units": 4 + ((index * 3 + warehouse_index * 2) % 9),
                    "reserved_units": (index + warehouse_index) % 3,
                }
            )
        inventory[sku] = {"sku": sku, "warehouses": warehouses}

        daily_forecast = [
            {
                "date": (as_of + timedelta(days=day_index + 1)).isoformat(),
                "units": 1 + ((index * 2 + day_index) % 5),
            }
            for day_index in range(7)
        ]
        demand[sku] = {"sku": sku, "daily_forecast": daily_forecast}

        shipments = [
            {
                "shipment_id": f"ship-{index + 1:03d}-a",
                "eta_date": (as_of + timedelta(days=2 + (index % 3))).isoformat(),
                "units": 3 + (index % 5),
                "status": "scheduled" if index % 3 else "delayed",
            },
            {
                "shipment_id": f"ship-{index + 1:03d}-b",
                "eta_date": (as_of + timedelta(days=10)).isoformat(),
                "units": 8 + (index % 4),
                "status": "scheduled",
            },
            {
                "shipment_id": f"ship-{index + 1:03d}-c",
                "eta_date": (as_of - timedelta(days=1)).isoformat(),
                "units": 2,
                "status": "arrived",
            },
        ]
        inbound[sku] = {"sku": sku, "shipments": shipments}

    return InventoryDataset(
        scale=scale,
        as_of_date=as_of.isoformat(),
        skus=skus,
        inventory=inventory,
        demand=demand,
        inbound=inbound,
    )


def compact_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True)


def _function_tool(
    *,
    name: str,
    description: str,
    output_schema: dict[str, Any],
    allowed_callers: list[str],
) -> dict[str, Any]:
    return {
        "type": "function",
        "name": name,
        "description": description,
        "parameters": {
            "type": "object",
            "properties": {"sku": {"type": "string"}},
            "required": ["sku"],
            "additionalProperties": False,
        },
        "output_schema": output_schema,
        "allowed_callers": allowed_callers,
        "strict": True,
    }


def _inventory_output_schema() -> dict[str, Any]:
    return {
        "type": "object",
        "properties": {
            "sku": {"type": "string"},
            "warehouses": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "warehouse_id": {"type": "string"},
                        "on_hand_units": {"type": "integer"},
                        "reserved_units": {"type": "integer"},
                    },
                    "required": ["warehouse_id", "on_hand_units", "reserved_units"],
                    "additionalProperties": False,
                },
            },
        },
        "required": ["sku", "warehouses"],
        "additionalProperties": False,
    }


def _demand_output_schema() -> dict[str, Any]:
    return {
        "type": "object",
        "properties": {
            "sku": {"type": "string"},
            "daily_forecast": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "date": {"type": "string"},
                        "units": {"type": "integer"},
                    },
                    "required": ["date", "units"],
                    "additionalProperties": False,
                },
            },
        },
        "required": ["sku", "daily_forecast"],
        "additionalProperties": False,
    }


def _inbound_output_schema() -> dict[str, Any]:
    return {
        "type": "object",
        "properties": {
            "sku": {"type": "string"},
            "shipments": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "shipment_id": {"type": "string"},
                        "eta_date": {"type": "string"},
                        "units": {"type": "integer"},
                        "status": {"type": "string"},
                    },
                    "required": ["shipment_id", "eta_date", "units", "status"],
                    "additionalProperties": False,
                },
            },
        },
        "required": ["sku", "shipments"],
        "additionalProperties": False,
    }
