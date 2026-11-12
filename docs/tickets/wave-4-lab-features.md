# Wave 4: lab features (what makes this tool useful for biologists)

Create these when wave 2 is merged. Tickets here are independent of each other unless a "Depends on" line
says otherwise, so they can be picked up in any order. Priority order for the client: SnapGene link first,
then the data-entry helpers (they prevent wrong data), then the nice-to-haves.

Conventions for the whole wave
- Biology rules come from docs/DOMAIN.md and docs/DECISIONS.md. If a rule is not written there (for example
  the melting-temperature formula), the ticket is BLOCKED until the lead records the client's answer
  (wave 0, ticket L-6). Never invent biology.
- Sequences are stored as plain uppercase letters (A, C, G, T; more letters only if the client says so).
- Pure helper functions (no database, no web) are easiest to test and are written once in `apps/core/`
  (SHARED: announce first) when two apps need them.
- Never write real lab data into tests or screenshots. Use obviously fake data (`Example-042`).

---

# LEAD AND SPIKE

## W4-L1: SnapGene spike on a lab computer (lead + client)

```text
Summary: SnapGene spike: can the browser open a .dna file on a lab PC?
Zone: Lead (with the client)
Depends on: client answers to the SnapGene and Hessenbox questions (ticket L-6)

In plain words (for beginners)
SnapGene is the program biologists use to look at plasmid maps. The client wants one click in our website to open a plasmid file in SnapGene. Browsers are strict about opening local programs, so we first TRY the possible ways on a real lab PC before anyone builds anything. A "spike" is a short experiment that ends with a decision, not with finished code.

What
Try on one lab PC (Windows, SnapGene installed, Hessenbox folder synced) and write down what works:
1. Plain download: the website serves the .dna file as a download; the browser opens it with SnapGene (file type association).
2. A link to the synced file path (file:// links are usually blocked from web pages: confirm).
3. A custom link scheme if SnapGene offers one (check SnapGene documentation).
4. A link to the file in the Hessenbox/Nextcloud web page.
Record per option: works yes/no, number of clicks, what the user sees, any security warning.

Output
- Decision in docs/DECISIONS.md (lead pull request): which option we build, and what the database must store (a path relative to a folder, or a full link).
- The hessenbox_path field format (what a valid value looks like) is written into docs/DOMAIN.md.

Acceptance criteria
- [ ] Tested on at least one real lab PC with the client's help.
- [ ] A decision is written; W4-B1 and W4-F1 can be updated with it.
```

---

# BACKEND

## W4-B1: Open plasmid in SnapGene (backend)

```text
Summary: Serve or link plasmid files so SnapGene can open them
Zone: Backend (the mounted folder in docker-compose.yml is a LEAD change: see W4-L2)
Depends on: SnapGene spike (decision), Plasmid pages (backend)
Files allowed (optional): apps/plasmids/ (views, urls, tests)

In plain words (for beginners)
Depending on the spike's decision, either (a) our server hands the .dna file to the browser as a download, or (b) the page just shows a link. This ticket is written for option (a), the most likely one; adjust it after the spike.

What (option a)
- URL name `plasmids:snapgene_file` (GET only, login required, permission plasmids.view_plasmid).
- Reads the file named by the plasmid's `sequence_file`/`hessenbox_path` from ONE configured base folder (setting name defined by the lead in W4-L2). Nothing outside that folder can ever be read:
  - reject absolute paths, `..`, and symbolic links that leave the folder;
  - only allow the extensions the client uses (.dna, .gb, .fa ...), defined once as a constant.
- Sends the file with Django's FileResponse as an attachment with a safe file name; a missing file shows a friendly 404 page, not a crash.
- Never logs file contents.

Contract for the frontend
- Plasmid detail context gets `snapgene_url` (the address above) or None when the plasmid has no file.

Acceptance criteria
- [ ] Tests: file served for a valid name; `../` and absolute path rejected; missing file -> 404; no permission -> 403; no file set -> `snapgene_url` is None.
- [ ] Reviewer guide in the pull request names the path-safety code as the place needing most attention.
- [ ] Six checks green.
Out of scope: Docker volume, template.
```

