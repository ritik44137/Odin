#!/usr/bin/env python3
"""Reproduce the oracle & nop funnel stage locally with Docker.

Two runs against the same image built from environment/Dockerfile:

  nop    - untouched starting state, then tests/test.sh. Must sit at the floor.
  oracle - solution/solve.sh, then tests/test.sh. Must reach full reward.

Failing this stage upstream is the most expensive way to lose a submission, and
it is entirely reproducible here. The verifier is mounted outside /app so the
run also demonstrates that grading does not depend on agent-readable files.

Score is read from an `ODYSSEY_SCORE=<float>` line in verifier stdout (the
convention in templates/odyssey-test.template.sh); if the verifier prints no such
line, exit status alone is used (0 -> 1.0, non-zero -> 0.0).
"""
import argparse
import json
import re
import shutil
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Tuple

try:
    import tomllib as _toml
except ModuleNotFoundError:
    try:
        import tomli as _toml  # type: ignore[no-redef]
    except ModuleNotFoundError:
        _toml = None  # type: ignore[assignment]

sys.path.insert(0, str(Path(__file__).resolve().parent))

import odyssey_paths as paths  # noqa: E402

SCORE_RE = re.compile(r"ODYSSEY_SCORE=([0-9]*\.?[0-9]+)")
VERIFIER_MOUNT = "/odyssey/tests"
SOLUTION_MOUNT = "/odyssey/solution"

RUN_SHELL = (
    "if command -v bash >/dev/null 2>&1; then exec bash \"$0\"; else exec sh \"$0\"; fi"
)


@dataclass
class RunOutcome:
    label: str
    score: float
    exit_code: int
    seconds: float
    stdout: str
    stderr: str


def run(cmd: List[str], timeout: Optional[int] = None) -> Tuple[int, str, str]:
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    except subprocess.TimeoutExpired as exc:
        out = exc.stdout or ""
        err = (exc.stderr or "") + f"\n[timed out after {timeout}s]"
        return 124, out if isinstance(out, str) else out.decode(), err if isinstance(err, str) else err.decode()
    return proc.returncode, proc.stdout, proc.stderr


DAEMON_MARKERS = (
    "cannot connect to the docker daemon",
    "is the docker daemon running",
    "permission denied while trying to connect to the docker daemon",
    "error during connect",
)
EXIT_INFRA = 3


def daemon_unreachable(text: str) -> bool:
    lowered = text.lower()
    return any(marker in lowered for marker in DAEMON_MARKERS)


def require_daemon() -> None:
    """Separate an unreachable daemon from a broken task, as the funnel does."""
    if shutil.which("docker") is None:
        print("docker is not installed; the oracle and nop checks cannot run here", file=sys.stderr)
        raise SystemExit(EXIT_INFRA)
    # `docker info --format` exits 0 even when the daemon is unreachable, so the
    # output has to be inspected rather than the status alone.
    code, out, err = run(["docker", "info", "--format", "{{.ServerVersion}}"], timeout=60)
    combined = out + err
    if code != 0 or daemon_unreachable(combined) or not out.strip():
        if daemon_unreachable(combined):
            print(
                "docker daemon is not reachable, so the oracle and nop checks did not run.\n"
                "This is an environment problem, not a defect in your task: start Docker and re-run.",
                file=sys.stderr,
            )
        else:
            print(f"docker is not usable: {(err or out).strip() or 'no server version reported'}", file=sys.stderr)
        raise SystemExit(EXIT_INFRA)
    print(f"docker daemon reachable, server version {out.strip()}")


def load_task_toml(bundle: Path) -> dict:
    path = bundle / "task.toml"
    if not path.is_file() or _toml is None:
        return {}
    try:
        return _toml.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def resource_flags(task_toml: dict) -> List[str]:
    """Run under the sandbox limits the bundle declares, so timings are honest."""
    env = task_toml.get("environment", {}) or {}
    flags: List[str] = []
    cpus = env.get("cpus")
    memory_mb = env.get("memory_mb")
    if isinstance(cpus, (int, float)) and cpus > 0:
        flags += ["--cpus", str(cpus)]
    if isinstance(memory_mb, int) and memory_mb >= 128:
        flags += ["--memory", f"{memory_mb}m"]
    return flags


