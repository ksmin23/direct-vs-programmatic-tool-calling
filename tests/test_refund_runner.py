from __future__ import annotations

from types import SimpleNamespace

import pytest

from ptc_benchmark.refund import build_refund_selection
from ptc_benchmark.refund_workflow import RefundWorkflowRunner
from ptc_benchmark.runner import RunConfig


class _UnsafeSelectionResponses:
    def __init__(self) -> None:
        self.calls: list[dict[str, object]] = []

    def create(self, **request: object) -> SimpleNamespace:
        self.calls.append(request)
        return SimpleNamespace(
            id="response-1",
            status="completed",
            output=[{"type": "message"}],
            usage=None,
            output_text='RESULT_JSON: {"candidates":[]}',
        )


def test_refund_workflow_stops_before_actions_when_selection_fails() -> None:
    responses = _UnsafeSelectionResponses()
    runner = RefundWorkflowRunner(SimpleNamespace(responses=responses))

    with pytest.raises(RuntimeError, match="approval stage was not started"):
        runner.run(
            arm="hybrid",
            selection=build_refund_selection("small"),
            config=RunConfig(model="test", max_requests=1),
            run_id="unsafe-test",
        )

    assert len(responses.calls) == 1
