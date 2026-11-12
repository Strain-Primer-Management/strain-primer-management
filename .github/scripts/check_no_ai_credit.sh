#!/bin/sh
# LEAD-ONLY FILE. Fails when text credits an AI tool as author or co-author. Rule: AGENTS.md section 5.
# The human is the author. AI use is disclosed in docs/ai-log/, never through authorship.
#
#   ... | sh .github/scripts/check_no_ai_credit.sh          commit messages, PR title and body
#   ... | sh .github/scripts/check_no_ai_credit.sh ident    "Name <e-mail>" lines (commit authors)
# Used by the commit-msg hook and by CI on every pull request. Dependabot is not an AI tool.

AI='claude|anthropic|copilot|openai|chatgpt|gpt-[0-9]|gemini|cursor|codex|devin|aider|codeium|tabnine|windsurf'
input=$(cat)
if [ "$1" = ident ]; then
  hits=$(printf '%s\n' "$input" | grep -i -E "$AI")
else
  hits=$(printf '%s\n' "$input" | grep -i -E \
    -e "^[[:space:]]*(co-authored-by|signed-off-by|reviewed-by|generated-by|assisted-by)[[:space:]]*:.*($AI)" \
    -e '🤖' -e "generated (with|by) .*($AI)")
fi
[ -z "$hits" ] && exit 0
echo "Blocked: an AI tool is credited as author or co-author. Nobody but the human is credited" >&2
echo "(no Co-authored-by trailer, no 'Generated with' line, no AI author). Remove it and try again:" >&2
printf '%s\n' "$hits" | head -3 | cut -c1-100 | sed 's/^/  /' >&2
exit 1