def build_image(bundle: Path, tag: str, network_mode: str) -> None:
    context = bundle / "environment"
    cmd = [
        "docker", "build",
        "-f", str(context / "Dockerfile"),
        "-t", tag,
    ]
    if network_mode == "none":
        cmd += ["--network", "none"]
    cmd.append(str(context))
    print(f"$ {' '.join(cmd)}")
    code, out, err = run(cmd, timeout=3600)
    if code != 0:
        print(out)
        print(err, file=sys.stderr)
        if daemon_unreachable(out + err):
            print("docker daemon became unreachable during the build; nothing was measured", file=sys.stderr)
            raise SystemExit(EXIT_INFRA)
        raise SystemExit("image build failed; the funnel would fail before your task ever runs")


def start_container(tag: str, name: str, flags: List[str], network: str) -> None:
    cmd = [
        "docker", "run", "-d", "--name", name,
        "--network", network,
        *flags,
        "--entrypoint", "/bin/sh",
        tag, "-c", "sleep infinity",
    ]
    code, _, err = run(cmd, timeout=120)
    if code != 0:
        raise SystemExit(f"could not start container from {tag}: {err.strip()}")


def remove_container(name: str) -> None:
    run(["docker", "rm", "-f", name], timeout=120)


def copy_in(name: str, src: Path, dest_parent: str) -> None:
    run(["docker", "exec", name, "/bin/sh", "-c", f"mkdir -p {dest_parent}"], timeout=60)
    code, _, err = run(["docker", "cp", str(src), f"{name}:{dest_parent}/"], timeout=600)
    if code != 0:
        raise SystemExit(f"could not copy {src} into container: {err.strip()}")


def exec_script(name: str, script_path: str, timeout: int) -> Tuple[int, str, str, float]:
    started = time.monotonic()
    code, out, err = run(
        [
            "docker", "exec", "-w", "/app", name,
            "/bin/sh", "-c", RUN_SHELL, script_path,
        ],
        timeout=timeout,
    )
    return code, out, err, time.monotonic() - started


def emit(out: str, err: str) -> None:
    """Print captured output in order.

    stdout is block-buffered when this script is piped, so stderr written straight
    after would otherwise land mid-line. Flushing between the two keeps a verifier's
    output readable in a log.
    """
    if out.strip():
        print(out.rstrip())
        sys.stdout.flush()
    if err.strip():
        print(err.rstrip(), file=sys.stderr)
        sys.stderr.flush()


def extract_score(stdout: str, exit_code: int) -> float:
    matches = SCORE_RE.findall(stdout)
    if matches:
        try:
            return max(0.0, min(1.0, float(matches[-1])))
        except ValueError:
            pass
    return 1.0 if exit_code == 0 else 0.0


