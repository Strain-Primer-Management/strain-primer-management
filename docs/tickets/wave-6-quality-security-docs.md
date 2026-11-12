# Wave 6: quality, security, accessibility and documentation

These tickets run ALONGSIDE waves 2 to 5 (the earlier you do them, the cheaper they are) and must be
finished before wave 7 (go-live). Many of them are reviews: someone looks at the whole project with one
topic in mind, writes down findings, and each finding becomes a small fix ticket.

Conventions for the whole wave
- A review ticket ends with a short written result in the pull request (or in a docs file, lead only) and a
  list of follow-up tickets. It does not change code except for its own tests/docs.
- A finding is small, or it gets its own ticket. Nobody fixes "while they are there" (rule: surgical edits).
- Security findings that are serious are told to the lead privately in the team chat, not in a public ticket.

---

# BACKEND

## W6-B1: Permission matrix tests

```text
Summary: Permission matrix tests: who can do what, on every page
Zone: Backend
Depends on: Roles and permissions, wave 2 pages merged
Files allowed (optional): apps/core/tests/test_permission_matrix.py (SHARED: announce first)

In plain words (for beginners)
We promised three roles (Student, Staff, Admin) and "not logged in = nothing". A matrix test checks every page for every role in one table, so a future change that accidentally opens a page fails loudly in CI.

What
- A table in the test file: URL name x role -> expected result (200, 302 to login, 403).
- Loops over every named URL of the project (a test fails if a new URL is added without a row, so nobody can forget).
- Covers: anonymous, pending (not yet approved) user, Student, Staff, Admin, deactivated user.
Acceptance criteria
- [ ] All current URLs are in the table; adding a URL without a row makes the test fail with a clear message.
- [ ] Six checks green.
```

## W6-B2: Security review and hardening

