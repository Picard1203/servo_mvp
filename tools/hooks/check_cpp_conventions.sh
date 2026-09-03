#!/usr/bin/env bash
# PostToolUse hook (Write|Edit): advisory check of sketch/src/**/*.{h,cpp}
# edits against docs/CONVENTIONS.md's C++ section. Non-blocking.

set -uo pipefail

input=$(cat)
file_path=$(echo "$input" | jq -r '.tool_input.file_path // .tool_response.filePath // empty' 2>/dev/null)

if [ -z "$file_path" ]; then
  exit 0
fi

case "$file_path" in
  sketch/src/*.cpp | */sketch/src/*.cpp | sketch/src/*.h | */sketch/src/*.h) ;;
  *)
    exit 0
    ;;
esac

new_text=$(echo "$input" | jq -r '.tool_input.new_string // .tool_input.content // empty' 2>/dev/null)
if [ -z "$new_text" ]; then
  exit 0
fi

findings=""

case "$file_path" in
  *.cpp)
    doc_comments=$(echo "$new_text" | grep -nE '^\s*(///|/\*\*)' || true)
    if [ -n "$doc_comments" ]; then
      findings="${findings}Doc comment(s) added in a .cpp - docs/CONVENTIONS.md requires /// and /** live in the .h (public interface), not the .cpp:\n${doc_comments}\n"
    fi
    ;;
esac

loop_hits=$(echo "$new_text" | grep -nE '\bwhile\s*\(\s*true\s*\)|\bbreak\s*;|\bcontinue\s*;' || true)
if [ -n "$loop_hits" ]; then
  findings="${findings}break/continue/while(true) found - docs/CONVENTIONS.md bans these except the RELAY_NOTES.md drain-loop exception; confirm this is that exception:\n${loop_hits}\n"
fi

if [ -n "$findings" ]; then
  printf 'C++ CONVENTIONS (advisory, %s):\n%b\n' "$file_path" "$findings" >&2
  exit 2
fi

exit 0
