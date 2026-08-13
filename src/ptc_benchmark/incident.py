from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

from .inventory import Arm

INCIDENT_CASE_IDS = (
    "database-pool-exhaustion",
    "expired-tls-certificate",
    "pricing-schema-mismatch",
)


@dataclass(frozen=True)
class IncidentOracle:
    root_cause: str
    affected_service: str
    confidence: str
    evidence_ids: tuple[str, ...]
    recommended_action: str

    def result(self, incident_id: str) -> dict[str, Any]:
        return {
            "incident_id": incident_id,
            "root_cause": self.root_cause,
            "affected_service": self.affected_service,
            "confidence": self.confidence,
            "evidence_ids": sorted(self.evidence_ids),
            "recommended_action": self.recommended_action,
        }


@dataclass(frozen=True)
class IncidentScenario:
    case_id: str
    title: str
    window_start: str
    window_end: str
    entry_service: str
    logs: dict[str, list[dict[str, Any]]]
    traces: dict[str, dict[str, Any]]
    deployments: dict[str, list[dict[str, Any]]]
    metrics: dict[tuple[str, str], dict[str, Any]]
    oracle: IncidentOracle

    @property
    def scenario_name(self) -> str:
        return "incident"

    def expected_result(self) -> dict[str, Any]:
        return self.oracle.result(self.case_id)

    def execute(self, tool_name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        if tool_name == "search_logs":
            service = _required_string(arguments, "service")
            return {
                "service": service,
                "query": _required_string(arguments, "query"),
                "window_start": _required_string(arguments, "window_start"),
                "window_end": _required_string(arguments, "window_end"),
                "events": self.logs.get(service, []),
            }
        if tool_name == "get_trace":
            trace_id = _required_string(arguments, "trace_id")
            return self.traces.get(
                trace_id,
                {"trace_id": trace_id, "found": False, "spans": []},
            )
        if tool_name == "list_recent_deployments":
            service = _required_string(arguments, "service")
            return {
                "service": service,
                "window_start": _required_string(arguments, "window_start"),
                "window_end": _required_string(arguments, "window_end"),
                "deployments": self.deployments.get(service, []),
            }
        if tool_name == "get_service_metrics":
            service = _required_string(arguments, "service")
            metric = _required_string(arguments, "metric")
            return self.metrics.get(
                (service, metric),
                {
                    "service": service,
                    "metric": metric,
                    "unit": "unknown",
                    "evidence_id": f"metric-{service}-{metric}-not-found",
                    "points": [],
                    "summary": "No matching metric series was found.",
                },
            )
        raise ValueError(f"Unknown tool: {tool_name}")

    def tool_definitions(self, arm: Arm) -> list[dict[str, Any]]:
        allowed_callers = ["direct"] if arm == "direct" else ["programmatic"]
        tools = [
            _function_tool(
                "search_logs",
                (
                    "Return a deterministic semi-structured log snapshot for one service and "
                    "time window. Read the natural-language message, error_code, trace_id, "
                    "dependency, and evidence_id fields before choosing the next investigation."
                ),
                _search_logs_parameters(),
                _search_logs_output(),
                allowed_callers,
            ),
            _function_tool(
                "get_trace",
                (
                    "Return all spans for one trace. Span messages contain the dependency-level "
                    "evidence needed to decide which service, metric, or deployment to inspect next."
                ),
                _single_string_parameters("trace_id"),
                _trace_output(),
                allowed_callers,
            ),
            _function_tool(
                "list_recent_deployments",
                "Return deployment and configuration-change records for one service and time window.",
                _service_window_parameters(),
                _deployment_output(),
                allowed_callers,
            ),
            _function_tool(
                "get_service_metrics",
                (
                    "Return one named metric series for one service. Useful metric names in this "
                    "fixture include error_rate, db_pool_wait_ms, tls_handshake_errors, and "
                    "response_parse_errors."
                ),
                _metric_parameters(),
                _metric_output(),
                allowed_callers,
            ),
        ]
        if arm == "programmatic":
            tools.append({"type": "programmatic_tool_calling"})
        return tools

    def prompt(self, arm: Arm) -> tuple[str, str]:
        shared = f"""
Investigate incident {self.case_id!r}: {self.title}.
The investigation window is {self.window_start} through {self.window_end}, and the
entry service is {self.entry_service}.

Start with exactly these two independent observations:
1. search_logs for {self.entry_service} using query "errors timeouts failures".
2. get_service_metrics for {self.entry_service} metric "error_rate".

Then investigate adaptively. Use trace IDs, dependency names, error messages, and
metric summaries from returned evidence to choose the next service and tool. Do not
call every tool for every service, do not repeat an identical call, and stop when the
root cause is supported by independent log/trace/metric or deployment evidence.

Use only the following canonical diagnosis taxonomy:
- database connection-pool saturation after a pool-capacity change:
  root_cause="database_connection_pool_exhaustion",
  recommended_action="restore_database_pool_capacity".
- an expired service certificate causing TLS handshakes to fail:
  root_cause="expired_tls_certificate",
  recommended_action="rotate_expired_service_certificate".
- a newly deployed pricing response schema that callers cannot parse:
  root_cause="pricing_schema_version_mismatch",
  recommended_action="rollback_pricing_schema_deployment".

Return exactly one structured JSON object with keys incident_id, root_cause,
affected_service, confidence, evidence_ids, and recommended_action. Use confidence
"high" only when at least three independent evidence records corroborate the same
cause. Sort evidence_ids ascending. Include only evidence IDs that were actually
returned by tools.

The final assistant message must contain:
RESULT_JSON: <the exact one-line JSON object>
EXPLANATION: <a concise causal chain that names the affected service, root cause,
recommended action, and every evidence ID in RESULT_JSON>.
""".strip()
        if arm == "direct":
            orchestration = """
Use Direct Tool Calling. Make only the two required starting calls initially. Inspect
their semantic content before selecting subsequent calls. Parallelize independent
calls only after the preceding evidence justifies them. Do not use a generated program.
""".strip()
        else:
            orchestration = """
Use Programmatic Tool Calling for the investigation. In generated JavaScript, make
the two required starting calls with Promise.all, inspect their structured fields and
natural-language messages, and branch to later trace, metric, or deployment calls.
Keep intermediate results inside the program. Emit exactly the required result with
text(JSON.stringify(result)). Do not call investigation functions directly.
""".strip()
        instructions = (
            f"<task_contract>\n{shared}\n</task_contract>\n\n"
            f"<tool_orchestration>\n{orchestration}\n</tool_orchestration>"
        )
        user = (
            f"Find the root cause of incident {self.case_id}, cite the evidence, "
            "and recommend the immediate remediation."
        )
        return instructions, user


def build_incident_scenario(case_id: str = INCIDENT_CASE_IDS[0]) -> IncidentScenario:
    builders = {
        "database-pool-exhaustion": _database_pool_case,
        "expired-tls-certificate": _expired_certificate_case,
        "pricing-schema-mismatch": _pricing_schema_case,
    }
    try:
        return builders[case_id]()
    except KeyError as exc:
        raise ValueError(f"Unknown incident case: {case_id}") from exc


def _database_pool_case() -> IncidentScenario:
    start, end = "2026-08-06T10:00:00Z", "2026-08-06T10:20:00Z"
    logs = {
        "checkout-api": [
            _log(
                "log-checkout-payment-timeout",
                "2026-08-06T10:02:12Z",
                "ERROR",
                "UPSTREAM_TIMEOUT",
                "Checkout failed after payment-api timed out while authorizing the order.",
                trace_id="trace-payment-001",
                dependency="payment-api",
            ),
            _log(
                "log-checkout-cache-noise",
                "2026-08-06T10:03:44Z",
                "WARN",
                "CACHE_MISS",
                "Promotion cache miss recovered on retry and did not fail the request.",
                trace_id="trace-noise-001",
                dependency="promotion-cache",
            ),
            _log(
                "log-checkout-client-noise",
                "2026-08-06T10:05:09Z",
                "WARN",
                "CLIENT_CANCELLED",
                "Client disconnected after 120 ms.",
                trace_id="trace-noise-002",
            ),
        ],
        "payment-api": [
            _log(
                "log-payment-pool-wait",
                "2026-08-06T10:02:11Z",
                "ERROR",
                "DB_CONNECTION_TIMEOUT",
                "Authorization waited 4.8 seconds for a database connection; pool utilization remained at 100%.",
                trace_id="trace-payment-001",
                dependency="payments-db",
            )
        ],
    }
    traces = {
        "trace-payment-001": {
            "trace_id": "trace-payment-001",
            "found": True,
            "spans": [
                _span(
                    "span-checkout-payment",
                    "checkout-api",
                    "payment-api.authorize",
                    5012,
                    "ERROR",
                    "The checkout span exhausted its upstream timeout budget.",
                ),
                _span(
                    "span-payment-db-pool",
                    "payment-api",
                    "payments-db.acquire_connection",
                    4801,
                    "ERROR",
                    "The request spent nearly all latency waiting for a database connection from a saturated pool.",
                ),
            ],
        }
    }
    deployments = {
        "payment-api": [
            {
                "evidence_id": "deploy-payment-pool-capacity",
                "deployment_id": "deploy-payment-20260806-0955",
                "timestamp": "2026-08-06T09:55:00Z",
                "kind": "configuration",
                "summary": "Reduced database pool max_connections from 80 to 20.",
            }
        ],
        "checkout-api": [
            {
                "evidence_id": "deploy-checkout-copy-only",
                "deployment_id": "deploy-checkout-20260806-0930",
                "timestamp": "2026-08-06T09:30:00Z",
                "kind": "application",
                "summary": "Changed checkout confirmation copy only.",
            }
        ],
    }
    metrics = {
        ("checkout-api", "error_rate"): _metric(
            "metric-checkout-error-spike",
            "checkout-api",
            "error_rate",
            "percent",
            [0.8, 1.1, 18.4, 21.0],
            "Error rate rose from about 1% to above 18% at 10:02 UTC.",
        ),
        ("payment-api", "db_pool_wait_ms"): _metric(
            "metric-payment-db-pool-wait",
            "payment-api",
            "db_pool_wait_ms",
            "milliseconds",
            [12, 18, 4720, 4890],
            "Database pool wait p95 rose from below 20 ms to above 4.7 seconds.",
        ),
    }
    return IncidentScenario(
        case_id="database-pool-exhaustion",
        title="Checkout errors increased sharply after 10:00 UTC",
        window_start=start,
        window_end=end,
        entry_service="checkout-api",
        logs=logs,
        traces=traces,
        deployments=deployments,
        metrics=metrics,
        oracle=IncidentOracle(
            root_cause="database_connection_pool_exhaustion",
            affected_service="payment-api",
            confidence="high",
            evidence_ids=(
                "deploy-payment-pool-capacity",
                "log-checkout-payment-timeout",
                "metric-payment-db-pool-wait",
                "span-payment-db-pool",
            ),
            recommended_action="restore_database_pool_capacity",
        ),
    )


def _expired_certificate_case() -> IncidentScenario:
    start, end = "2026-08-06T11:00:00Z", "2026-08-06T11:20:00Z"
    logs = {
        "checkout-api": [
            _log(
                "log-checkout-identity-tls",
                "2026-08-06T11:01:31Z",
                "ERROR",
                "TOKEN_VALIDATION_FAILED",
                "Identity token validation failed because the TLS peer certificate expired at 11:00 UTC.",
                trace_id="trace-identity-002",
                dependency="identity-api",
            ),
            _log(
                "log-checkout-retry-noise",
                "2026-08-06T11:02:14Z",
                "WARN",
                "RETRY_SCHEDULED",
                "A retry was scheduled after an upstream handshake failure.",
                trace_id="trace-identity-002",
                dependency="identity-api",
            ),
        ],
        "identity-api": [
            _log(
                "log-identity-certificate-expired",
                "2026-08-06T11:01:30Z",
                "ERROR",
                "TLS_CERTIFICATE_EXPIRED",
                "The serving certificate is expired and incoming TLS handshakes are rejected.",
                trace_id="trace-identity-002",
            )
        ],
    }
    traces = {
        "trace-identity-002": {
            "trace_id": "trace-identity-002",
            "found": True,
            "spans": [
                _span(
                    "span-checkout-identity",
                    "checkout-api",
                    "identity-api.validate_token",
                    92,
                    "ERROR",
                    "The dependency call failed during TLS negotiation before an HTTP response.",
                ),
                _span(
                    "span-identity-tls-certificate",
                    "identity-api",
                    "tls.accept",
                    4,
                    "ERROR",
                    "Certificate not_after is 2026-08-06T11:00:00Z; handshake occurred after expiry.",
                ),
            ],
        }
    }
    deployments = {"identity-api": []}
    metrics = {
        ("checkout-api", "error_rate"): _metric(
            "metric-checkout-auth-error-spike",
            "checkout-api",
            "error_rate",
            "percent",
            [0.5, 0.7, 14.2, 16.1],
            "Checkout authentication failures rose immediately after 11:00 UTC.",
        ),
        ("identity-api", "tls_handshake_errors"): _metric(
            "metric-identity-tls-handshake-errors",
            "identity-api",
            "tls_handshake_errors",
            "errors_per_minute",
            [0, 0, 140, 166],
            "TLS handshake errors changed from zero to more than 140 per minute at certificate expiry.",
        ),
    }
    return IncidentScenario(
        case_id="expired-tls-certificate",
        title="Checkout authentication failures began exactly at 11:00 UTC",
        window_start=start,
        window_end=end,
        entry_service="checkout-api",
        logs=logs,
        traces=traces,
        deployments=deployments,
        metrics=metrics,
        oracle=IncidentOracle(
            root_cause="expired_tls_certificate",
            affected_service="identity-api",
            confidence="high",
            evidence_ids=(
                "log-checkout-identity-tls",
                "metric-identity-tls-handshake-errors",
                "span-identity-tls-certificate",
            ),
            recommended_action="rotate_expired_service_certificate",
        ),
    )


def _pricing_schema_case() -> IncidentScenario:
    start, end = "2026-08-06T12:00:00Z", "2026-08-06T12:20:00Z"
    logs = {
        "checkout-api": [
            _log(
                "log-checkout-pricing-parse",
                "2026-08-06T12:03:08Z",
                "ERROR",
                "UPSTREAM_RESPONSE_INVALID",
                "Pricing response could not be parsed because required field total_amount was missing.",
                trace_id="trace-pricing-003",
                dependency="pricing-api",
            ),
            _log(
                "log-checkout-promo-noise",
                "2026-08-06T12:04:22Z",
                "INFO",
                "PROMOTION_SKIPPED",
                "An ineligible promotion was skipped as expected.",
                trace_id="trace-noise-003",
                dependency="promotion-api",
            ),
        ],
        "pricing-api": [
            _log(
                "log-pricing-v2-response",
                "2026-08-06T12:03:07Z",
                "INFO",
                "SCHEMA_V2_RESPONSE",
                "Returned schema_version=2 with grand_total; legacy callers still require total_amount.",
                trace_id="trace-pricing-003",
            )
        ],
    }
    traces = {
        "trace-pricing-003": {
            "trace_id": "trace-pricing-003",
            "found": True,
            "spans": [
                _span(
                    "span-checkout-pricing-parse",
                    "checkout-api",
                    "pricing-api.quote",
                    63,
                    "ERROR",
                    "The HTTP call succeeded, but checkout rejected schema_version=2 because total_amount was absent.",
                ),
                _span(
                    "span-pricing-v2-serialization",
                    "pricing-api",
                    "serialize_quote_v2",
                    8,
                    "OK",
                    "Serializer emitted grand_total under schema version 2.",
                ),
            ],
        }
    }
    deployments = {
        "pricing-api": [
            {
                "evidence_id": "deploy-pricing-schema-v2",
                "deployment_id": "deploy-pricing-20260806-1200",
                "timestamp": "2026-08-06T12:00:00Z",
                "kind": "application",
                "summary": "Enabled schema_version=2 and renamed total_amount to grand_total.",
            }
        ]
    }
    metrics = {
        ("checkout-api", "error_rate"): _metric(
            "metric-checkout-pricing-error-spike",
            "checkout-api",
            "error_rate",
            "percent",
            [0.9, 1.0, 11.8, 13.4],
            "Checkout errors increased immediately after the pricing deployment.",
        ),
        ("pricing-api", "response_parse_errors"): _metric(
            "metric-pricing-response-parse-errors",
            "pricing-api",
            "response_parse_errors",
            "errors_per_minute",
            [0, 1, 98, 107],
            "Caller parse errors rose sharply after schema version 2 was enabled.",
        ),
    }
    return IncidentScenario(
        case_id="pricing-schema-mismatch",
        title="Checkout quote failures started after a pricing deployment",
        window_start=start,
        window_end=end,
        entry_service="checkout-api",
        logs=logs,
        traces=traces,
        deployments=deployments,
        metrics=metrics,
        oracle=IncidentOracle(
            root_cause="pricing_schema_version_mismatch",
            affected_service="pricing-api",
            confidence="high",
            evidence_ids=(
                "deploy-pricing-schema-v2",
                "log-checkout-pricing-parse",
                "metric-pricing-response-parse-errors",
                "span-checkout-pricing-parse",
            ),
            recommended_action="rollback_pricing_schema_deployment",
        ),
    )


def collect_evidence_ids(value: Any) -> set[str]:
    found: set[str] = set()
    if isinstance(value, dict):
        for key, child in value.items():
            if key == "evidence_id" and isinstance(child, str):
                found.add(child)
            else:
                found.update(collect_evidence_ids(child))
    elif isinstance(value, list):
        for child in value:
            found.update(collect_evidence_ids(child))
    return found


def compact_incident_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True)


