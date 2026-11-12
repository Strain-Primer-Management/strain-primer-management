#!/usr/bin/env bash
# LEAD-ONLY FILE. Fails a pull request that changes a lead-only path when its author is not the lead.
#
# Why: AGENTS.md section 3 says only the lead edits config, Docker, CI, docs, tools... AIs are told
# not to, and CODEOWNERS makes the lead's approval mandatory, but a clear red check right away is
# kinder than a silent "waiting for review" days later. This is the fast, friendly layer.
#
# Usage (CI passes these; see .github/workflows/ci.yml):
#   PR_AUTHOR=<github login> ALLOWED_AUTHORS="Nour833 dependabot[bot]" \
#     .github/scripts/check_lead_only.sh <base-sha> <head-sha>
#
# KEEP IN SYNC with: AGENTS.md section 3 ("Lead-only" row) and .github/CODEOWNERS.
set -euo pipefail

base="${1:?base sha missing}"
head="${2:?head sha missing}"
author="${PR_AUTHOR:-}"
allowed="${ALLOWED_AUTHORS:-}"

# Lead (and Dependabot, whose PRs the lead reviews) may change anything here.
for who in $allowed; do
  if [ "$author" = "$who" ]; then
    echo "Author '$author' is allowed to change lead-only files. Nothing to check."
    exit 0
  fi
done

# Lead-only paths (anchored regular expressions on the repository-relative path).
lead_only='^(config/|requirements/|\.github/|\.githooks/|docs/|data/|tools/|Dockerfile$|docker-compose\.yml$|pyproject\.toml$|manage\.py$|setup\.sh$|setup\.ps1$|\.gitignore$|\.gitattributes$|\.editorconfig$|\.dockerignore$|\.env\.example$|AGENTS\.md$|CLAUDE\.md$|GEMINI\.md$|CONTRIBUTING\.md$|README\.md$|LICENSE$|SECURITY\.md$)'

# The only exception: a NEW file in docs/ai-log/ (every developer adds their own log per task).
# Status A = added. Editing or deleting an existing log is still lead-only.
violations=()
while IFS=$'\t' read -r status path; do
  [ -n "$path" ] || continue
  if [[ "$path" =~ $lead_only ]]; then
    if [ "$status" = "A" ] && [[ "$path" == docs/ai-log/* ]]; then
      continue
    fi
    violations+=("$path")
  fi
done < <(git diff --name-status --no-renames "$base...$head")

if [ "${#violations[@]}" -eq 0 ]; then
  echo "OK: no lead-only files changed."
  exit 0
fi

echo "This pull request changes files that only the lead may change:"
for path in "${violations[@]}"; do
  echo "::error file=${path}::Lead-only file. Remove this change from your pull request."
  echo "  - $path"
done
cat <<'EOF'

What to do:
  1. Undo your change to those files (they must look exactly like they do on main).
     Ask your AI assistant: "Restore these lead-only files to the version on origin/main and show me the diff."
  2. If you really need a change there, write a short comment on your Jira ticket for Nour saying
     which file and what you need. Nour makes the change in a separate pull request.
See AGENTS.md section 3 and docs/TEAM.md.
EOF
exit 1
