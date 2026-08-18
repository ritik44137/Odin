#!/usr/bin/env bash
# Canonical verifier entrypoint. The grader runs exactly this file.
set -uo pipefail

cd /app

TESTS_DIR="$(cd "$(dirname "$0")" && pwd)"
SCORE_FILE="${ODYSSEY_SCORE_FILE:-/tmp/odyssey_score}"
export PYTHONPATH="/app:${PYTHONPATH:-}"
export PYTHONDONTWRITEBYTECODE=1

total_weight=0
earned_weight=0
failed_groups=()

run_group() {
  local name="$1" weight="$2"
  shift 2
  total_weight=$((total_weight + weight))
  echo "--- group: ${name} (weight ${weight})"
  if "$@"; then
    earned_weight=$((earned_weight + weight))
    echo "--- group ${name}: PASS"
  else
    failed_groups+=("${name}")
    echo "--- group ${name}: FAIL"
  fi
}

# Guard against a solution that satisfies the verifier by replacing it: grade the
# library through its public import surface only, from a directory the agent does
# not control.
cd /tmp

run_group "visible-behavior"   30 python -m pytest -q "${TESTS_DIR}/visible"
run_group "hidden-edge-cases"  40 python -m pytest -q "${TESTS_DIR}/hidden/test_edge_cases.py"
run_group "hidden-invariants"  30 python -m pytest -q "${TESTS_DIR}/hidden/test_invariants.py"

if [ "${total_weight}" -eq 0 ]; then
  echo "verifier ran no groups" >&2
  exit 1
fi

score=$(awk -v e="${earned_weight}" -v t="${total_weight}" 'BEGIN { printf "%.4f", e / t }')
echo "${score}" > "${SCORE_FILE}"
echo "ODYSSEY_SCORE=${score}"
echo "earned ${earned_weight} of ${total_weight} weight"

if [ "${#failed_groups[@]}" -gt 0 ]; then
  echo "failed groups: ${failed_groups[*]}" >&2
  exit 1
fi

exit 0
