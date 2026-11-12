# Decisions

Settled choices (so nobody — human or AI — re-argues them in a ticket) and open questions.
Changing a decision needs Nour and a note here. **AI agents: do not contradict these.**

## Decided

| # | Decision | Why |
|---|---|---|
| D1 | **Django 5.2 LTS with server-rendered Django templates.** | Required by the team; LTS = security fixes until April 2028. |
| D2 | **PostgreSQL in Docker Compose** (confirmed 2026-11-10). SQLite is only a fallback so tests can run without Docker. | Same database for everyone and for the lab deployment; strict types; real JSON querying; no file-locking problems on Windows Docker. |
| D3 | **Central folders:** Python in `apps/`, HTML in `templates/`, CSS/JS in `static/`, config in `config/`. | Backend and frontend work in different top-level folders, so their branches rarely touch the same file. |
| D4 | **Custom user model from day one** (`accounts.User`). | Cannot be changed cleanly after the first migration. |
| D5 | **Login required for every page by default** (`LoginRequiredMiddleware`). | Safe by default: a forgotten check cannot expose lab data. |
| D6 | **Flexible columns = real columns + one `extra_data` JSONField per model.** Confirmed fields (see `DOMAIN.md`) stay real columns. Later ticket: a "field definitions" table so admins can declare allowed extra keys (name, type, label) and forms validate/render them. | Pure JSON for everything recreates the Word-file chaos (`temp`/`Temp`/`temperature`) and loses type checks and good list tables. Separate EAV tables are slow and complex. |
| D7 | **Roles are Django groups + permissions** (Admin / Staff / Student). Views check permissions, never role names. A `setup_roles` management command (own ticket) creates them. | Native Django, one place to change who may do what. |
| D8 | **All relations are optional**: M2M `blank=True`; FK `null=True, on_delete=SET_NULL`; no `CASCADE` from one domain model to another. **Deleting a record that has relations shows a confirmation that lists what is linked and lets the user choose:** delete only this record (default, links are removed) or also delete the linked records. "Also delete" is offered **only for linked records that are not linked to anything else**. The view does this explicitly; the database never cascades. | Client: records must be creatable without relations; the user stays in control of deletions; a shared plasmid can never be deleted from under another strain. |
| D9 | **Plain CSS (design tokens as CSS variables) and plain JavaScript. Never HTMX/Alpine/React/Vue, no build step, no CDN.** Pages are server-rendered first. When a page needs dynamic content (live search, filters), plain JS calls a small **JSON endpoint** with `fetch()`. Endpoints are plain Django views returning `JsonResponse`, not Django REST Framework (revisit only if the API grows or other tools need it). | Works offline on lab PCs, nothing to install, students see exactly what happens. The JSON shape is the contract between backend and frontend (see `ARCHITECTURE.md`). |
| D10 | **Tooling:** `ruff` (lint + format, enforced in CI), `djlint` (templates, lint only). | Identical formatting for everyone prevents reformat wars and conflicts. |
| D11 | **Trunk-based Git:** short-lived `feature/SCRUM-<n>-<slug>` branches, PRs into protected `main`, 1 approval + green CI, **squash merge**. | Simplest workflow that works for five people. |
| D12 | **One short, general AI-log file per task** in `docs/ai-log/`: at most 40 lines, first name only, no pasted prompts, no private details; CI checks the format. | The course asks which AI tool was used for what and the client wants a record of AI use; separate files cannot conflict; short and general because the repository is public. |
| D13 | **Hosting: Docker Compose on the group's own hardware** (client answer). A lab computer is the baseline; a **NAS server** is being considered, and the team brings its pros and cons to the next meeting. | The group wants the database and files on its own hardware; the app is on-site only. Consequences below. |
| D14 | **Open source under AGPL-3.0-or-later; the repository becomes public in a free GitHub organisation** (see `LEAD_SETUP.md`, "Moving to the public organisation"). Per the course rules, students keep the rights to their own code and the client gets usage rights. AGPL means anyone who runs a modified version as a network service must publish their changes, which discourages closed commercial forks; it does not forbid commercial use. | Team decision 2026-11-12. The client confirmed by e-mail that open source is fine and left the choice of licence to the team. Replaces the earlier "closed source" decision. |
| D15 | **Plasmid `.dna` files stay in the lab's Hessenbox (Nextcloud) folder**, synced to the lab PCs by the Nextcloud client. The database stores the file name and the path *inside* that folder. **Under review (client e-mail):** the group would like the database and the SnapGene files on its own hardware (NAS idea); to be decided at the next meeting. | Answered in the client Q&A; avoids copying files into the app. The files folder is one configured base path (ticket W4-L2), so a move to a NAS changes a setting, not the data model. |
| D16 | **The client approved all suggested ("to verify") fields.** They are listed as approved in `DOMAIN.md`. Tickets decide when each one is built. | Client answer, relayed by Nour. |
| D17 | **Shared ownership, no frontend lead.** Nour and Lina share all of `apps/`; Eya, Zahraa and Judy share all of `templates/` and `static/`. The Jira ticket decides who edits which files. Safeguards in `docs/TEAM.md`: files claimed through tickets (no overlap), **one open migration PR per app**, shared frontend files only through their own ticket. | Team decision. Higher conflict risk than one owner per folder, so the safeguards are mandatory. |
| D18 | **Jira project key is `SCRUM`** (board in `docs/TEAM.md`). **GitHub:** squash-merge only, merged branches auto-deleted, and a ruleset "Protect main": PR required, 1 approval, conversations resolved, status checks `checks` and `docker` must pass, no force-push, no deletion. Only the lead can bypass it (a one-person team); in return the AI must ask before every push and PR (see `LEAD_SETUP.md`). A GitHub autolink turns `SCRUM-<n>` text into links to the Jira ticket. | Applied 2026-11-10; moved to the organisation 2026-11-12. |
| D19 | **The AI runs the Git delivery for the human** (branch from fresh `origin/main`, commits, push, pull request) with two human checkpoints: **"go"** on the plan and **"ship it"** on the result. The AI **asks before every push and PR, each time**: one approval covers one push. It also checks open PRs for overlap before planning, audits scope, size and freshness before asking, and watches CI after the PR. The AI never merges or closes a PR; the human clicks *Squash and merge*. Local hooks (`.githooks/`, enabled by the setup scripts) block commits and pushes on `main` on every PC. | The team are Git beginners; the client requires human-reviewed AI code; the hooks protect `main` even where GitHub does not enforce the ruleset (plan-dependent). |
| D20 | **Testing policy.** Backend work needs tests (views: login, permission, real content; JSON endpoints: exact shape; forms and models; delete choices). **No automated frontend tests**: JS unit tests and browser tools (Playwright etc.) need tooling D9 rules out. Frontend is covered by the backend view tests (they render the real template), `djlint`, and a manual checklist the human confirms. Revisit if the JavaScript grows. | Keeps the stack simple (no Node) while still catching broken templates in CI. |
| D21 | **The AI may sync a feature branch with `main`**, only when asked, as `git merge --no-commit --no-ff origin/main`, by the strict procedure in `docs/SYNC_WITH_MAIN.md`: a clean merge means zero AI edits; conflicts only inside the markers, only independent changes, only lines that already exist (checked mechanically), only after the human says yes; anything else is aborted and goes to the lead. | Beginners cannot resolve conflicts alone; every risky step has a mechanical check against invented or stray edits. |
| D22 | **Keep things centralized.** Search before creating, never copy-paste, one home per kind of thing (`docs/ARCHITECTURE.md`), a new shared piece only on the *second* need, shared homes (shared frontend files, `apps/core/`) changed only through their own ticket. | Prevents three people building three versions of the same thing, without inventing abstractions early. |
| D25 | **A Git helper menu** (`tools/git-helper.sh`, and `tools/git-helper.ps1` for Windows) covers every manual Git case of this project in plain language: explains, shows the command, asks first, refuses `main`, never force-pushes, prefixes commits with the ticket, and can run the six checks. Tested with 38 scripted cases. | Stuck beginners need one place with the answers; it enforces the team rules instead of relying on memory. |
| D24 | **The team's AI assistant is Claude Code.** The handbook and onboarding name only it, and show how to install and sign in on every system. `docs/GIT_BY_HAND.md` covers working without it. | One tool means one set of instructions that can be tested and supported. |
| D23 | **Setup and documentation support Windows, macOS and Linux**, with one install block per system in `docs/ONBOARDING.md` and the handbook. The Jira invitation is already accepted by everyone. | The team does not share one operating system. |

