#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

yamllint slos dashboards demo .github
(cd demo/exporter && "${PYTHON:-python3}" -m unittest --quiet)
sloth validate --input slos
rm -rf generated
mkdir -p generated
for spec in slos/*/*.yml; do
  service="$(basename "$(dirname "$spec")")"
  sloth generate --input "$spec" --out "generated/${service}.yml"
done
promtool check rules generated/*.yml
for dashboard in dashboards/*.json; do
  jq empty "$dashboard"
done
