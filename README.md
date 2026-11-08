# prometheus-slo-manifests

SLO definitions for Hotel Key services, written as [Sloth](https://github.com/slok/sloth)
`prometheus/v1` specs. Sloth turns each spec into Prometheus recording rules and
multi-window, multi-burn-rate alerts.

## Layout

```
slos/<service>/<service>.yml     Sloth spec, one file per service (source of truth)
generated/<service>.yml          Prometheus rules produced by Sloth (committed, never hand-edited)
docs/runbooks/<service>.md       On-call runbook per service, linked from alert annotations
docs/error-budget-policy.md      What teams do at each level of remaining error budget
docs/postmortem-template.md      Postmortem template
dashboards/slo-overview.json     Grafana dashboard (uid hk-slo-overview)
dashboards/provisioning.yml      Example Grafana provisioning config
demo/                            docker compose stack: fake exporter, Prometheus, Grafana, verify.py
scripts/check.sh                 Lint, test, validate, generate, check rules and dashboard JSON
.github/workflows/validate.yml   CI
```

Current services:

| Service | SLI | Objective | Budget / 30d | Runbook |
|---|---|---|---|---|
| reservations-api | non-5xx share of `http_requests_total{service="reservations"}` | 99.9% | 43.2 min | [runbook](docs/runbooks/reservations-api.md) |
| licensing-service | non-5xx share of `http_requests_total{service="licensing"}` (metric name TODO) | 99.5% | 216 min | [runbook](docs/runbooks/licensing-service.md) |

## Adding a service

1. Create `slos/<service>/<service>.yml` (copy an existing spec as a template).
2. Write `docs/runbooks/<service>.md` using an existing runbook as the template, and point the
   spec's `runbook_url` annotation at it.
3. Run `./scripts/check.sh` to regenerate `generated/`.
4. Commit the spec, runbook, and generated file together.

The dashboard picks up new services automatically through `sloth_slo_info`.

## Dashboard

Import into Grafana or provision via [dashboards/provisioning.yml](dashboards/provisioning.yml).

- **Import:** Grafana > Dashboards > New > Import, upload `dashboards/slo-overview.json`,
  then pick your Prometheus datasource in the `Datasource` dropdown.
- **Provision:** copy `dashboards/provisioning.yml` into `/etc/grafana/provisioning/dashboards/`
  and mount `dashboards/` at the path it names.

The dashboard needs Grafana 10 or later. It has no hardcoded datasource UID; the `DS_PROMETHEUS`
variable selects the datasource. Panels: SLI vs objective, error budget remaining, burn rate
over 1h, 6h, and 3d with lines at the alert thresholds (14.4x, 6x, 1x), and an annotation for
firing SLO alerts.

### Pointing alert links at a live Grafana

Alert `dashboard` annotations currently link to the dashboard JSON on GitHub, because there is
no shared Grafana URL yet. Once there is one (call it `GRAFANA_URL`), change each spec's
`dashboard` annotation to:

```yaml
dashboard: "https://grafana.example.internal/d/hk-slo-overview?var-service=<service>"
```

Replace `https://grafana.example.internal` with the real `GRAFANA_URL` and `<service>` with the
spec's `service` value. Sloth copies annotations verbatim and does not expand environment
variables, so write the literal URL. Then run `./scripts/check.sh` and commit the regenerated rules.

## Demo stack

`demo/` runs the whole pipeline on your machine: a fake exporter, Prometheus loading
`generated/*.yml`, and Grafana provisioned through `dashboards/provisioning.yml`.

```sh
cd demo
docker compose up -d --build
```

- Grafana: http://localhost:3000 (anonymous admin; opens the SLO dashboard)
- Prometheus: http://localhost:9090 (rules and alerts under Status > Rules and Alerts)
- Exporter: http://localhost:8000/metrics

The exporter emits `http_requests_total{service, code}` for `reservations` and `licensing`
at 50 requests per second each, with 0.05% errors by default (`ERROR_RATE`,
`ERROR_RATE_RESERVATIONS`, `ERROR_RATE_LICENSING`, `REQUESTS_PER_SECOND` in
`demo/docker-compose.yml`). Change the error rate while it runs:

```sh
curl -X POST 'http://localhost:8000/error-rate?value=0.2'                       # all services
curl -X POST 'http://localhost:8000/error-rate?service=licensing&value=0.05'    # one service
curl http://localhost:8000/error-rate                                           # current rates
```

At 20% errors the burn-rate panels cross their threshold lines within a few minutes and both
SLO alerts fire, which shows up as red annotations. Windows longer than the stack's uptime
are computed from the data available, so the 6h and 3d panels move as fast as the 1h panel
in the demo.

Check everything automatically (CI runs the same script):

```sh
python demo/verify.py
```

It confirms the `service` dropdown lists both services, every burn-rate panel query rises
above its alert threshold after raising the error rate, and the firing-alert annotation query
returns page alerts for both services. Stop the stack with `docker compose down`.

## Running locally

Requires `yamllint`, `sloth` (v0.16.0), `promtool`, and `jq` on `PATH`.

```sh
./scripts/check.sh
```

The script lints YAML, runs `sloth validate`, regenerates `generated/` from scratch,
runs `promtool check rules` on the output, and runs `jq empty` on the dashboard JSON.

Check markdown links the same way CI does (needs Docker):

```sh
docker run --rm -v "$PWD:/input" -w /input lycheeverse/lychee:latest --offline --include-fragments README.md docs
```

## CI

`.github/workflows/validate.yml` runs on every push and pull request:

1. Installs pinned versions of yamllint, Sloth, and promtool.
2. Runs `scripts/check.sh` (yamllint, `sloth validate`, `sloth generate`, `promtool check rules`, `jq empty`).
3. Fails if `generated/` differs from what is committed, so the rules Prometheus loads
   stay in sync with the specs.
4. Checks every link in `README.md` and `docs/` with [lychee](https://github.com/lycheeverse/lychee).

## Links

- Dashboard: [dashboards/slo-overview.json](dashboards/slo-overview.json)
- Runbooks: [docs/runbooks/](docs/runbooks)
- Issues: [GitHub Issues](https://github.com/ematobi1/prometheus-slo-manifests/issues)

## License

MIT. See [LICENSE](LICENSE).
