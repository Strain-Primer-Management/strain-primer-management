# Briefing your AI assistant

Your AI does the Git work for you: it creates the branch, commits, pushes and opens the pull
request. You give it two things: **who you are** and **the ticket**. Start every session with this:

```text
Read AGENTS.md completely and follow it strictly.

I am <your name>.
Ticket: SCRUM-<n> — <title>
<paste the ticket from Jira: description and acceptance criteria (and "Files allowed" if it has them)>

Give me your plan and the exact files you will touch, and wait for my "go".
```

That is enough. The AI cannot read Jira, so the pasted ticket text matters: the number alone
tells it nothing. It looks up your role in `docs/TEAM.md`, takes the files from the ticket (or
proposes them if the ticket has none), and handles the branch name, commits and pull request.

## Your two checkpoints (you stay in control)

1. **"go"** — after you read its plan. Check that the files it lists match the ticket. If it wants
   to touch something else, say no.
2. **"ship it"** — after you look at what changed. Ask *"explain the changes in plain language"* if
   anything is unclear. Nothing leaves your PC (no push, no pull request) before you say this. One
   "ship it" covers one push: the AI asks again before every later push (review fixes, conflict merges).

After that it opens the pull request and gives you the link. A teammate reviews it, and **you** click
**Squash and merge** on GitHub when it is approved. The AI never merges or closes pull requests.

## Examples

**Backend** — *"I am Lina. Ticket SCRUM-21 — Add the Primer model: <paste>. Give me your plan and
files, wait for my go."* (Expected files: `apps/primers/models.py`, `apps/primers/admin.py`, one
new migration, `apps/primers/tests/`. No views, forms or templates.)

**Frontend** — *"I am Zahraa. Ticket SCRUM-34 — Strain list page: <paste>. Give me your plan and
files, wait for my go."* (Expected: `templates/strains/index.html` and
`static/css/pages/strains-list.css`. It reads the view's docstring for the template variables and
tells you if one is missing.)

## While it works

- Ask it to **explain** anything you don't understand. If you can't explain it, you can't submit it.
- Watch for scope creep: "I also fixed…", "while I was there…". Answer *"Revert that, it's out of
  scope."*
- Long or confusing session? Start a **fresh** one with the starter message. Short sessions behave better.

## Looking at the changes before "ship it"

The easiest way: open the project in VS Code and look at the **Source Control** tab (the branch
icon in the left bar): every changed file and line is listed. Or ask the AI to run `git status` and
`git diff`. Check that only files from the plan changed and nothing was deleted by surprise.

## Afterwards

| What happened | What you tell the AI |
|---|---|
| A reviewer left comments | *"Address the review comments on my PR."* It fixes them on the same branch and pushes. |
| GitHub says the PR has conflicts | *"My PR has conflicts, help me update from main."* Git does the merge. If nothing conflicts, the AI edits nothing. For a real conflict it shows you both sides, resolves only inside the conflict markers using lines that already exist, and waits for your yes. It stops and asks the lead for migrations, files outside your ticket, or when both sides changed the same line (`docs/SYNC_WITH_MAIN.md`). |
| The PR is merged | Nothing. Start a new session with the starter message for your next ticket. |

## No `gh`, or no Claude Code?

- **`gh` (GitHub CLI) not installed or not logged in:** **Claude Code** pushes the branch and gives you a
  link plus the title and text to paste into the pull request form. Install it from
  `docs/ONBOARDING.md` to skip that step.
- **Claude Code cannot reach Git, or you work without it:** do the Git steps yourself with
  `docs/GIT_BY_HAND.md` (ready-made commands for every case).

## Never paste into an AI

Passwords, `.env` contents, API keys, real lab data (strain lists, sequences from the client).
Use fake examples like `Example-042` and `P-017`.

## Log it

The AI adds `docs/ai-log/YYYY-MM-DD_SCRUM-<n>_<firstname>.md` from `docs/ai-log/_TEMPLATE.md` to your
branch by itself. The repository is public, so the entry is **short and general**: what was asked in
one or two sentences, what the AI did, what you checked. Check that it is there and that it contains
no pasted prompts, names other than your first name, links or private details. CI checks the format.
