# Jira tickets: ready to copy and paste

How to use this file
1. Create each ticket in Jira. Copy everything inside one grey box into the ticket description. The first line (`Summary:`) is the ticket title.
2. "Depends on" uses ticket TITLES. After you create them, replace each title with its `SCRUM-` number.
3. Create the frontend sub-tasks (F-1 to F-7) as Jira **sub-tasks** of the parent ticket F-MAIN.
4. The person who takes a ticket starts **Claude Code** in the project folder and pastes the starter message from `docs/PROMPTING_GUIDE.md` together with the ticket text.

Who does what at the start (only Nour and Eya have joined so far)
- Nour: B1, then B2, B3, B4.
- Eya: F-1 first (needs no backend), then F-2, F-3, F-4, F-7. F-5 and F-6 wait for B3.
- Lina, Zahraa and Judy take wave-2 tickets when they join (list at the end).

Order (what blocks what)
```
B1 Database schema v1  ->  B2 Roles, B3 Accounts v1, B4 Fake data
F-1 Design foundation  ->  F-2 Components, F-3 Navbar, F-7 Error pages  ->  F-4 Login page
B3 Accounts v1         ->  F-5 Register page, F-6 Password change pages
```

## Words you will see (for people who build their first website)

| Word | Plain meaning |
|---|---|
| **Model** | A description of one kind of thing we store (a strain, a plasmid, a primer). Django turns each model into a database table. |
| **Field** | One piece of information on a model, like `strain_id` or `genotype`. A table column. |
| **Migration** | A small file that tells the database "add this table / this column". Whenever a model changes, a migration is created, and it is shared with the team through Git. |
| **Admin** | Django's built-in back office (`/admin/`) where an administrator can see and edit the data and the users. |
| **View** | Python code that answers one web address: it fetches data and hands it to a template. |
| **URL name** | A short nickname for a web address, like `accounts:login`. Templates use the nickname, never the typed address. |
| **Template** | An HTML file with holes in it, filled with data from the view. This is what the person sees. |
| **Context variable** | A piece of data a view hands to its template (for example `form`). |
| **Form** | The fields a person fills in. It also checks what they typed and shows error messages. |
| **Permission / role** | What a user is allowed to do. Our roles: Student (look only), Staff (look, add, edit), Admin (everything). |
| **Test** | A small program that checks our code still works. GitHub runs them for every pull request. |
| **Stub** | A tiny placeholder page, so another person can fill it in properly later. |
| **Design token** | A named value, like "the main colour" or "the standard spacing", defined once and used everywhere. |
| **Shared file** | A file everyone uses (the page layout, the components). It changes only through its own small ticket, announced in the team chat first. |

---

# BACKEND

## B1: Database schema v1 (one shot)

