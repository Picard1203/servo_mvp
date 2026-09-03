#!/usr/bin/env bash
# PostToolUse hook (Write|Edit): advisory check, across every source file
# (not just Python/C++ - this covers python/static/app.js too, ahead of the
# frontend work already queued in the backlog), for two house rules stated
# in CLAUDE.md itself:
#   - "no backlog IDs in code comments" - a D/T/R/ADR tag means nothing to a
#     reader who only has the code, not the docs; explain WHY instead.
#   - "use the glossary's words: timestamp never ts, count never tick,
#     datum never home" (docs/CONTEXT.md).
# Non-blocking - the edit already landed; this only surfaces a reminder.

set -uo pipefail

input=$(cat)
file_path=$(echo "$input" | jq -r '.tool_input.file_path // .tool_response.filePath // empty' 2>/dev/null)

if [ -z "$file_path" ]; then
  exit 0
fi

case "$file_path" in
  *.py | *.cpp | *.h | *.js | *.css) ;;
  *)
    exit 0
    ;;
esac

new_text=$(echo "$input" | jq -r '.tool_input.new_string // .tool_input.content // empty' 2>/dev/null)
if [ -z "$new_text" ]; then
  exit 0
fi

findings=""

# Backlog-ID patterns inside a comment line (# for Python, // or /* for the rest).
# Excludes a D<n>-D<n> shape (sketch/src pin ranges, e.g. "D11-D13" in
# SpiRemap.h - a hardware pin range, not a backlog defect ID) by requiring
# the ID not be immediately followed by a hyphen and another bare number.
id_hits=$(echo "$new_text" | grep -nE '(#|//|/\*).*\b([DTR][0-9]+|ADR-[0-9]+)\b' \
  | grep -vE '\b[DTR][0-9]+-[DTR]?[0-9]+\b' || true)
if [ -n "$id_hits" ]; then
  findings="${findings}Backlog-ID tag in a code comment - explain WHY instead, an ID means nothing to a reader without the docs:\n${id_hits}\n"
fi

# Glossary substitutions: timestamp never ts, count never tick, datum never home.
# Scoped to declaration/assignment shapes (an identifier being introduced),
# not every occurrence of the bare word - "ts"/"tick"/"home" are common
# enough as English or as unrelated identifiers (isolation_service.py's own
# tick() heartbeat method, "/home/arduino/..." paths in config.py, a chart's
# "tick-label" axis terminology in app.js) that a bare-word match is mostly
# noise on this codebase, confirmed by running it against python/app and
# sketch/src before this hook was wired in.
glossary_hits=$(echo "$new_text" | grep -nE '\b(ts|tick|home)\s*[:=]|\bdef[^(]*\((ts|tick|home)\b|,\s*(ts|tick|home)\s*[,)]' \
  | grep -vE '/home/|\.tick\(|tick-label' || true)
if [ -n "$glossary_hits" ]; then
  findings="${findings}Non-glossary identifier found - docs/CONTEXT.md requires timestamp/count/datum, never ts/tick/home:\n${glossary_hits}\n"
fi

if [ -n "$findings" ]; then
  printf 'GLOSSARY & BACKLOG-ID CHECK (advisory, %s):\n%b\n' "$file_path" "$findings" >&2
  exit 2
fi

exit 0