```text
Summary: Security review of the project and fix list
Zone: Backend (review) with the lead (config changes are lead-only)
Depends on: waves 2 and 3 merged
Files allowed (optional): none for the review itself; findings become tickets

In plain words (for beginners)
We check the usual web mistakes one by one. Each check below has an expected answer; anything different becomes a ticket.

Checklist (tick each, or write the problem)
- Django's own check: run `manage.py check --deploy` with the production settings and read every warning.
- Login required everywhere except login, register, password reset pages (list them).
- Every POST form has a CSRF token; no view is exempt (search for csrf_exempt: should be zero results).
- Cross-site scripting: no `|safe`, no `mark_safe` on user text, no innerHTML with data (search the repo).
- SQL injection: no raw SQL or string-built queries with user input (search for `.raw(`, `.extra(`, `cursor.execute`).
- File access: the SnapGene file view cannot read outside its folder (try `../` by hand).
- Redirects: the login `next` parameter only allows our own addresses.
- Sessions: lifetime decided (for example 12 hours), cookies are HttpOnly, and Secure/SameSite are set for production.
- Passwords: Django's validators on, minimum length decided, the dev admin/admin account does NOT exist in production.
- Error pages: DEBUG off in production, a custom 403/404/500 page shows no technical details.
- Secrets: SECRET_KEY and the database password come from the environment, none is in Git history (run a secret scan over the history).
- Dependencies: pip audit (or GitHub Dependabot alerts) shows no known serious problems.
- Rate limiting of login attempts: see W6-L1.
Acceptance criteria
- [ ] Every line of the checklist has a result in the pull request; each failure has a ticket.
```

## W6-B3: Error handling and logging

```text
Summary: Friendly error pages and useful logs
Zone: Backend (settings parts are lead-only: ask via ticket W6-L2)
Depends on: wave 2 merged
Files allowed (optional): apps/core/views.py, apps/core/tests/ (SHARED: announce first)

In plain words (for beginners)
When something breaks, a lab user should see a calm page that says what to do, and the team should find the cause in a log, without ever showing technical details to the user.

What
- Views for 400, 403, 404 and 500 (names and the 500 handler as Django expects), using the 403, 404 and 500 templates from wave 1 and a minimal stub for the new 400 page (the frontend ticket "Complete the error pages" fills it in).
- The 500 view must not depend on the database (it must work even when the database is down).
- Log one line per unexpected error with the request path, the username and the error (never passwords, never POST data).
Contract for the frontend
- Templates `403.html`, `404.html` and `500.html` already exist (wave 1); `400.html` is created by backend as a minimal STUB (new file only) and completed by the frontend.
Acceptance criteria
- [ ] Tests: each error status renders its template with the right status code; the 500 page works with the database connection closed.
```

## W6-B4: Test coverage review

```text
Summary: Test coverage review: find and close the gaps
Zone: Backend
Depends on: waves 2 and 3 merged
Files allowed (optional): apps/*/tests/ (new test files only)

In plain words (for beginners)
"Coverage" shows which lines of our code no test ever runs. We do not chase 100 percent; we look for important code (permissions, delete behaviour, validation, import) with no test.

What
- Run the tests with coverage in the container (the tool is installed only for this check, NOT added to requirements without a lead decision; use a temporary install inside the container).
- List files under 80 percent; for the important ones write the missing tests (new files only, never edit others' tests).
- Write the list of what is deliberately not tested and why.
Acceptance criteria
- [ ] Permissions, delete choice, forms, import and export each have tests for their error paths.
- [ ] The summary table is in the pull request.
```

## W6-B5: Performance test with realistic size

```text
Summary: Performance test with a large data set
Zone: Backend
Depends on: Search performance and indexes (wave 3)
Files allowed (optional): apps/core/tests/ (a slow-test file), the large fake-data command

What
- With the large data set (5000 strains, 2000 plasmids, 5000 primers, with links): measure list pages, detail pages, search, export and the dashboard; write the numbers in the pull request.
- Any page over 500 ms or over 30 database queries becomes a ticket.
Acceptance criteria
- [ ] Table of timings and query counts; every slow item has a follow-up ticket or an explanation.
```

---

# LEAD

## W6-L1: Login attempt limiting (decision, then maybe a package)

```text
Summary: Limit repeated failed logins
Zone: Lead (decision) then Backend
Depends on: Login page (wave 1)
Files allowed (optional): docs/DECISIONS.md, requirements/, config/settings/, apps/accounts/

In plain words (for beginners)
Without a limit, a person (or program) can try thousands of passwords. Inside a lab network the risk is small but real. Options: (a) do nothing, because the app is on the internal network only, (b) a small in-house counter, (c) a package such as django-axes. Packages need the lead's approval.

What
- The lead decides and records the choice with the reason in docs/DECISIONS.md.
- If (b) or (c): a ticket with tests (5 wrong tries -> locked for 15 minutes, a message on the login page, the admin can unlock).
Acceptance criteria
- [ ] Decision written. If implemented: tests for lock, unlock and message.
```

## W6-L2: Production settings review

```text
Summary: Production settings review (HTTPS flags, hosts, sessions, logging)
Zone: Lead
Depends on: Security review
Files allowed (optional): config/settings/prod.py, config/settings/base.py, .env.example, docs/DECISIONS.md

What
- Go through the output of `manage.py check --deploy` and the security review; set ALLOWED_HOSTS from the environment, session lifetime, cookie flags (Secure only if HTTPS is used: see W7-L2), CSRF trusted origins, logging to a file and the console, static file serving.
- Document each setting and its reason in a comment.
Acceptance criteria
- [ ] `manage.py check --deploy` has no warnings that are not explained in docs/DECISIONS.md.
```

## W6-L3: Dependency and base image updates

```text
Summary: Keep dependencies and Docker images up to date
Zone: Lead
Depends on: nothing (repeat every month)
Files allowed (optional): requirements/, Dockerfile, docker-compose.yml, .github/dependabot.yml

What
- Review the Dependabot pull requests (one per package, small); read the changelog for breaking changes; merge only when CI is green.
- Check Django 5.2 security releases monthly; update within a week for security fixes.
- Update the postgres and python base images to the newest patch versions.
Acceptance criteria
- [ ] A short note per month in docs/DECISIONS.md or the pull request: what was updated, what was skipped and why.
```

## W6-L4: CI improvements

```text
Summary: CI improvements (speed, extra checks, required docker job)
Zone: Lead
Depends on: CI has run at least 10 times
Files allowed (optional): .github/workflows/ci.yml, docs/LEAD_SETUP.md

What
- Pip and Docker layer caching if the checks take more than 3 minutes.
- (The "lead-only files" guard already exists: `.github/scripts/check_lead_only.sh`, a step of the `checks` job. Keep its path list in sync with AGENTS.md section 3 whenever the lead-only list changes.)
- Optional: a check that the migrations folder has no more than one new migration per app per pull request.
- Make the `docker` job required (also in wave 0 ticket L-4).
Acceptance criteria
- [ ] Each change proven on a test pull request; the average CI time is written down before and after.
```

## W6-L5: Compile the AI log for the supervisor

```text
Summary: Compile the AI usage log for the course supervisor
Zone: Lead
Depends on: about half of the project done, then again at the end
Files allowed (optional): docs/ai-log/ (read), docs/AI_USAGE_SUMMARY.md (new)

In plain words (for beginners)
The client allows AI code if it is documented and human-reviewed. Every ticket already has its own log file. The supervisor wants the overview: how much AI was used, for what, and how it was reviewed.

What
- Read all files in docs/ai-log/ and summarise: number of tickets, kinds of tasks, tools used, typical problems found in review, what was changed by humans.
- A one-page summary with a table (ticket, person, what the AI did, reviewer, result).
Acceptance criteria
- [ ] The summary exists, is accurate (spot-check 5 log files), and was shown to the supervisor.
```

## W6-L6: Centralization refactor pass

```text
Summary: Centralization pass: find and remove duplicates
Zone: Lead (with one backend and one frontend dev)
Depends on: waves 2 and 3 merged
Files allowed (optional): split into small tickets, one per duplicate found

In plain words (for beginners)
Our rule is "one place for each thing". After a few weeks, copies creep in anyway. This ticket is a hunt: find each copy, and make a SMALL ticket to move it to its home.

What
- Search for repeated template blocks, repeated CSS values (colours, spacings not using tokens), repeated JS helpers, repeated queryset code in views, repeated labels or choices in several files.
- One ticket per duplicate, each tiny (the shared-piece rule: announced to the team).
Acceptance criteria
- [ ] A list of what was found and the tickets created; no big-bang refactor.
```

---

# FRONTEND

## W6-F1: Accessibility audit

```text
Summary: Accessibility audit of every page
Zone: Frontend
Depends on: wave 2 merged (re-check after wave 3 and 5)
Files allowed (optional): none for the audit; findings become tickets

In plain words (for beginners)
Accessibility means people who use only the keyboard, a screen reader, a big font or poor eyesight can use the site. It also makes the site better for everyone. We check every page against a short list.

Checklist per page (tick in a table: page x item)
- Everything works with the keyboard only; the Tab order follows the visual order; focus is always visible.
- Every input has a label; errors are described in text and linked to the field (aria-describedby).
- Headings in order (one h1, then h2...); landmarks (header, nav, main, footer); "skip to content" link.
- Colour contrast at least 4.5:1 for text (check with the browser's tools); information is never shown by colour alone.
- Images have alt text (decorative ones empty alt); icon-only buttons have an accessible name.
- Zoom to 200 percent without losing content; no horizontal scroll at 1280 px width.
- Tables have header cells and a caption or accessible name.
- Messages that appear without a page load use aria-live.
Acceptance criteria
- [ ] The completed table is in the pull request; every failure has a ticket.
```

## W6-F2: Complete the error pages (400 and database-free 500)

```text
Summary: Complete the error pages: add 400 and make 500 independent of the database
Zone: Frontend
Depends on: Error pages 403, 404, 500 (wave 1), Friendly error pages and useful logs (backend)
Files allowed (optional): templates/400.html, templates/500.html, static/css/pages/errors.css (and small fixes to the wave 1 403/404 pages if the review finds problems)

In plain words (for beginners)
Wave 1 already created the 403, 404 and 500 pages. This ticket does NOT redo them: it adds the missing 400 page and checks all four against the rules below, fixing only what is wrong.

What
- Calm and short: what happened, what to do (go to the home page, search, contact the admin), a link home.
- 403 explains "you do not have permission; ask an admin if you need it" and does not reveal which permission.
- 500 must not use anything that needs the database (no menus that load data, no username), and no technical details.
Acceptance criteria
- [ ] Screenshots of the four pages; the 500 page still renders when the database is stopped (the backend's test covers the status; check visually).
```

## W6-F3: Cross-browser and screen check

```text
Summary: Manual check in Chrome, Edge and Firefox at three screen sizes
Zone: Frontend (a team task, share the work)
Depends on: waves 2 to 5 pages merged
Files allowed (optional): none; findings become tickets

In plain words (for beginners)
The lab uses Windows PCs with Chrome, Edge and Firefox. Pages can look different between them. We open every page in all three and write down differences.

What
- Pages: login, register, home, the three lists, the three details, the three forms, delete confirmation, search results, approvals, error pages.
- Browsers: Chrome, Edge, Firefox (latest version). Sizes: 1920, 1366 (a common lab laptop), 800 pixels wide.
- Check: layout, fonts, forms, date and number inputs, print preview, copy button, live search.
Acceptance criteria
- [ ] A table (page x browser) with ok or a screenshot of the problem; each problem is a ticket.
```

## W6-F4: Frontend polish pass

```text
Summary: Frontend polish pass: spacing, wording, consistency
Zone: Frontend
Depends on: Manual check in Chrome, Edge and Firefox at three screen sizes
Files allowed (optional): decided by the ticket list; split into small tickets

What
- One person reads every page like a new user: wording consistent (Create / Edit / Delete / Cancel), same capitalisation, same button order and colours, same empty states, no placeholder text left, favicon and page titles set.
- Findings are tiny tickets, each its own pull request.
Acceptance criteria
- [ ] The list of findings is done or ticketed.
```

---

# DOCUMENTATION (lead with help from everyone)

## W6-D1: User manual (English, with screenshots)

```text
Summary: User manual for lab members
Zone: Lead (writing) with Frontend (screenshots)
Depends on: waves 2 to 5 merged
Files allowed (optional): docs/USER_MANUAL.md (new), docs/img/ (new, fake data only)

In plain words (for beginners)
The people who will use the tool are biologists, not programmers. They need short instructions with pictures: how to sign up, how to find a strain, how to add one, how to link a plasmid, how to export.

What
- Sections: first login and sign-up; finding things (search and filters); adding and editing a record; linking records; deleting safely; opening a plasmid in SnapGene; downloading data; what the roles mean; who to ask for help.
- Every screenshot uses FAKE data. Plain sentences, no jargon.
- Review by one person who has not seen the tool before (they follow it and write down where they got stuck).
Acceptance criteria
- [ ] A newcomer completed "add a strain with a plasmid" using only the manual.
```

## W6-D2: Admin manual

```text
Summary: Admin manual: approving users, extra fields, backups, updates
Zone: Lead
Depends on: waves 2 to 5 merged
Files allowed (optional): docs/ADMIN_MANUAL.md (new)

What
- Approving or rejecting sign-ups; changing a role; deactivating a person who left the lab; resetting a password; defining extra fields; reading the history; running and checking backups (link to docs/BACKUP.md); updating the app (link to the update guide, W7-L4); what to do if the app does not start.
Acceptance criteria
- [ ] A lab admin followed it for three tasks without help.
```

## W6-D3: Developer documentation refresh

```text
Summary: Refresh developer documentation to match the real code
Zone: Lead
Depends on: waves 2 to 5 merged
Files allowed (optional): docs/ARCHITECTURE.md, docs/DOMAIN.md, docs/DECISIONS.md, README.md, CONTRIBUTING.md

What
- Folder map, URL list, model diagram, the JSON endpoint contracts, the list of settings and environment variables, the decisions made along the way.
- Remove anything that no longer matches (ask: is this still true?).
Acceptance criteria
- [ ] A new developer can set up, run the tests and find any file using only the docs.
```

## W6-D4: Final report for the course

```text
Summary: Final project report
Zone: Team (lead coordinates)
Depends on: wave 7 mostly done
Files allowed (optional): docs/FINAL_REPORT.md (new)

What
- Goals and client requirements and how each was met; architecture in one page; the workflow with AI (rules, logs, what worked and what did not); testing; deployment; what remains open; lessons learned. Each member writes the part about their own work.
Acceptance criteria
- [ ] Reviewed by the supervisor before the deadline.
```
