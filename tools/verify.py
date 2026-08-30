"""Runs the five verification checks once and prints one summary block.

    python3 tools/verify.py                  # run everything, compare to baseline
    python3 tools/verify.py --update-baseline # accept the current counts as new

Replaces re-running pytest two or three times a session to answer "did it
pass", "how many", and "which one failed" separately (backlog D24) - one run
answers all three, and on failure prints the failing names/tracebacks inline.

Deliberately does not scrape pytest's final "N passed in Ys" text line: it is
unreliable under a non-tty stdout in this environment (confirmed empirically,
25 Aug 2026 - reproduces even on a trivial coverage-free file, so it is an
environment quirk, not a test result). Counts come from per-test result lines
(`-v`) and from exit codes instead, which do not depend on that line existing.
"""

import argparse
import hashlib
import json
import re
import subprocess
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
PYTHON_DIR = REPO_ROOT / "python"
TOOLS_DIR = REPO_ROOT / "tools"
VENV_DIR = REPO_ROOT / ".venv"
NATIVE_DIR = REPO_ROOT / "sketch" / "tests" / "native"
BASELINE_PATH = Path(__file__).resolve().parent / "verify_baseline.json"

# .venv stays on the mount (CLAUDE.md sec.6) - moving it was considered and
# declined, 25 Aug 2026, for portability/safety. But importing it from there
# costs ~40s of pure CIFS round-trip latency PER RUN, confirmed not fixed by
# Python's own bytecode cache (still 39s with __pycache__ fully warm - the
# cost is per-file network round trips, not compilation). This mirrors just
# the venv locally, rebuilt only when the requirement files change, so that
# cost is paid once instead of every run. python/ itself is re-mirrored
# every run regardless (a few hundred KB, near-instant) so edits are never
# stale.
LOCAL_CACHE = Path.home() / ".cache" / "servo_mvp" / "verify-mirror"
LOCAL_VENV = LOCAL_CACHE / "venv"
LOCAL_PYTHON_DIR = LOCAL_CACHE / "python"
LOCAL_TOOLS_DIR = LOCAL_CACHE / "tools"
LOCAL_VENV_MANIFEST = LOCAL_CACHE / ".venv-manifest"

PASS_RE = re.compile(r"^(?P<name>\S+) PASSED\b")
FAIL_RE = re.compile(r"^(?P<name>\S+) (?:FAILED|ERROR)\b")
COVERAGE_GATE_RE = re.compile(
    r"Required test coverage of (?P<gate>[\d.]+)% (?P<verdict>reached|not reached)"
    r"\. Total coverage: (?P<actual>[\d.]+)%")
NATIVE_RE = re.compile(r"^(?P<checks>\d+) checks, (?P<failures>\d+) failure")
CLIENT_OK_RE = re.compile(r"^  ok   ")
CLIENT_FAIL_RE = re.compile(r"^  FAIL ")


def _requirements_hash() -> str:
    """Hashes the requirement files that determine .venv's contents.

    Returns:
        A short hash - changes whenever a dependency is added or upgraded.
    """
    digest = hashlib.sha256()
    for name in ("requirements.txt", "requirements-dev.txt"):
        digest.update((PYTHON_DIR / name).read_bytes())
    return digest.hexdigest()[:16]


def _ensure_local_venv_mirror() -> tuple[Path, float]:
    """Mirrors .venv locally if the requirement files have changed.

    Returns:
        (path to the local venv's python binary, seconds spent rebuilding
        - 0.0 on a cache hit).
    """
    current = _requirements_hash()
    cached = LOCAL_VENV_MANIFEST.read_text().strip() \
        if LOCAL_VENV_MANIFEST.exists() else None
    if cached == current and (LOCAL_VENV / "bin" / "python").exists():
        return LOCAL_VENV / "bin" / "python", 0.0

    started = time.monotonic()
    LOCAL_CACHE.mkdir(parents=True, exist_ok=True)
    subprocess.run(["rsync", "-a", "--delete", f"{VENV_DIR}/", f"{LOCAL_VENV}/"],
                   check=True)
    LOCAL_VENV_MANIFEST.write_text(current)
    return LOCAL_VENV / "bin" / "python", time.monotonic() - started


