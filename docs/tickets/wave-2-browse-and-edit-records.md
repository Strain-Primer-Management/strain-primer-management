# Wave 2: browse, create, edit, link and delete records

Create these when Database schema v1 is merged (and the fake data command exists). Backend and frontend
pairs run in parallel: the backend ticket publishes the contract (URL names and context variables in the
view docstrings), the frontend ticket builds on it.

Conventions for the whole wave (so the tickets stay short)
- URL names per entity: `<app>:list`, `<app>:detail`, `<app>:create`, `<app>:update`, `<app>:delete`
  (apps: primers, plasmids, strains). The detail page address uses the record's database id.
- Page size: 25 per page, defined once as a constant in apps/core.
- Views are class-based Django views, protected with the permission mixin from apps/core: view = *.view_*,
  create = *.add_*, edit = *.change_*, delete = *.delete_*.
- Forms are strict (required fields enforced here, not in the database); the database stays permissive.
- Each view sets created_by / updated_by on save.

---

# BACKEND

## W2-B1: Shared view helpers (shared backend)

```text
Summary: Shared view helpers in apps/core (page size, audit fields, messages)
Zone: Backend (SHARED: apps/core, announce to the team first)
Depends on: Database schema v1, Roles and permissions
Files allowed (optional): apps/core/ (views mixins, constants, tests)

In plain words (for beginners)
Strain pages, plasmid pages and primer pages all need the same boring things: the same page size, "remember who saved this record", "show a success message". We write those ONCE here so the three apps do not each invent their own version.

What
- PAGE_SIZE = 25 constant.
- AuditedFormMixin: on save sets created_by (first save) and updated_by (every save) from request.user.
- A small mixin that adds a success message after create/update/delete (text supplied by each view).
- A base class or mixin combining: login (already global), permission check, pagination, the `page_obj` and `object_list` context names.
- Tests for each helper using a tiny test model inside the tests package.

Contract for others (docstrings)
- How to use each mixin in three lines with an example.

Acceptance criteria
- [ ] Tests for each helper; six checks green.
Out of scope: any real entity view.
```

## W2-B2: Primer pages (backend)

```text
Summary: Primer pages: list, detail, create, edit
Zone: Backend
Depends on: Shared view helpers, Database schema v1
Files allowed (optional): apps/primers/ (views.py, forms.py, urls.py, tests/)

In plain words (for beginners)
This makes the primers usable in the website. A "view" answers a web address; a "form" checks what a person typed. The pretty pages come from the frontend tickets; here we provide the data and the rules.

What
- URL names primers:list, primers:detail, primers:create, primers:update (delete comes in the delete ticket).
- List: all primers, newest first, 25 per page.
- Detail: the primer, and the plasmids it is linked to (with orientation and position).
- Form (strict): primer_id and sequence required; purpose, freezer_location optional; the sequence is cleaned by the model rules; length and Tm are shown read-only after saving; extra_data is edited later (extra-fields ticket), not here.
- The purpose field offers suggestions from a list defined in ONE place in the form (a datalist), but accepts other text.
- Permissions: viewing needs primers.view_primer, create needs add, edit needs change.

Contract for the frontend (also in the view docstrings)
- list: context `page_obj`, `object_list`, `is_paginated`. Each row: id, primer_id, sequence, purpose, freezer_location, length_bp, melting_temp_tm.
- detail: context `object` (the primer) and `links` (rows with plasmid, orientation, binding_position).
- create/update: context `form`, fields primer_id, sequence, purpose, freezer_location, and `object` on update. Server messages through the messages framework.

Acceptance criteria
- [ ] Tests per view: anonymous -> login; permitted user -> 200 with the expected content; user without permission -> 403; the form rejects invalid sequence letters and a duplicate primer_id (any capitalisation); created_by/updated_by are set.
- [ ] Six checks green.
Out of scope: delete, search, templates (frontend tickets).
```

## W2-B3: Plasmid pages (backend)

```text
Summary: Plasmid pages: list, detail, create, edit
Zone: Backend
Depends on: Shared view helpers, Database schema v1
Files allowed (optional): apps/plasmids/ (views.py, forms.py, urls.py, tests/)

In plain words (for beginners)
Same idea as the primer pages, for plasmids (small circles of DNA). A plasmid can have primers and can be carried by strains.

What
- URL names plasmids:list, plasmids:detail, plasmids:create, plasmids:update.
- List: plasmid_name, size_bp, resistance_markers, copy_number.
- Detail: all fields, the primers linked to it (orientation, binding_position), and the strains that carry it.
- Form (strict): plasmid_name required; size_bp a positive whole number when given; copy_number a dropdown (High, Medium, Low, or empty); sequence_file and hessenbox_path are plain text boxes (the SnapGene ticket later makes them clickable); description optional.
- Permissions as in the primer ticket.

Contract for the frontend
- list: `page_obj`, `object_list`. detail: `object`, `primer_links`, `strains`. form: `form` with the field names above.

Acceptance criteria
- [ ] Same test set as the primer pages (login, permission, content, validation, duplicate names, audit fields).
- [ ] Six checks green.
Out of scope: delete, search, templates.
```

