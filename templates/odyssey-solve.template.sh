#!/usr/bin/env bash
# Canonical reference-solution entrypoint. The oracle runs exactly this file.
#
# After this script exits, running tests/test.sh must reach full reward. If it
# cannot, the oracle stage fails and there is no task.
#
# The oracle runs in the same sealed environment as the agent, so this script may
# not fetch anything from the network unless the task declares allowlist egress.
set -euo pipefail

cd /app

# ---------------------------------------------------------------------------
# Replace the steps below with the concrete work that solves the task.
#
#   1. apply the implementation changes the objective asks for
#   2. run any build, codegen, or migration step the solution needs
#   3. leave /app in exactly the state tests/test.sh expects
#
# Prefer applying a checked-in patch or copying prepared source files over
# inlining a large heredoc, so the reference stays reviewable.
#
# Derive the answer. Do not echo held-out goldens:
#   GOOD: python /app/calculate.py > /app/output/result.txt
#   BAD:  echo "42" > /app/output/result.txt
# ---------------------------------------------------------------------------

SOLUTION_DIR="$(cd "$(dirname "$0")" && pwd)"

if [ -f "${SOLUTION_DIR}/reference.patch" ]; then
  git apply --whitespace=nowarn "${SOLUTION_DIR}/reference.patch"
fi

echo "reference solution applied"
