#!/usr/bin/env bash
# PostToolUse hook (Write|Edit): advisory check of python/**/*.py edits against
# docs/CONVENTIONS.md. Non-blocking - the edit already landed; this only
# surfaces a reminder back to the model. Mirrors the vendored
# skills/phd-skills/plugin/scripts/jargon_scrub.sh pattern.

set -uo pipefail

input=$(cat)
file_path=$(echo "$input" | jq -r '.tool_input.file_path // .tool_response.filePath // empty' 2>/dev/null)

if [ -z "$file_path" ]; then
  exit 0
fi

case "$file_path" in
  python/*.py | */python/*.py) ;;
  *)
    exit 0
    ;;
esac

repo_root=$(git -C "$(dirname "$file_path")" rev-parse --show-toplevel 2>/dev/null) || exit 0
ruff_bin="$repo_root/.venv/bin/ruff"
ruff_config="$repo_root/python/ruff.toml"

findings=""

if [ -x "$ruff_bin" ] && [ -f "$ruff_config" ]; then
  ruff_out=$("$ruff_bin" check --config "$ruff_config" "$file_path" 2>/dev/null || true)
  if [ -n "$ruff_out" ]; then
    findings="${findings}ruff (docs/CONVENTIONS.md's machine-checkable subset):\n${ruff_out}\n"
  fi
fi

new_text=$(echo "$input" | jq -r '.tool_input.new_string // .tool_input.content // empty' 2>/dev/null)
if [ -n "$new_text" ]; then
  # docs/CONVENTIONS.md: "Args:/Returns: always carry the type in parentheses"
  # - flag a param/return line, inside an Args:/Returns: block only, that
  # names something but has no (type).
  bad_doc_lines=$(echo "$new_text" | awk '
    /^[[:space:]]*(Args|Returns):[[:space:]]*$/ { in_block = 1; next }
    in_block && /^[[:space:]]*$/ { in_block = 0 }
    in_block && !/^[[:space:]]/ { in_block = 0 }
    in_block && /^[[:space:]]+[A-Za-z_][A-Za-z0-9_]*:[[:space:]]/ && !/\(/ { print NR": "$0 }
  ')
  if [ -n "$bad_doc_lines" ]; then
    findings="${findings}Args:/Returns: line(s) missing a (type) parenthetical (docs/CONVENTIONS.md's own measured gap):\n${bad_doc_lines}\n"
  fi
fi

if [ -n "$findings" ]; then
  printf 'PYTHON CONVENTIONS (advisory, %s):\n%b\n' "$file_path" "$findings" >&2
  exit 2
fi

exit 0