def do_run(
    label: str,
    bundle: Path,
    tag: str,
    flags: List[str],
    network: str,
    verifier_timeout: int,
    solve_timeout: int,
    apply_solution: bool,
    keep: bool,
) -> RunOutcome:
    name = f"odyssey-preflight-{label}-{int(time.time())}"
    print(f"\n=== {label} run ({'oracle: solve then verify' if apply_solution else 'nop: verify untouched state'})")
    start_container(tag, name, flags, network)
    try:
        if apply_solution:
            copy_in(name, bundle / "solution", "/odyssey")
            code, out, err, secs = exec_script(name, f"{SOLUTION_MOUNT}/solve.sh", solve_timeout)
            emit(out, err if code != 0 else "")
            if code != 0:
                print(f"[{label}] solution/solve.sh exited {code} after {secs:.1f}s")
                return RunOutcome(label, 0.0, code, secs, out, err)

        copy_in(name, bundle / "tests", "/odyssey")
        code, out, err, secs = exec_script(name, f"{VERIFIER_MOUNT}/test.sh", verifier_timeout)
        emit(out, err)
        score = extract_score(out, code)
        print(f"[{label}] verifier exited {code}, score {score:.4f}, {secs:.1f}s")
        return RunOutcome(label, score, code, secs, out, err)
    finally:
        if keep:
            print(f"[{label}] container kept for inspection: docker exec -it {name} sh")
        else:
            remove_container(name)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the oracle and nop checks locally")
    parser.add_argument("bundle", type=Path, nargs="?", help="Path to the unpacked bundle directory")
    parser.add_argument("--slug", help="Resolve tasks/<slug>/ automatically")
    parser.add_argument("--tag", default=None, help="Docker image tag to build (default derives from the bundle name)")
    parser.add_argument("--skip-build", action="store_true", help="Reuse an existing image instead of rebuilding")
    parser.add_argument("--nop-only", action="store_true", help="Run only the untouched-state check")
    parser.add_argument("--oracle-only", action="store_true", help="Run only the reference-solution check")
    parser.add_argument("--nop-max", type=float, default=0.0, help="Highest score the untouched state may reach")
    parser.add_argument("--oracle-min", type=float, default=1.0, help="Lowest score the reference solution must reach")
    parser.add_argument("--solve-timeout", type=int, default=3600, help="Seconds allowed for solution/solve.sh")
    parser.add_argument("--keep", action="store_true", help="Keep containers after the run for debugging")
    parser.add_argument("--json", type=Path, default=None, help="Write the outcome summary to this JSON file")
    args = parser.parse_args()

    if args.bundle is None:
        if not args.slug:
            parser.error("provide a bundle directory or --slug")
        args.bundle = paths.task_dir(args.slug)

    bundle = args.bundle.resolve()
    if not bundle.is_dir():
        raise SystemExit(f"{paths.rel(bundle)} is not a directory; the oracle and nop runs need an unpacked bundle")
    if not (bundle / "environment" / "Dockerfile").is_file():
        raise SystemExit(f"{bundle} does not look like a bundle: environment/Dockerfile is missing")
    require_daemon()

    task_toml = load_task_toml(bundle)
    verifier_cfg = task_toml.get("verifier", {}) or {}
    agent_cfg = task_toml.get("agent", {}) or {}
    env_cfg = task_toml.get("environment", {}) or {}

    verifier_timeout = verifier_cfg.get("timeout_sec")
    if isinstance(verifier_timeout, bool) or not isinstance(verifier_timeout, (int, float)):
        verifier_timeout = 1800
    else:
        verifier_timeout = int(verifier_timeout)

    # Harbor NetworkMode: no-network / public / allowlist. Unset agent mode
    # inherits the environment baseline (Harbor default: public).
    sealed = {"no-network", "none", "disabled"}
    agent_network = agent_cfg.get("network_mode")
    if agent_network is None:
        agent_network = env_cfg.get("network_mode", "no-network")
    run_network = "none" if agent_network in sealed else "bridge"
    if run_network != "none":
        print(f"note: [agent].network_mode is '{agent_network}'; running with docker network 'bridge' "
              "which is broader than an allowlist, so a host-dependency bug can hide here")

    # [environment].network_mode is the runtime baseline, not docker-build networking.
    # Image builds that fetch a base image need the default Docker network.
    build_network = "default"
    tag = args.tag or f"odyssey-preflight/{bundle.name.lower()}"

    if not args.skip_build:
        build_image(bundle, tag, build_network)
    flags = resource_flags(task_toml)

    outcomes: List[RunOutcome] = []
    if not args.oracle_only:
        outcomes.append(do_run("nop", bundle, tag, flags, run_network, verifier_timeout,
                               args.solve_timeout, apply_solution=False, keep=args.keep))
    if not args.nop_only:
        outcomes.append(do_run("oracle", bundle, tag, flags, run_network, verifier_timeout,
                               args.solve_timeout, apply_solution=True, keep=args.keep))

    print("\n=== verdict")
    ok = True
    for outcome in outcomes:
        if outcome.label == "nop":
            passed = outcome.score <= args.nop_max
            expectation = f"<= {args.nop_max:.4f}"
        else:
            passed = outcome.score >= args.oracle_min
            expectation = f">= {args.oracle_min:.4f}"
        ok = ok and passed
        status = "PASS" if passed else "FAIL"
        print(f"[{status}] {outcome.label}: score {outcome.score:.4f} (expected {expectation}), {outcome.seconds:.1f}s")

    if len(outcomes) == 2:
        gap = outcomes[1].score - outcomes[0].score
        print(f"       oracle/nop gap: {gap:.4f}")
        if gap <= 0:
            print("       no gap means the verifier does not distinguish a solved task from an untouched one")

    if args.json:
        args.json.write_text(
            json.dumps(
                {
                    "bundle": str(bundle),
                    "ok": ok,
                    "runs": [
                        {
                            "label": o.label,
                            "score": o.score,
                            "exit_code": o.exit_code,
                            "seconds": round(o.seconds, 2),
                        }
                        for o in outcomes
                    ],
                },
                indent=2,
            ),
            encoding="utf-8",
        )

    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
