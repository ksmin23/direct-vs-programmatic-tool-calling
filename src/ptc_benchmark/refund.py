from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Literal

from .inventory import Arm

RefundScale = Literal["small", "medium", "large"]
REFUND_SCALE_COUNTS: dict[RefundScale, int] = {"small": 4, "medium": 6, "large": 8}


@dataclass(frozen=True)
class RefundSelectionScenario:
    scale: RefundScale
    date_start: str
    date_end: str
    order_ids: tuple[str, ...]
    orders: dict[str, dict[str, Any]]
    deliveries: dict[str, dict[str, Any]]
    histories: dict[str, dict[str, Any]]
    policies: dict[str, dict[str, Any]]

    @property
    def scenario_name(self) -> str:
        return "refund_selection"

    @property
    def case_id(self) -> str:
        return f"refund-{self.scale}"

    def expected_selection(self) -> dict[str, Any]:
        candidates: list[dict[str, Any]] = []
        for order_id in self.order_ids:
            order = self.orders[order_id]
            delivery = self.deliveries[order_id]
            history = self.histories[order["customer_id"]]
            policy = self.policies[order_id]
            eligible = (
                delivery["status"] == "delivered"
                and policy["delay_refund_eligible"]
                and delivery["delay_hours"] >= policy["minimum_delay_hours"]
                and order_id not in history["refunded_order_ids"]
            )
            if not eligible:
                continue
            refund_amount_cents = min(order["order_total_cents"], policy["maximum_refund_cents"])
            candidates.append(
                {
                    "order_id": order_id,
                    "customer_id": order["customer_id"],
                    "delay_hours": delivery["delay_hours"],
                    "refund_amount_cents": refund_amount_cents,
                    "reason": f"delivery_delay_{delivery['delay_hours']}_hours",
                    "evidence_ids": sorted(
                        (
                            order["evidence_id"],
                            delivery["evidence_id"],
                            history["evidence_id"],
                            policy["evidence_id"],
                        )
                    ),
                }
            )
        candidates.sort(key=lambda row: row["order_id"])
        return {
            "candidates": candidates,
            "total_refund_amount_cents": sum(row["refund_amount_cents"] for row in candidates),
        }

    def execute(self, tool_name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        if tool_name == "list_delayed_orders":
            if arguments != {"date_start": self.date_start, "date_end": self.date_end}:
                raise ValueError("The delayed-order query must use the fixture date range")
            return {
                "date_start": self.date_start,
                "date_end": self.date_end,
                "orders": [
                    {
                        "order_id": order_id,
                        "customer_id": self.orders[order_id]["customer_id"],
                        "status": self.deliveries[order_id]["status"],
                    }
                    for order_id in self.order_ids
                ],
            }
        order_id = _required(arguments, "order_id")
        if order_id not in self.order_ids:
            raise ValueError(f"Unknown order_id: {order_id!r}")
        if tool_name == "get_order":
            return self.orders[order_id]
        if tool_name == "get_delivery_events":
            return self.deliveries[order_id]
        if tool_name == "get_refund_policy":
            return self.policies[order_id]
        if tool_name == "get_refund_history":
            customer_id = _required(arguments, "customer_id")
            expected_customer = self.orders[order_id]["customer_id"]
            if customer_id != expected_customer:
                raise ValueError(f"Customer {customer_id!r} does not own {order_id!r}")
            return self.histories[customer_id]
        raise ValueError(f"Unknown tool: {tool_name}")

    def tool_definitions(self, arm: Arm) -> list[dict[str, Any]]:
        callers = ["direct"] if arm == "direct" else ["programmatic"]
        tools = [
            _function_tool(
                "list_delayed_orders",
                "List delayed-order identifiers for the fixed date range before retrieving details.",
                _object_schema(
                    {"date_start": {"type": "string"}, "date_end": {"type": "string"}},
                    ["date_start", "date_end"],
                ),
                _delayed_orders_output_schema(),
                callers,
            ),
            _function_tool(
                "get_order",
                "Return immutable order value and customer details for one order.",
                _order_id_schema(),
                _order_output_schema(),
                callers,
            ),
            _function_tool(
                "get_delivery_events",
                "Return promised and actual delivery state, including deterministic delay_hours.",
                _order_id_schema(),
                _delivery_output_schema(),
                callers,
            ),
            _function_tool(
                "get_refund_history",
                "Return whether this exact order was already refunded for the supplied customer.",
                _object_schema(
                    {"order_id": {"type": "string"}, "customer_id": {"type": "string"}},
                    ["order_id", "customer_id"],
                ),
                _history_output_schema(),
                callers,
            ),
            _function_tool(
                "get_refund_policy",
                "Return the delay threshold, eligibility flag, and refund cap for one order.",
                _order_id_schema(),
                _policy_output_schema(),
                callers,
            ),
        ]
        if arm == "programmatic":
            tools.append({"type": "programmatic_tool_calling"})
        return tools

    def prompt(self, arm: Arm) -> tuple[str, str]:
        shared = f"""
Select refund candidates from delayed orders between {self.date_start} and {self.date_end}.

First call list_delayed_orders exactly once. For every returned order, call get_order,
get_delivery_events, get_refund_history, and get_refund_policy exactly once. The
get_refund_history call must include both order_id and its customer_id.

An order is a candidate only when it is delivered, delay_refund_eligible is true,
delay_hours is at least minimum_delay_hours, and the exact order_id is absent from
refunded_order_ids. refund_amount_cents is the smaller of order_total_cents and
maximum_refund_cents. reason must be "delivery_delay_<delay_hours>_hours".

Sort candidates by order_id. Sort each evidence_ids list. The structured result must
be exactly {{"candidates":[{{"order_id":"...","customer_id":"...","delay_hours":0,
"refund_amount_cents":0,"reason":"...","evidence_ids":["..."]}}],
"total_refund_amount_cents":0}}.

The final message must contain:
RESULT_JSON: <the exact one-line JSON object>
EXPLANATION: <each candidate's order ID, delay, amount, reason, and all evidence IDs>.
Do not request approval or issue a refund in this selection stage.
""".strip()
        if arm == "direct":
            orchestration = """
Use Direct Tool Calling. Inspect the initial order list, then issue independent detail
calls in parallel. Calculate the candidate set from returned data. Do not generate a program.
""".strip()
        else:
            orchestration = """
Use Programmatic Tool Calling for the complete read and calculation stage. Retrieve the
order list, create all independent detail-call promises, resolve them with Promise.all,
and filter, calculate, and sort inside JavaScript. Emit only the result with
text(JSON.stringify(result)). Do not call refund functions directly.
""".strip()
        return (
            f"<task_contract>\n{shared}\n</task_contract>\n\n"
            f"<tool_orchestration>\n{orchestration}\n</tool_orchestration>",
            "Find last week's policy-eligible delayed orders and prepare refund candidates.",
        )


@dataclass(frozen=True)
class RefundApprovalScenario:
    selection: RefundSelectionScenario
    candidate_plan: dict[str, Any]
    decisions: dict[str, dict[str, Any]]

    @property
    def scenario_name(self) -> str:
        return "refund_approval"

    @property
    def case_id(self) -> str:
        return self.selection.case_id

    def expected_result(self) -> dict[str, Any]:
        approvals: list[dict[str, Any]] = []
        refunds: list[dict[str, Any]] = []
        for candidate in self.candidate_plan["candidates"]:
            order_id = candidate["order_id"]
            decision = self.decisions[order_id]
            approvals.append(
                {
                    "order_id": order_id,
                    "decision": decision["decision"],
                    "approval_id": decision["approval_id"],
                    "rationale": decision["rationale"],
                }
            )
            if decision["decision"] == "approved":
                refunds.append(
                    {
                        "order_id": order_id,
                        "approval_id": decision["approval_id"],
                        "refund_amount_cents": candidate["refund_amount_cents"],
                        "refund_transaction_id": f"refund-{order_id}",
                        "status": "issued",
                    }
                )
        return {
            "approvals": approvals,
            "refunds": refunds,
            "total_issued_cents": sum(row["refund_amount_cents"] for row in refunds),
        }

    def execute(self, tool_name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        order_id = _required(arguments, "order_id")
        candidates = {row["order_id"]: row for row in self.candidate_plan["candidates"]}
        if order_id not in candidates:
            raise ValueError(f"Order {order_id!r} is not an approved selection-stage candidate")
        candidate = candidates[order_id]
        if arguments.get("amount_cents") != candidate["refund_amount_cents"]:
            raise ValueError("Refund amount does not match the selected candidate")
        if tool_name == "request_refund_approval":
            if arguments.get("reason") != candidate["reason"]:
                raise ValueError("Approval reason does not match the selected candidate")
            return {"order_id": order_id, **self.decisions[order_id]}
        if tool_name == "issue_refund":
            decision = self.decisions[order_id]
            if decision["decision"] != "approved" or arguments.get("approval_id") != decision["approval_id"]:
                raise ValueError("A valid approval_id is required before issuing a refund")
            return {
                "order_id": order_id,
                "approval_id": decision["approval_id"],
                "refund_amount_cents": candidate["refund_amount_cents"],
                "refund_transaction_id": f"refund-{order_id}",
                "status": "issued",
            }
        raise ValueError(f"Unknown tool: {tool_name}")

    def tool_definitions(self, arm: Arm) -> list[dict[str, Any]]:
        if arm != "direct":
            raise ValueError("Approval and refund tools are direct-only")
        return [
            _function_tool(
                "request_refund_approval",
                "Request a simulated human approval for one selected refund candidate.",
                _object_schema(
                    {
                        "order_id": {"type": "string"},
                        "amount_cents": {"type": "integer"},
                        "reason": {"type": "string"},
                    },
                    ["order_id", "amount_cents", "reason"],
                ),
                _approval_output_schema(),
                ["direct"],
            ),
            _function_tool(
                "issue_refund",
                "Issue a simulated refund only after an approved decision supplies approval_id.",
                _object_schema(
                    {
                        "order_id": {"type": "string"},
                        "amount_cents": {"type": "integer"},
                        "approval_id": {"type": "string"},
                    },
                    ["order_id", "amount_cents", "approval_id"],
                ),
                _issued_refund_output_schema(),
                ["direct"],
            ),
        ]

    def prompt(self, arm: Arm) -> tuple[str, str]:
        if arm != "direct":
            raise ValueError("Approval and refund tools are direct-only")
        candidates_json = compact_refund_json(self.candidate_plan)
        instructions = f"""
<task_contract>
The read-only selection stage produced this validated candidate plan:
{candidates_json}

For every candidate, call request_refund_approval exactly once with its exact amount
and reason. Inspect each decision. Call issue_refund exactly once only for approved
candidates, using the exact approval_id and amount. Never issue a rejected candidate.

Return exactly {json.dumps(self.expected_result(), separators=(',', ':'), sort_keys=True)}.
The final message must contain RESULT_JSON with that exact one-line object and an
EXPLANATION naming every approval decision and every issued refund transaction.
</task_contract>

<tool_orchestration>
Use Direct Tool Calling for all approval and refund actions. Approval and write tools
must never be invoked from generated code. Parallel approval requests are allowed;
refund calls may begin only after their corresponding approvals are observed.
</tool_orchestration>
""".strip()
        return instructions, "Request approval for the candidates and issue only approved refunds."


def build_refund_selection(scale: RefundScale = "medium") -> RefundSelectionScenario:
    if scale not in REFUND_SCALE_COUNTS:
        raise ValueError(f"Unsupported refund scale: {scale}")
    rows = _fixture_rows()[: REFUND_SCALE_COUNTS[scale]]
    orders: dict[str, dict[str, Any]] = {}
    deliveries: dict[str, dict[str, Any]] = {}
    histories: dict[str, dict[str, Any]] = {}
    policies: dict[str, dict[str, Any]] = {}
    for row in rows:
        order_id = row["order_id"]
        customer_id = row["customer_id"]
        orders[order_id] = {
            "evidence_id": f"order-{order_id}",
            "order_id": order_id,
            "customer_id": customer_id,
            "category": row["category"],
            "order_total_cents": row["order_total_cents"],
        }
        deliveries[order_id] = {
            "evidence_id": f"delivery-{order_id}",
            "order_id": order_id,
            "status": row["status"],
            "promised_at": "2026-08-01T12:00:00Z",
            "delivered_at": row["delivered_at"],
            "delay_hours": row["delay_hours"],
        }
        histories[customer_id] = {
            "evidence_id": f"history-{customer_id}",
            "customer_id": customer_id,
            "refunded_order_ids": [order_id] if row["already_refunded"] else [],
        }
        policies[order_id] = {
            "evidence_id": f"policy-{order_id}",
            "order_id": order_id,
            "delay_refund_eligible": row["policy_eligible"],
            "minimum_delay_hours": row["minimum_delay_hours"],
            "maximum_refund_cents": row["maximum_refund_cents"],
        }
    return RefundSelectionScenario(
        scale=scale,
        date_start="2026-07-27",
        date_end="2026-08-02",
        order_ids=tuple(orders),
        orders=orders,
        deliveries=deliveries,
        histories=histories,
        policies=policies,
    )


def build_refund_approval(selection: RefundSelectionScenario) -> RefundApprovalScenario:
    decisions = {
        "ord-001": {
            "decision": "approved",
            "approval_id": "approval-ord-001",
            "rationale": "Verified carrier delay qualifies for automatic approval.",
        },
        "ord-003": {
            "decision": "rejected",
            "approval_id": None,
            "rationale": "Cold-chain damage investigation is still open.",
        },
        "ord-005": {
            "decision": "approved",
            "approval_id": "approval-ord-005",
            "rationale": "Extended delay is fully documented.",
        },
        "ord-007": {
            "decision": "approved",
            "approval_id": "approval-ord-007",
            "rationale": "Delay exceeded the standard-policy threshold.",
        },
    }
    return RefundApprovalScenario(
        selection=selection,
        candidate_plan=selection.expected_selection(),
        decisions={row["order_id"]: decisions[row["order_id"]] for row in selection.expected_selection()["candidates"]},
    )


def collect_refund_evidence_ids(value: Any) -> set[str]:
    found: set[str] = set()
    if isinstance(value, dict):
        for key, child in value.items():
            if key == "evidence_id" and isinstance(child, str):
                found.add(child)
            else:
                found.update(collect_refund_evidence_ids(child))
    elif isinstance(value, list):
        for child in value:
            found.update(collect_refund_evidence_ids(child))
    return found


def compact_refund_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True)


def _fixture_rows() -> list[dict[str, Any]]:
    return [
        {"order_id": "ord-001", "customer_id": "cus-001", "category": "standard", "order_total_cents": 8500, "status": "delivered", "delivered_at": "2026-08-03T00:00:00Z", "delay_hours": 36, "already_refunded": False, "policy_eligible": True, "minimum_delay_hours": 24, "maximum_refund_cents": 3000},
        {"order_id": "ord-002", "customer_id": "cus-002", "category": "standard", "order_total_cents": 6200, "status": "delivered", "delivered_at": "2026-08-02T00:00:00Z", "delay_hours": 12, "already_refunded": False, "policy_eligible": True, "minimum_delay_hours": 24, "maximum_refund_cents": 3000},
        {"order_id": "ord-003", "customer_id": "cus-003", "category": "perishable", "order_total_cents": 4200, "status": "delivered", "delivered_at": "2026-08-01T22:00:00Z", "delay_hours": 10, "already_refunded": False, "policy_eligible": True, "minimum_delay_hours": 8, "maximum_refund_cents": 5000},
        {"order_id": "ord-004", "customer_id": "cus-004", "category": "standard", "order_total_cents": 9100, "status": "delivered", "delivered_at": "2026-08-03T12:00:00Z", "delay_hours": 48, "already_refunded": True, "policy_eligible": True, "minimum_delay_hours": 24, "maximum_refund_cents": 3000},
        {"order_id": "ord-005", "customer_id": "cus-005", "category": "standard", "order_total_cents": 1800, "status": "delivered", "delivered_at": "2026-08-04T12:00:00Z", "delay_hours": 72, "already_refunded": False, "policy_eligible": True, "minimum_delay_hours": 24, "maximum_refund_cents": 3000},
        {"order_id": "ord-006", "customer_id": "cus-006", "category": "digital", "order_total_cents": 2500, "status": "delivered", "delivered_at": "2026-08-03T12:00:00Z", "delay_hours": 48, "already_refunded": False, "policy_eligible": False, "minimum_delay_hours": 0, "maximum_refund_cents": 0},
        {"order_id": "ord-007", "customer_id": "cus-007", "category": "standard", "order_total_cents": 12000, "status": "delivered", "delivered_at": "2026-08-02T14:00:00Z", "delay_hours": 26, "already_refunded": False, "policy_eligible": True, "minimum_delay_hours": 24, "maximum_refund_cents": 3000},
        {"order_id": "ord-008", "customer_id": "cus-008", "category": "standard", "order_total_cents": 7600, "status": "in_transit", "delivered_at": None, "delay_hours": 80, "already_refunded": False, "policy_eligible": True, "minimum_delay_hours": 24, "maximum_refund_cents": 3000},
    ]


def _required(arguments: dict[str, Any], name: str) -> str:
    value = arguments.get(name)
    if not isinstance(value, str) or not value:
        raise ValueError(f"{name} must be a non-empty string")
    return value


def _function_tool(name: str, description: str, parameters: dict[str, Any], output_schema: dict[str, Any], allowed_callers: list[str]) -> dict[str, Any]:
    return {"type": "function", "name": name, "description": description, "parameters": parameters, "strict": True, "output_schema": output_schema, "allowed_callers": allowed_callers}


def _object_schema(properties: dict[str, Any], required: list[str]) -> dict[str, Any]:
    return {"type": "object", "properties": properties, "required": required, "additionalProperties": False}


def _order_id_schema() -> dict[str, Any]:
    return _object_schema({"order_id": {"type": "string"}}, ["order_id"])


def _delayed_orders_output_schema() -> dict[str, Any]:
    item = _object_schema({"order_id": {"type": "string"}, "customer_id": {"type": "string"}, "status": {"type": "string"}}, ["order_id", "customer_id", "status"])
    return _object_schema({"date_start": {"type": "string"}, "date_end": {"type": "string"}, "orders": {"type": "array", "items": item}}, ["date_start", "date_end", "orders"])


def _order_output_schema() -> dict[str, Any]:
    return _object_schema({"evidence_id": {"type": "string"}, "order_id": {"type": "string"}, "customer_id": {"type": "string"}, "category": {"type": "string"}, "order_total_cents": {"type": "integer"}}, ["evidence_id", "order_id", "customer_id", "category", "order_total_cents"])


def _delivery_output_schema() -> dict[str, Any]:
    return _object_schema({"evidence_id": {"type": "string"}, "order_id": {"type": "string"}, "status": {"type": "string"}, "promised_at": {"type": "string"}, "delivered_at": {"type": ["string", "null"]}, "delay_hours": {"type": "integer"}}, ["evidence_id", "order_id", "status", "promised_at", "delivered_at", "delay_hours"])


def _history_output_schema() -> dict[str, Any]:
    return _object_schema({"evidence_id": {"type": "string"}, "customer_id": {"type": "string"}, "refunded_order_ids": {"type": "array", "items": {"type": "string"}}}, ["evidence_id", "customer_id", "refunded_order_ids"])


def _policy_output_schema() -> dict[str, Any]:
    return _object_schema({"evidence_id": {"type": "string"}, "order_id": {"type": "string"}, "delay_refund_eligible": {"type": "boolean"}, "minimum_delay_hours": {"type": "integer"}, "maximum_refund_cents": {"type": "integer"}}, ["evidence_id", "order_id", "delay_refund_eligible", "minimum_delay_hours", "maximum_refund_cents"])


def _approval_output_schema() -> dict[str, Any]:
    return _object_schema({"order_id": {"type": "string"}, "decision": {"type": "string", "enum": ["approved", "rejected"]}, "approval_id": {"type": ["string", "null"]}, "rationale": {"type": "string"}}, ["order_id", "decision", "approval_id", "rationale"])


def _issued_refund_output_schema() -> dict[str, Any]:
    return _object_schema({"order_id": {"type": "string"}, "approval_id": {"type": "string"}, "refund_amount_cents": {"type": "integer"}, "refund_transaction_id": {"type": "string"}, "status": {"type": "string", "enum": ["issued"]}}, ["order_id", "approval_id", "refund_amount_cents", "refund_transaction_id", "status"])