## W4-B2: Sequence helpers (shared backend)

```text
Summary: Sequence helper functions: reverse complement, GC content, cleaning
Zone: Backend (SHARED: apps/core, announce first)
Depends on: Database schema v1 (and the client's answer about Tm formula and allowed letters, for the two marked items)
Files allowed (optional): apps/core/sequence.py, apps/core/tests/test_sequence.py

In plain words (for beginners)
DNA is written as a string of the letters A, C, G and T. Biologists constantly need small calculations on those strings. We write them as plain Python functions with clear tests, once, so models, forms and pages all use the same ones.

What (each a small, pure function with a docstring)
- clean_sequence(text): uppercase, remove spaces/newlines/digits, remove 5'- and -3' markers; raise a clear error for letters that are not allowed.
- reverse_complement(seq): A<->T, C<->G, reversed.
- gc_content(seq): percentage of G and C (rounded to 1 decimal).
- melting_temperature(seq): ONLY after the client confirms the formula (a function with the chosen formula named in its docstring).
- format_blocks(seq, size=10): "ACGTACGTAC GTACGTACGT ..." for display.
Acceptance criteria
- [ ] Unit tests with hand-checked values (write the calculation in a comment next to each test); wrong letters raise the expected error; empty input handled.
- [ ] The existing models/forms are NOT changed in this ticket (a follow-up small ticket switches them to these helpers if they have their own copies).
- [ ] Six checks green.
```

## W4-B3: Duplicate and near-duplicate warnings

```text
Summary: Warn about duplicate IDs and duplicate sequences when saving
Zone: Backend
Depends on: Primer pages, Plasmid pages, Strain pages, Sequence helpers
Files allowed (optional): apps/primers/forms.py, apps/plasmids/forms.py, apps/strains/forms.py, tests

In plain words (for beginners)
Two people entering the same primer twice is the most common data problem in a lab database. Identical IDs are already blocked (that is a hard rule, any capitalisation). Two DIFFERENT IDs with the SAME sequence is allowed but suspicious, so we show a warning with a link to the existing record and let the person continue.

What
- On the primer form: if another primer has the same cleaned sequence, show a non-blocking warning ("Primer P-017 has the same sequence") naming the records, with links.
- The user can still save (an explicit tick box "Save anyway").
- Same idea for plasmids with the same name ignoring spaces and capitals ("pUC19" vs "puc 19").
Contract for the frontend
- Form context: `duplicate_warnings` (list of: message, record label, record url) and the field `confirm_duplicate`.
Acceptance criteria
- [ ] Tests: warning shown, can save with confirmation, cannot save without it, no warning for unique data, own record not counted when editing.
- [ ] Six checks green.
```

## W4-B4: Strain lineage data

```text
Summary: Strain lineage: ancestors and descendants
Zone: Backend
Depends on: Strain pages (backend)
Files allowed (optional): apps/strains/ (models methods, views, tests)

In plain words (for beginners)
"Lineage" is the family tree of a strain: its parent, grandparent, and so on, and the strains made from it. The strain page already shows the direct parent and children; this ticket adds the full chain, safely (a data mistake must never freeze the page in an endless loop).

What
- Methods `ancestors()` and `descendants()` (lists, with the depth number), written with a loop and a visited-set so a cycle in bad data stops cleanly; limit depth to 20.
- Detail view context: `ancestors` (nearest first) and `descendants` (tree order with depth).
- No new database columns (uses the existing parent link).
Contract for the frontend
- `ancestors`: list of {strain, depth}. `descendants`: list of {strain, depth}.
Acceptance criteria
- [ ] Tests: chain of 3, branching children, no parent/no children, a deliberate loop does not hang, query count stays small (use assertNumQueries).
- [ ] Six checks green.
```

## W4-B5: Suggestions for fields (datalists)

