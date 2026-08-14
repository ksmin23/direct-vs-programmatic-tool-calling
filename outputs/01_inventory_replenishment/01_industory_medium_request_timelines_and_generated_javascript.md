# Inventory Medium Request Timelines and Generated JavaScript

- **Source notebook:** `notebooks/01_inventory_replenishment.ipynb`
- **Dataset name:** `inventory`
- **Dataset size:** `medium`
- **Case ID:** `inventory-medium`
- **SKU count:** 10
- **Execution date:** 2026-08-07 (Asia/Seoul)
- **Notebook cell:** 21 of 27 (code cell)
- **Section title:** `8. Inspect request timelines and generated JavaScript`

## Direct request timeline

| request | output_types | input_tokens | cached_tokens | cache_write_tokens | output_tokens | latency_seconds |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | reasoning, function_call, function_call, function_call, function_call, function_call, function_call, function_call, function_call, function_call, function_call, function_call, function_call, function_call, function_call, function_call, function_call, function_call, function_call, function_call, function_call, function_call, function_call, function_call, function_call, function_call, function_call, function_call, function_call, function_call, function_call | 527 | 0 | 0 | 577 | 7.012 |
| 2 | reasoning, message | 4050 | 0 | 4047 | 486 | 6.636 |

**Quality passed:** `True`  

**Estimated cost:** `$0.059834`  

**End-to-end latency:** `13.651s`

## Programmatic request timeline

| request | output_types | input_tokens | cached_tokens | cache_write_tokens | output_tokens | latency_seconds |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | reasoning, program, function_call, function_call, function_call, function_call, function_call, function_call, function_call, function_call, function_call, function_call, function_call, function_call, function_call, function_call, function_call, function_call, function_call, function_call, function_call, function_call, function_call, function_call, function_call, function_call, function_call, function_call, function_call, function_call, function_call, function_call | 1188 | 0 | 1054 | 556 | 11.129 |
| 2 | program_output, reasoning, message | 1879 | 1185 | 691 | 252 | 4.179 |

**Quality passed:** `True`  

**Estimated cost:** `$0.036424`  

**End-to-end latency:** `15.309s`

## Generated JavaScript

```javascript
const skus = Array.from({length: 10}, (_, i) => `sku-${String(i + 1).padStart(3, "0")}`);

const inventoryPromises = skus.map(sku => tools.get_inventory({sku}));
const demandPromises = skus.map(sku => tools.get_weekly_demand({sku}));
const inboundPromises = skus.map(sku => tools.get_inbound_shipments({sku}));
const allPromises = [...inventoryPromises, ...demandPromises, ...inboundPromises];

const allResults = await Promise.all(allPromises);
const inventories = allResults.slice(0, 10);
const demands = allResults.slice(10, 20);
const inbounds = allResults.slice(20, 30);

const recommendations = skus.map((sku, i) => {
  const available_units = inventories[i].warehouses.reduce(
    (sum, row) => sum + row.on_hand_units - row.reserved_units, 0
  );
  const forecast_units = demands[i].daily_forecast.reduce(
    (sum, row) => sum + row.units, 0
  );
  const inbound_units = inbounds[i].shipments
    .filter(row => row.status === "scheduled" && row.eta_date <= "2026-08-17")
    .reduce((sum, row) => sum + row.units, 0);
  const reorder_units = Math.max(
    forecast_units + 5 - available_units - inbound_units, 0
  );
  return {sku, available_units, forecast_units, inbound_units, reorder_units};
}).filter(row => row.reorder_units > 0)
  .sort((a, b) => b.reorder_units - a.reorder_units || a.sku.localeCompare(b.sku));

const result = {
  recommendations,
  total_reorder_units: recommendations.reduce((sum, row) => sum + row.reorder_units, 0)
};

text(JSON.stringify(result));
```

## Program output

```json
{
  "recommendations": [
    {
      "sku": "sku-010",
      "available_units": 15,
      "forecast_units": 24,
      "inbound_units": 0,
      "reorder_units": 14
    },
    {
      "sku": "sku-007",
      "available_units": 15,
      "forecast_units": 22,
      "inbound_units": 0,
      "reorder_units": 12
    },
    {
      "sku": "sku-004",
      "available_units": 15,
      "forecast_units": 20,
      "inbound_units": 0,
      "reorder_units": 10
    },
    {
      "sku": "sku-001",
      "available_units": 15,
      "forecast_units": 18,
      "inbound_units": 0,
      "reorder_units": 8
    }
  ],
  "total_reorder_units": 44
}
```