## What "hosting on a lab computer" means (for the later deployment ticket)

Not built yet; production settings (`config/settings/prod.py`, `requirements/prod.txt`) are ready.

- A production compose file with gunicorn and `restart: unless-stopped`.
- The lab PCs run Windows, and Docker Desktop starts when someone **logs in**, not at boot. Plan
  for the app to come back after a reboot or Windows update (auto-login, or Docker Engine in WSL2).
- Give the PC a fixed hostname or IP so the URL never changes; reachable from the lab network only.
- One PC is a single point of failure, so backups must be stored somewhere else. **Decision (client
  e-mail): backups run automatically on the server, and an admin copies them to another system by
  hand.** The copy step is written down in `docs/BACKUP.md` and checked in the weekly checklist.
- Check Docker Desktop's licence terms for the lab (free for education and small organisations;
  confirm for your case).
- **Never run `setup.sh` / `setup.ps1` on the lab server.** They create the throw-away login
  `admin` / `admin` for development PCs. The server gets its own production setup and a real
  superuser with a strong password.

## Open

- **SnapGene "click to open":** the files are in Hessenbox (D15), but a browser page cannot open a
  local file, so the click mechanism needs a short spike on a lab PC. Candidates: (a) mount the
  synced folder into the container read-only and let the app serve the `.dna` file, so a click
  downloads it and Windows opens it in SnapGene; (b) a Nextcloud share/WebDAV link; (c) a custom URL
  handler on each PC, only if SnapGene supports one. Option (a) looks best because the server PC
  can have the folder (synced, or a NAS share).
