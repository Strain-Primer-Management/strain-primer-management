# How we work

Five people, one repo, no conflicts. The rules are few; they matter.

## The 7 rules

1. **One Jira ticket = one branch = one pull request.** Keep it small (ideally under a day or two).
2. **Stay in your zone** (`docs/TEAM.md`). Need something from another zone? Ask on Jira. Never edit their files.
3. **Never push to `main`.** Everything goes through a pull request.
4. **Sync with `main` every day** (see below). Old branches are where conflicts come from.
5. **Never force-push** and never rewrite pushed history. Not you, not your AI.
6. **You are responsible for every line**, including AI-written ones. If you can't explain it, don't open the PR.
7. **Stuck or unsure? Ask early.** Five minutes of asking beats an hour of untangling.

## Daily flow

### With your AI (the normal way): you only say who you are and which ticket

1. Open your AI in the project folder and paste the starter message from `docs/PROMPTING_GUIDE.md`
   (your name plus the ticket text from Jira).
2. The AI proposes a plan and the exact files it will touch. Compare them with the ticket, then
   say **go**.
3. It creates the branch, does the work, runs the checks and commits on your PC only.
4. It shows you what changed. **Look at it** (ask it to explain anything you don't understand),
   then say **ship it**. Nothing leaves your PC before that, and the AI asks again before every later push.
5. It pushes the branch and opens the pull request. Ask a teammate to review (`docs/TEAM.md`).
6. **You** click **Squash and merge** on GitHub once it has one approval and green CI, then move the
   Jira ticket to Done. The AI never merges or closes a PR.

### By hand (no Claude Code, or it can't reach Git). Easiest: run the menu `bash tools/git-helper.sh` (Windows: `tools\git-helper.ps1`). More cases: `docs/GIT_BY_HAND.md`

```bash
# 1. Start from fresh main
git switch main
git pull --ff-only                     # fast-forward only: can never create a mess
git switch -c feature/SCRUM-12-strain-list-view

# 2. Work (with your AI: see docs/PROMPTING_GUIDE.md). Run the app: docker compose up

# 3. Check, then commit ONLY your files
docker compose exec web python manage.py test        # + the other checks in README
git status                                           # are these exactly the files you meant to change?
git add path/to/file1 path/to/file2                  # never `git add .`
git commit -m "SCRUM-12: Add strain list view"

# 4. Push and open a pull request on GitHub
git push -u origin feature/SCRUM-12-strain-list-view
```

- **Branch:** `feature/SCRUM-<n>-<short-slug>` (bug fixes: `fix/SCRUM-<n>-<slug>`). The Jira key makes
  Jira link the branch and PR automatically.
- **Commit message:** `SCRUM-<n>: <imperative summary>`. **PR title:** `SCRUM-<n> <summary>`.
- **Why the key matters:** GitHub knows nothing about Jira. Once the Jira app is connected, *Jira*
  scans branch names, commit messages and PR titles for `SCRUM-<n>` and attaches them to that ticket.
  Write it exactly like that, with a real ticket number. Without the app the naming still keeps the
  history searchable.
- **Pull request:** the template is filled in (by your AI, or by you), a teammate reviews
  (`docs/TEAM.md`), CI is green and there is one approval. Then the **author** clicks **Squash and
  merge** (the only allowed merge); GitHub deletes the branch by itself. Move the Jira ticket to Done.
- **Safety net:** the setup scripts enable local hooks that block `git commit` and `git push` directly
  on `main`, on every PC.

## Staying up to date with `main` (do this daily, and before opening a PR)

```bash
git fetch origin
git merge origin/main
```

Conflict? Don't panic and don't guess:

1. `git status` lists the conflicted files. **If one is outside your zone or you didn't edit it, stop and ask.**
2. Open each file; keep the intent of **both** sides (never delete the other person's lines just to make it go away).
3. Run the tests, then `git add <file>` and `git commit`.
4. Want to start over? `git merge --abort` puts everything back exactly as it was.

Your AI handles Git for you, but it only touches conflicts when you ask ("my PR has conflicts,
help me update from main"). Read its result line by line.

## Migrations — the #1 danger in Django teams

Two people changing models at the same time create two migrations with the same number. Prevent it:

- Only **backend** people create migrations, only for **their own app**, one per ticket:
  `docker compose exec web python manage.py makemigrations strains -n add_strain_model`
- Commit the migration file in the same PR as the model change.
- **Never edit, rename or delete a migration that is already on `main`.** Need to change a model
  again? Make a *new* migration.
- **Never hand-merge migrations.** CI fails with "conflicting migrations" if two collide.
- Model PRs follow the dependency order **primers → plasmids → strains** and are merged quickly.
- **Only one open migration PR per app at a time.** Nour and Lina share every app, so before you
  start a model change, check the board and ask in chat: if the other one has an open migration in
  the same app, wait for it to merge (or agree to build both changes in one ticket).

**After you pull migrations that someone else created:** the app applies migrations only when it *starts*,
so restart it: `docker compose restart web` (helper: option 14, a). **If the team reset or squashed the
migrations** (old files deleted, a new initial file), your old local database no longer matches: the app
may refuse to start, or run with a stale database and no warning. Everyone then resets their own local
database: `docker compose down -v`, then run the setup script again (it recreates `admin` / `admin`), or
helper option 14, d. Whoever resets the migrations must announce it in the team chat first.

**CI says "Conflicting migrations detected" (or `migrate` complains) — recovery:**

```bash
git fetch origin && git merge origin/main
git diff --name-only origin/main -- "*/migrations/*"      # these are YOUR new migration files
# delete ONLY those files (they are yours and not on main), then regenerate:
docker compose exec web python manage.py makemigrations <app> -n <same_name>
docker compose down -v && docker compose up -d             # reset your local DB so it matches
git add <the new migration> && git commit -m "SCRUM-12: Regenerate migration after merging main"
```

## Backend ↔ frontend handoff

See `docs/ARCHITECTURE.md`. In short: backend merges the view first and documents the URL name and
every template variable in the view's docstring; frontend builds on top of that. A missing
variable is a comment on the backend ticket, not an edit to `apps/`. For live content (search,
filters) the contract is a documented JSON endpoint that plain JS calls with `fetch()`; no HTMX.

## Review checklist (reviewer)

- Only files the ticket needs? Nothing from another zone slipped in?
- No reformatting noise, no deleted code that the ticket didn't mention?
- Backend: one new migration at most, tests added, relations optional, no `CASCADE` between domain models.
- Frontend: no inline styles/scripts, no hard-coded URLs, CSRF token in forms, works without JS.
- Can the author explain every change? Is there an AI-log entry if AI was used?
- Start with the PR's **Reviewer guide**: it points to the riskiest places. Then check CI is green.
- Nothing copy-pasted: shared pieces are reused from their one home (`docs/ARCHITECTURE.md`, "One place
  for each thing"), not duplicated.

## Working with AI (summary)

The team works with **Claude Code**, which reads `AGENTS.md` automatically (through `CLAUDE.md`). Brief
it with the template in `docs/PROMPTING_GUIDE.md`, **review its diff yourself**, and make sure a log file
is added in `docs/ai-log/` (short and general, see `docs/ai-log/README.md`). No Claude Code, or it cannot reach Git? Use
`docs/GIT_BY_HAND.md`.

AI tools are never credited as author or co-author: no `Co-authored-by:` trailer and no "Generated with" line
in commits or PRs (the hook and CI enforce it). AI use is disclosed in the AI log.

## License

The project is open source under **AGPL-3.0-or-later** (see `LICENSE`). By opening a pull request you
agree that your contribution is released under the same license. Never commit real lab data, secrets or
personal data: the repository is public.

**Outside contributions:** this is a graded course project, so pull requests from people outside the
team are not accepted for now. Security reports go through `SECURITY.md`.