def _required_string(arguments: dict[str, Any], name: str) -> str:
    value = arguments.get(name)
    if not isinstance(value, str) or not value:
        raise ValueError(f"{name} must be a non-empty string")
    return value


def _log(
    evidence_id: str,
    timestamp: str,
    severity: str,
    error_code: str,
    message: str,
    *,
    trace_id: str,
    dependency: str | None = None,
) -> dict[str, Any]:
    return {
        "evidence_id": evidence_id,
        "timestamp": timestamp,
        "severity": severity,
        "error_code": error_code,
        "message": message,
        "trace_id": trace_id,
        "dependency": dependency,
    }


def _span(
    evidence_id: str,
    service: str,
    operation: str,
    duration_ms: int,
    status: str,
    message: str,
) -> dict[str, Any]:
    return {
        "evidence_id": evidence_id,
        "service": service,
        "operation": operation,
        "duration_ms": duration_ms,
        "status": status,
        "message": message,
    }


def _metric(
    evidence_id: str,
    service: str,
    metric: str,
    unit: str,
    values: list[float],
    summary: str,
) -> dict[str, Any]:
    return {
        "service": service,
        "metric": metric,
        "unit": unit,
        "evidence_id": evidence_id,
        "points": [
            {"offset_minutes": index * 5, "value": value}
            for index, value in enumerate(values)
        ],
        "summary": summary,
    }


