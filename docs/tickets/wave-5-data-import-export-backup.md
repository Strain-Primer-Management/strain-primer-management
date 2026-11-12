# Wave 5: data in, data out, and never losing data

Create these when the schema (wave 1) and the record pages (wave 2) are merged. This wave is where the
client's real value sits: their data currently lives in Word files, and a lab database that can lose data
is worse than Word.

Conventions for the whole wave
- Real lab data is NEVER committed to Git, put in tests, pasted into prompts or shown in screenshots.
  The client's sample file (after the professor allows it) lives in `data/sample/` ONLY if the client says
  it may; otherwise tests use fake files with the same shape.
- Import is a command first (safe, repeatable, testable). A web upload page may come later, only if the client asks.
- Everything that changes many records at once has a DRY-RUN mode that changes nothing and prints a report.
- Backups are the lead's responsibility (Docker, schedule, storage); the Django side only provides commands.
- Import format is not final until the client answers the questions in wave 0 (L-6, question 6).
  Tickets marked WAITING must not start before the lead records the answer.

---

# LEAD

## W5-L1: Backup and restore setup (lead only)

```text
Summary: Backups: schedule, storage, retention and a restore drill
Zone: Lead
Depends on: client answers about backups (ticket L-6, question 5), Management commands to back up and restore the database
Files allowed (optional): docker-compose.yml, tools/, docs/BACKUP.md (new), docs/DECISIONS.md, .env.example

In plain words (for beginners)
A backup is a copy of the whole database kept somewhere else. The rule of thumb: a backup you have never restored is only a hope. So this ticket ends with a REAL restore test on a clean machine.

What
- Decide with the client: how often (suggestion: every night), how long we keep them (suggestion: 14 daily + 12 monthly). The client has already decided the rest: the backup runs automatically on the server, and an admin copies it to another system by hand.
- A script in tools/ (works on the lab PC: Windows with Docker) that calls the backup command from W5-B3, names the file with the date, writes it to the backup folder on the server and deletes old ones by the retention rule.
- A scheduled task (Windows Task Scheduler, or cron on Linux) that runs it, with the exact steps in docs/BACKUP.md and a screenshot checklist for the person who sets it up.
- docs/BACKUP.md: how to restore, step by step, with copy-paste commands, for someone who has never done it. It also describes the admin's manual copy to another system: who does it, how often, and how to check it worked.
- THE RESTORE DRILL: on a different computer, take last night's backup, restore it, log in, and check that the record counts match. Write the date and result in docs/BACKUP.md.

Acceptance criteria
- [ ] A backup runs by itself at the scheduled time and appears in the server's backup folder; the manual copy to another system is documented and was done once in the drill.
- [ ] Old backups are removed by the retention rule (tested with fake dates).
- [ ] The restore drill succeeded and is recorded.
- [ ] Failure is noticed: the script writes a log and the checklist says who looks at it weekly.
```

---

# BACKEND

## W5-B1: Import command (WAITING for the client's file format)

```text
Summary: Import command for strains, plasmids and primers (CSV)
Zone: Backend
Depends on: Database schema v1, Agree the import format with the client and write it down, Sequence helper functions: reverse complement, GC content, cleaning
Files allowed (optional): apps/core/management/commands/import_data.py (SHARED: announce first), apps/core/importing.py, apps/core/tests/, apps/core/tests/fixtures/

In plain words (for beginners)
The lab's data is in Word tables today. Somebody exports them to CSV (a plain text table that Excel and Python both read). This command reads the CSV files and creates the records, and the links between them. It must be safe to run twice: running it again updates existing records instead of making duplicates.

What
- `python manage.py import_data --strains strains.csv --plasmids plasmids.csv --primers primers.csv [--dry-run]`
- Each row is validated with the SAME form/model rules as the website (never a second set of rules): wrong rows are collected into a report, good rows are still imported (unless `--strict`, which imports nothing when any row is wrong).
- Match existing records by their ID (case-insensitive): found = update, not found = create. Counts of created / updated / skipped are printed.
- Links by ID columns (for example a strain row lists its plasmid names separated by `;`; a plasmid row lists primers with orientation). A link to an ID that does not exist is a reported error, not a crash and not a silently created empty record.
- The whole import runs in one database transaction: a crash halfway leaves nothing half-imported.
- `--dry-run`: does everything, rolls back, prints the report.
- The report: a text file next to the input (`import-report-<date>.txt`) listing row number, ID, and the problem in plain English.
- Sets created_by/updated_by to a configured "import" user (created if missing), so it is visible in the audit fields.
- UTF-8 (with or without BOM) and both comma and semicolon separators (Excel in Germany uses semicolons).

Acceptance criteria
- [ ] Tests with small FAKE CSV files: clean import; dry-run changes nothing; re-import updates not duplicates; bad rows reported; unknown link target reported; transaction rolls back on failure; semicolon file; BOM file; capital letters in IDs.
- [ ] No real data in the repository.
- [ ] Six checks green.
Out of scope: web upload page, Word (.docx) parsing.
```

