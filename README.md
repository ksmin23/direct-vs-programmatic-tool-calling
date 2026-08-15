# Direct vs Programmatic Tool Calling

This project is an English, notebook-first benchmark that compares
[Direct Tool Calling](https://developers.openai.com/api/docs/guides/function-calling)
with [Programmatic Tool Calling](https://developers.openai.com/api/docs/guides/tools-programmatic-tool-calling)
on deterministic workflows. It includes
fixed-fan-out inventory replenishment, adaptive incident investigation, and a
refund workflow with an explicit approval boundary.

## Implemented scenarios

### 1. Inventory replenishment

#### What the inventory notebook measures

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

Saved results:

- [Small live comparison](outputs/00_inventory_tool_call_trace/inventory_small_live_comparison_trace_export.md)
- [Small normalized timeline](outputs/00_inventory_tool_call_trace/inventory_small_normalized_semantic_timeline.md)
- [Medium live comparison](outputs/00_inventory_tool_call_trace/inventory_medium_live_comparison_trace_export.md)
- [Medium normalized timeline](outputs/00_inventory_tool_call_trace/inventory_medium_normalized_semantic_timeline.md)
- [Inventory replenishment outputs](outputs/01_inventory_replenishment/)

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

Saved results: [Incident investigation outputs](outputs/02_incident_investigation/)

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

Saved results: [Refund selection and approval outputs](outputs/03_refund_selection_and_approval/)

## Project layout

```text
notebooks/00_inventory_tool_call_trace.ipynb # OpenAI Trace lifecycle comparison
notebooks/01_inventory_replenishment.ipynb  # fixed fan-out tutorial
notebooks/02_incident_investigation.ipynb   # adaptive investigation tutorial
notebooks/03_refund_selection_and_approval.ipynb # read/action boundary tutorial
src/ptc_benchmark/                          # shared API loop, fixtures, evaluation
src/ptc_trace_demo/                         # bounded OpenAI Trace integration
pricing/                                    # dated, replaceable pricing snapshot
outputs/                                    # checked-in Markdown experiment reports
tests/                                      # offline fixture, pricing, and mocked runner tests
results/                                    # generated JSONL, excluded from Git
pyproject.toml                              # package and uv dependency configuration
requirements.txt                           # pip-compatible minimum dependencies
```

## Setup

Python 3.11 or newer is required. Choose either `uv` or a standard virtual
environment with `pip`.

### Using `uv`

```bash
cd direct-vs-programmatic-tool-calling
uv sync --group dev
cp .env.local.example .env.local
```

### Using `pip`

`requirements.txt` lists the minimum dependency versions for the notebooks,
tests, and Trace export.

```bash
cd direct-vs-programmatic-tool-calling
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

The Trace integration uses `openai-agents`, which is included by both
`uv sync --group dev` and `requirements.txt`; no separate Trace extra is needed.

## Verify without API cost

```bash
uv run pytest
```

With the `pip` setup, use:

```bash
PYTHONPATH=src python -m pytest
```

This validates all fixture families, pricing and result parsing, plus the mocked
Responses runner's function-call continuation path. The test suite does not make
API calls or execute the notebooks top to bottom.

## Opt-in live runs

There is no automated live smoke-test target. To run a live comparison, open the
relevant notebook, review its scale and reasoning settings, then explicitly set
only the required `RUN_*` controls to `True`. Live runs require `OPENAI_API_KEY`
and may incur API charges.

`OPENAI_MODEL` defaults to `gpt-5.6`. Both arms use the same model and reasoning
effort within one comparison. `OPENAI_PRICING_PATH` can override the checked-in
pricing snapshot used for estimates.

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