def _function_tool(
    name: str,
    description: str,
    parameters: dict[str, Any],
    output_schema: dict[str, Any],
    allowed_callers: list[str],
) -> dict[str, Any]:
    return {
        "type": "function",
        "name": name,
        "description": description,
        "parameters": parameters,
        "output_schema": output_schema,
        "allowed_callers": allowed_callers,
        "strict": True,
    }


def _single_string_parameters(name: str) -> dict[str, Any]:
    return {
        "type": "object",
        "properties": {name: {"type": "string"}},
        "required": [name],
        "additionalProperties": False,
    }


def _service_window_parameters() -> dict[str, Any]:
    return {
        "type": "object",
        "properties": {
            "service": {"type": "string"},
            "window_start": {"type": "string"},
            "window_end": {"type": "string"},
        },
        "required": ["service", "window_start", "window_end"],
        "additionalProperties": False,
    }


def _search_logs_parameters() -> dict[str, Any]:
    schema = _service_window_parameters()
    schema["properties"]["query"] = {"type": "string"}
    schema["required"] = ["service", "query", "window_start", "window_end"]
    return schema


def _metric_parameters() -> dict[str, Any]:
    schema = _service_window_parameters()
    schema["properties"]["metric"] = {"type": "string"}
    schema["required"] = ["service", "metric", "window_start", "window_end"]
    return schema