## W5-B2: Export (CSV, JSON, full export)

```text
Summary: Export lists as CSV and everything as one download
Zone: Backend (shared helper in apps/core: announce first)
Depends on: Search and filter methods (wave 3), Roles and permissions
Files allowed (optional): apps/core/export.py, apps/strains/views.py, apps/plasmids/views.py, apps/primers/views.py, apps/strains/urls.py, apps/plasmids/urls.py, apps/primers/urls.py, tests

In plain words (for beginners)
People want their data out: for a paper, for Excel, for safety. Two things: (1) "download this list as CSV", respecting the current search and filters, and (2) one button for admins that downloads everything.

What
- `<app>:export_csv` (GET): the CURRENT filtered list as CSV, all rows (not just page 1), UTF-8 with BOM (so German Excel shows umlauts correctly), semicolon-safe quoting. Columns = the list columns plus all fields and the audit dates. `extra_data` is written as one JSON text column.
- `core:export_all` (GET, admins only, permission-based): a zip with the three CSV files plus a JSON dump with all the links.
- Needs a specific permission (for example `strains.export_strain`); whether Students get it is a client question (L-6 question 9). Default: staff and admin only.
- Uses streaming (StreamingHttpResponse) so a big table does not fill memory.
- Cells that start with `=`, `+`, `-` or `@` are prefixed with an apostrophe (protects Excel users from formula injection).

Contract for the frontend
- Context on list pages: `export_url` (with the current query string) or None when not allowed.

Acceptance criteria
- [ ] Tests: filtered export contains only the matches; permission check; BOM present; formula-injection cells escaped; zip contains the expected files; JSON links correct.
- [ ] Six checks green.
```

## W5-B3: Backup and restore commands

```text
Summary: Management commands to back up and restore the database
Zone: Backend (command in apps/core: SHARED, announce first)
Depends on: Database schema v1
Files allowed (optional): apps/core/management/commands/backup_db.py, apps/core/management/commands/restore_db.py, apps/core/tests/

In plain words (for beginners)
These are the two buttons the lead's script (W5-L1) presses. A command is a program you run with `python manage.py <name>`. `pg_dump` is PostgreSQL's own tool that writes the database to a file; we just call it correctly and safely.

What
- `backup_db --output <folder>`: runs pg_dump (custom format, compressed) using the database settings, writes `strain-db-YYYY-MM-DD-HHMM.dump`, prints the file name and size, exits with an error code if anything failed. The database password is passed through the environment, NEVER on the command line and never printed.
- `restore_db <file> --yes-really`: refuses to run without the flag, and refuses when DEBUG is off unless a second flag `--production` is given; shows what database it will overwrite and asks to type its name.
- The Docker image must contain the postgres client tools (this needs a Dockerfile change: a LEAD ticket W5-L3; until then tests mock the subprocess).
- Tests mock the subprocess and assert the exact command line; one slow test (marked) runs a real dump and restore only when pg_dump exists.

Acceptance criteria
- [ ] Tests: arguments, file naming, failure exit code, password not in the printed output, restore refuses without the flags.
- [ ] Six checks green.
```

## W5-B4: Extra fields (flexible columns) management

