# Refund Small Approval Workflow Comparison

- **Source notebook:** `notebooks/03_refund_selection_and_approval.ipynb`
- **Dataset name:** `refund_workflow`
- **Dataset size:** `small (4 delayed orders)`
- **Case ID:** `refund-small`
- **Execution date:** 2026-08-07 (Asia/Seoul)
- **Notebook cell:** 25 of 33 (code cell)
- **Section title:** `9. Optional All-Direct vs Hybrid workflow`

## Comparison results

| arm | passed | requests | tool_calls | input_tokens | cached_tokens | cache_write_tokens | output_tokens | reasoning_tokens | estimated_cost_usd | end_to_end_seconds |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| all_direct | False | 6 | 20 | 5132 | 0 | 1874 | 1016 | 67 | 0.058482 | 25.274 |
| hybrid | False | 11 | 20 | 5299 | 1266 | 1847 | 1171 | 178 | 0.058237 | 30.841 |