def _mirror_python_source() -> None:
    """Mirrors python/ and tools/ locally, fresh every run.

    Both, not just python/: test_soak_report.py imports tools/soak_report.py
    directly by path, so the mirror must keep the same sibling layout as
    the real repo or that import breaks inside the mirror. Cheap either
    way - a few hundred KB, near-instant - so edits are never stale.

    Returns:
        None.
    """
    LOCAL_CACHE.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        ["rsync", "-a", "--delete",
         "--exclude=__pycache__", "--exclude=.pytest_cache",
         f"{PYTHON_DIR}/", f"{LOCAL_PYTHON_DIR}/"],
        check=True)
    subprocess.run(
        ["rsync", "-a", "--delete", "--exclude=__pycache__",
         f"{TOOLS_DIR}/", f"{LOCAL_TOOLS_DIR}/"],
        check=True)


def _run(cmd: list, cwd: Path) -> tuple[int, str]:
    """Runs a command, capturing combined stdout+stderr as text.

    Args:
        cmd: Argv list.
        cwd: Working directory.

    Returns:
        (exit_code, combined_output).
    """
    result = subprocess.run(cmd, cwd=str(cwd), capture_output=True, text=True)
    return result.returncode, result.stdout + result.stderr


def run_python_suite() -> dict:
    """Runs the pytest suite against the local mirror (coverage gate comes

    from pytest.ini).

    Returns:
        Findings: passed/failed counts, failing names, coverage, mirror cost.
    """
    venv_python, rebuild_seconds = _ensure_local_venv_mirror()
    _mirror_python_source()
    # pytest.ini's addopts bakes in one -q (net verbosity -1, for humans
    # running bare `pytest` directly) and the coverage flags (left owned
    # by pytest.ini, not duplicated here). Two -v here nets to +1
    # (-1 + 2), which is what actually switches dots to one PASSED/FAILED
    # line per test - a single -v only cancels the -q back to dot mode,
    # confirmed empirically.
    code, output = _run(
        [str(venv_python), "-m", "pytest", "-vv", "--tb=short"],
        LOCAL_PYTHON_DIR)
    passed = [m.group("name") for m in map(PASS_RE.match, output.splitlines())
             if m]
    failed = [m.group("name") for m in map(FAIL_RE.match, output.splitlines())
             if m]
    # The per-file TOTAL row rounds to a whole percent; the fail-under
    # message below it carries the real precision - use that one.
    gate = COVERAGE_GATE_RE.search(output)
    coverage_pct = float(gate.group("actual")) if gate else None
    return {
        "exit_code": code,
        "passed": len(passed),
        "failed": len(failed),
        "failed_names": failed,
        "coverage_pct": coverage_pct,
        "coverage_gate_met": gate.group("verdict") == "reached" if gate else None,
        "coverage_gate_pct": float(gate.group("gate")) if gate else None,
        "venv_rebuild_seconds": rebuild_seconds,
        "raw": output,
    }


def run_native_checks() -> dict:
    """Runs the native sketch checks.

    Returns:
        Findings: check/failure counts.
    """
    code, output = _run(["make"], NATIVE_DIR)
    checks = failures = None
    for line in output.splitlines():
        m = NATIVE_RE.match(line)
        if m:
            checks = int(m.group("checks"))
            failures = int(m.group("failures"))
    return {"exit_code": code, "checks": checks, "failures": failures,
            "raw": output}


def run_bridge_contract() -> dict:
    """Runs the Bridge contract checker.

    Returns:
        Findings: whether both sides agree.
    """
    code, output = _run([sys.executable, "tools/check_bridge_contract.py"],
                        REPO_ROOT)
    return {"exit_code": code, "agrees": "both sides agree" in output,
            "raw": output}


def run_client_behaviour() -> dict:
    """Runs the client-behaviour checker (T12: promoted to a real check).

    Returns:
        Findings: ok/fail assertion counts.
    """
    code, output = _run(["node", "tools/check_client_behaviour.js"], REPO_ROOT)
    ok = sum(1 for line in output.splitlines() if CLIENT_OK_RE.match(line))
    fail = sum(1 for line in output.splitlines() if CLIENT_FAIL_RE.match(line))
    return {"exit_code": code, "ok": ok, "fail": fail, "raw": output}