```text
Summary: Database schema v1 (all models, one shot)
Zone: Backend
Depends on: nothing. This is the first backend ticket; the schema-dependent tickets (roles, accounts v1, fake data, CRUD views, search) wait for it.
Files allowed (optional): apps/core/models.py, apps/primers/, apps/plasmids/, apps/strains/, apps/accounts/ (models, admin, migrations, tests)

In plain words (for beginners)
Everything the lab wants to store (strains, plasmids, primers, and who may log in) needs a place in the database. This ticket creates ALL of those places in one go, on purpose: if we add them one at a time we create many migration files, and migrations are the thing that most often causes conflicts between teammates. After this ticket the structure is fixed, and later changes are small.
Think of each model as a form-sheet with named boxes (fields). The database is the cabinet that keeps the filled-in sheets. A "link table" is a small sheet saying "strain X contains plasmid Y".

Why
Fields come from docs/DOMAIN.md (all approved by the client). The audit fields (who created / changed a record, and when) on all models are approved by Nour.

Design rules (follow all of them)
- Permissive database, strict forms: only the ID field is required in the database; everything else may be blank. Required fields are enforced later by the forms. (Reason: the Word-file import will bring incomplete records, and making a field required later should not need a migration.)
- Link tables from day one: no automatic many-to-many. (Reason: converting an automatic one into a link table later is a migration nightmare.)
- No `choices` on lists that may grow (purpose, biosafety level). Changing `choices` creates a migration. Use `choices` only for stable sets (copy_number, orientation, approval_status).
- Case-insensitive unique IDs: UniqueConstraint on Lower(field), so "ex-042" and "EX-042" cannot both exist.
- Generous lengths; TextField for long content; so we never need to widen a field later.
- extra_data = JSONField(default=dict, blank=True) on every domain model (decision D6: this is how the lab adds new "columns" without a migration).
- Nothing is ever deleted because another record was deleted. Link rows are deleted together with either side; no other record is.

Abstract base (apps/core/models.py, creates no table): AuditedModel
- created_at (auto_now_add), updated_at (auto_now)
- created_by, updated_by: FK to User, null, on_delete SET_NULL, related_name "+"

Models (all inherit AuditedModel and have extra_data)
- Primer: primer_id (unique, case-insens.), sequence (Text), purpose (Char, free text), freezer_location, length_bp (filled automatically from the sequence), melting_temp_tm (Decimal, nullable, filled automatically).
  The sequence is cleaned in ONE place: strips 5'-/-3' and whitespace, uppercases, and validates the letters against ONE constant (A,C,G,T; confirm with the client whether IUPAC codes are allowed).
  Tm formula: ask the client; keep it in ONE function so it is easy to change.
- Plasmid: plasmid_name (unique, case-insens.), size_bp (> 0 when set), resistance_markers, sequence_file, hessenbox_path, copy_number (choices High/Medium/Low), promoter_type, description (Text).
- PlasmidPrimerLink: plasmid FK, primer FK (both CASCADE), orientation (choices Forward/Reverse, blank ok), binding_position (Char), notes (Text). No exact duplicate rows.
- Strain: strain_id (unique, case-insens.), host_organism, genotype (Text), culturing_temp (Decimal 4,1 nullable), culturing_medium, freezer_location, biosafety_level (Char, free text), parent_strain (FK to itself, null, SET_NULL), plasmids (many-to-many through StrainPlasmid). The approved created_date and created_by are the audit fields created_at / created_by.
- StrainPlasmid: strain FK, plasmid FK (both CASCADE), notes (Text). One row per pair.
- accounts.User (extra fields, so sign-up approval never needs a later migration):
  - approval_status: Char, choices pending / approved / rejected, default "approved" (users created by an admin or by createsuperuser are approved; self-registration sets "pending")
  - approved_by: FK to User, null, on_delete SET_NULL, related_name "+"
  - approved_at: DateTimeField, null
  - signup_note: TextField, blank (filled at registration: why access is needed / which group)
  - email: unique, case-insensitive, ignoring blank emails
  Regenerate accounts/0001_initial to include all of this (nobody has real data yet) and announce the local database reset in the team chat.
- Plain database indexes on the fields people search (host_organism, culturing_medium, resistance_markers, purpose, promoter_type, freezer_location). No trigram indexes.

Contract for the rest of the team
- Each model's docstring lists every field with a one-line meaning. The frontend and the later tickets build on those docstrings.

Acceptance criteria
- [ ] One `makemigrations` run creates exactly one new migration per app (primers, plasmids, strains, accounts); no migration for core.
- [ ] Every model is registered in the admin.
- [ ] Tests: each record can be created with NO relations; case-insensitive ID uniqueness; optional parent strain; deleting a strain, plasmid or primer never deletes another record (only its link rows); sequence cleaning and rejection of invalid letters; length_bp and melting_temp_tm calculation; link uniqueness; unique email; the default approval_status is "approved".
- [ ] The six checks are green.
- [ ] A 20-minute schema review with the team happens BEFORE merge (it is expensive to change afterwards).

Out of scope: views, forms, templates, search, roles.

Notes
- Until real data exists, the schema owner may regenerate the initial migrations and announce a reset: everyone then runs `docker compose down -v` and the setup script (or helper option 14, d). After go-live: only small additive migrations.
- Tip for beginners: ask Claude Code to explain each field and each rule above before you say "go".
```

