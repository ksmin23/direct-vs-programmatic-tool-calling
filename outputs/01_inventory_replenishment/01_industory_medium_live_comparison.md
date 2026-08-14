# Inventory Medium Live Direct vs Programmatic Comparison

- **Source notebook:** `notebooks/01_inventory_replenishment.ipynb`
- **Dataset name:** `inventory`
- **Dataset size:** `medium`
- **Case ID:** `inventory-medium`
- **SKU count:** 10
- **Execution date:** 2026-08-07 (Asia/Seoul)
- **Notebook cell:** 19 of 27 (code cell)
- **Section title:** `7. Optional live Direct vs Programmatic comparison`

## Comparison results

| arm | passed | requests | tool_calls | input_tokens | cached_tokens | cache_write_tokens | output_tokens | reasoning_tokens | estimated_cost_usd | end_to_end_seconds |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| direct | True | 2 | 30 | 4577 | 0 | 4047 | 1063 | 260 | 0.059834 | 13.651 |
| programmatic | True | 2 | 30 | 3067 | 1185 | 1745 | 808 | 154 | 0.036424 | 15.309 |