## W2-B4: Strain pages (backend)

```text
Summary: Strain pages: list, detail, create, edit
Zone: Backend
Depends on: Shared view helpers, Database schema v1
Files allowed (optional): apps/strains/ (views.py, forms.py, urls.py, tests/)

In plain words (for beginners)
The strain is the heart of the database: a bacterial line with its genetics and where it is stored. A strain can carry plasmids and can descend from another strain (its "parent").

What
- URL names strains:list, strains:detail, strains:create, strains:update.
- List: strain_id, host_organism, genotype (shortened), culturing_temp, culturing_medium, freezer_location.
- Detail: all fields, the plasmids it carries, its parent strain and its child strains.
- Form (strict): strain_id required; culturing_temp a number in a sensible range (set the range in ONE constant); parent_strain a dropdown of other strains that cannot be the strain itself; biosafety_level offers suggestions from a list in one place but accepts other text.
- Permissions as in the other entities.

Contract for the frontend
- list: `page_obj`, `object_list`. detail: `object`, `plasmid_links`, `parent`, `children`. form: `form`.

Acceptance criteria
- [ ] Tests: the usual set, plus "a strain cannot be its own parent", "a loop of parents is rejected", "a strain without plasmids or parent saves fine".
- [ ] Six checks green.
Out of scope: delete, search, templates.
```

## W2-B5: Link management (backend)

```text
Summary: Link plasmids to strains and primers to plasmids
Zone: Backend
Depends on: Primer pages, Plasmid pages, Strain pages
Files allowed (optional): apps/strains/, apps/plasmids/ (views, forms, urls, tests)

In plain words (for beginners)
A strain carries plasmids; a plasmid binds primers. This ticket lets a person add and remove those connections from a detail page. Remember the rule: a record never has to have links, and removing a link NEVER deletes either record.

What
- On a strain's page: add a plasmid (pick from a list, optional note) and remove a plasmid link. URL names strains:link_plasmid, strains:unlink_plasmid.
- On a plasmid's page: add a primer (pick the primer, orientation, binding position, note) and remove a primer link. URL names plasmids:link_primer, plasmids:unlink_primer.
- The same pair cannot be linked twice (friendly error message, not a crash).
- Needs the change permission of the page's record; unlinking is a POST request with a CSRF token.

Contract for the frontend
- Link forms as `link_form` in the detail page context, with the field names; unlink buttons post to the unlink URL with the link row's id.

Acceptance criteria
- [ ] Tests: link, duplicate link, unlink, unlinking keeps both records, permissions (student cannot link), the page works for a record with no links.
- [ ] Six checks green.
```

## W2-B6: Delete with a choice

```text
Summary: Delete with a choice (shared helper and all three apps)
Zone: Backend (the helper lives in apps/core, a SHARED area: announce first)
Depends on: Link management
Files allowed (optional): apps/core/, apps/strains/, apps/plasmids/, apps/primers/ (views, urls, tests)

In plain words (for beginners)
Deleting a record that is connected to others is risky. Decision D8: we always ask. The confirmation page lists what is linked and lets the person choose: delete only this record (its links disappear, the others stay), or also delete the linked records, but only those that are not linked to anything else.

What
- One shared delete view/mixin in apps/core, used by the three apps: URL names primers:delete, plasmids:delete, strains:delete.
- GET shows the confirmation (context below); POST performs the choice, with a CSRF token.
- "Also delete linked records" is offered only for linked records that nothing else is linked to. A plasmid carried by another strain is NEVER deleted by this option.
- Needs the delete permission (Admin only by default).
- A success message says exactly what was deleted.

Contract for the frontend
- Context: `object`, `linked_exclusive` (linked records that nothing else uses), `linked_shared` (linked records that something else also uses), form field `delete_linked` (checkbox).

Acceptance criteria
- [ ] Tests: delete only this record keeps the others; also-delete removes only exclusive ones; shared ones stay; no permission -> 403; a record without links deletes simply; nothing else is deleted in any case.
- [ ] Six checks green.
```

## W2-B7: Dashboard data and admin approvals page (backend)

