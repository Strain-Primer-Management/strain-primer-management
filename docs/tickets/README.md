# Jira tickets: the whole project, wave by wave

> **For AI assistants (and humans): this folder is CONTEXT, not permission.** It shows the whole plan so
> you understand what the other people are working on and what your ticket connects to. Your scope is
> still only what the human pastes (the Jira ticket) plus the plan they approved with "go"
> (`AGENTS.md` section 1). Never start work on a ticket just because it is listed here, and never touch
> files "because another ticket will need them".
>
> How to use it in a session:
> 1. Read this README. Then open ONLY the wave file that contains your ticket (find it by the `Summary:` line
>    of the pasted ticket; the SCRUM number is only in Jira) and skim the tickets next to it.
> 2. Check "Depends on": a dependency that is not on `origin/main` yet means stop and tell the human.
> 3. Check the tickets of the OTHER zone in the same wave: they tell you the contract (URL names, context
>    variables, JSON shape) the other side expects. Match it, or tell the human about the difference.
> 4. If the pasted ticket and this folder disagree, the pasted ticket wins; mention the difference.
> 5. These files are lead-only (`docs/**`). Do not edit them; the lead updates them when plans change.

One file per wave. Wave 1 (foundation: database, accounts, login/register, design foundation) was created
in Jira first. Later waves are created in Jira only when the wave they depend on is (mostly) merged, so a
ticket listed here may not exist in Jira yet.

## How to use these files
1. Copy a whole grey box into a Jira ticket. Its first line (`Summary:`) is the title.
2. "Depends on" uses ticket TITLES. Replace them with `SCRUM-` numbers after you create the tickets.
3. A "parent" ticket (names ending in `-MAIN`) gets its sub-tasks as Jira **sub-tasks**.
4. Whoever takes a ticket starts **Claude Code** in the project folder and pastes the starter message from
   `docs/PROMPTING_GUIDE.md` together with the ticket text. "Files allowed" can stay empty: Claude Code
   proposes the files and you approve them.
5. Words you do not know? See the glossary at the top of `wave-1-foundation.md`.
6. Labels like `W2-B3` or `W5-L1` (wave, B = backend, F = frontend, L = lead) are only for finding your way in
   these files and in the chat. Jira only needs the `Summary:` line as the title.
7. Tickets marked WAITING or "Depends on: client answers" must not start before the lead has written the
   client's answer in `docs/DECISIONS.md` (wave 0, ticket L-6).

## Import into Jira (CSV)

`jira-import.csv` has every ticket of waves 0 and 2 to 7 (98 tickets), ready for Jira's CSV import. Wave 1
is already in Jira, so it is not in the file. Rebuild the file after editing the ticket files with
`python docs/tickets/tickets_to_csv.py` (add `--waves 2,3` for only some waves). The script sits next to the
ticket files it reads.

What is in it:
- **Order:** wave by wave, as in the files, so Jira numbers the tickets in that order.
- **Parents and sub-tasks:** the four frontend parent tickets (W2-F-MAIN to W5-F-MAIN) are Tasks, and their
  25 frontend tickets (W2-F1 ...) are **Sub-tasks** that point at the parent through the **Parent** column.
  Every other ticket is a Task.
- **Description:** the whole ticket box (zone, depends on, what, acceptance criteria), with its plan ID on top.
- **Sprint = wave:** a `Sprint` column, empty until you give it the sprint IDs (see "Sprints" below). The
  label `wave-N` is always there, so you can also assign sprints in the backlog.
- **Backend / Frontend:** the component Backend, Frontend or Lead (three team-wide tickets have the label
  `team` and no component), plus the labels `wave-N`, the plan ID and the zone.

How to import (company-managed project; create the components Backend, Frontend and Lead first, ticket L-5):
1. Jira: Settings (gear) → System → External system import → CSV. Upload the file, choose the project SCRUM.
2. Map the columns: Summary, Issue Type, Description, **Parent → Parent**, all four **Labels** columns →
   Labels, Component/s → Components, Sprint → Sprint (only if you filled it), and Issue id → Issue id (the
   Parent column refers to it). In a
   team-managed project the sub-task type is called "Subtask": map the value "Sub-task" to it.
