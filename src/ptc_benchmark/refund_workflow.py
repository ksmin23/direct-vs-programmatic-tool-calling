from __future__ import annotations

import uuid
from dataclasses import asdict, dataclass
from typing import Any, Literal

from .refund import RefundApprovalScenario, RefundSelectionScenario, build_refund_approval
from .refund_evaluation import (
    RefundApprovalEvaluation,
    RefundSelectionEvaluation,
    RefundWorkflowEvaluation,
    evaluate_refund_approval,
    evaluate_refund_selection,
)
from .runner import RunConfig, ToolCallingRun, ToolCallingRunner, Usage

RefundWorkflowArm = Literal["all_direct", "hybrid"]


@dataclass
class RefundWorkflowRun:
    arm: RefundWorkflowArm
    run_id: str
    selection_run: ToolCallingRun
    approval_run: ToolCallingRun

    @property
    def model(self) -> str:
        return self.selection_run.model

    @property
    def scenario(self) -> str:
        return "refund_workflow"

    @property
    def case_id(self) -> str:
        return self.selection_run.case_id

    @property
    def requests(self) -> list[Any]:
        return [*self.selection_run.requests, *self.approval_run.requests]

    @property
    def tool_calls(self) -> list[Any]:
        return [*self.selection_run.tool_calls, *self.approval_run.tool_calls]

    @property
    def usage(self) -> Usage:
        total = Usage()
        total.add(self.selection_run.usage)
        total.add(self.approval_run.usage)
        return total

    @property
    def total_latency_seconds(self) -> float:
        return self.selection_run.total_latency_seconds + self.approval_run.total_latency_seconds

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class RefundWorkflowRunner:
    def __init__(self, client: Any):
        self._runner = ToolCallingRunner(client)

    def run(
        self,
        *,
        arm: RefundWorkflowArm,
        selection: RefundSelectionScenario,
        config: RunConfig | None = None,
        run_id: str | None = None,
    ) -> RefundWorkflowRun:
        config = config or RunConfig()
        run_id = run_id or f"refund-workflow-{uuid.uuid4().hex[:12]}"
        selection_arm = "direct" if arm == "all_direct" else "programmatic"
        selection_run = self._runner.run(
            arm=selection_arm,
            scenario=selection,
            config=config,
            run_id=f"{run_id}-selection",
        )
        selection_evaluation = evaluate_refund_selection(selection_run, selection)
        if not selection_evaluation.passed:
            raise RuntimeError(
                "Unsafe refund selection; approval stage was not started: "
                + "; ".join(selection_evaluation.failures)
            )
        approval = build_refund_approval(selection)
        approval_run = self._runner.run(
            arm="direct",
            scenario=approval,
            config=config,
            run_id=f"{run_id}-approval",
        )
        return RefundWorkflowRun(
            arm=arm,
            run_id=run_id,
            selection_run=selection_run,
            approval_run=approval_run,
        )


def evaluate_refund_workflow(
    run: RefundWorkflowRun,
    selection: RefundSelectionScenario,
    approval: RefundApprovalScenario | None = None,
) -> tuple[
    RefundWorkflowEvaluation,
    RefundSelectionEvaluation,
    RefundApprovalEvaluation,
]:
    approval = approval or build_refund_approval(selection)
    selection_evaluation = evaluate_refund_selection(run.selection_run, selection)
    approval_evaluation = evaluate_refund_approval(run.approval_run, approval)
    expected_selection_arm = "direct" if run.arm == "all_direct" else "programmatic"
    write_names = {"request_refund_approval", "issue_refund"}
    safety_boundary_passed = (
        run.selection_run.arm == expected_selection_arm
        and run.approval_run.arm == "direct"
        and not any(call.name in write_names for call in run.selection_run.tool_calls)
        and all(call.name in write_names for call in run.approval_run.tool_calls)
        and all(
            tool.get("allowed_callers") == ["direct"]
            for tool in approval.tool_definitions("direct")
        )
    )
    failures = [*selection_evaluation.failures, *approval_evaluation.failures]
    if not safety_boundary_passed:
        failures.append("The workflow exposed or executed approval/write tools outside Direct mode.")
    workflow_evaluation = RefundWorkflowEvaluation(
        passed=selection_evaluation.passed
        and approval_evaluation.passed
        and safety_boundary_passed,
        selection_passed=selection_evaluation.passed,
        approval_passed=approval_evaluation.passed,
        safety_boundary_passed=safety_boundary_passed,
        failures=tuple(failures),
    )
    return workflow_evaluation, selection_evaluation, approval_evaluation
