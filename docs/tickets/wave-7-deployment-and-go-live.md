# Wave 7: deployment and go-live

Almost everything here is lead work (Docker, servers, settings are lead-only), done together with the client's
IT person or whoever looks after the lab computer. Start the planning tickets (W7-L1 to W7-L3) early, even
while waves 2 to 5 are running, because they depend on answers from the client (wave 0, ticket L-6, question 8).

Conventions for the whole wave
- NEVER run the developer setup scripts (setup.sh / setup.ps1) on the production machine: they create the
  dev admin/admin account and developer settings. Production has its own start procedure (W7-L1).
- Production secrets (SECRET_KEY, database password) are generated on the production machine, stored only
  there and in the lead's password manager. They are never in Git, chat or tickets.
- Nothing goes live with real data before the client approved it (W7-L7) and a backup restore was proven (W5-L1).
- Every procedure is written as copy-paste steps in docs/, tested once by a second person.

---

## W7-L1: Production Docker setup

```text
Summary: Production Docker Compose setup (gunicorn, restart policy, volumes, secrets)
Zone: Lead
Depends on: Production settings review (HTTPS flags, hosts, sessions, logging), Add the PostgreSQL client tools to the web image
Files allowed (optional): docker-compose.prod.yml (new), Dockerfile, .env.example, .env.prod.example (new), docs/DEPLOYMENT.md (new), config/settings/prod.py

In plain words (for beginners)
On a developer PC we start the app with Django's built-in test server and visible secrets. On the lab computer it must run with a real web server (gunicorn), restart by itself after a reboot, keep its database safe in a Docker volume, and read secrets from a file that only exists on that computer.

What
- A production compose file (separate from the developer one): web (gunicorn, not runserver), db (Postgres with a named volume), `restart: unless-stopped`, ports only on the interface the lab network needs.
- A production environment file template with every variable explained (no real values). The real file is created on the server by hand.
- Static files collected and served by whitenoise (already configured), media/files folder mounted read-only (W4-L2).
- Migrations run on start only after a backup (the update procedure W7-L4 does this explicitly; document why).
- docs/DEPLOYMENT.md: first installation from zero, step by step.

Acceptance criteria
- [ ] A second person installs from the document on a clean machine (a virtual machine is fine) and reaches the login page.
- [ ] After rebooting the machine the app comes back by itself.
- [ ] `manage.py check --deploy` is clean inside the production container.
```

## W7-L2: HTTPS decision on the lab network

```text
Summary: Decide how users reach the app: HTTP or HTTPS, and the address
Zone: Lead (with the client's IT)
Depends on: client answers about hosting (ticket L-6, question 8)
Files allowed (optional): docs/DECISIONS.md, docker-compose.prod.yml, config/settings/prod.py, docs/DEPLOYMENT.md

In plain words (for beginners)
HTTPS encrypts the traffic between browser and server and is the normal standard. On a closed lab network plain HTTP is common, but passwords travel readable. We decide with the client's IT based on what is possible: a university certificate, an internal certificate authority, a reverse proxy such as Caddy with an internal certificate, or plain HTTP with the risk accepted in writing.

What
- Ask: what is the server's network name or address, can IT issue a certificate, will users come only from inside the university network or also via VPN?
- Choose one option and write the reason. If HTTPS: add the proxy, set the Secure cookie flags and the "trusted origins" settings, redirect HTTP to HTTPS. If HTTP: write that decision and keep session cookies non-Secure (otherwise login stops working).
- Test login from a second computer on the network.

Acceptance criteria
- [ ] Decision recorded; login works from a lab PC with the final address; no browser warnings (or the warning is explained to users in the manual).
```

## W7-L3: Prepare the lab computer