```text
Summary: Suggestion lists for free-text fields (host organism, medium, location, markers)
Zone: Backend (the helper in apps/core is SHARED: announce first)
Depends on: Strain pages, Plasmid pages, Primer pages
Files allowed (optional): apps/core/, apps/strains/forms.py, apps/plasmids/forms.py, apps/primers/forms.py, tests

In plain words (for beginners)
Fields like "host organism" are free text (so scientists are never blocked), but typing "E.coli", "E. coli" and "Escherichia coli" for the same thing makes searching messy. A suggestion list (an HTML <datalist>) offers the values already used, so people usually pick an existing one. This is decision D-permissive-database + strict-forms in practice: we guide, we do not block.

What
- One shared helper that returns the distinct existing values of a field, most used first, limited to 50.
- Used by the forms for: host_organism, culturing_medium, biosafety_level, freezer_location (strains/primers), resistance_markers (plasmids), purpose (primers, together with the fixed starter list from the client).
- The form exposes them as `suggestions` for each field.
Acceptance criteria
- [ ] Tests: ordering by use, empty database gives an empty list, a value typed outside the list still saves.
- [ ] Query count tested (one query per field at most).
- [ ] Six checks green.
```

---

# LEAD

## W4-L2: Mount the SnapGene folder (lead only)

```text
Summary: Mount the Hessenbox/SnapGene folder into the web container (read-only)
Zone: Lead
Depends on: SnapGene spike (decision)
Files allowed (optional): docker-compose.yml, .env.example, config/settings/base.py, docs/DECISIONS.md, docs/ONBOARDING.md

In plain words (for beginners)
The website runs inside a Docker container that cannot see the computer's folders unless we say so. We "mount" the plasmid-file folder into the container as read-only, so the website can read the files but can never change or delete them.

What
- A volume in docker-compose.yml mapping a host folder (from an environment variable, default an empty example folder inside the repo's data/ that is git-ignored) to a fixed path in the container, mounted read-only.
- A setting (for example PLASMID_FILES_ROOT) read from the environment, documented in .env.example.
- ONBOARDING note: developers do NOT need the real folder; the default example folder is enough.
Acceptance criteria
- [ ] `docker compose up` still works for everybody without extra steps (no real folder needed).
- [ ] The container cannot write into the folder (try `touch` inside, it fails).
```

---

# FRONTEND

## W4-F-MAIN: Lab features on the pages (parent ticket)

```text
Summary: Lab features on the pages (parent)
Zone: Frontend

In plain words (for beginners)
These pieces make the pages feel made for biologists: reading sequences comfortably, opening SnapGene with a click, seeing the family tree of a strain, and getting gentle hints while typing.

Sub-tasks
  1. W4-F1 SnapGene button on the plasmid page
  2. W4-F2 Sequence display component (blocks, copy button, counts)
  3. W4-F3 Lineage section on the strain page
  4. W4-F4 Duplicate warning and suggestion lists in the forms
  5. W4-F5 Live sequence tools on the primer form (length, GC%, reverse complement while typing)
  6. W4-F6 Print-friendly detail pages

Definition of done for the parent
A biologist can open a plasmid in SnapGene from its page, read and copy a sequence without errors, understand a strain's family tree at a glance, and is warned before creating a duplicate.

Things to take care of
- Everything from the earlier frontend rules still applies (plain CSS, no CDN, no inline styles, no frameworks, English only, works without JavaScript, textContent not innerHTML).
- DNA letters use the monospace tokens from the design foundation; the optional colouring of A/C/G/T must not rely on colour alone and must keep readable contrast.
```

## W4-F1: SnapGene button

```text
Summary: SnapGene button on the plasmid page
Zone: Frontend
Depends on: Serve or link plasmid files (backend), Plasmid pages (frontend)
Files allowed (optional): templates/plasmids/ (detail), static/css/pages/plasmids-*.css

What
- If `snapgene_url` exists: a clear button "Open in SnapGene" (a normal link), with a small help text ("Your browser downloads the file; open it with SnapGene").
- If not: a calm text "No sequence file stored" (no broken button); users with the edit permission see a link to the edit form.
Acceptance criteria
- [ ] States: with file, without file, read-only user; keyboard use; screenshot.
```

## W4-F2: Sequence display component