```text
Summary: Home dashboard data and the admin approvals page
Zone: Backend
Depends on: Accounts v1, Strain pages (for the counts)
Files allowed (optional): apps/core/views.py, apps/core/urls.py, apps/accounts/ (views, urls, tests)

In plain words (for beginners)
The home page should say something useful: how many records exist, what changed recently, and (for admins) who is waiting for approval. Admins should be able to approve new sign-ups on a normal page without learning the Django admin.

What
- core:home context: counts of strains, plasmids, primers; the 5 most recently changed records of each kind; for users with the permission, `pending_users` (sign-ups waiting).
- accounts:approvals (Admin only): list of pending sign-ups with their signup_note; POST actions approve (with a role dropdown: Student, Staff or Admin) and reject. Approving sets approval_status, is_active, approved_by, approved_at and adds the chosen group.

Contract for the frontend
- Home: `counts` (dict), `recent` (lists), `pending_users` (or empty). Approvals page: `pending_users`, a form with `user_id` and `role`, POST to accounts:approve and accounts:reject.

Acceptance criteria
- [ ] Tests: counts are right; recent lists are ordered; pending_users only for admins; approve gives the chosen role; reject deactivates; a Student gets 403 on the approvals page.
- [ ] Six checks green.
```

---

# FRONTEND

## W2-F-MAIN: Browse, create and edit records (parent ticket)

```text
Summary: Browse, create and edit records (parent)
Zone: Frontend

In plain words (for beginners)
This is where the lab's data becomes visible and usable: tables to browse, pages to read one record, forms to add and change records, and a clear way to link and delete. You build on what the backend tickets publish (URL names and context variables in the view docstrings). If a variable you need is missing, ask on the backend ticket; never edit apps/.

Sub-tasks (Jira sub-tasks; each its own PR)
  1. W2-F1 Shared list layout (table, empty state, pagination)       (SHARED FILES)
  2. W2-F2 Primer pages: list, detail, form
  3. W2-F3 Plasmid pages: list, detail, form
  4. W2-F4 Strain pages: list, detail (with lineage), form
  5. W2-F5 Link management on the detail pages
  6. W2-F6 Delete confirmation page
  7. W2-F7 Home dashboard
  8. W2-F8 Admin approvals page
  9. W2-F9 Permission-aware buttons and final polish

Definition of done for the parent
A Staff user can find, read, create, edit and link records; a Student can only read and sees no edit buttons; an Admin can delete with a clear choice; every page has loading-free empty, error and success states.

Things to take care of (apply to every sub-task)
- Everything from the F-MAIN checklist of wave 1 still applies (plain CSS, no CDN, no inline styles, CSRF, labels, no-JS, keyboard, English only).
- Tables: real <table> with header cells (scope="col"), sensible column widths, long text (genotype, sequence) shortened with the full text on the detail page.
- DNA sequences use the monospace style and may wrap anywhere.
- Never show a button the user may not use (check the permissions the backend provides, e.g. {% if perms.strains.change_strain %}).
- Links between records are real links (deep links), keyboard reachable.
- Show friendly empty states ("No primers yet") and a "Create" button only for those allowed.
- Every PR: screenshots (list, detail, form, an error state) and the browser checklist.
```

## W2-F1: Shared list layout (shared files)

```text
Summary: Shared list layout: table, empty state, pagination
Zone: Frontend (SHARED FILES: announce first)
Depends on: Design foundation, Form and feedback components
Files allowed (optional): templates/components/, static/css/base.css

In plain words (for beginners)
All three list pages (strains, plasmids, primers) look alike: a title, a button, a table, page numbers. Build that frame once as components.

What
- components/page_header.html (title + optional action button), components/table.html pattern or CSS (zebra rows, hover, sticky header if easy), components/empty_state.html, components/pagination.html using `page_obj`.
Acceptance criteria
- [ ] Used by the first list page that follows; states: normal, empty, one page, many pages.
- [ ] Browser checklist, screenshot.
```

## W2-F2: Primer pages

```text
Summary: Primer pages: list, detail, form
Zone: Frontend
Depends on: Primer pages (backend), Shared list layout
Files allowed (optional): templates/primers/, static/css/pages/primers-*.css

In plain words (for beginners)
The primer is a short piece of DNA, written as a row of letters. Show the letters in a monospace font so they line up and are easy to read.

What
- list.html: columns primer_id (link to detail), sequence (monospace, shortened), purpose, length, Tm, freezer location.
- detail.html: all fields, the linked plasmids (links to their pages with orientation and position), Edit button for those who may.
- form.html: the form using the shared components; help text under sequence ("letters A, C, G, T; 5'- and -3' are removed automatically"); read-only length and Tm shown after saving.
Acceptance criteria
- [ ] States: empty list, one page/many pages, a primer with no links, validation errors, success message, permission-less view (no buttons).
```

## W2-F3: Plasmid pages

