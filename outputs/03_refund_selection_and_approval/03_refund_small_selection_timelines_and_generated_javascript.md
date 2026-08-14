# Refund Small Selection Timelines and Generated JavaScript

- **Source notebook:** `notebooks/03_refund_selection_and_approval.ipynb`
- **Dataset name:** `refund_selection`
- **Dataset size:** `small (4 delayed orders)`
- **Case ID:** `refund-small`
- **Execution date:** 2026-08-07 (Asia/Seoul)
- **Notebook cell:** 23 of 33 (code cell)
- **Section title:** `8. Inspect selection traces`

## Direct timeline

| request | output_types | input_tokens | cached_tokens | cache_write_tokens | output_tokens | latency_seconds |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | reasoning, function_call | 520 | 0 | 0 | 51 | 3.922 |
| 2 | reasoning, function_call, function_call, function_call, function_call, function_call, function_call, function_call, function_call, function_call, function_call, function_call, function_call, function_call, function_call, function_call, function_call | 685 | 0 | 0 | 358 | 4.509 |
| 3 | reasoning, message | 1878 | 0 | 1875 | 324 | 5.407 |

**Quality:** `True`  

**Estimated cost:** `$0.039749`  

**Latency:** `13.842s`

## Programmatic timeline

| request | output_types | input_tokens | cached_tokens | cache_write_tokens | output_tokens | latency_seconds |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | reasoning, program, function_call | 1269 | 0 | 1135 | 718 | 12.785 |
| 2 | function_call, function_call, function_call, function_call | 0 | 0 | 0 | 0 | 1.207 |
| 3 | function_call, function_call, function_call, function_call, function_call, function_call, function_call, function_call | 0 | 0 | 0 | 0 | 1.313 |
| 4 | function_call | 0 | 0 | 0 | 0 | 0.765 |
| 5 | function_call | 0 | 0 | 0 | 0 | 0.985 |
| 6 | function_call | 0 | 0 | 0 | 0 | 1.474 |
| 7 | function_call | 0 | 0 | 0 | 0 | 0.837 |
| 8 | program_output, reasoning, message | 2141 | 1266 | 872 | 279 | 4.965 |

**Quality:** `True`  

**Estimated cost:** `$0.043772`  

**Latency:** `24.332s`

## Generated selection JavaScript

```javascript
const listed = await tools.list_delayed_orders({
  date_start: "2026-07-27",
  date_end: "2026-08-02"
});

const orderDetails = await Promise.all(
  listed.orders.map(({ order_id }) => tools.get_order({ order_id }))
);

const customerByOrder = new Map(
  orderDetails.map(o => [o.order_id, o.customer_id])
);

const nonPolicyPromises = listed.orders.flatMap(({ order_id }) => [
  tools.get_delivery_events({ order_id }),
  tools.get_refund_history({
    order_id,
    customer_id: customerByOrder.get(order_id)
  })
]);
const nonPolicyResults = await Promise.all(nonPolicyPromises);

const eventsByOrder = new Map();
const historyByOrder = new Map();
for (const item of nonPolicyResults) {
  if (Object.prototype.hasOwnProperty.call(item, "delay_hours")) {
    eventsByOrder.set(item.order_id, item);
  } else {
    const matchedOrderId = listed.orders.find(
      o => o.customer_id === item.customer_id &&
           customerByOrder.get(o.order_id) === item.customer_id &&
           !historyByOrder.has(o.order_id)
    )?.order_id;
    if (matchedOrderId) historyByOrder.set(matchedOrderId, item);
  }
}

const policiesByOrder = new Map();
for (const { order_id } of listed.orders) {
  const policy = await tools.get_refund_policy({ order_id });
  policiesByOrder.set(order_id, policy);
}

const detailsByOrder = new Map(orderDetails.map(o => [o.order_id, o]));
const candidates = listed.orders
  .map(({ order_id }) => {
    const order = detailsByOrder.get(order_id);
    const delivery = eventsByOrder.get(order_id);
    const history = historyByOrder.get(order_id);
    const policy = policiesByOrder.get(order_id);
    if (
      delivery.status !== "delivered" ||
      !policy.delay_refund_eligible ||
      delivery.delay_hours < policy.minimum_delay_hours ||
      history.refunded_order_ids.includes(order_id)
    ) return null;
    return {
      order_id,
      customer_id: order.customer_id,
      delay_hours: delivery.delay_hours,
      refund_amount_cents: Math.min(
        order.order_total_cents,
        policy.maximum_refund_cents
      ),
      reason: `delivery_delay_${delivery.delay_hours}_hours`,
      evidence_ids: [
        order.evidence_id,
        delivery.evidence_id,
        history.evidence_id,
        policy.evidence_id
      ].sort()
    };
  })
  .filter(Boolean)
  .sort((a, b) => a.order_id.localeCompare(b.order_id));

const result = {
  candidates,
  total_refund_amount_cents: candidates.reduce(
    (sum, c) => sum + c.refund_amount_cents,
    0
  )
};
text(JSON.stringify(result));
```

## Reduced program output

```json
{
  "candidates": [
    {
      "order_id": "ord-001",
      "customer_id": "cus-001",
      "delay_hours": 36,
      "refund_amount_cents": 3000,
      "reason": "delivery_delay_36_hours",
      "evidence_ids": [
        "delivery-ord-001",
        "history-cus-001",
        "order-ord-001",
        "policy-ord-001"
      ]
    },
    {
      "order_id": "ord-003",
      "customer_id": "cus-003",
      "delay_hours": 10,
      "refund_amount_cents": 4200,
      "reason": "delivery_delay_10_hours",
      "evidence_ids": [
        "delivery-ord-003",
        "history-cus-003",
        "order-ord-003",
        "policy-ord-003"
      ]
    }
  ],
  "total_refund_amount_cents": 7200
}
```
