#!/usr/bin/env python3
"""Emergency recovery: cut torque and restore a safe minimum-drive floor.

Run this BEFORE powering the servo back on. It polls for the servo to
answer, then immediately disables torque and rewrites the minimum-drive
floor, so the window in which a dangerous EEPROM value can drive the motor
is as short as the bus allows.

Why it is needed: the minimum-drive floor (register 0x18) lives in EEPROM
and survives a power cut. A campaign run was interrupted with a high value
written, and the restore-on-exit could not complete because the servo had
stopped answering the bus.

    python3 tools/d48_recover_registers.py            # restore to 150
    python3 tools/d48_recover_registers.py --value 40 # restore to something else

Order of operations matters. Torque off comes first: it is a RAM register,
takes effect immediately, and stops the motor driving at all. Only then is
the EEPROM floor rewritten, and only then is torque restored.
"""

import argparse
import json
import sys
import time
import urllib.error
import urllib.request

DEFAULT_SAFE_FLOOR = 150
POLL_SECONDS = 0.05


def post(base_url: str, path: str, body: dict, timeout: float = 3.0) -> dict:
    """Sends one POST and decodes the reply.

    Args:
        base_url (str): API base URL.
        path (str): Endpoint path.
        body (dict): JSON body.
        timeout (float): Socket timeout in seconds.

    Returns:
        dict: Decoded reply.
    """
    req = urllib.request.Request(
        f"{base_url}{path}", data=json.dumps(body).encode(),
        headers={"Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(req, timeout=timeout) as handle:
        return json.loads(handle.read())


def get(base_url: str, path: str, timeout: float = 3.0) -> dict:
    """Sends one GET and decodes the reply.

    Args:
        base_url (str): API base URL.
        path (str): Endpoint path.
        timeout (float): Socket timeout in seconds.

    Returns:
        dict: Decoded reply.
    """
    with urllib.request.urlopen(f"{base_url}{path}", timeout=timeout) as handle:
        return json.loads(handle.read())


def wait_for_servo(base_url: str, timeout_s: float) -> bool:
    """Polls until the servo answers a register read with real values.

    Args:
        base_url (str): API base URL.
        timeout_s (float): How long to keep trying.

    Returns:
        bool: True once the servo answers.
    """
    print("waiting for the servo to answer - power it on now", flush=True)
    deadline = time.time() + timeout_s
    while time.time() < deadline:
        try:
            reply = get(base_url, "/servo/diagnostics/tuning_registers", 1.0)
            if reply.get("min_start_force") is not None:
                print(f"servo answered: min_start_force="
                      f"{reply['min_start_force']}", flush=True)
                return True
        except (urllib.error.URLError, TimeoutError, OSError, ValueError):
            pass
        time.sleep(POLL_SECONDS)
    return False


def main() -> int:
    """Runs the recovery sequence.

    Returns:
        int: Process exit code.
    """
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8001)
    parser.add_argument("--value", type=int, default=DEFAULT_SAFE_FLOOR,
                        help="minimum-drive floor to restore")
    parser.add_argument("--wait", type=float, default=300.0,
                        help="how long to wait for the servo to appear")
    args = parser.parse_args()
    base_url = f"http://{args.host}:{args.port}/api/v1"

    if not wait_for_servo(base_url, args.wait):
        print("servo never answered - is the app running and the board up?")
        return 1

    # Torque first: RAM register, immediate, stops the motor driving while
    # the EEPROM write below is still in flight.
    for attempt in range(5):
        try:
            post(base_url, "/servo/isolate", {"isolated": True})
            print("torque DISABLED", flush=True)
            break
        except Exception as exc:  # noqa: BLE001 - retried
            print(f"  isolate attempt {attempt + 1} failed ({exc!r})")
            time.sleep(0.2)
    else:
        print("COULD NOT DISABLE TORQUE - cut power again before continuing")
        return 2

    for attempt in range(5):
        try:
            post(base_url, "/servo/diagnostics/tuning_registers",
                 {"min_start_force": args.value})
            got = get(base_url, "/servo/diagnostics/tuning_registers")
            if got.get("min_start_force") == args.value:
                print(f"min_start_force restored to {args.value} "
                      "and confirmed by readback", flush=True)
                break
            print(f"  readback says {got.get('min_start_force')}, retrying")
        except Exception as exc:  # noqa: BLE001 - retried
            print(f"  write attempt {attempt + 1} failed ({exc!r})")
        time.sleep(0.3)
    else:
        print("COULD NOT RESTORE THE FLOOR - leave power off and say so")
        return 3

    print("\nregisters now:")
    print(f"  {get(base_url, '/servo/diagnostics/tuning_registers')}")
    print("\nTorque is still OFF. Re-enable it only once you are ready:")
    print("  curl -s -X POST -H 'Content-Type: application/json' \\")
    print(f"    -d '{{\"isolated\": false}}' {base_url}/servo/isolate")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