## B2: Roles and permissions

```text
Summary: Roles and permissions (Admin / Staff / Student)
Zone: Backend
Depends on: Database schema v1
Files allowed (optional): apps/accounts/ (roles.py, management/commands/setup_roles.py, tests/), apps/core/mixins.py (shared backend: announce to the team first)

In plain words (for beginners)
Not everybody in the lab may do everything. Students may only look, staff may add and edit, admins may also delete and manage accounts. Django already has a "permissions" system; this ticket sets up three "groups" (roles) with the right permissions, in one place, so nobody has to remember who may do what.

What
- apps/accounts/roles.py: ONE place defining the roles and the models they cover (strain, plasmid, primer, both link models, and user for admins).
- `python manage.py setup_roles`: creates or refreshes the groups. Safe to run twice (same result). Student = view; Staff = view + add + change; Admin = view + add + change + delete, plus user management.
- apps/core/mixins.py: a PermissionRequiredMixin variant that shows a proper 403 page to a logged-in user who lacks the right (not a redirect to the login page).
- setup_roles runs automatically when the app starts in development (add it to the compose start command: a lead-only file, so Nour).
- Documentation note: Admin users also need the "staff" flag to use the Django admin site.

Acceptance criteria
- [ ] Running the command twice gives the same result.
- [ ] Tests: each role has exactly the permissions above; a Student gets 403 on a write view; Staff cannot delete; Admin can.
- [ ] Views check permissions, never role names.
- [ ] The six checks are green.

Out of scope: the views that use the mixin, any user interface.
```

## B3: Accounts v1 (login, registration with approval, password change)

```text
Summary: Accounts v1: registration with admin approval, login messages, password change
Zone: Backend
Depends on: Database schema v1
Files allowed (optional): apps/accounts/, config/settings/base.py (lead-only: Nour), templates/accounts/ (new STUB templates only)

In plain words (for beginners)
Logging in already works. This ticket adds what a real lab needs around it: a new student can ask for an account, but cannot get in until an admin approves; the login page tells people why they cannot get in; and people can change their own password. "Backend" means the Python part: the rules and the data. The pretty pages are the frontend tickets F-4 to F-6, built on top of what this ticket provides.

Decision (by the lead): registration is self-service, but the account stays INACTIVE until an admin approves it. The register view is public, so it needs login_not_required (approved here; every other page stays protected).

What
- accounts:register: form with username, email (required), first_name, last_name, signup_note (optional), password1, password2 (Django password validators). Creates the user with approval_status="pending", is_active=False and no group. No automatic login. Redirects to accounts:register_done.
- accounts:register_done: the "waiting for approval" page.
- Login: a custom AuthenticationForm (needs AllowAllUsersModelBackend, a one-line settings change). Messages, shown ONLY when the password is correct:
    pending  -> "Your account is waiting for approval."
    rejected -> "Your access request was declined. Ask an admin."
    approved but is_active=False (disabled later) -> "This account is disabled. Ask an admin."
  Wrong username or password -> ONE generic message (never reveals whether a username exists).
- Admin: the User list shows approval_status and is_active, with a filter on approval_status (pending first).
  Actions: "Approve selected users" (status approved, is_active True, approved_by = the admin, approved_at = now) and "Reject selected users" (status rejected, is_active False).
  Roles are assigned by group in the admin.
- accounts:password_change and accounts:password_change_done using Django's built-in views.
- New STUB templates for the new pages ({% extends "base.html" %}, marked STUB), so the frontend can fill them in.

Contract for the frontend (also put it in the view docstrings)
- URL names: accounts:login, accounts:logout (POST only), accounts:register, accounts:register_done, accounts:password_change, accounts:password_change_done.
- Context: `form` on login, register and password_change. Fields: login = username, password. Register = username, email, first_name, last_name, signup_note, password1, password2. Password change = old_password, new_password1, new_password2. Messages use the Django messages framework.

Acceptance criteria
- [ ] Tests: registration creates a pending, inactive user; duplicate username and duplicate email (any capitalisation) are rejected; weak passwords are rejected; each of the three login messages appears for the right user; wrong credentials show the generic message; an approved user can log in; `?next=` is honoured; logout works (POST only); password change needs the old password; approve and reject actions set approval_status and the audit fields; anonymous users are redirected to login on protected pages.
- [ ] The six checks are green.

Out of scope: email verification or password reset by email (there is no mail server), brute-force lockout (needs an extra package: separate decision), single sign-on.
```