def _nullable_string() -> dict[str, Any]:
    return {"type": ["string", "null"]}


def _search_logs_output() -> dict[str, Any]:
    event = {
        "type": "object",
        "properties": {
            "evidence_id": {"type": "string"},
            "timestamp": {"type": "string"},
            "severity": {"type": "string"},
            "error_code": {"type": "string"},
            "message": {"type": "string"},
            "trace_id": {"type": "string"},
            "dependency": _nullable_string(),
        },
        "required": [
            "evidence_id",
            "timestamp",
            "severity",
            "error_code",
            "message",
            "trace_id",
            "dependency",
        ],
        "additionalProperties": False,
    }
    return _object_schema(
        {
            "service": {"type": "string"},
            "query": {"type": "string"},
            "window_start": {"type": "string"},
            "window_end": {"type": "string"},
            "events": {"type": "array", "items": event},
        }
    )


def _trace_output() -> dict[str, Any]:
    span = {
        "type": "object",
        "properties": {
            "evidence_id": {"type": "string"},
            "service": {"type": "string"},
            "operation": {"type": "string"},
            "duration_ms": {"type": "integer"},
            "status": {"type": "string"},
            "message": {"type": "string"},
        },
        "required": ["evidence_id", "service", "operation", "duration_ms", "status", "message"],
        "additionalProperties": False,
    }
    return _object_schema(
        {
            "trace_id": {"type": "string"},
            "found": {"type": "boolean"},
            "spans": {"type": "array", "items": span},
        }
    )


