#!/bin/sh
# LEAD-ONLY FILE. Reads a unified diff on stdin and fails if an ADDED line looks like a secret or key.
# The repository is public, so anything pushed is permanent. E-mail addresses are NOT checked
# (lead decision: team members may use their personal e-mail).
#
# One script, two users, so the rules cannot drift apart:
#   - the local pre-commit hook:  git diff --cached ... | sh .github/scripts/check_sensitive.sh
#   - CI on every pull request:   git diff <base>...<head> ... | sh .github/scripts/check_sensitive.sh
#
# Domain words, titles and first names are never flagged.
# A real false alarm: the lead adjusts the patterns below in a lead-only change.

added=$(grep -E '^\+' | grep -v -E '^\+\+\+' | sed 's/^+//')

secrets=$(printf '%s\n' "$added" | grep -n -E -e '-----BEGIN [A-Z ]*PRIVATE KEY-----' \
  -e 'ghp_[A-Za-z0-9]{30,}' -e 'github_pat_[A-Za-z0-9_]{30,}' -e 'AKIA[0-9A-Z]{16}' \
  -e 'xox[baprs]-[A-Za-z0-9-]{10,}' -e 'sk-[A-Za-z0-9]{20,}' | head -3)

if [ -z "$secrets" ]; then
  exit 0
fi

echo "Blocked: the added lines contain something that looks private. The repository is public," >&2
echo "and anything pushed is permanent." >&2
echo "Looks like a secret or key (only the line number is shown):" >&2
echo "$secrets" | cut -d: -f1 | sed 's/^/  line /' >&2
echo "Remove it and commit again. A real false alarm? Ask the lead." >&2
exit 1