```text
Summary: Sequence display component: blocks, copy button, counts
Zone: Frontend (SHARED FILES: components, announce first)
Depends on: Sequence helpers (backend), Design foundation
Files allowed (optional): templates/components/sequence.html, static/js/app.js (only if a shared helper is needed; otherwise static/js/pages/), static/css/base.css (shared look)

In plain words (for beginners)
Long DNA strings are hard to read. We show them in groups of 10 letters, with the length, and a "Copy" button.

What
- components/sequence.html used with `{% include "components/sequence.html" with sequence=... %}`: monospace, grouped by 10 (the backend helper `format_blocks`, passed in or a template filter owned by backend), line numbers every 60 letters on long sequences, length shown.
- A "Copy" button (JavaScript, navigator.clipboard with a fallback that selects the text) that copies the plain letters WITHOUT spaces; works without JavaScript by showing selectable text.
- Used on primer and plasmid detail pages (replace the plain text there; one small PR touching only the include lines).
Acceptance criteria
- [ ] States: empty, short (20), long (3000) sequence; copy gives clean letters; no horizontal page scroll; screenshot.
```

## W4-F3: Lineage section

```text
Summary: Lineage section on the strain page
Zone: Frontend
Depends on: Strain lineage data (backend), Strain pages (frontend)
Files allowed (optional): templates/strains/ (detail or a new partial), static/css/pages/strains-lineage.css

In plain words (for beginners)
Show the family tree as an indented list: ancestors above the strain (oldest first), then the strain highlighted, then its descendants indented by depth. Each name is a link.

What
- Indentation by `depth` using CSS classes (no inline style).
- Marks the current strain; "No parent" and "No child strains" states.
- Long trees (more than 30 entries) collapse in a <details> element.
Acceptance criteria
- [ ] States: none, only parents, only children, both, a long tree; keyboard; screenshot.
```

## W4-F4: Duplicate warning and suggestions in forms

```text
Summary: Duplicate warnings and suggestion lists in the forms
Zone: Frontend
Depends on: Duplicate warnings (backend), Suggestion lists (backend), Form and feedback components
Files allowed (optional): templates/primers/form.html, templates/plasmids/form.html, templates/strains/form.html, templates/components/form_field.html (SHARED: announce first if it needs a change), static/css/pages/*

What
- Warning box (using the shared message/alert component) above the form listing `duplicate_warnings` with links, plus the "Save anyway" checkbox.
- <datalist> for the suggestion fields; the input stays free text.
Acceptance criteria
- [ ] States: no warning, warning, saved after confirmation; suggestion list shown and a custom value accepted.
```

## W4-F5: Live sequence tools on the primer form

```text
Summary: Live sequence tools on the primer form
Zone: Frontend
Depends on: Primer pages (frontend), Sequence display component
Files allowed (optional): static/js/pages/primers-form.js, templates/primers/form.html, static/css/pages/primers-form.css

In plain words (for beginners)
While the person types a primer, show instantly: how long it is, the GC percentage, and the reverse complement. This is only a convenience: the server recalculates and validates everything when saving (the numbers shown are never trusted by the server).

What
- Plain JavaScript that reads the sequence box and updates three small read-only outputs (use textContent). Invalid letters are highlighted with text, not only colour.
- The formulas are written once in the JS file with a comment pointing to the Python helper they mirror; a short test list of 3 example sequences with expected results goes in the pull request (no automated JS tests, decision D9).
- No melting temperature in JavaScript; Tm appears only after saving (server value).
Acceptance criteria
- [ ] Results equal the backend helper for the example sequences; empty, very long (5000 letters) and invalid input checked; page works without JavaScript.
```

## W4-F6: Print-friendly detail pages

```text
Summary: Print-friendly detail pages
Zone: Frontend
Depends on: Primer, Plasmid and Strain pages (frontend)
Files allowed (optional): static/css/pages/ (a print stylesheet per page type) or one shared print block in base.css via a shared ticket

In plain words (for beginners)
Labs print labels and sheets. A "print" style hides the menu and buttons and keeps the record readable on paper.

What
- `@media print` rules: hide navigation, search bar, buttons and messages; black on white; keep sequences from being cut mid-line; show the URL of the record at the bottom.
Acceptance criteria
- [ ] Print preview screenshots (Chrome and Firefox) for one primer, one plasmid, one strain.
```