```text
Summary: Extra fields: definitions and forms for the flexible columns (extra_data)
Zone: Backend (new model = migration: follow the migration rules)
Depends on: Database schema v1, Strain/Plasmid/Primer pages, decision D6
Files allowed (optional): apps/core/ (SHARED: models, forms), apps/*/forms.py, apps/*/migrations/ (ONE app's migration only), tests

In plain words (for beginners)
The client said "we want the database to be flexible in the columns". Every record has an `extra_data` box (JSON) for extra attributes. But a JSON box is useless if nobody knows which keys exist or what they mean. So admins DEFINE extra fields ("Gel band size", a number, for primers) and the forms then show them as normal inputs. No new database column is ever needed.

What
- A model `ExtraFieldDefinition`: applies_to (strain / plasmid / primer), key (short, letters/digits/underscore, unique per kind, never changed after creation), label, type (text, number, yes/no, date, one-of-list), choices (for one-of-list), required (False by default), help_text, order, active. Follows the project model rules (audited, no `choices=` on growing lists).
- Forms: for each active definition of the kind, add a field to the create/edit form and store the value under `extra_data[key]`. Existing records without the key stay valid.
- Deactivating a definition hides the field but NEVER deletes stored values.
- Validation by the field type; wrong value -> a normal form error.
- Admin screen to manage the definitions (Django admin is fine for version 1).

Contract for the frontend
- Forms: extra fields appear as ordinary `form` fields named `extra__<key>`, in order, after the fixed fields. Detail pages get `extra_values` (list of label + value).

Acceptance criteria
- [ ] Tests: each type validates; saving stores the key; editing a record without the key works; deactivate hides but keeps; duplicate key rejected; key format enforced.
- [ ] Exactly one new migration file, in ONE app, announced to the other backend developer first.
- [ ] Six checks green.
```

## W5-B5: Change history (audit log)

```text
Summary: Change history: who changed what and when
Zone: Backend (migration: follow the migration rules)
Depends on: Strain/Plasmid/Primer pages, Delete with a choice
Files allowed (optional): apps/core/ (SHARED: model, signals or mixin, views, tests), apps/core/migrations/

In plain words (for beginners)
The created_by / updated_by columns tell you who touched a record LAST. A change history keeps EVERY change: "Anna changed freezer location from F2 to F5 on 3 May". Labs need this when something goes missing or a value looks wrong. We write it ourselves in a few lines (no extra package, per the project rules).

What
- A model `ChangeLogEntry`: what kind of record, its id, a text label (so it stays readable after deletion), who, when, action (created / changed / deleted / linked / unlinked) and a small JSON with the changed fields {name: [old, new]}. Never stores passwords or personal data beyond the username.
- Recorded in the shared view mixins (create/update/delete/link views), not with hidden magic, so it is easy to read and to test. Import and the Django admin are covered too (document how).
- A page `core:history` (admins and staff): newest first, filter by record kind, user and date, paginated.
- A per-record "History" section on the detail page context: `history` (last 20 entries).
- Entries are never editable or deletable through the website.

Contract for the frontend
- `history_entries`: list of {when, who, action, summary, changes}. The summary text is built by the backend in English.

Acceptance criteria
- [ ] Tests: create/update/delete/link each produce one entry with the right fields; unchanged save produces none; deleted record's history survives; no secrets in entries; permissions.
- [ ] Six checks green.
```

## W5-B6: Data quality report

```text
Summary: Data quality report: find records that need attention
Zone: Backend
Depends on: Strain/Plasmid/Primer pages, Sequence helpers
Files allowed (optional): apps/core/ (SHARED: view, checks module, tests)

In plain words (for beginners)
After importing old Word data there will be gaps and oddities. This page lists them so the lab can clean up: it is a to-do list for the data, not an error screen.

What
- URL name `core:data_quality`, for users with the change permission. Sections, each with a count and links to the records:
  - primers without a freezer location; plasmids without a size; strains without a host organism;
  - primers whose stored length or Tm does not match the sequence (should be impossible, but import can bypass forms);
  - sequences with letters that are not allowed;
  - records that are not linked to anything (informational only, since standalone records are allowed);
  - possible duplicates (same sequence, or same name ignoring spaces and capitals).
- Every check is a small function in one module, easy to add to.
- Read-only: it never changes data.

Contract for the frontend
- `sections`: list of {title, description, count, items (record label + url)}.

Acceptance criteria
- [ ] Tests: each check finds its planted case and ignores clean records; a user without permission gets 403.
- [ ] Six checks green.
```

## W5-B7: Sample data as test fixtures (only if allowed by the client)

```text
Summary: Anonymised client sample records as development data
Zone: Lead (data) + Backend (loader)
Depends on: client permission and sample file (ticket L-6, question 6), Import command
Files allowed (optional): data/sample/ (lead only), apps/core/management/commands/ (extend the fake data command)

In plain words (for beginners)
Fake data is easy but unrealistic. If the client allows 20 to 50 anonymised real records, we can test the import and the pages against real shapes and real mess (typos, odd units, empty cells).

What
- The lead stores the anonymised file in data/sample/ ONLY after written permission from the client and checking that it contains no personal or confidential data.
- The fake-data command gets `--sample` to load it via the import command.
- Tests that need realistic shapes use a tiny fake copy with the same columns.

Acceptance criteria
- [ ] Permission recorded in docs/DECISIONS.md. If the answer is no, this ticket is closed without work.
```

