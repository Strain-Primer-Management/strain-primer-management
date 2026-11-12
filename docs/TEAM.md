# Team, zones and ownership

**This file is the source of truth for "who may edit what".** AI agents read it to know what their
user may change. Edit it when the team agrees on a change, and tell everyone.

## People

| Person | GitHub | Role | Zone |
|---|---|---|---|
| Nour | `Nour833` | Backend; also maintains the lead-only files (config, Docker, CI, docs) | Backend + lead-only |
| Lina | `linamrayeh-sudo` | Backend | Backend (also backup reviewer for frontend) |
| Eya | `eya-bm` | Frontend | Frontend |
| Zahraa | `Zhayraa101` | Frontend | Frontend |
| Judy | `JudyW12` | Frontend | Frontend |

There is no frontend lead. Links: Jira board (project key **SCRUM**; the link is pinned in the team chat) ·
GitHub <https://github.com/Strain-Primer-Management/strain-primer-management>

## Zones

```
apps/**                        BACKEND    Nour + Lina share ALL apps (accounts, core, strains, plasmids, primers)
templates/**  static/**        FRONTEND   Eya + Zahraa + Judy share ALL frontend files
config/** requirements/** Docker* setup.* .github/** docs/** data/** root files     LEAD-ONLY (Nour)
```

## Nobody owns a folder alone, so the Jira ticket is the owner

Because several people share the same folders, conflicts are prevented by **process**. These four
rules replace "one owner per folder". They matter more than anything else in this file.

1. **Claim files through the ticket.** A ticket may list its "Files allowed". Most will not, and
   that is normal: the file list approved at Claude Code's "go" is the claim, and the assignee posts
   it as a one-line Jira comment. Before you start, look at the tickets in *In Progress* and
   *In Review*, and let Claude Code check the open pull requests: if anything touches the same file,
   one of you waits, or you re-split the tickets. Only the assignee edits those files while the
   ticket is open.
2. **One open migration PR per app.** If a PR with a migration for `strains` is open, nobody else
   starts a migration for `strains` until it is merged. Different apps can go in parallel.
   (Order for the model tickets: primers → plasmids → strains.)
3. **One page = one set of files, and one person at a time.** Page files are
   `templates/<app>/<page>.html`, `static/css/pages/<app>-<page>.css`,
   `static/js/pages/<app>-<page>.js`. Two people never work on the same page at once.
4. **Shared frontend files** (`templates/base.html`, `templates/components/**`,
   `static/css/base.css`, `static/js/app.js`) change only in their **own small ticket** (one
   purpose, e.g. "add table component"). Announce it in the team chat before you start, merge it
   fast, and everyone else pulls `main` before touching related pages. **Shared backend code**
   (`apps/core/**`, helpers used by several apps) works the same way: its own small ticket, announced
   to the other backend dev first.

## Reviews

- Backend PRs: reviewed by the **other backend dev** (Nour ↔ Lina).
- Frontend PRs: reviewed by **a frontend dev who is not the author** (any of the other two). Nour or Lina step in as backup reviewers when the frontend devs are away.
- PRs touching a lead-only file: need Nour's approval (if Nour wrote it, Lina reviews).
- Cross-zone PRs: need a reviewer from each zone.
- Reviewers use the checklist in `CONTRIBUTING.md`. "I don't understand this code" is a valid
  reason to request changes, because the client will ask the team to explain it.

## Decisions and questions

- Quick questions: team chat. Anything that changes scope, data model or architecture: a Jira
  comment on the ticket, then (if settled) a line in `docs/DECISIONS.md` by Nour.
- Need a change from another zone? Comment on **their** Jira ticket or create a linked one. Do not
  edit their files.