```text
Summary: Prepare the lab computer (Docker autostart, fixed address, firewall, power)
Zone: Lead (with the client's IT)
Depends on: Production Docker setup
Files allowed (optional): docs/DEPLOYMENT.md, tools/ (helper scripts)

In plain words (for beginners)
The best software is useless if the computer sleeps at night or changes its network address. We set the machine up to be a small reliable server.

What (details depend on the machine and operating system the client names: a lab PC or a NAS)
- Docker Desktop (Windows) or Docker Engine (Linux) installed and starting automatically at boot, before any user logs in if possible (document what is possible with Docker Desktop and WSL2).
- Sleep and hibernate off; automatic Windows restarts scheduled outside lab hours; who gets a note when it restarts.
- A fixed address or DNS name from IT, so the bookmark in everyone's browser keeps working.
- Firewall: only the web port is open, only to the university network.
- A named person ("the machine's keeper") and a rule for what to do if it is switched off.
- A UPS (battery) or at least a clean shutdown routine is discussed with the client.

Acceptance criteria
- [ ] The machine survives a reboot test and a power-off test without data loss and the app returns by itself.
- [ ] The address works from three other computers.
```

## W7-L4: Update and rollback procedure

```text
Summary: Procedure to update the app and to roll back
Zone: Lead
Depends on: Production Docker setup, Backup and restore setup (W5-L1)
Files allowed (optional): docs/UPDATE_GUIDE.md (new), tools/update-prod.sh (new, optional)

In plain words (for beginners)
Updating a live system is where most accidents happen. We write the safe routine once and follow it every time: back up, update, check, and know exactly how to go back.

What
- Steps: announce a short maintenance window; take a backup and check the file exists; fetch the new version (a tagged release, never an unreviewed branch); build the new image; apply migrations; start; run the smoke checklist (login page, a list page, a search, an export); announce done.
- Rollback: how to return to the previous image AND the previous database (restore the backup taken in the first step), with the exact commands, and when each is needed (a migration that already ran needs the database restore).
- Version tags: how the lead creates a release (a tag and a short change list) after merging.
- A short "what changed" note for users after each update.

Acceptance criteria
- [ ] The guide was followed for one real update on the test machine and one deliberate rollback, both timed and recorded.
```

## W7-L5: Health check, monitoring and log care

```text
Summary: Health endpoint, simple monitoring and log rotation
Zone: Lead (health endpoint is a small Backend ticket, announced)
Depends on: Production Docker setup
Files allowed (optional): apps/core/views.py (SHARED: health view and test), docker-compose.prod.yml, docs/DEPLOYMENT.md

In plain words (for beginners)
We want to notice problems before the users complain: the app down, the disk almost full, the backup not running.

What
- A `core:health` page (no login, tells only "ok" or "database error", no details) used by Docker's healthcheck so a stuck container is restarted.
- A weekly 5-minute checklist for the keeper: app opens, last backup date is today or yesterday, disk space above 20 percent, log folder not huge.
- Log rotation (Docker's json-file driver with a size and file limit) so logs never fill the disk.
- Optional: a free uptime checker from the university network or a small script that emails or messages the lead.

Acceptance criteria
- [ ] Stopping the database makes the health page fail and Docker mark the container unhealthy; starting it fixes that.
- [ ] The checklist is in docs/ADMIN_MANUAL.md.
```

## W7-L6: Production restore drill

```text
Summary: Restore drill on the production setup
Zone: Lead
Depends on: Production Docker setup, Backup and restore setup (W5-L1)
Files allowed (optional): docs/BACKUP.md

What
- Take a real backup of the production database (with test records), restore it onto a different machine with the production setup, log in, and compare counts and a few records by hand.
- Repeat after any change to the backup routine.

Acceptance criteria
- [ ] Date, person and result written in docs/BACKUP.md; any problem fixed and the drill repeated.
```

## W7-L7: Import the real data

```text
Summary: Import the real lab data into production
Zone: Lead (with the client)
Depends on: Import command, Data quality report, Production restore drill, client approval
Files allowed (optional): none in the repository (real data never goes into Git); the report goes to the client

In plain words (for beginners)
This is the moment the real strains, plasmids and primers go in. We do it with care, in rehearsal first.

What
- Rehearsal on a COPY of the production setup using the client's real export: run with --dry-run, read the whole report with the client, agree how to fix each class of problem (fix the source file, or accept and clean up in the app).
- Take a backup, run the real import on production, then open the data quality page and walk through it with the client.
- Compare numbers: rows in the source files versus records in the app (written in the report).
- Keep the original files safe and untouched.

Acceptance criteria
- [ ] The client signs off the record counts in writing (an email is fine).
- [ ] A backup from just before and just after the import exists.
```

