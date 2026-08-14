# Incident Database Pool Exhaustion Generated JavaScript and Program Output

- **Source notebook:** `notebooks/02_incident_investigation.ipynb`
- **Dataset name:** `incident`
- **Dataset size:** `single case`
- **Case ID:** `database-pool-exhaustion`
- **Execution date:** 2026-08-07 (Asia/Seoul)
- **Notebook cell:** 22 of 28 (code cell)
- **Section title:** `8. Inspect the adaptive route`

## Generated JavaScript

```javascript
const window_start = "2026-08-06T10:00:00Z";
const window_end = "2026-08-06T10:20:00Z";

const [checkoutLogs, checkoutErrorRate] = await Promise.all([
  tools.search_logs({
    service: "checkout-api",
    window_start,
    window_end,
    query: "errors timeouts failures"
  }),
  tools.get_service_metrics({
    service: "checkout-api",
    window_start,
    window_end,
    metric: "error_rate"
  })
]);

const events = checkoutLogs.events || [];
const poolPattern = /pool|connection|database|db|checkout|timeout/i;
const tlsPattern = /tls|certificate|handshake|x509|expired/i;
const schemaPattern = /schema|parse|deserialize|response version|unknown field/i;

let signal = "pool";
const combinedInitial = [
  ...events.map(e => `${e.error_code} ${e.message} ${e.dependency || ""}`),
  checkoutErrorRate.summary || ""
].join(" ");
if (tlsPattern.test(combinedInitial) && !poolPattern.test(combinedInitial)) signal = "tls";
if (schemaPattern.test(combinedInitial) && !poolPattern.test(combinedInitial)) signal = "schema";

const leadEvent =
  events.find(e => signal === "pool" && poolPattern.test(`${e.error_code} ${e.message}`)) ||
  events.find(e => signal === "tls" && tlsPattern.test(`${e.error_code} ${e.message}`)) ||
  events.find(e => signal === "schema" && schemaPattern.test(`${e.error_code} ${e.message}`)) ||
  events.find(e => e.trace_id) ||
  events[0];

let trace = { found: false, spans: [] };
if (leadEvent && leadEvent.trace_id) {
  trace = await tools.get_trace({ trace_id: leadEvent.trace_id });
}

const failedSpans = (trace.spans || []).filter(s => s.status !== "OK");
const causalSpan =
  failedSpans.find(s => signal === "pool" && poolPattern.test(`${s.operation} ${s.message}`)) ||
  failedSpans.find(s => signal === "tls" && tlsPattern.test(`${s.operation} ${s.message}`)) ||
  failedSpans.find(s => signal === "schema" && schemaPattern.test(`${s.operation} ${s.message}`)) ||
  failedSpans[failedSpans.length - 1] ||
  (trace.spans || [])[0];

let affectedService =
  (causalSpan && causalSpan.service) ||
  (leadEvent && leadEvent.dependency) ||
  "checkout-api";

if (affectedService === "checkout-api" && leadEvent && leadEvent.dependency) {
  affectedService = leadEvent.dependency;
}

let downstreamLogs = { events: [] };
if (affectedService !== "checkout-api") {
  downstreamLogs = await tools.search_logs({
    service: affectedService,
    window_start,
    window_end,
    query:
      signal === "pool" ? "connection pool exhausted timeout database" :
      signal === "tls" ? "TLS handshake certificate expired" :
      "response parse schema version"
  });
}

const allDiagnosticText = [
  combinedInitial,
  ...(trace.spans || []).map(s => `${s.service} ${s.operation} ${s.message}`),
  ...(downstreamLogs.events || []).map(e => `${e.error_code} ${e.message} ${e.dependency || ""}`)
].join(" ");

if (tlsPattern.test(allDiagnosticText) && !/pool exhausted|pool saturation|connection pool/i.test(allDiagnosticText)) signal = "tls";
else if (schemaPattern.test(allDiagnosticText) && !/pool exhausted|pool saturation|connection pool/i.test(allDiagnosticText)) signal = "schema";
else if (poolPattern.test(allDiagnosticText)) signal = "pool";

const metricName =
  signal === "pool" ? "db_pool_wait_ms" :
  signal === "tls" ? "tls_handshake_errors" :
  "response_parse_errors";

const causalMetric = await tools.get_service_metrics({
  service: affectedService,
  window_start,
  window_end,
  metric: metricName
});

let deployment = { deployments: [] };
if (signal === "pool" || signal === "schema") {
  deployment = await tools.list_recent_deployments({
    service: affectedService,
    window_start,
    window_end
  });
}

const supportPattern =
  signal === "pool" ? /pool|capacity|connection|database|db_pool|wait/i :
  signal === "tls" ? /tls|certificate|handshake|x509|expired/i :
  /schema|parse|version|response/i;

const evidence = new Set();

for (const e of events) {
  if (supportPattern.test(`${e.error_code} ${e.message} ${e.dependency || ""}`)) evidence.add(e.evidence_id);
}
if (supportPattern.test(checkoutErrorRate.summary || "") || (checkoutErrorRate.points || []).some(p => p.value > 0)) {
  evidence.add(checkoutErrorRate.evidence_id);
}
for (const s of trace.spans || []) {
  if (supportPattern.test(`${s.operation} ${s.message}`)) evidence.add(s.evidence_id);
}
for (const e of downstreamLogs.events || []) {
  if (supportPattern.test(`${e.error_code} ${e.message} ${e.dependency || ""}`)) evidence.add(e.evidence_id);
}
if (supportPattern.test(causalMetric.summary || "") || (causalMetric.points || []).some(p => p.value > 0)) {
  evidence.add(causalMetric.evidence_id);
}
for (const d of deployment.deployments || []) {
  if (supportPattern.test(`${d.kind} ${d.summary}`)) evidence.add(d.evidence_id);
}

const taxonomy =
  signal === "tls"
    ? {
        root_cause: "expired_tls_certificate",
        recommended_action: "rotate_expired_service_certificate"
      }
    : signal === "schema"
    ? {
        root_cause: "pricing_schema_version_mismatch",
        recommended_action: "rollback_pricing_schema_deployment"
      }
    : {
        root_cause: "database_connection_pool_exhaustion",
        recommended_action: "restore_database_pool_capacity"
      };

const evidence_ids = [...evidence].filter(Boolean).sort();
const result = {
  incident_id: "database-pool-exhaustion",
  root_cause: taxonomy.root_cause,
  affected_service: affectedService,
  confidence: evidence_ids.length >= 3 ? "high" : "medium",
  evidence_ids,
  recommended_action: taxonomy.recommended_action
};

text(JSON.stringify(result));
```

## Program output

```json
{
  "incident_id": "database-pool-exhaustion",
  "root_cause": "database_connection_pool_exhaustion",
  "affected_service": "payment-api",
  "confidence": "high",
  "evidence_ids": [
    "deploy-payment-pool-capacity",
    "log-payment-pool-wait",
    "metric-checkout-error-spike",
    "metric-payment-db-pool-wait",
    "span-payment-db-pool"
  ],
  "recommended_action": "restore_database_pool_capacity"
}
```
