"""Brace-balance check for sketch/src/ files the native suite can't compile.

sketch/tests/native only builds pure-logic headers; anything pulling in
Arduino.h/Ethernet.h/Zephyr headers (NetworkRelay.cpp and friends) is never
compiled at all, so a plain syntax error there is invisible until a real
board build. This script does not compile anything — it strips comments and
string/char literals, then checks every file's brace depth returns to zero.
Wired into verify.py's gate as its 5th check.
"""

import sys
from pathlib import Path

SKETCH_SRC = Path(__file__).resolve().parent.parent / "sketch" / "src"


def strip_comments_and_strings(text: str) -> str:
    """Removes // and /* */ comments and "..."/'...' literals.

    Args:
        text (str): Raw file contents.

    Returns:
        str: Same text with comments and literals blanked to spaces,
            preserving line structure and all brace characters.
    """
    out = []
    i = 0
    n = len(text)
    while i < n:
        two = text[i:i + 2]
        if two == "//":
            while i < n and text[i] != "\n":
                i += 1
            continue
        if two == "/*":
            i += 2
            while i < n and text[i:i + 2] != "*/":
                out.append("\n" if text[i] == "\n" else " ")
                i += 1
            i += 2
            continue
        if text[i] in ("\"", "'"):
            quote = text[i]
            out.append(" ")
            i += 1
            while i < n and text[i] != quote:
                if text[i] == "\\" and i + 1 < n:
                    i += 2
                else:
                    i += 1
            i += 1
            continue
        out.append(text[i])
        i += 1
    return "".join(out)


def check_file(path: Path) -> int:
    """Returns the file's final brace depth (0 means balanced).

    Args:
        path (Path): Source file to check.

    Returns:
        int: Net depth of '{' minus '}' after stripping comments/strings.
    """
    stripped = strip_comments_and_strings(path.read_text())
    return stripped.count("{") - stripped.count("}")


def main() -> int:
    failures = []
    for path in sorted(SKETCH_SRC.glob("*.cpp")) + sorted(SKETCH_SRC.glob("*.h")):
        depth = check_file(path)
        if depth != 0:
            failures.append((path, depth))

    if failures:
        for path, depth in failures:
            print(f"UNBALANCED: {path} (final brace depth {depth:+d})")
        print(f"{len(failures)} file(s) unbalanced")
        return 1

    print(f"brace balance ok ({len(list(SKETCH_SRC.glob('*.cpp')))} .cpp, "
          f"{len(list(SKETCH_SRC.glob('*.h')))} .h)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