## B4: Fake development data

```text
Summary: seed_dev_data command (fake data for development)
Zone: Backend
Depends on: Database schema v1
Files allowed (optional): apps/core/management/commands/seed_dev_data.py, apps/core/tests/

In plain words (for beginners)
An empty app is hard to design pages for. This ticket adds one command that fills your LOCAL database with about 20 made-up strains, plasmids and primers (with links between them), so everyone can see something on screen. It must never use real lab data.

What
- `docker compose exec web python manage.py seed_dev_data`: creates about 20 obviously fake strains, plasmids and primers (Example-042, pEX-12, P-017) with realistic links, plus one fake user per role (student, staff, admin). The passwords are written in the command's help text (development only).
- Safe to run twice (no duplicates). `--reset` removes only the fake rows it created.

Acceptance criteria
- [ ] Never real lab data. The command refuses to run when DEBUG is off.
- [ ] Tests: runs twice without duplicates; --reset leaves other data alone.
- [ ] The six checks are green.
```

---

# FRONTEND

## F-MAIN: Login and register experience (parent ticket)

```text
Summary: Login and register experience (parent)
Zone: Frontend

In plain words (for beginners)
This is the first thing every user sees, so we do it first and do it properly. It is a "parent" ticket: the real work is in 7 sub-tasks. Each sub-task is its own small pull request, done in the order below. Frontend = what the person sees in the browser: the HTML files in templates/ and the CSS and JavaScript files in static/. You never edit the Python files in apps/; if you need data from the backend, you ask on the backend ticket.

Sub-tasks (create them as Jira sub-tasks; each is its own PR, in this order)
  1. F-1 Design foundation: tokens and base layout   (SHARED FILES)
  2. F-2 Form and feedback components                 (SHARED FILES)
  3. F-3 Navbar for logged-out and logged-in users   (SHARED FILES)
  4. F-4 Login page
  5. F-5 Register page and "waiting for approval" page   (needs backend "Accounts v1")
  6. F-6 Password change pages                           (needs backend "Accounts v1")
  7. F-7 Error pages 403, 404, 500

Definition of done for the parent
A visitor can open the app, see a clean login page, ask for an account, understand that an admin must approve it, log in once approved, change the password, and log out, with no unstyled page anywhere in that flow.

Things to take care of (apply to EVERY sub-task)
- Desktop-first (Windows PCs; Chrome, Edge, Firefox), still usable at about 1024 px width.
- Plain CSS using variables, plain JavaScript. No framework, no CDN, no inline style or script.
- Reuse the components in templates/components/ and the shared CSS. Never copy-paste a block of markup.
- Web addresses only through {% url 'app:name' %}; static files through {% static %}. Never type an address by hand.
- Every POST form contains {% csrf_token %}. Logout is a POST form (never a plain link).
- Forms: every input has a label tied to it; correct autocomplete values (username, current-password, new-password); autofocus on the first field; the hidden `next` field is kept.
- Errors: field errors under each field; general errors at the top (role="alert"); the login error stays generic.
- Password fields: show the password rules as help text; an optional show/hide toggle that is not required for the form to work.
- Prevent double submit (disable the button after the first click).
- Everything works with JavaScript switched off.
- Accessibility: visible keyboard focus, sensible Tab order, readable contrast, messages announced.
- English only. Use only obviously fake examples.
- Every pull request: a screenshot, the browser checklist (width, Tab key, empty state, error state, no JS, console), and a list of the states you checked: empty, wrong password, waiting for approval, declined, disabled, success, server error.
```

