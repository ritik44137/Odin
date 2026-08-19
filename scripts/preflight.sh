#!/usr/bin/env bash
# Run every local gate that can be checked before packaging a task.
#
# Usage:
#   scripts/preflight.sh --slug <slug> [--with-oracle]
#   scripts/preflight.sh <draft.md> <bundle-dir-or-zip> [--with-oracle]
#
# The slug form resolves drafts/<slug>.md and tasks/<slug>/ for you, which is the
# normal way to call this. The explicit-path form exists for one-off checks, such as
# validating examples/reference-bundle/.
#
# The oracle and nop runs need Docker and an unpacked bundle directory, so they are
# opt-in via --with-oracle. Nothing should be uploaded until they have passed once.
set -uo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${REPO_ROOT}"

usage() {
  echo "usage: scripts/preflight.sh --slug <slug> [--with-oracle]" >&2
  echo "       scripts/preflight.sh <draft.md> <bundle-dir-or-zip> [--with-oracle]" >&2
  exit 2
}

SLUG=""
DRAFT=""
BUNDLE=""
WITH_ORACLE=0

while [ "$#" -gt 0 ]; do
  case "$1" in
    --slug)
      [ "$#" -ge 2 ] || usage
      SLUG="$2"
      shift 2
      ;;
    --with-oracle)
      WITH_ORACLE=1
      shift
      ;;
    -h|--help)
      usage
      ;;
    *)
      if [ -z "${DRAFT}" ]; then
        DRAFT="$1"
      elif [ -z "${BUNDLE}" ]; then
        BUNDLE="$1"
      else
        usage
      fi
      shift
      ;;
  esac
done

if [ -n "${SLUG}" ]; then
  DRAFT="drafts/${SLUG}.md"
  BUNDLE="tasks/${SLUG}"
  [ -f "${DRAFT}" ] || { echo "no draft at ${DRAFT}" >&2; exit 2; }
  [ -d "${BUNDLE}" ] || { echo "no task directory at ${BUNDLE}" >&2; exit 2; }
elif [ -z "${DRAFT}" ] || [ -z "${BUNDLE}" ]; then
  usage
fi

failures=()
skipped=()

stage() {
  local name="$1"
  shift
  echo
  echo "############ ${name}"
  "$@"
  local code=$?
  # run_oracle_nop.py exits 3 when Docker itself is unusable. That is an
  # environment problem, not a verdict on the task, so it is reported separately.
  if [ "${code}" -eq 3 ]; then
    skipped+=("${name}")
  elif [ "${code}" -ne 0 ]; then
    failures+=("${name}")
  fi
}

stage "structure and consistency" python3 scripts/validate_odyssey_task.py --draft "${DRAFT}" --bundle "${BUNDLE}"
stage "anti-gaming leak scan" python3 scripts/scan_bundle_leaks.py "${BUNDLE}"
stage "difficulty design" python3 scripts/check_difficulty_design.py --draft "${DRAFT}" "${BUNDLE}"
stage "novelty" python3 scripts/check_novelty.py "${DRAFT}"

if [ "${WITH_ORACLE}" -eq 1 ]; then
  if [ -d "${BUNDLE}" ]; then
    stage "oracle and nop" python3 scripts/run_oracle_nop.py "${BUNDLE}"
  else
    echo
    echo "############ oracle and nop"
    echo "skipped: pass an unpacked bundle directory to run the oracle and nop checks" >&2
    failures+=("oracle and nop (needs an unpacked directory)")
  fi
else
  echo
  echo "############ oracle and nop"
  echo "not run: pass --with-oracle to build the image and run both checks"
  skipped+=("oracle and nop (not requested)")
fi

echo
echo "############ preflight summary"
for item in "${skipped[@]}"; do
  echo "NOT MEASURED: ${item}"
done
for item in "${failures[@]}"; do
  echo "FAILED: ${item}"
done
if [ "${#failures[@]}" -eq 0 ]; then
  if [ "${#skipped[@]}" -eq 0 ]; then
    echo "all local gates passed"
  else
    echo "every gate that could run passed; the ones above were not measured"
  fi
  if [ -n "${SLUG}" ]; then
    echo "next: python3 scripts/package_task.py --slug ${SLUG}"
  fi
  exit 0
fi
exit 1
