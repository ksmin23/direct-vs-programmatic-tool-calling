# Direct vs Programmatic Tool Calling

This project is an English, notebook-first benchmark that compares Direct Tool
Calling with Programmatic Tool Calling on deterministic workflows. It includes
fixed-fan-out inventory replenishment, adaptive incident investigation, and a
refund workflow with an explicit approval boundary.

## Implemented scenarios

### 1. Inventory replenishment

## What the inventory notebook measures

Both arms use the same model, reasoning effort, task contract, SKU fixtures, and
three function tools. Direct Tool Calling may issue parallel function calls. The
Programmatic arm must coordinate the calls from generated JavaScript and reduce
the detailed intermediate data before returning a result.

Quality is a hard gate. A run must satisfy all of the following before its cost
is compared:

- Call all three tools exactly once for every SKU.
- Produce the exact structured replenishment plan.
- Preserve program caller linkage in the Programmatic arm.
- Return a matching `RESULT_JSON` final result.
- Explain every recommendation using its source and calculated unit values.

The benchmark records request-level input, cached-input, cache-write, output, and
reasoning tokens; estimated model cost; tool calls; output item types; request
latency; and task end-to-end latency. The pricing snapshot is versioned and every
dollar value is labeled as an estimate.

### 2. Incident investigation

Both arms start with the same checkout log search and error-rate metric, then use
the evidence semantics to choose a trace, dependent-service metric, or recent
deployment lookup. The deterministic suite includes database pool exhaustion, an
expired TLS certificate, and a pricing schema mismatch.

The quality gate requires the exact root cause and remediation, a grounded
evidence-complete explanation, exactly the required two-call start, no duplicate
calls, and correct Direct or Programmatic caller linkage. This scenario highlights
the tradeoff between keeping intermediate evidence inside generated JavaScript and
letting the model perform semantic judgment between Direct calls.

### 3. Refund selection and approval

This scenario separates bulk read processing from sensitive actions. Candidate
selection compares Direct with Programmatic across delayed-order, delivery,
refund-history, and policy records. The end-to-end comparison is All-Direct versus
Hybrid: Hybrid uses Programmatic for selection and a separate Direct stage for
approval requests and simulated refund issuance.

Approval and refund tools declare `allowed_callers=["direct"]` and are never exposed
to generated programs. An invalid or ungrounded selection stops the workflow before
the action stage. All actions are deterministic local simulations; no real refund
system is connected.

## Project layout

```text
notebooks/00_inventory_tool_call_trace.ipynb # OpenAI Trace lifecycle comparison
notebooks/01_inventory_replenishment.ipynb  # fixed fan-out tutorial
notebooks/02_incident_investigation.ipynb   # adaptive investigation tutorial
notebooks/03_refund_selection_and_approval.ipynb # read/action boundary tutorial
src/ptc_benchmark/                          # shared API loop, fixtures, evaluation
pricing/                                    # dated, replaceable pricing snapshot
tests/                                      # offline, notebook, mocked, and live smoke tests
results/                                    # generated JSONL, excluded from Git
```

## Setup

Python 3.11 or newer is required. Choose either `uv` or a standard virtual
environment with `pip`.

### Using `uv`

```bash
cd programmatic_tool_calling_demo
uv sync --extra dev
cp .env.local.example .env.local
```

### Using `pip`

`requirements.txt` pins the dependencies for the notebooks, tests, and optional
Trace export.

```bash
cd programmatic_tool_calling_demo
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
cp .env.local.example .env.local
```

Add an API key to `.env.local` only when you want to opt into a live run. Never
commit that file.

## Run the notebook

```bash
uv run jupyter lab notebooks/00_inventory_tool_call_trace.ipynb
uv run jupyter lab notebooks/01_inventory_replenishment.ipynb
uv run jupyter lab notebooks/02_incident_investigation.ipynb
uv run jupyter lab notebooks/03_refund_selection_and_approval.ipynb
```

All notebooks default to `RUN_LIVE = False`. The inventory notebook separately
gates three repetitions with `RUN_REPEATED_COMPARISON`. The incident notebook
separately gates its six-run, three-case suite with `RUN_ALL_CASES`. Set only
`RUN_LIVE = True` to run one detailed Direct and Programmatic comparison.
The refund notebook additionally requires `RUN_APPROVAL_WORKFLOW = True` before it
runs its simulated action stage, and `RUN_ALL_SCALES = True` before a scale sweep.

The `00_` Trace tutorial has three independent controls: `RUN_LIVE = False`
controls API usage, `EXPORT_OPENAI_TRACE = False` controls export of bounded
event summaries, and `SHOW_TRACE_ERROR_DETAILS = False` keeps trace-error
response bodies redacted. Full synthetic payloads remain local when
`INCLUDE_LOCAL_PAYLOADS = True`.

Set `SHOW_TRACE_ERROR_DETAILS = True` temporarily to include the Trace ingest
response body in SDK error logs. Keep it `False` during normal use because detailed
logs may include sensitive model or tool data.

Install the optional exporter before enabling Trace export:

```bash
uv sync --extra dev --extra trace
```

The exporter is already included when installing from `requirements.txt`.

## Verify without API cost

```bash
uv run pytest -m "not live"
```

With the `pip` setup, use:

```bash
PYTHONPATH=src python -m pytest -m "not live"
```

This validates all fixture families, pricing, Direct and multi-pause Programmatic
continuation loops with mocked Responses objects, and top-to-bottom execution of
all notebooks with live calls disabled.

## Opt-in live smoke test

The following command sends one small inventory flow, one database-pool incident
flow, and one simulated refund workflow per arm and may incur API charges:

```bash
RUN_LIVE_SMOKE=1 uv run pytest -m live -s
```

`OPENAI_MODEL` defaults to `gpt-5.6`. Both arms always use the same model and
reasoning effort in one comparison.

## Interpretation limits

- Programmatic Tool Calling is not expected to win every task or every scale.
- A lower token count is not a win when a quality gate fails.
- Bulk read efficiency does not justify exposing approval or write tools to generated code.
- Local tools are deterministic and have no network latency, so end-to-end
  latency primarily reflects the OpenAI requests and model behavior.
- Pricing changes over time. Update or override the dated pricing snapshot.
- The snapshot calculator intentionally excludes the GPT-5.6 long-context
  surcharge because this tutorial stays far below 272K input tokens.

## Future work

- Compare Direct and Programmatic Tool Calling performance when function tools are
  deferred with `defer_loading: true`, including tool-loading requests, token usage,
  estimated cost, quality pass rate, and end-to-end latency.
- Determine where Prompt Caching breakpoints should be placed for each workflow.
  Compare stable task instructions, tool definitions, fixture-independent prefixes,
  and stage boundaries while keeping cache state isolated across arms and runs.

Official references:

- [Programmatic Tool Calling](https://developers.openai.com/api/docs/guides/tools-programmatic-tool-calling)
- [GPT-5.6 model comparison and pricing](https://developers.openai.com/api/docs/models/compare)
