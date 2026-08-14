# Inventory small — Live comparison and OpenAI Trace export

- Source notebook: `notebooks/00_inventory_tool_call_trace.ipynb`
- Execution cell: 5 (`live-comparison`)
- Dataset name: `inventory`
- Dataset size: `small`
- Case ID: `inventory-small`
- SKU count: 3
- Execution date: `2026-08-07` (`Asia/Seoul`)

## Comparison metrics

| arm | quality_passed | model_requests | host_round_trips | tool_calls | intermediate_payload_bytes | input_tokens | output_tokens | reasoning_tokens | latency_seconds | estimated_cost_usd |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| direct | True | 2 | 2 | 9 | 5042 | 2080 | 385 | 119 | 10.715 | 0.023922 |
| programmatic | True | 5 | 5 | 9 | 11304 | 3108 | 850 | 265 | 14.524 | 0.038101 |
