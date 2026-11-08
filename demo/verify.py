"""End-to-end check of the demo stack.

Run after `docker compose up -d` in demo/:

    python demo/verify.py

1. The Grafana `service` variable (label_values(sloth_slo_info, sloth_service)) lists both services.
2. The dashboard's burn-rate panel queries rise when the exporter's error rate is raised.
3. The firing SLO alert annotation query returns the page alert.

The error rate is reset to the baseline when the script exits.
"""

import json
import sys
import time
import urllib.parse
import urllib.request

GRAFANA = "http://localhost:3000"
EXPORTER = "http://localhost:8000"
DATASOURCE_UID = "demo-prometheus"
DASHBOARD_UID = "hk-slo-overview"
EXPECTED_SERVICES = {"reservations-api", "licensing-service"}
BURN_RATE_PANELS = {"Burn rate 1h (page at 14.4x)": 14.4, "Burn rate 6h (page at 6x)": 6, "Burn rate 3d (ticket at 1x)": 1}
BASELINE_ERROR_RATE = 0.0005
RAISED_ERROR_RATE = 0.2
TIMEOUT_SECONDS = 10


def http_json(url, method="GET"):
    request = urllib.request.Request(url, method=method)
    with urllib.request.urlopen(request, timeout=TIMEOUT_SECONDS) as response:
        return json.load(response)


def wait_until(description, check, timeout, interval=5):
    deadline = time.monotonic() + timeout
    last_error = None
    while time.monotonic() < deadline:
        try:
            result = check()
            if result:
                return result
        except Exception as err:  # noqa: BLE001 - services may still be starting
            last_error = err
        time.sleep(interval)
    raise SystemExit(f"FAIL: timed out waiting for {description} (last error: {last_error})")


def set_error_rate(value):
    return http_json(f"{EXPORTER}/error-rate?value={value}", method="POST")


def grafana_label_values():
    query = urllib.parse.urlencode({"match[]": "sloth_slo_info"})
    url = f"{GRAFANA}/api/datasources/uid/{DATASOURCE_UID}/resources/api/v1/label/sloth_service/values?{query}"
    return set(http_json(url)["data"])


def grafana_instant_query(expr):
    query = urllib.parse.urlencode({"query": expr})
    url = f"{GRAFANA}/api/datasources/proxy/uid/{DATASOURCE_UID}/api/v1/query?{query}"
    return http_json(url)["data"]["result"]


def dashboard_panel_exprs():
    dashboard = http_json(f"{GRAFANA}/api/dashboards/uid/{DASHBOARD_UID}")["dashboard"]
    exprs = {panel["title"]: panel["targets"][0]["expr"] for panel in dashboard["panels"]}
    annotation = next(item for item in dashboard["annotations"]["list"] if item["name"] == "Firing SLO alerts")
    return exprs, annotation["expr"]


def with_all_services(expr):
    return expr.replace("$service", ".*")


def burn_rates(expr):
    return {series["metric"]["sloth_service"]: float(series["value"][1]) for series in grafana_instant_query(expr)}


def main():
    wait_until("Grafana health", lambda: http_json(f"{GRAFANA}/api/health").get("database") == "ok", timeout=120)
    wait_until("exporter", lambda: http_json(f"{EXPORTER}/error-rate"), timeout=60)
    set_error_rate(BASELINE_ERROR_RATE)

    services = wait_until(
        "both services in the service variable",
        lambda: (lambda found: found if EXPECTED_SERVICES <= found else None)(grafana_label_values()),
        timeout=180,
    )
    print(f"PASS: service variable lists {sorted(services)}")

    exprs, annotation_expr = dashboard_panel_exprs()
    one_hour_expr = with_all_services(exprs["Burn rate 1h (page at 14.4x)"])
    baseline = wait_until(
        "baseline burn rate for both services",
        lambda: (lambda rates: rates if EXPECTED_SERVICES <= rates.keys() else None)(burn_rates(one_hour_expr)),
        timeout=180,
    )
    print("baseline burn rates:")
    for title in BURN_RATE_PANELS:
        print(f"  {title}: {burn_rates(with_all_services(exprs[title]))}")

    set_error_rate(RAISED_ERROR_RATE)
    print(f"raised exporter error rate to {RAISED_ERROR_RATE}")
    try:
        for title, threshold in BURN_RATE_PANELS.items():
            expr = with_all_services(exprs[title])
            raised = wait_until(
                f"{title} above {threshold}x for both services",
                lambda expr=expr, threshold=threshold: (
                    lambda rates: rates if all(rates.get(s, 0) > threshold for s in EXPECTED_SERVICES) else None
                )(burn_rates(expr)),
                timeout=300,
            )
            print(f"PASS: {title} moved above {threshold}x: {raised}")
            if title.startswith("Burn rate 1h"):
                for service in EXPECTED_SERVICES:
                    if raised[service] <= baseline[service]:
                        raise SystemExit(f"FAIL: {service} 1h burn rate did not rise ({baseline[service]} -> {raised[service]})")

        firing = wait_until(
            "firing page alerts for both services",
            lambda: (
                lambda result: result
                if EXPECTED_SERVICES <= {r["metric"]["sloth_service"] for r in result if r["metric"].get("sloth_severity") == "page"}
                else None
            )(grafana_instant_query(with_all_services(annotation_expr))),
            timeout=300,
        )
        alerts = sorted({(r["metric"]["alertname"], r["metric"]["sloth_severity"]) for r in firing})
        print(f"PASS: firing SLO alert annotation query returns {alerts}")
    finally:
        set_error_rate(BASELINE_ERROR_RATE)
        print(f"reset exporter error rate to {BASELINE_ERROR_RATE}")

    print("ALL CHECKS PASSED")


if __name__ == "__main__":
    sys.exit(main())