3. Test with a few rows first (`--waves 0` makes a short file), check the result, then import the rest.
4. Links between tickets are not in the file (Jira Cloud's importer is unreliable for them). Each description
   keeps its "Depends on:" line, which uses ticket titles; replace them with SCRUM numbers if you like.

### Sprints (one sprint per wave)

Jira's CSV import **cannot create sprints**, and for the Sprint column it wants the sprint's **numeric ID, not
its name** (a name imports the ticket without a sprint). So:
1. In the board's backlog create one sprint per wave and name it `Wave 0`, `Wave 2`, `Wave 3`, `Wave 4`,
   `Wave 5`, `Wave 6`, `Wave 7`. Do not start them yet.
2. Find each ID: in the issue search type `sprint = ` and Jira lists the sprints with their IDs (or hover
   the sprint). Then build the file: `python docs/tickets/tickets_to_csv.py --sprint-ids 0=101,2=102,...`
3. Import, mapping Sprint → Sprint. A wave you leave out of `--sprint-ids` gets no sprint.
4. Simpler alternative with no IDs: import without sprints, then in the backlog filter `labels = wave-2`,
   select all, and use *Add to sprint*.

Waves 0 and 6 run alongside the others, and Jira normally allows only one active sprint per board (the site
admin can enable parallel sprints). Start only the sprint of the wave being built, and leave waves 0 and 6 out
of `--sprint-ids` (or start them only if parallel sprints is on). Demos stay every two weeks, whatever sprint
is running.

Create later waves in Jira only when the wave they depend on is mostly merged (see above): import one wave at
a time with `--waves 2` if you prefer.

## The waves

| Wave | File | What it delivers |
|---|---|---|
| 0 | `wave-0-lead-and-team-tasks.md` | Not code: verifying the setup, GitHub/Jira settings, client questions, team routines |
| 1 | `wave-1-foundation.md` | Database schema, roles, accounts, login/register, design foundation (already in Jira) |
| 2 | `wave-2-browse-and-edit-records.md` | Pages to list, view, create, edit and delete strains, plasmids and primers, and to link them (7 backend + 10 frontend) |
| 3 | `wave-3-search-and-filter.md` | Fast search and filtering, including live search (5 backend + 7 frontend) |
| 4 | `wave-4-lab-features.md` | SnapGene link, sequence display, lineage, data-entry helpers (1 spike, 5 backend, 1 lead, 7 frontend) |
| 5 | `wave-5-data-import-export-backup.md` | Import from CSV, export, backups and restore, extra fields, change history, data quality (7 backend, 3 lead, 5 frontend) |
| 6 | `wave-6-quality-security-docs.md` | Security, accessibility, performance, testing, manuals, final report (runs alongside waves 2 to 5) |
| 7 | `wave-7-deployment-and-go-live.md` | Production setup on the lab computer, real data, go-live, support, handover (11 lead tickets) |

## What blocks what
```
Wave 1  B1 Schema ──┬─> B2 Roles ──────────┐
                    ├─> B3 Accounts ──> F-5, F-6
                    └─> B4 Fake data       │
        F-1 Design foundation ─> F-2 ─> F-3 ─> F-4 Login
Wave 2  W2-B1 Shared helpers ─> W2-B2/B3/B4 CRUD per entity ─> W2-B5 Links ─> W2-B6 Delete-with-choice
        W2-F-MAIN (lists, details, forms, links, delete page) follows each backend ticket
Wave 3  Search and filter (needs wave 2 lists)
Wave 4  Lab features (SnapGene, sequences, lineage) (needs wave 2; SnapGene also needs a client decision)
Wave 5  Import / export / backups / extra fields / history (needs the schema and wave 2)
Wave 6  Quality, security, docs (runs alongside waves 2 to 5, finishes before wave 7)
Wave 7  Deployment and go-live (needs waves 2 to 5 and the client decisions)
```
Wave 0 tickets run in parallel with everything.

## Rules that apply to every ticket (so they are not repeated each time)
- One ticket = one branch = one pull request. Small and fast.
- Backend changes ship with tests. Frontend changes ship with a screenshot and the browser checklist.
- A change to the database structure follows the migration rules: one open migration pull request per app,
  never edit a merged migration, and announce any reset in the team chat.
- Shared files (the page layout, the components, `apps/core/`) change only through their own small ticket,
  announced in the team chat first.
- Search the project for an existing piece before creating a new one. Never copy-paste a block.
- The six checks must be green before saying "ship it".

## Who does what (when the team is complete)
- Backend: Nour and Lina. Frontend: Eya, Zahraa and Judy. Lead tasks (`config/`, Docker, CI, docs): Nour.
- Suggested split in wave 2: Nour = primers + plasmids pages, Lina = strains pages; Eya = list pages and shared
  components, Zahraa = strains pages, Judy = plasmids and primers pages. Adjust as people join.

## Parking lot: ideas NOT planned (only if the client asks)
Barcode or QR labels for tubes, a freezer map view, a plasmid-map viewer, sequence alignment, email
notifications, single sign-on, a mobile layout, German translation (the client wants English only).