## F-1: Design foundation (shared files)

```text
Summary: Design foundation: tokens and base layout
Zone: Frontend (SHARED FILES: announce in the team chat before you start)
Depends on: nothing. Start on day 1 (no backend needed).
Files allowed (optional): static/css/base.css, templates/base.html

In plain words (for beginners)
Before any page can look good, the team needs one shared "look": the colours, the spacing, the fonts, and the frame every page sits in (header, content, footer). A "design token" is just a named value (like --color-primary) that we define once and use everywhere, so changing the look later means changing one line.

What
- CSS variables for colours, spacing, corner radius and fonts (system font stack, plus a monospace font for DNA sequences).
- The base layout: header, content container, footer, "skip to content" link, area for messages.
- Tidy the existing placeholder CSS into one foundation file.

Acceptance criteria
- [ ] No colour or size is typed outside the variables block.
- [ ] Keyboard focus is visible; text contrast is readable.
- [ ] Every existing placeholder page still renders.
- [ ] Browser checklist done, screenshot attached.

Out of scope: the components, styling individual pages.
Tip for beginners: open the page, press F12, and look at "Elements" to see how the HTML and CSS belong together.
```

## F-2: Form and feedback components (shared files)

```text
Summary: Form and feedback components
Zone: Frontend (SHARED FILES: announce first)
Depends on: Design foundation
Files allowed (optional): templates/components/, static/css/base.css

In plain words (for beginners)
Every page with a form (login, register, later every data form) needs the same pieces: a label, an input, a help text, error messages. We build them ONCE as a "component" (a small reusable template), so all forms look and behave the same and nobody copy-pastes.

What
- A form_field component (label, input, help text, errors, required marker), used like: {% include "components/form_field.html" with field=form.username %}
- Buttons (primary, secondary, danger), message styles (info, success, warning, danger), a card container for forms.

Acceptance criteria
- [ ] One home for each piece; the login page will reuse them.
- [ ] States shown: normal, focus, error, disabled.
- [ ] Browser checklist done, screenshot attached.
```

## F-3: Navbar for logged-out and logged-in users (shared files)

```text
Summary: Navbar for logged-out and logged-in users
Zone: Frontend (SHARED FILES: announce first)
Depends on: Design foundation
Files allowed (optional): templates/components/navbar.html, static/css/base.css

In plain words (for beginners)
The bar at the top of every page changes depending on who is looking: a visitor who is not logged in sees almost nothing; a logged-in person sees the navigation and their account menu. A template can test "is this person logged in?" with {% if user.is_authenticated %}.

What
- Logged out: the app name and a "Log in" link.
- Logged in: links to Strains, Plasmids and Primers (the current section highlighted), the user's name, "Change password", and a "Log out" button (a POST form).

Acceptance criteria
- [ ] Both states checked; fully keyboard accessible; works without JavaScript.
```

## F-4: Login page

