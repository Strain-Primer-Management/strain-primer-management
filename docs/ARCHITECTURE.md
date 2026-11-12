# Architecture

## Folder map

```
Strain-Primer-Management/
├── AGENTS.md  CLAUDE.md  GEMINI.md     AI rules (AGENTS.md is the real one)
├── manage.py
├── setup.sh  setup.ps1      one-command local setup (Linux/macOS/WSL · Windows)
├── config/                  LEAD-ONLY: project wiring
│   ├── settings/            base.py (shared) · dev.py · test.py · prod.py
│   └── urls.py              mounts every app: you should never need to edit it
├── apps/                    BACKEND zone: all Python
│   ├── accounts/            custom User model, login/logout URLs, user admin
│   ├── core/                home page (placeholder)
│   ├── strains/  plasmids/  primers/     one app per entity (placeholders for now)
│   └── <app>/  models.py views.py urls.py admin.py migrations/ tests/
├── templates/               FRONTEND zone: ALL HTML in one place
│   ├── base.html            the one layout every page extends
│   ├── components/          shared partials (navbar, messages, …)
│   └── <app>/               one folder per app: templates/strains/…
├── static/                  FRONTEND zone: css/ (base.css + pages/), js/ (app.js + pages/), img/
├── requirements/            base.txt · dev.txt · prod.txt (pinned versions)
├── docs/                    team + domain docs, ai-log/, tickets/ (the whole project plan, wave by wave)
├── Dockerfile  docker-compose.yml  pyproject.toml  .github/
└── data/                    only anonymised, approved sample data (never real lab data)
```

Templates and static files are **centralised on purpose** (not inside each app): backend and
frontend work in different top-level folders, so their branches almost never touch the same file.

## How one page is built (backend ↔ frontend handoff)

1. Jira has two linked tickets: a **backend** ticket (model/view/urls) and a **frontend** ticket (template/CSS).
2. Backend implements the view and writes in its docstring: the URL name and **every context
   variable** the template receives. If the ticket says so, they add a minimal `STUB` template.
   Merge this PR **first and quickly** (aim for 1–2 days) — it unblocks the frontend.
3. Frontend pulls fresh `main`, builds the template/CSS against that documented contract.
4. Need a variable that is not there? Comment on the backend ticket. Nobody edits the other zone.

## Dynamic content (live search, filters) — plain JS + a JSON endpoint

Rule of thumb: the page is **server-rendered first** and works without JavaScript (a normal
`?q=` form). Only when something must update without a reload does JavaScript step in. No HTMX,
no framework (D9).

```
Browser (templates/ + static/js/pages/*.js)            Django (apps/<app>/)
  user types in the search box
  JS waits ~300 ms, then:
  fetch("/strains/api/search/?q=recA")  ───────────▶  api.py: checks login + permission,
                                                       queries the DB, returns JsonResponse
  receives  {"count": 1, "results": [                ◀─
     {"id": 7, "strain_id": "Example-042", "url": "/strains/7/"} ]}
  JS builds the table rows with textContent / <template>
```

- **The JSON shape is the contract**, exactly like template variables are for normal pages.
  Backend documents URL name, query parameters, JSON shape and errors in the view's docstring and
  merges it first. Frontend builds the JS against that.
- Backend: a plain view returning `JsonResponse`, in `apps/<app>/api.py`, routed under `api/` in
  that app's `urls.py`. Same login and permission rules as any other view. Not Django REST
  Framework (revisit if the API grows or other tools need it).
- Frontend: the template renders `data-search-url="{% url 'strains:api_search' %}"` on the
  element, so the JS never hard-codes a URL. Writes (POST/DELETE) send the `X-CSRFToken` header.
  Insert text with `textContent` or a `<template>`, never `innerHTML` with data.

## Conventions

- **URLs:** each app has `app_name` and its own `urls.py`; templates use `{% url 'strains:index' %}`.
- **Templates:** path is `templates/<app>/<page>.html`; every page extends `base.html`.
- **Static:** `static/css/pages/<app>-<page>.css`, `static/js/pages/<app>-<page>.js` — one file
  per page keeps three frontend devs out of each other's files.
- **Settings:** values that differ per machine come from environment variables (see `.env.example`).
- **Login:** required everywhere by default; only the login page is public.
- **Database:** PostgreSQL in Docker; migrations are committed and shared (see `CONTRIBUTING.md`).

## One place for each thing

Search for the existing piece before you create one, and never copy-paste a block. Create a new
shared piece only when the same thing is needed a *second* time, and put it in its home. Changing a
shared home (shared frontend files, `apps/core/`) happens in its own small ticket, announced first.

| Thing | Its one home |
|---|---|
| Page layout (head, navigation, footer, blocks) | `templates/base.html` |
| Pieces repeated on several pages (navbar, messages, form field, pagination, table, card) | `templates/components/`, used with `{% include %}` |
| Colours, spacing, fonts | the shared design tokens in `static/css/` (never hard-coded in page CSS) |
| Look of shared components | the shared CSS (`static/css/base.css` and what it grows into) |
| Page-only styling | `static/css/pages/<app>-<page>.css` |
| Helpers several pages need (for example `fetch` with the CSRF header) | `static/js/app.js` |
| Page-only behaviour | `static/js/pages/<app>-<page>.js` |
| Field labels, help texts, choices, validators | the model or form, once (not in templates) |
| Search and filter queries | queryset or manager methods on the model (not repeated in views) |
| Helpers several apps need (mixins, template tags, shared forms and widgets, delete confirmation) | `apps/core/` |
| URL names | each app's `urls.py`, namespaced |
| Settings, secrets, per-machine values | `config/settings/` and environment variables |
| Rules and settled decisions | `AGENTS.md`, `docs/DECISIONS.md` |
| The plan: every ticket, wave by wave (context for AIs and humans) | `docs/tickets/` |
