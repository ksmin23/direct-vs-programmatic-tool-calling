from __future__ import annotations

import pytest

from ptc_benchmark.refund import build_refund_approval, build_refund_selection


@pytest.mark.parametrize(
    ("scale", "candidate_ids"),
    [
        ("small", ["ord-001", "ord-003"]),
        ("medium", ["ord-001", "ord-003", "ord-005"]),
        ("large", ["ord-001", "ord-003", "ord-005", "ord-007"]),
    ],
)
def test_refund_scenarios_preserve_selection_and_write_boundary(
    scale: str,
    candidate_ids: list[str],
) -> None:
    selection = build_refund_selection(scale)
    plan = selection.expected_selection()
    approval = build_refund_approval(selection)

    assert [row["order_id"] for row in plan["candidates"]] == candidate_ids
    assert all(
        tool["allowed_callers"] == ["direct"]
        for tool in approval.tool_definitions("direct")
    )
    assert approval.expected_result()["total_issued_cents"] > 0
