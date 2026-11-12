## Jira ticket

SCRUM-

## What and why (2–3 sentences)

## Scope

- [ ] **Backend** (`apps/**`)
- [ ] **Frontend** (`templates/**`, `static/**`)
- [ ] **Lead-only files** (needs Nour's approval)
- [ ] I changed **only** the files this ticket needs; nothing from another zone

## Checks (run in Docker, see README)

- [ ] `check`, `makemigrations --check --dry-run`, `test`, `ruff check`, `ruff format --check`, `djlint --lint` all pass
- [ ] Migrations: none / one new (`apps/<app>/migrations/____`), no existing migration edited
- [ ] UI change: screenshot attached

## AI usage

- [ ] No AI used
- [ ] AI used; log file added in `docs/ai-log/`
- [ ] I read and can explain every line of this PR

## Reviewer guide (the AI fills this in)

The 2–4 places that most need human eyes, and what was deliberately left alone.

## Notes for the reviewer / needs from other zones
