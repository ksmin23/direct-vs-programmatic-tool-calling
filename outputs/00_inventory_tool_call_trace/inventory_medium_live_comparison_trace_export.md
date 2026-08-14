# Inventory medium — Live comparison and OpenAI Trace export

- Source notebook: `notebooks/00_inventory_tool_call_trace.ipynb`
- Execution cell: 15 (`live-comparison`)
- Dataset name: `inventory`
- Dataset size: `medium`
- Case ID: `inventory-medium`
- SKU count: 10
- Execution date: `2026-08-07` (`Asia/Seoul`)

## Comparison metrics

| arm | quality_passed | model_requests | host_round_trips | tool_calls | intermediate_payload_bytes | input_tokens | output_tokens | reasoning_tokens | latency_seconds | estimated_cost_usd |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| direct | True | 2 | 2 | 30 | 16805 | 4578 | 1061 | 267 | 15.873 | 0.05978 |
| programmatic | True | 3 | 3 | 30 | 25301 | 3158 | 920 | 267 | 23.616 | 0.040352 |
