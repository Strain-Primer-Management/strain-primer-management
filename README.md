# Strain & Primer Management

Central, web-based database for a synthetic-biology lab: **strains, plasmids and primers**, linked
to each other, with search, validated input, user roles and backups. Replaces the lab's scattered
Word files. University internship project.

**Stack:** Python 3.12 · Django 5.2 LTS (server-rendered templates) · PostgreSQL · Docker Compose.

> **Team members and AI assistants: read [`CONTRIBUTING.md`](CONTRIBUTING.md) first. AI tools
> read [`AGENTS.md`](AGENTS.md).**
>
> **New to the team? Follow [`docs/ONBOARDING.md`](docs/ONBOARDING.md) step by step, or read the
> printable [`docs/TEAM_HANDBOOK.pdf`](docs/TEAM_HANDBOOK.pdf): setup plus how to do your job.**

## Quick start (about 5 minutes)

1. Install **Git**, **Docker** (Docker Desktop on Windows and macOS; Docker Engine plus the compose
   plugin on Linux), the **GitHub CLI** (`gh`) and **Claude Code**. The exact commands for **Windows, macOS and Linux**
   are in [`docs/ONBOARDING.md`](docs/ONBOARDING.md). Install the *EditorConfig* extension in your editor.
2. Clone and run the setup script. It checks your tools, builds and starts everything, waits until
   the app answers, and creates a local dev login:

   ```bash
   git clone https://github.com/Strain-Primer-Management/strain-primer-management.git
   cd strain-primer-management
   bash setup.sh                  # Linux / macOS / WSL / Git Bash
   ```

   Windows PowerShell: `powershell -ExecutionPolicy Bypass -File .\setup.ps1`

3. Open <http://localhost:8000> and log in with **`admin` / `admin`** (local development only; your
   database lives only on your PC and is not shared with anyone).

**You do not install Python, Django or PostgreSQL.** They all run inside Docker; the database,
its user and its password are created automatically. The only things to install by hand are
**Git** and **Docker Desktop**. No `.env` file is needed. Edit code normally; the server reloads
by itself. The script is safe to run again whenever something looks broken.

Prefer to do it by hand? `docker compose up --build`, then
`docker compose exec web python manage.py createsuperuser`.

## Everyday commands

| Task | Command |
|---|---|
| Start (background) / stop | `docker compose up -d` / `docker compose down` |
| Rebuild after `requirements/` changed | `docker compose up --build` |
| Follow logs | `docker compose logs -f web` |
| Create migrations (backend, own app only) | `docker compose exec web python manage.py makemigrations <app> -n <name>` |
| Django shell | `docker compose exec web python manage.py shell` |
| SQL shell | `docker compose exec db psql -U spm` |
| **Check everything** (run before every PR) | see below |
| **Reset my local database** | `docker compose down -v` then `docker compose up` |
| **Stuck with Git?** | `bash tools/git-helper.sh` (Windows: `powershell -ExecutionPolicy Bypass -File tools\git-helper.ps1`): a menu that explains and asks first |

Before every pull request (all must pass; CI runs the same):

```bash
docker compose exec web python manage.py check
docker compose exec web python manage.py makemigrations --check --dry-run
docker compose exec web python manage.py test
docker compose exec web ruff check .
docker compose exec web ruff format --check .
docker compose exec web djlint templates --lint
```

Switched to a branch with different migrations and Django complains? Reset your local DB (last
row of the table). Your local data is disposable.

## Run it, test it, review a teammate's branch

The setup script is for the **first time** and for repairs. Day to day you only need these:

| Situation | What to do |
|---|---|
| First time, or something is broken | `bash setup.sh` or `setup.ps1` (safe to repeat) |
| Start working | `docker compose up -d`, then open <http://localhost:8000> |
| Try your change by hand | Save the file and refresh the browser (it reloads by itself). Errors: `docker compose logs -f web` |
| Run all automated tests | `docker compose exec web python manage.py test` (uses a separate test database; your dev data is safe) |
| Run the tests of one app | `docker compose exec web python manage.py test apps.strains` |
| You pulled new code with **new migrations** | `docker compose restart web` (migrations are applied on start) |
| You pulled new code that changed `requirements/` | `docker compose up -d --build` |
| Review a teammate's PR on your PC | Commit your own work first, then `git fetch origin`, `git switch <their-branch>`, `docker compose restart web`. Afterwards `git switch main`. If their migrations differ from yours, reset your DB (row below) |
| Start over with an empty database | `docker compose down -v`, then `docker compose up -d` (or run the setup script: it also recreates `admin` / `admin`) |
| The team **reset or squashed the migrations** (app will not start, or migration errors) | Same as the row above: reset your own local database. Announce a migration reset in the team chat first |
| Stop | `docker compose down` |

Every pull request is also tested automatically by GitHub (the `checks` job runs the same checks as
the list above).

## Troubleshooting

- **`port is already allocated` on 8000:** something else uses the port. Stop it, or change the
  `8000` before the last colon in `"127.0.0.1:8000:8000"` in your own checkout only (don't commit that).
- **`.ps1` scripts are blocked on Windows:** use the `powershell -ExecutionPolicy Bypass -File .\setup.ps1` form.
- **First start is slow:** the first build downloads a few hundred MB. Later starts take seconds.
- **`exec ... no such file or directory` or odd characters in files (Windows):** line endings.
  The repo forces LF via `.gitattributes`; re-clone, or run `git add --renormalize .` and ask the lead.
- **`Cannot connect to the Docker daemon`:** start Docker Desktop.
- **Files created by Docker are owned by root (Linux):** put your IDs into `.env` (see `.env.example`).

## Map

`apps/` Python (backend) · `templates/` HTML and `static/` CSS/JS (frontend) · `config/` settings ·
`docs/` documentation. Details: [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md). Data model and client
requirements: [`docs/DOMAIN.md`](docs/DOMAIN.md). Who owns what: [`docs/TEAM.md`](docs/TEAM.md).

## License

Open source under the **GNU Affero General Public License v3.0 or later** (`LICENSE`). In short: you may
use, study and change the code, but anyone who runs a modified version as a network service must publish
their changes under the same license. Copyright (C) 2026 the authors of this project (the student team).

This is a graded course project: pull requests from outside the team are not accepted for now. Security
reports: see `SECURITY.md`.
