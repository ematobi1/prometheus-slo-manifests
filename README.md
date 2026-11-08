# prometheus-slo-manifests

SLO definitions for Hotel Key services, written as [Sloth](https://github.com/slok/sloth)
`prometheus/v1` specs. Sloth turns each spec into Prometheus recording rules and
multi-window, multi-burn-rate alerts.

## Layout

```
slos/<service>/<service>.yml   Sloth spec, one file per service (source of truth)
generated/<service>.yml        Prometheus rules produced by Sloth (committed, never hand-edited)
scripts/check.sh               Lint, validate, generate, check rules
.github/workflows/validate.yml CI
```

Current services:

| Service | SLI | Objective |
|---|---|---|
| reservations-api | non-5xx share of `http_requests_total{service="reservations"}` | 99.9% |
| licensing-service | non-5xx share of `http_requests_total{service="licensing"}` (metric name TODO) | 99.5% |

## Adding a service

1. Create `slos/<service>/<service>.yml` (copy an existing spec as a template).
2. Run `./scripts/check.sh` to regenerate `generated/`.
3. Commit both the spec and the generated file.

## Running locally

Requires `yamllint`, `sloth` (v0.16.0), and `promtool` on `PATH`.

```sh
./scripts/check.sh
```

The script lints YAML, runs `sloth validate`, regenerates `generated/` from scratch,
and runs `promtool check rules` on the output.

## CI

`.github/workflows/validate.yml` runs on every push and pull request. It installs
pinned versions of yamllint, Sloth, and promtool, runs `scripts/check.sh`, then fails
if `generated/` differs from what is committed. That keeps the rules Prometheus loads
in sync with the specs.

## Links

- Dashboards: Grafana, `https://grafana.example.com` (TODO: set real URL)
- Runbooks: `https://runbooks.example.com` (TODO: set real URL)
- Issues: [GitHub Issues](https://github.com/ematobi1/prometheus-slo-manifests/issues)

## License

MIT. See [LICENSE](LICENSE).
