"""D40d/D48 measurement tool: does a move actually stop trembling.

Board-testing tool built during the D40d hand-held-load investigation
(docs/backlog/D.md D48, docs/history/CLOSED.md D40). The firmware's own
settle metric (servo.move.fine_approach's wait_elapsed_s) reported a fast,
clean settle on moves that raw position polling showed were still
oscillating 10+ seconds later - this tool polls output_deg/current_a
continuously through the whole move instead of trusting that event, and
counts direction reversals near the target as the real trembling signature.
Measures only - never writes a register or a setting.

Run example:
    python3 tools/jitter_probe.py --host 192.168.10.60 -60 --repeats 5
"""
import argparse
import json
import time
import urllib.request

NEAR_TARGET_DEG = 3.0
POLL_SECONDS = 0.08
WINDOW_SECONDS = 15.0
RESET_STABLE_SECONDS = 0.03
RESET_TIMEOUT_SECONDS = 12.0


def get(base_url: str, path: str) -> dict:
    """Performs one GET request with retry, decoding the JSON reply.

    Args:
        base_url (str): API base URL.
        path (str): Endpoint path relative to base_url.

    Returns:
        dict: The decoded JSON body.
    """
    for attempt in range(3):
        try:
            with urllib.request.urlopen(f"{base_url}{path}", timeout=5) as r:
                return json.loads(r.read())
        except Exception:
            if attempt == 2:
                raise
            time.sleep(0.2)


def move(base_url: str, target_deg: float) -> dict:
    """Commands one move with retry.

    Args:
        base_url (str): API base URL.
        target_deg (float): Target output angle in degrees.

    Returns:
        dict: The decoded JSON body.
    """
    req = urllib.request.Request(
        f"{base_url}/servo/move",
        data=json.dumps({"target_deg": target_deg}).encode(),
        headers={"Content-Type": "application/json"}, method="POST")
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=5) as r:
                return json.loads(r.read())
        except Exception:
            if attempt == 2:
                raise
            time.sleep(0.2)


def reset_to(base_url: str, anchor_deg: float) -> None:
    """Moves to an anchor and waits for it to genuinely settle there.

    Args:
        base_url (str): API base URL.
        anchor_deg (float): Anchor angle in degrees.
    """
    move(base_url, anchor_deg)
    stable = 0
    last = None
    t0 = time.time()
    while time.time() - t0 < RESET_TIMEOUT_SECONDS:
        d = get(base_url, "/servo/state")["output_deg"]
        if last is not None and abs(d - last) < RESET_STABLE_SECONDS:
            stable += 1
            if stable > 15:
                return
        else:
            stable = 0
        last = d
        time.sleep(POLL_SECONDS)


def latest_fine_approach_event(base_url: str, after_iso: str) -> dict:
    """Finds the most recent fine-approach event issued after a timestamp.

    Args:
        base_url (str): API base URL.
        after_iso (str): ISO timestamp; only events at or after this count.

    Returns:
        dict: The matching event, or None if none was found yet.
    """
    events = get(base_url, "/system/events?limit=5")["events"]
    for e in events:
        if e["event"] == "servo.move.fine_approach" and e["timestamp"] >= after_iso:
            return e
    return None


def probe(base_url: str, target_deg: float, label: str, tag: str) -> dict:
    """Resets to 0, commands one fresh move, and measures trembling near target.

    Args:
        base_url (str): API base URL.
        target_deg (float): Target output angle in degrees.
        label (str): Trial label, printed with each reading.
        tag (str): Condition tag (e.g. "unloaded", "hand_plus_weight").

    Returns:
        dict: swing_deg, reversals, final_deg, and the matching server event.
    """
    reset_to(base_url, 0.0)
    print(f"\n--- {label} [{tag}]: -> {target_deg} deg ---")
    issued_iso = time.strftime("%Y-%m-%dT%H:%M:%S+00:00", time.gmtime())
    t0 = time.time()
    move(base_url, target_deg)

    trace: list[tuple[float, float, float]] = []
    near_target_vals: list[float] = []
    reversals = 0
    trend = None
    last_val = None
    reversal_times: list[float] = []

    while time.time() - t0 < WINDOW_SECONDS:
        d = get(base_url, "/servo/state")
        elapsed = time.time() - t0
        val = d["output_deg"]
        trace.append((elapsed, val, d["current_a"]))

        if abs(val - target_deg) <= NEAR_TARGET_DEG:
            near_target_vals.append(val)
            if last_val is not None and val != last_val:
                new_trend = "up" if val > last_val else "down"
                if trend is not None and new_trend != trend:
                    reversals += 1
                    reversal_times.append(elapsed)
                trend = new_trend
            last_val = val
        time.sleep(POLL_SECONDS)

    for elapsed, val, cur in trace:
        near = " *" if abs(val - target_deg) <= NEAR_TARGET_DEG else ""
        print(f"  {elapsed:6.2f}s  output_deg={val:8.3f}  current_a={cur:.3f}{near}")

    swing = (max(near_target_vals) - min(near_target_vals)) if near_target_vals else 0.0
    final_deg = trace[-1][1] if trace else None
    print(f"  => near-target swing={swing:.3f} deg  reversals={reversals}"
          f"  final={final_deg}"
          f"  last_reversal_t={reversal_times[-1] if reversal_times else None}")

    fa = latest_fine_approach_event(base_url, issued_iso)
    if fa:
        print(f"  server event: wait_elapsed_s={fa['data'].get('wait_elapsed_s')}"
              f"  overshoot_deg={fa['data'].get('overshoot_deg')}")
    else:
        print("  server event: none found yet (may still be settling past window)")

    return {"swing_deg": swing, "reversals": reversals, "final_deg": final_deg,
            "event": fa}


def main() -> int:
    """Parses arguments and runs repeated probes at one target."""
    parser = argparse.ArgumentParser(
        description="Measure real settling trembling via continuous "
                    "position/current polling, not the firmware's own "
                    "settle-completion event. Measures only.")
    parser.add_argument("target_deg", type=float, help="target output angle")
    parser.add_argument("--host", default="192.168.10.60")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--label", default="probe")
    parser.add_argument("--tag", default="unloaded",
                        help="condition tag, e.g. unloaded, hand_plus_weight")
    parser.add_argument("--repeats", type=int, default=1)
    args = parser.parse_args()

    base_url = f"http://{args.host}:{args.port}/api/v1"
    results = [probe(base_url, args.target_deg, f"{args.label} repeat {i}", args.tag)
               for i in range(1, args.repeats + 1)]

    print("\n=== summary ===")
    for i, r in enumerate(results, 1):
        wes = r["event"]["data"].get("wait_elapsed_s") if r["event"] else None
        print(f"repeat {i}: swing={r['swing_deg']:.3f} deg  reversals={r['reversals']}"
              f"  final={r['final_deg']}  server_wait_elapsed_s={wes}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