---

# LEAD (infrastructure for this wave)

## W5-L2: Agree the import format with the client

```text
Summary: Agree the import format with the client and write it down
Zone: Lead
Depends on: client answers (ticket L-6, question 6)
Files allowed (optional): docs/DOMAIN.md, docs/IMPORT_FORMAT.md (new)

In plain words (for beginners)
Before anybody writes the import code, we need an exact description of the file: which columns, in which order, what a cell may contain. We write that description first and let the client confirm it.

What
- One table per record kind: column header, meaning, required or optional, example (fake), allowed values.
- How links are written (for example "pUC19;pET28a").
- Which separator and encoding to expect; how empty cells and "n/a" are treated.
- A tiny example file for each kind, with fake data, in docs/.
- The client confirms by reply or in the demo.

Acceptance criteria
- [ ] docs/IMPORT_FORMAT.md exists, the client confirmed it, W5-B1 is updated with any differences.
```

## W5-L3: Postgres tools in the Docker image

```text
Summary: Add the PostgreSQL client tools to the web image
Zone: Lead
Depends on: nothing
Files allowed (optional): Dockerfile, .github/workflows/ci.yml (only if the image test needs it), docs/ARCHITECTURE.md

What
- Install the postgresql-client package matching the database version (16) in the web image so pg_dump and pg_restore exist inside the container.
- The docker CI job still builds and starts the stack.
Acceptance criteria
- [ ] `docker compose exec web pg_dump --version` prints version 16.
- [ ] CI is green.
```

---

# FRONTEND

## W5-F-MAIN: Import, export, history and data pages (parent ticket)

```text
Summary: Export buttons, history, extra fields and data quality pages (parent)
Zone: Frontend

In plain words (for beginners)
Most of this wave is behind the scenes, but a few parts need pages: buttons to download data, a history list, a list of data problems, and the extra fields inside the forms.

Sub-tasks
  1. W5-F1 Export buttons on the list pages and the "download everything" page
  2. W5-F2 Extra fields in the forms and detail pages
  3. W5-F3 History section on detail pages and the global history page
  4. W5-F4 Data quality page

Things to take care of
- Everything from the earlier frontend rules still applies.
- Buttons for actions the user is not allowed to do are not shown.
- Wording is plain English a lab person understands ("Download as CSV (opens in Excel)").
```

## W5-F1: Export buttons

```text
Summary: Export buttons on the lists and the download-everything page
Zone: Frontend
Depends on: Export (backend), Shared list layout
Files allowed (optional): templates/components/ (the list header: SHARED, announce first), templates/core/export.html, static/css/pages/core-export.css

What
- "Download as CSV" button next to the filters on the three lists (uses `export_url`; says "includes all N results, not only this page").
- A small page for admins: "Download everything" with a short explanation of what is in the zip and a warning that it contains all lab data.
Acceptance criteria
- [ ] States: allowed, not allowed (no button), zero results (button disabled with a reason).
```

## W5-F2: Extra fields in forms and details

```text
Summary: Extra fields in the forms and on the detail pages
Zone: Frontend
Depends on: Extra fields (backend), Form and feedback components
Files allowed (optional): templates/*/form.html, templates/*/detail.html, templates/components/form_field.html (SHARED: only if it needs a change)

What
- Extra fields render through the SAME field component as fixed ones (no special markup), under a heading "Additional information".
- Detail pages list `extra_values` as label/value rows; empty values are hidden.
Acceptance criteria
- [ ] States: no extra fields defined (no heading shown), several types, validation errors.
```

## W5-F3: History UI

```text
Summary: History section on detail pages and the global history page
Zone: Frontend
Depends on: Change history (backend)
Files allowed (optional): templates/components/history_list.html (SHARED), templates/core/history.html, static/css/pages/core-history.css

What
- Component listing entries (who, when in a readable form, action word, summary, a collapsible "details" with old -> new values), used on the three detail pages.
- Global history page with the filter form (kind, user, date range) and pagination.
Acceptance criteria
- [ ] States: no history, many entries (pagination), deleted record entries; keyboard use.
```

## W5-F4: Data quality page

```text
Summary: Data quality page
Zone: Frontend
Depends on: Data quality report (backend)
Files allowed (optional): templates/core/data_quality.html, static/css/pages/core-data-quality.css

What
- One card per section with a count badge, a short plain-language description, and the list of records (links); sections with count 0 show a friendly "Nothing to fix" line; long lists collapse.
Acceptance criteria
- [ ] States: all clean, some problems, many problems (collapsing).
```