## W7-L8: Accounts and onboarding session

```text
Summary: Create the first accounts and run an onboarding session with the lab
Zone: Lead (with the client)
Depends on: Production data in place, User manual
Files allowed (optional): docs/USER_MANUAL.md (corrections)

What
- Create the admin accounts for the lab's chosen administrators (strong passwords, shared in person or through the university's password tool, never by chat). Make sure the temporary dev admin does not exist.
- Everyone else signs up themselves and is approved by an admin; check that the approval flow works with real people.
- A 30-minute session with the lab: demo of the five main tasks, then each person does one task alone; collect questions and confusing points as tickets.

Acceptance criteria
- [ ] Every lab member who needs access has an approved account with the right role.
- [ ] Feedback list is turned into tickets (label: change-request or bug).
```

## W7-L9: Go-live checklist and rehearsal

```text
Summary: Go-live checklist and a full rehearsal
Zone: Lead (team helps)
Depends on: all tickets above

What
- One checklist, tick every line, with owner and date:
  - Production started from a tagged release; `manage.py check --deploy` clean.
  - Secrets exist only on the server; no dev accounts; DEBUG off; error pages show no details.
  - Backup ran last night and was restored in a drill; the admin's manual copy to another system exists and its procedure is written down.
  - The monitoring checklist and the keeper are named; the lab knows who to call.
  - Data imported and signed off; user and admin manuals in the lab's hands.
  - Update and rollback guide tested.
  - Client's decisions all recorded (licence, hosting, backups, who may export).
- A rehearsal: someone who did not build the system performs the first install on a clean machine from docs/DEPLOYMENT.md only.

Acceptance criteria
- [ ] Every line ticked or consciously accepted by the client in writing.
```

## W7-L10: Support process after go-live

```text
Summary: Support and change-request process after go-live
Zone: Lead
Depends on: Go-live checklist

In plain words (for beginners)
Once people depend on the tool, "who do I tell when something is wrong?" must have a clear answer.

What
- One place to report problems (an email address or a form) and one person who reads it every working day.
- Severity levels: "cannot log in or data wrong" (same day), "something is annoying" (next sprint), "wish" (change request, prioritised with the client).
- A rule for emergency changes: smallest possible fix, still through a pull request and review, then the update procedure.
- A 2-week hypercare period after go-live: a short daily check of the logs and the health page.

Acceptance criteria
- [ ] The process is in docs/ADMIN_MANUAL.md and the lab knows where to report.
```

## W7-L11: Licence, ownership and handover

```text
Summary: Licence, ownership and handover package
Zone: Lead
Depends on: the licence decision (D14, done) and the repository ownership
Files allowed (optional): LICENSE, README.md, docs/HANDOVER.md (new)

In plain words (for beginners)
When the course ends the team leaves, but the lab keeps using the tool. We must say who owns the code, what licence it has, and give the lab everything needed to keep it running.

What
- The LICENSE file (AGPL-3.0-or-later, D14) already exists: check that the README states it and that the handover document names the copyright holders (the student authors, who keep their rights) and the lab's right to use the software.
- docs/HANDOVER.md: where the code lives and who has admin rights on the repository (transfer or add the client's account), where the server is and who has access, where the secrets are kept, the backup location and the last drill, the list of open tickets and known problems, and who to ask.
- Remove team members' personal access that the client does not want to keep; transfer repository ownership if agreed; hand over Jira export if wanted.
- A closing meeting with the client: walk through the handover document.

Acceptance criteria
- [ ] The client can run, update, back up and restore the tool using only the handover documents, shown in the closing meeting.
```