```text
Summary: Plasmid pages: list, detail, form
Zone: Frontend
Depends on: Plasmid pages (backend), Shared list layout
Files allowed (optional): templates/plasmids/, static/css/pages/plasmids-*.css

What
- list.html: plasmid_name (link), size_bp, resistance_markers, copy_number.
- detail.html: all fields; two sections "Primers" (orientation and position) and "Carried by strains"; sequence_file and hessenbox_path shown as plain text for now (becomes a button later).
- form.html: shared components; copy_number dropdown; size_bp number input with a min value.
Acceptance criteria
- [ ] Same states as the primer pages, plus a plasmid with no primers and no strains.
```

## W2-F4: Strain pages

```text
Summary: Strain pages: list, detail with lineage, form
Zone: Frontend
Depends on: Strain pages (backend), Shared list layout
Files allowed (optional): templates/strains/, static/css/pages/strains-*.css

In plain words (for beginners)
"Lineage" means where a strain came from: its parent, and the strains made from it. Show it simply as two small lists with links.

What
- list.html: strain_id (link), host_organism, genotype (shortened), culturing temperature (with the unit °C), medium, freezer location.
- detail.html: all fields; sections "Plasmids" (links), "Parent strain" (link or "none") and "Child strains" (links).
- form.html: shared components; temperature input with step 0.1; parent dropdown with a clear "none" option.
Acceptance criteria
- [ ] States: empty, validation errors, a strain with no plasmids and no parent, a strain with several plasmids and children.
```

## W2-F5: Link management UI

```text
Summary: Link management on the detail pages
Zone: Frontend
Depends on: Link management (backend), Strain pages, Plasmid pages (frontend)
Files allowed (optional): templates/strains/, templates/plasmids/, templates/components/link_form.html, static/css/pages/*-links.css

In plain words (for beginners)
On a strain page you add or remove the plasmids it carries; on a plasmid page you add or remove its primers. Removing a link only removes the connection, never the records, and the page must say so.

What
- Small "add" form (a dropdown plus optional fields) and a "remove" button per row (a POST form with a CSRF token) on the two detail pages, shown only to users who may change the record.
- Clear wording under remove: "This only removes the link. Both records stay."
Acceptance criteria
- [ ] States: no links, many links, duplicate-link error, success message, a read-only user sees no add/remove controls.
```

## W2-F6: Delete confirmation page

```text
Summary: Delete confirmation page
Zone: Frontend
Depends on: Delete with a choice (backend)
Files allowed (optional): templates/core/confirm_delete.html (or per-app folders), static/css/pages/delete.css

In plain words (for beginners)
Deleting is permanent, so the page must be calm and clear. It names the record, lists what is linked to it, and offers the choice from decision D8.

What
- A page showing the record, the linked records that nothing else uses (can be deleted too) and the linked records others still use (will stay).
- A checkbox "Also delete the linked records that nothing else uses" (unchecked by default), a red Delete button, and a Cancel link back to the record.
Acceptance criteria
- [ ] States: no links; only exclusive links; shared links; the cancel path; keyboard use.
```

## W2-F7: Home dashboard

```text
Summary: Home dashboard
Zone: Frontend
Depends on: Dashboard data and admin approvals page (backend), Design foundation
Files allowed (optional): templates/core/home.html, static/css/pages/core-home.css

What
- Three count cards (Strains, Plasmids, Primers) linking to the lists; "Recently changed" lists; for admins a "N people are waiting for approval" notice linking to the approvals page.
Acceptance criteria
- [ ] States: empty database, normal, admin with pending users, student view.
```

## W2-F8: Admin approvals page

```text
Summary: Admin approvals page
Zone: Frontend
Depends on: Dashboard data and admin approvals page (backend)
Files allowed (optional): templates/accounts/approvals.html, static/css/pages/accounts-approvals.css

What
- A table of pending sign-ups (name, username, email, note, date) with a role dropdown and Approve and Reject buttons per row (POST forms with CSRF).
- Empty state "Nobody is waiting".
Acceptance criteria
- [ ] States: empty, one pending, many pending; success and error messages; only admins can open it (403 page otherwise).
```

## W2-F9: Permission-aware buttons and polish

```text
Summary: Permission-aware buttons and final polish of wave 2
Zone: Frontend
Depends on: all W2-F tickets above

What
- Go through every page as Student, Staff and Admin: hide anything the role cannot use, make wording consistent (Create / Edit / Delete), consistent page titles, breadcrumbs or "back to list" links, same spacing everywhere.
- Fix duplicated markup by moving it into components (rule of two).
Acceptance criteria
- [ ] A short table in the PR: page x role, with a screenshot or "ok" for each.
- [ ] No page has unstyled areas or copy-pasted blocks.
```
