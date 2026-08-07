#!/usr/bin/env python3
"""Cross-checks the Bridge contract between the sketch and the Python side.

Every function that crosses the MCU/Linux boundary is declared twice - once
in C++ and once in Python - and nothing makes the compiler or the interpreter
compare them. A name typo or an argument-count change compiles and imports
cleanly on both sides and only fails at runtime, usually as silence rather
than an error.

Run it after touching either side:

    python3 tools/check_bridge_contract.py

Exit code is non-zero when anything disagrees, so it can go in a pre-commit
hook or a build step.
"""

import pathlib
import re
import sys


def collect_python(root: pathlib.Path) -> tuple[dict, dict]:
    """Finds what Python calls and what it provides.

    Args:
        root: The python/app folder.

    Returns:
        Tuple of (calls, provides) keyed by Bridge function name.
    """
    calls, provides = {}, {}
    for path in root.rglob("*.py"):
        text = path.read_text(encoding="utf-8")
        for match in re.finditer(
                r'(?:Bridge|_bridge)\.call\(\s*"([a-z_]+)"\s*((?:,[^)]*)?)\)',
                text):
            count = len([a for a in match.group(2).split(",") if a.strip()])
            calls[match.group(1)] = (count, path.name)
        # the repository funnels its calls through _call/_command wrappers,
        # which add exactly one payload argument
        for match in re.finditer(r'self\._(?:call|command)\(\s*"([a-z_]+)"',
                                 text):
            calls[match.group(1)] = (1, path.name)
        for match in re.finditer(
                r'Bridge\.provide\("([a-z_]+)",\s*self\.(\w+)\)', text):
            signature = re.search(rf'def {match.group(2)}\(self(,[^)]*)?\)',
                                  text)
            count = 0
            if signature and signature.group(1):
                count = len([a for a in signature.group(1).split(",")
                             if a.strip()])
            provides[match.group(1)] = (count, match.group(2), path.name)
    return calls, provides


def collect_sketch(path: pathlib.Path) -> tuple[dict, dict]:
    """Finds what the sketch provides and what it notifies.

    Args:
        path: BridgeApi.cpp.

    Returns:
        Tuple of (provides, notifies) keyed by Bridge function name.
    """
    text = path.read_text(encoding="utf-8")
    provides, notifies = {}, {}
    for name, function in re.findall(
            r'Bridge\.provide(?:_safe)?\("([a-z_]+)",\s*(\w+)\)', text):
        signature = re.search(
            rf'\b\w[\w:<>\s\*]*\s{function}\(([^)]*)\)\s*\{{', text)
        params = []
        if signature and signature.group(1).strip():
            params = [p for p in signature.group(1).split(",") if p.strip()]
        provides[name] = (len(params), function)
    for match in re.finditer(r'Bridge\.notify\("([a-z_]+)"((?:,[^;]*)?)\)',
                             text):
        count = len([a for a in match.group(2).split(",") if a.strip()])
        notifies[match.group(1)] = count
    return provides, notifies


def main() -> int:
    """Entry point.

    Returns:
        0 when both sides agree, 1 otherwise.
    """
    here = pathlib.Path(__file__).resolve().parent.parent
    py_calls, py_provides = collect_python(here / "python" / "app")
    sk_provides, sk_notifies = collect_sketch(
        here / "sketch" / "src" / "BridgeApi.cpp")

    problems = []
    print("Linux -> MCU   (python calls, sketch provides)")
    for name in sorted(set(py_calls) | set(sk_provides)):
        py = py_calls.get(name)
        sk = sk_provides.get(name)
        if py is None:
            problems.append(f"{name}: sketch provides it, python never calls")
            print(f"  {name:<24} ORPHAN - never called by python")
        elif sk is None:
            problems.append(f"{name}: python calls it, sketch never provides")
            print(f"  {name:<24} MISSING in the sketch")
        elif py[0] != sk[0]:
            problems.append(
                f"{name}: python passes {py[0]}, sketch takes {sk[0]}")
            print(f"  {name:<24} MISMATCH  py={py[0]} sketch={sk[0]}")
        else:
            print(f"  {name:<24} ok  ({py[0]} arg(s))")

    print("\nMCU -> Linux   (sketch notifies, python provides)")
    for name in sorted(set(sk_notifies) | set(py_provides)):
        sk = sk_notifies.get(name)
        py = py_provides.get(name)
        if sk is None:
            problems.append(f"{name}: python provides it, sketch never sends")
            print(f"  {name:<24} ORPHAN - never sent by the sketch")
        elif py is None:
            problems.append(f"{name}: sketch sends it, python never provides")
            print(f"  {name:<24} MISSING in python")
        elif sk != py[0]:
            problems.append(
                f"{name}: sketch sends {sk}, python takes {py[0]}")
            print(f"  {name:<24} MISMATCH  sketch={sk} py={py[0]}")
        else:
            print(f"  {name:<24} ok  ({sk} arg(s))")

    print()
    if problems:
        for problem in problems:
            print(f"  !! {problem}")
        print(f"\n{len(problems)} problem(s)")
        return 1
    print("both sides agree")
    return 0


if __name__ == "__main__":
    sys.exit(main())
