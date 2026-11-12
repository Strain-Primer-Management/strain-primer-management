#!/usr/bin/env bash
# LEAD-ONLY FILE. Fails a pull request when an AI-log entry is not short and general.
#
# Why: the repository is public. Entries in docs/ai-log/ must stay a short record of how AI was used,
# without pasted prompts, other people's names, links, e-mail addresses or secrets (docs/ai-log/README.md).
#
# Usage (CI passes these; see .github/workflows/ci.yml):
#   .github/scripts/check_ai_log.sh <base-sha> <head-sha>
#
# KEEP IN SYNC with: docs/ai-log/_TEMPLATE.md and AGENTS.md section 11.
set -euo pipefail

base="${1:?base sha missing}"
head="${2:?head sha missing}"

max_lines=40
max_line_length=200
name_re='^docs/ai-log/[0-9]{4}-[0-9]{2}-[0-9]{2}_SCRUM-[0-9]+_[a-z0-9_-]+\.md$'
headings=("## What was asked" "## What the AI did" "## What a human checked" "## Follow-ups")

problems=()
checked=0

while IFS=$'\t' read -r status path; do
  [ -n "$path" ] || continue
  [ "$status" != "D" ] || continue
  case "$path" in
    docs/ai-log/README.md|docs/ai-log/_TEMPLATE.md) continue ;;
    docs/ai-log/*) ;;
    *) continue ;;
  esac
  checked=$((checked + 1))
  content="$(git show "$head:$path")"

  if ! [[ "$path" =~ $name_re ]]; then
    problems+=("$path: the name must look like YYYY-MM-DD_SCRUM-<n>_<firstname>.md (lowercase).")
  fi
  lines="$(printf '%s\n' "$content" | wc -l)"
  if [ "$lines" -gt "$max_lines" ]; then
    problems+=("$path: $lines lines; the maximum is $max_lines. Shorten it.")
  fi
  if printf '%s\n' "$content" | awk -v m="$max_line_length" 'length($0) > m { found = 1 } END { exit !found }'; then
    problems+=("$path: a line is longer than $max_line_length characters. Use short bullets.")
  fi
  for h in "${headings[@]}"; do
    if ! printf '%s\n' "$content" | grep -qxF "$h"; then
      problems+=("$path: the heading '$h' is missing (copy docs/ai-log/_TEMPLATE.md).")
    fi
  done
  if ! printf '%s\n' "$content" | grep -qE '^- \*\*Developer:\*\* [A-Za-z-]+$'; then
    problems+=("$path: the Developer line must contain your first name only.")
  fi
  if printf '%s\n' "$content" | grep -qE '[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}'; then
    problems+=("$path: remove the e-mail address.")
  fi
  if printf '%s\n' "$content" | grep -qiE 'https?://|www\.'; then
    problems+=("$path: remove the link. Say the PR number instead (#12).")
  fi
  if printf '%s\n' "$content" | grep -qiE 'password[[:space:]]*[=:]|api[ _-]?key|secret[ _-]?key|BEGIN [A-Z ]*PRIVATE KEY'; then
    problems+=("$path: remove anything that looks like a password or key.")
  fi
done < <(git diff --name-status --no-renames "$base...$head" -- docs/ai-log)

if [ "${#problems[@]}" -eq 0 ]; then
  echo "OK: $checked AI-log entr$([ "$checked" -eq 1 ] && echo y || echo ies) checked."
  exit 0
fi

echo "The AI log must be short and general (the repository is public). Please fix:" >&2
for p in "${problems[@]}"; do echo "  - $p" >&2; done
echo "Rules: docs/ai-log/README.md" >&2
exit 1