def run_brace_balance() -> dict:
    """Runs the brace-balance check (D37: catches what the native suite
    can't, since it never compiles sketch/src/ files needing Arduino.h).

    Returns:
        Findings: whether every checked file balances.
    """
    code, output = _run([sys.executable, "tools/check_brace_balance.py"],
                        REPO_ROOT)
    return {"exit_code": code, "ok": code == 0, "raw": output}


def _load_baseline() -> dict:
    if BASELINE_PATH.exists():
        return json.loads(BASELINE_PATH.read_text())
    return {}


def _delta(label: str, current, baseline) -> str:
    if baseline is None:
        return f"{label}  {current}  (no baseline yet)"
    if current == baseline:
        return f"{label}  {current}  (baseline {baseline}, no change)"
    sign = "+" if isinstance(current, (int, float)) and current > baseline else ""
    return f"{label}  {baseline} -> {current} ({sign}{current - baseline})"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--update-baseline", action="store_true",
                        help="accept current counts as the new baseline")
    args = parser.parse_args()

    baseline = _load_baseline()
    python_r = run_python_suite()
    native_r = run_native_checks()
    bridge_r = run_bridge_contract()
    client_r = run_client_behaviour()
    brace_r = run_brace_balance()

    all_green = (
        python_r["exit_code"] == 0
        and native_r["exit_code"] == 0
        and bridge_r["agrees"]
        and client_r["exit_code"] == 0
        and brace_r["ok"]
    )

    print("---- verify ----")
    if python_r["venv_rebuild_seconds"] > 0:
        print(f"(local venv mirror rebuilt: requirements changed, "
              f"{python_r['venv_rebuild_seconds']:.0f}s one-time cost)")
    print(_delta("python suite     ", python_r["passed"],
                baseline.get("pytest")))
    if python_r["coverage_pct"] is not None:
        gate_note = "ok" if python_r["coverage_gate_met"] else "GATE FAILED"
        print(f"coverage (app/)   {python_r['coverage_pct']}%  "
              f"gate {python_r['coverage_gate_pct']}%  {gate_note}")
    print(_delta("native checks    ", native_r["checks"], baseline.get("native")))
    print(f"bridge contract   {'both sides agree' if bridge_r['agrees'] else 'DISAGREE'}")
    print(_delta("client behaviour ", client_r["ok"], baseline.get("client")))
    print(f"brace balance     {'ok' if brace_r['ok'] else 'UNBALANCED'}")
    print()

    if python_r["failed_names"]:
        print(f"PYTHON FAILURES ({python_r['failed']}):")
        for name in python_r["failed_names"]:
            print(f"  {name}")
        # Print each failure's own traceback block, not just its name -
        # the whole point is not needing a second run to see why.
        in_failures = False
        for line in python_r["raw"].splitlines():
            if line.startswith("=") and "FAILURES" in line:
                in_failures = True
            elif line.startswith("=") and "warnings summary" in line:
                in_failures = False
            elif in_failures:
                print(line)
        print()

    if native_r["failures"]:
        print(f"NATIVE FAILURES: see raw output below")
        print(native_r["raw"])
        print()

    if not bridge_r["agrees"]:
        print("BRIDGE CONTRACT MISMATCH:")
        print(bridge_r["raw"])
        print()

    if client_r["fail"]:
        print(f"CLIENT FAILURES ({client_r['fail']}):")
        for line in client_r["raw"].splitlines():
            if CLIENT_FAIL_RE.match(line):
                print(f"  {line.strip()}")
        print()

    if not brace_r["ok"]:
        print("BRACE BALANCE FAILURES:")
        print(brace_r["raw"])
        print()

    if args.update_baseline:
        new_baseline = {"pytest": python_r["passed"], "native": native_r["checks"],
                        "client": client_r["ok"]}
        BASELINE_PATH.write_text(json.dumps(new_baseline, indent=2) + "\n")
        print(f"baseline updated: {new_baseline}")

    print("ALL GREEN" if all_green else "SOMETHING FAILED - see above")
    return 0 if all_green else 1


if __name__ == "__main__":
    sys.exit(main())
