# licensing-service runbook

## Overview

- **What it does:** validates property and key licenses for other Hotel Key services.
- **Owner:** Licensing team (`@hk-licensing`, placeholder; TODO: set real team handle).
- **Dependencies** (TODO: confirm against the service's architecture doc):
  - License database
  - Upstream ingress / load balancer
- **Callers:** reservations-api ([runbook](reservations-api.md)). An outage here can burn
  the reservations-api budget too.

## SLO

| Field | Value |
|---|---|
| SLO | `requests-availability` (`sloth_id="licensing-service-requests-availability"`) |
| SLI | Share of HTTP requests that do not return 5xx |
| Objective | 99.5% |
| Window | 30 days, rolling |
| Error budget | 0.5% of requests. At constant traffic that is about **216 minutes** of total outage per 30 days; an outage at peak traffic uses it faster. |

SLI PromQL (error ratio). The metric name is not confirmed yet (TODO: confirm metric name):

```promql
sum(rate(http_requests_total{service="licensing",code=~"5.."}[5m]))
/
sum(rate(http_requests_total{service="licensing"}[5m]))
```

Source of truth: [`slos/licensing-service/licensing-service.yml`](../../slos/licensing-service/licensing-service.yml).

## Alerts

Both alerts are named `LicensingServiceHighErrorRate` and come from
[`generated/licensing-service.yml`](../../generated/licensing-service.yml).
An alert fires only when **both** the long and short window exceed the threshold.
Error-ratio thresholds are burn rate times the 0.5% budget.

| Severity | Burn rate | Long window | Short window | Error ratio threshold | Budget used at trigger | Budget gone in |
|---|---|---|---|---|---|---|
| page (`severity=critical`) | 14.4x | 1h | 5m | 7.2% | 2% | 50h |
| page (`severity=critical`) | 6x | 6h | 30m | 3% | 5% | 5d |
| ticket (`severity=warning`) | 3x | 1d | 2h | 1.5% | 10% | 10d |
| ticket (`severity=warning`) | 1x | 3d | 6h | 0.5% | 10% | 30d |

**Page** means respond now. **Ticket** means fix within business hours, before the budget runs out.

## Triage (first 5 minutes)

1. **Dashboard:** open the [SLO overview dashboard](../../dashboards/slo-overview.json)
   in Grafana with `service=licensing-service`. Check the burn-rate panel and the error budget remaining.
2. **Current error ratio and burn rate:**

   ```promql
   slo:sli_error:ratio_rate5m{sloth_service="licensing-service"}
   slo:current_burn_rate:ratio{sloth_service="licensing-service"}
   slo:period_error_budget_remaining:ratio{sloth_service="licensing-service"}
   ```

3. **Where the errors are:**

   ```promql
   sum by (code) (rate(http_requests_total{service="licensing",code=~"5.."}[5m]))
   sum by (instance) (rate(http_requests_total{service="licensing",code=~"5.."}[5m]))
   ```

   One instance means a bad pod or node. All instances means a bad deploy or a broken dependency.
4. **Recent deploys:** check the deploy history for licensing-service in the last 2 hours
   (TODO: link the deploy pipeline). If the errors started right after a deploy, go to Rollback.
5. **Dependency health:** check the license database's error and latency metrics. Check
   whether reservations-api is also burning budget, which means the outage is visible to its callers.

## Mitigation

- **Rollback:** the errors started after a deploy. Roll back to the previous release
  (TODO: link the rollback command or pipeline job). Confirm the 5m error ratio drops within 10 minutes.
- **Scale out:** errors come with saturation. Add replicas, then confirm per-instance error rates fall.
- **Feature flag:** errors are limited to one license type or feature behind a flag. Turn the flag off.
- **Failover:** the license database or region is unhealthy. Fail over to the standby
  (TODO: document the failover procedure and owner).

## Escalation

1. Primary on-call: `licensing-oncall` rotation (placeholder; TODO: link the paging schedule).
2. Service owner: `John Placeholder`, licensing team lead (TODO: real name).
3. Incident commander: `IC Placeholder` (TODO: real IC rotation). Escalate when customer
   impact lasts more than 30 minutes or reservations-api is also paging.

## Post-incident

- Apply the [error budget policy](../error-budget-policy.md).
- Write a postmortem using the [postmortem template](../postmortem-template.md) for every page.
