# Inventory Medium Three-Run Comparison

- **Source notebook:** `notebooks/01_inventory_replenishment.ipynb`
- **Dataset name:** `inventory`
- **Dataset size:** `medium`
- **Case ID:** `inventory-medium`
- **SKU count:** 10
- **Execution date:** 2026-08-07 (Asia/Seoul)
- **Notebook cell:** 23 of 27 (code cell)
- **Section title:** `9. Optional three-run comparison`
- **Repetitions:** 3

## Comparison results

| arm | passed | requests | tool_calls | input_tokens | cached_tokens | cache_write_tokens | output_tokens | reasoning_tokens | estimated_cost_usd | end_to_end_seconds |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| direct | True | 2 | 30 | 4605 | 0 | 4075 | 1059 | 269 | 0.059889 | 12.838 |
| programmatic | True | 2 | 30 | 2998 | 1185 | 1676 | 733 | 111 | 0.033742 | 14.465 |
| direct | True | 2 | 30 | 4577 | 0 | 4047 | 1094 | 304 | 0.060764 | 14.658 |
| programmatic | True | 2 | 30 | 3148 | 1185 | 1826 | 888 | 209 | 0.03933 | 18.644 |
| direct | True | 2 | 30 | 4582 | 0 | 4052 | 1037 | 246 | 0.059085 | 12.241 |
| programmatic | True | 12 | 30 | 3412 | 1185 | 2090 | 1154 | 470 | 0.04896 | 30.991 |