def _deployment_output() -> dict[str, Any]:
    deployment = {
        "type": "object",
        "properties": {
            "evidence_id": {"type": "string"},
            "deployment_id": {"type": "string"},
            "timestamp": {"type": "string"},
            "kind": {"type": "string"},
            "summary": {"type": "string"},
        },
        "required": ["evidence_id", "deployment_id", "timestamp", "kind", "summary"],
        "additionalProperties": False,
    }
    return _object_schema(
        {
            "service": {"type": "string"},
            "window_start": {"type": "string"},
            "window_end": {"type": "string"},
            "deployments": {"type": "array", "items": deployment},
        }
    )


def _metric_output() -> dict[str, Any]:
    point = {
        "type": "object",
        "properties": {
            "offset_minutes": {"type": "integer"},
            "value": {"type": "number"},
        },
        "required": ["offset_minutes", "value"],
        "additionalProperties": False,
    }
    return _object_schema(
        {
            "service": {"type": "string"},
            "metric": {"type": "string"},
            "unit": {"type": "string"},
            "evidence_id": {"type": "string"},
            "points": {"type": "array", "items": point},
            "summary": {"type": "string"},
        }
    )


def _object_schema(properties: dict[str, Any]) -> dict[str, Any]:
    return {
        "type": "object",
        "properties": properties,
        "required": list(properties),
        "additionalProperties": False,
    }
