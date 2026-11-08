# reservations-api runbook

## Overview

- **What it does:** HTTP API that creates, reads, updates, and cancels hotel reservations.
- **Owner:** Reservations team (`@hk-reservations`, placeholder; TODO: set real team handle).
- **Dependencies** (TODO: confirm against the service's architecture doc):
  - Primary reservations database
  - licensing-service ([runbook](licensing-service.md)) for property and key licensing checks
  - Upstream ingress / load balancer

## SLO

| Field | Value |
|---|---|
| SLO | `requests-availability` (`sloth_id="reservations-api-requests-availability"`) |
| SLI | Share of HTTP requests that do not return 5xx |
| Objective | 99.9% |
| Window | 30 days, rolling |
| Error budget | 0.1% of requests, equal to **43.2 minutes** of total outage per 30 days |

SLI PromQL (error ratio):

```promql
sum(rate(http_requests_total{service="reservations",code=~"5.."}[5m]))
/
sum(rate(http_requests_total{service="reservations"}[5m]))
```

Source of truth: [`slos/reservations-api/reservations-api.yml`](../../slos/reservations-api/reservations-api.yml).

## Alerts

Both alerts are named `ReservationsApiHighErrorRate` and come from
[`generated/reservations-api.yml`](../../generated/reservations-api.yml).
An alert fires only when **both** the long and short window exceed the threshold.
Error-ratio thresholds are burn rate times the 0.1% budget.

| Severity | Burn rate | Long window | Short window | Error ratio threshold | Budget used at trigger | Budget gone in |
|---|---|---|---|---|---|---|
| page (`severity=critical`) | 14.4x | 1h | 5m | 1.44% | 2% | 50h |
| page (`severity=critical`) | 6x | 6h | 30m | 0.6% | 5% | 5d |
| ticket (`severity=warning`) | 3x | 1d | 2h | 0.3% | 10% | 10d |
| ticket (`severity=warning`) | 1x | 3d | 6h | 0.1% | 10% | 30d |

**Page** means respond now. **Ticket** means fix within business hours, before the budget runs out.

## Triage (first 5 minutes)

1. **Dashboard:** open the [SLO overview dashboard](../../dashboards/slo-overview.json)
   in Grafana with `service=reservations-api`. Check the burn-rate panel (which window is
   over threshold) and the error budget remaining.
2. **Current error ratio and burn rate:**

   ```promql
   slo:sli_error:ratio_rate5m{sloth_service="reservations-api"}
   slo:current_burn_rate:ratio{sloth_service="reservations-api"}
   slo:period_error_budget_remaining:ratio{sloth_service="reservations-api"}
   ```

3. **Where the errors are:** break 5xx down by status code and instance:

   ```promql
   sum by (code) (rate(http_requests_total{service="reservations",code=~"5.."}[5m]))
   sum by (instance) (rate(http_requests_total{service="reservations",code=~"5.."}[5m]))
   ```

   One instance means a bad pod or node. All instances means a bad deploy or a broken dependency.
4. **Recent deploys:** check the deploy history for reservations-api in the last 2 hours
   (TODO: link the deploy pipeline). If the errors started right after a deploy, go to Rollback.
5. **Dependency health:** check the licensing-service burn rate on the same dashboard
   (`service=licensing-service`) and the database's error and latency metrics.

## Mitigation

Pick the first option that matches what triage found.

- **Rollback:** the errors started after a deploy. Roll back to the previous release
  (TODO: link the rollback command or pipeline job). Confirm the 5m error ratio drops within 10 minutes.
- **Scale out:** errors come with saturation (CPU, connection pool, queue depth). Add replicas,
  then confirm per-instance error rates fall.
- **Feature flag:** errors are limited to one endpoint or feature behind a flag. Turn the flag off.
- **Failover:** a dependency or region is unhealthy. Fail over to the standby
  (TODO: document the failover procedure and owner).

## Escalation

1. Primary on-call: `reservations-oncall` rotation (placeholder; TODO: link the paging schedule).
2. Service owner: `Jane Placeholder`, reservations team lead (TODO: real name).
3. Incident commander: `IC Placeholder` (TODO: real IC rotation). Escalate when customer
   impact lasts more than 30 minutes or more than one service is affected.

## Post-incident

- Apply the [error budget policy](../error-budget-policy.md).
- Write a postmortem using the [postmortem template](../postmortem-template.md) for every page.
