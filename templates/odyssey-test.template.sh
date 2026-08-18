#!/usr/bin/env bash
# Canonical verifier entrypoint. The grader runs exactly this file.
#
# Shape of a strong verifier:
#   - a VISIBLE group the agent can also run, stating what "done" means
#   - a HIDDEN group holding the decisive cases and grading logic
#   - a monotone partial score built from weighted groups
#   - exit 0 only when the binary success condition holds
#
# Keep held-out fixtures under tests/ only. Anything the Dockerfile copies into
# /app is agent-readable and must not contain expected outputs.
set -uo pipefail

cd /app

# Uses $0 rather than BASH_SOURCE so the script still resolves its own directory
# if the harness invokes it with a POSIX shell.
TESTS_DIR="$(cd "$(dirname "$0")" && pwd)"
SCORE_FILE="${ODYSSEY_SCORE_FILE:-/tmp/odyssey_score}"

total_weight=0
earned_weight=0
failed_groups=()

# run_group <name> <weight> <command...>
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

# ---------------------------------------------------------------------------
# Replace the visible and hidden check bodies below with real grading logic.
#
# Visible groups: mirror the public expectations stated in instruction.md.
# Hidden groups:  held-out cases that a shallow, visible-only patch will fail.
#
# Weight the groups so core correctness dominates cosmetic compatibility, and so
# the score rises monotonically with real progress.
# ---------------------------------------------------------------------------

run_group "visible-behavior"  40 python -m pytest -q "${TESTS_DIR}/visible"
run_group "hidden-edge-cases" 40 python -m pytest -q "${TESTS_DIR}/hidden"
run_group "hidden-invariants" 20 python -m pytest -q "${TESTS_DIR}/hidden/test_invariants.py"

if [ "${total_weight}" -eq 0 ]; then
  echo "verifier ran no groups" >&2
  exit 1
fi

score=$(awk -v e="${earned_weight}" -v t="${total_weight}" 'BEGIN { printf "%.4f", e / t }')
echo "${score}" > "${SCORE_FILE}"
echo "ODYSSEY_SCORE=${score}"
echo "earned ${earned_weight} of ${total_weight} weight"

# Binary success condition: every group must pass. Partial score above is what
# gives credit for incomplete work; this line is the pass/fail gate.
if [ "${#failed_groups[@]}" -gt 0 ]; then
  echo "failed groups: ${failed_groups[*]}" >&2
  exit 1
fi

exit 0
