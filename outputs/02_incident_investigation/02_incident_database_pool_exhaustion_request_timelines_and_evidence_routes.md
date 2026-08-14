# Incident Database Pool Exhaustion Request Timelines and Evidence Routes

- **Source notebook:** `notebooks/02_incident_investigation.ipynb`
- **Dataset name:** `incident`
- **Dataset size:** `single case`
- **Case ID:** `database-pool-exhaustion`
- **Execution date:** 2026-08-07 (Asia/Seoul)
- **Notebook cell:** 21 of 28 (code cell)
- **Section title:** `8. Inspect the adaptive route`

## Direct request timeline

| request | output_types | input_tokens | cached_tokens | cache_write_tokens | output_tokens | latency_seconds |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | reasoning, function_call, function_call | 715 | 0 | 0 | 151 | 7.07 |
| 2 | reasoning, function_call | 1227 | 0 | 1224 | 33 | 2.111 |
| 3 | reasoning, function_call, function_call | 1381 | 1224 | 154 | 226 | 6.056 |
| 4 | reasoning, message | 1826 | 1378 | 445 | 408 | 8.19 |

## Direct evidence route

| request | tool | arguments | evidence_ids | caller |
| --- | --- | --- | --- | --- |
| 1 | search_logs | {"query": "errors timeouts failures", "service": "checkout-api", "window_end": "2026-08-06T10:20:00Z", "window_start": "2026-08-06T10:00:00Z"} | log-checkout-cache-noise, log-checkout-client-noise, log-checkout-payment-timeout | direct |
| 1 | get_service_metrics | {"metric": "error_rate", "service": "checkout-api", "window_end": "2026-08-06T10:20:00Z", "window_start": "2026-08-06T10:00:00Z"} | metric-checkout-error-spike | direct |
| 2 | get_trace | {"trace_id": "trace-payment-001"} | span-checkout-payment, span-payment-db-pool | direct |
| 3 | get_service_metrics | {"metric": "db_pool_wait_ms", "service": "payment-api", "window_end": "2026-08-06T10:20:00Z", "window_start": "2026-08-06T10:00:00Z"} | metric-payment-db-pool-wait | direct |
| 3 | list_recent_deployments | {"service": "payment-api", "window_end": "2026-08-06T10:20:00Z", "window_start": "2026-08-06T10:00:00Z"} | deploy-payment-pool-capacity | direct |

**Quality:** `False`  
**Estimated cost:** `$0.040855`  
**End-to-end latency:** `23.429s`

## Programmatic request timeline

| request | output_types | input_tokens | cached_tokens | cache_write_tokens | output_tokens | latency_seconds |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | reasoning, program, function_call, function_call | 1478 | 0 | 1344 | 1922 | 29.998 |
| 2 | function_call | 0 | 0 | 0 | 0 | 0.82 |
| 3 | function_call | 0 | 0 | 0 | 0 | 1.083 |
| 4 | function_call | 0 | 0 | 0 | 0 | 1.24 |
| 5 | function_call | 0 | 0 | 0 | 0 | 0.984 |
| 6 | program_output, reasoning, message | 3490 | 1475 | 2012 | 194 | 3.759 |

## Programmatic evidence route

| request | tool | arguments | evidence_ids | caller |
| --- | --- | --- | --- | --- |
| 1 | search_logs | {"query": "errors timeouts failures", "service": "checkout-api", "window_end": "2026-08-06T10:20:00Z", "window_start": "2026-08-06T10:00:00Z"} | log-checkout-cache-noise, log-checkout-client-noise, log-checkout-payment-timeout | program |
| 1 | get_service_metrics | {"metric": "error_rate", "service": "checkout-api", "window_end": "2026-08-06T10:20:00Z", "window_start": "2026-08-06T10:00:00Z"} | metric-checkout-error-spike | program |
| 2 | get_trace | {"trace_id": "trace-payment-001"} | span-checkout-payment, span-payment-db-pool | program |
| 3 | search_logs | {"query": "connection pool exhausted timeout database", "service": "payment-api", "window_end": "2026-08-06T10:20:00Z", "window_start": "2026-08-06T10:00:00Z"} | log-payment-pool-wait | program |
| 4 | get_service_metrics | {"metric": "db_pool_wait_ms", "service": "payment-api", "window_end": "2026-08-06T10:20:00Z", "window_start": "2026-08-06T10:00:00Z"} | metric-payment-db-pool-wait | program |
| 5 | list_recent_deployments | {"service": "payment-api", "window_end": "2026-08-06T10:20:00Z", "window_start": "2026-08-06T10:00:00Z"} | deploy-payment-pool-capacity | program |

**Quality:** `False`  
**Estimated cost:** `$0.085877`  
**End-to-end latency:** `37.886s`