```text
Summary: Login page
Zone: Frontend
Depends on: Form and feedback components, Navbar for logged-out and logged-in users (the login logic already works today)
Files allowed (optional): templates/accounts/login.html, static/css/pages/accounts-login.css

In plain words (for beginners)
The login page is a form with two fields. The backend (Django) already checks the password; your job is to make the page clear and friendly in every situation, including when something goes wrong. The messages come from the backend: you only place and style them.

What
- A clean, centred login card using the shared form components.
- Fields: username and password. A link to the register page. A line "Forgot your password? Ask an admin." (there is no email reset).
- States to design and check: empty; wrong username or password (one generic message); "Your account is waiting for approval."; "Your access request was declined. Ask an admin."; "This account is disabled. Ask an admin."; the button disabled after the first click.

Acceptance criteria
- [ ] Every state above is checked and listed in the PR.
- [ ] `next` is preserved; password managers can fill it in; Tab order is logical.
```

## F-5: Register page and "waiting for approval" page

```text
Summary: Register page and waiting-for-approval page
Zone: Frontend
Depends on: Accounts v1 (backend), Form and feedback components
Files allowed (optional): templates/accounts/register.html, templates/accounts/register_done.html, static/css/pages/accounts-register.css

In plain words (for beginners)
A new student fills in this page to ask for access. They cannot log in yet: an admin must approve them first. So this ticket has two pages: the form, and a friendly page that explains "your request was sent, an admin will approve it". The form fields and the rules come from the backend ticket; you build how it looks and make every error understandable.

What
- Register form with the fields from the backend contract: username, email, first name, last name, signup_note (a text area labelled "Why do you need access? (optional)"), password1, password2.
- Show the password rules as help text, and every validation error under its own field.
- After submitting: the "Your account is waiting for approval by an admin" page, with a link back to the login page.

Acceptance criteria
- [ ] States checked: empty; duplicate username; duplicate email; weak password; passwords that do not match; success.
- [ ] Nothing sensitive (like the password) is shown back to the user.
```

## F-6: Password change pages

```text
Summary: Password change pages
Zone: Frontend
Depends on: Accounts v1 (backend), Form and feedback components
Files allowed (optional): templates/accounts/password_change.html, templates/accounts/password_change_done.html, static/css/pages/accounts-password.css

In plain words (for beginners)
Logged-in users can change their own password. Two pages: the form (old password, new password twice) and a confirmation page.

What
- Both pages, consistent with the login page; errors under each field; the confirmation page links back home.

Acceptance criteria
- [ ] States checked: empty; wrong old password; weak new password; success.
```

## F-7: Error pages 403, 404, 500

```text
Summary: Error pages 403, 404, 500
Zone: Frontend
Depends on: Design foundation
Files allowed (optional): templates/403.html, templates/404.html, templates/500.html

In plain words (for beginners)
When something goes wrong, the user should see a friendly page, not a scary technical one. 403 = "you are not allowed", 404 = "this page does not exist", 500 = "something broke on our side".

What
- Friendly pages in the app's look, each with a link back to the home page or to login.
- The 500 page must stand alone: no base template and no template tags, so it still shows even when everything else is broken.

Acceptance criteria
- [ ] Each page checked; the 500 page opens on its own.
```

---

# Later (wave 2): create these once B1 is merged

Backend (Lina and Nour)
- CRUD views per entity (list, detail, create/edit) with forms, permission checks and tests. Each ticket documents its context variables in the view docstring.
- Search and filter (by name, genotype, culturing requirements) plus a JSON live-search endpoint.
- Delete with a choice: a shared helper in apps/core, used by all three apps (delete only this record, or also the linked ones, with a confirmation).
- Later: backups, the SnapGene link, the CSV import (bonus), extra-field definitions, deployment.

Frontend (Eya, Zahraa, Judy)
- List pages, detail pages with clickable links to related records, create/edit form pages, the delete-confirmation page, and live search in JavaScript (`fetch()` to the JSON endpoint).

# Two assumptions to confirm
1. Registration is self-service with admin approval and no email. If you prefer NO registration page (admins create every user in the Django admin), drop the registration parts of B3 and F-5, and keep login and password change.
2. B1 regenerates the accounts initial migration (unique email and the approval fields) and so needs one announced database reset. If you would rather not touch accounts, move those fields out of B1.