- **Claude accounts:** every teammate needs a Claude account that includes Claude Code (a paid Pro,
  Max, Team or Enterprise plan, or API/Console access). Who has what, and who pays, is not settled.
- **Backups:** automatic backups with a manual copy by an admin are decided (client e-mail). Still
  open: how often and how long to keep them (suggestion in W5-L1: nightly; 14 daily + 12 monthly).
- **NAS or lab PC for the database and the SnapGene files:** the group suggests a NAS server. The team
  prepares the pros and cons for the next meeting (can it run Docker, who maintains it, backups,
  speed, access from the lab PCs).
- **Sample data:** the client sent excerpts of the three Word files. They are real lab data, so they
  stay on team computers and **never go into this public repository**; examples in tests and docs are
  invented. A larger anonymised set (20 to 50 records) is still to be agreed.
- **Import script (bonus feature):** the client wants it, but its format and timing are to be
  discussed with them later. Low priority; ask what format the Word data can be exported in.
- **Prove the `main` ruleset is enforced** after any ruleset change, with the safe branch test in
  `LEAD_SETUP.md` (done at setup on 2026-11-12: the push was rejected). The only bypass is the lead (a
  one-person team); the lead's AI still asks before every push and PR (`AGENTS.md` §5) and the local hooks
  block pushes to `main`.
- **Jira ↔ GitHub link:** Eya (Jira site admin) installs the "GitHub for Atlassian" app and sends Nour the
  connect link; Nour (organisation owner) approves it for this repository (`LEAD_SETUP.md` §4).
