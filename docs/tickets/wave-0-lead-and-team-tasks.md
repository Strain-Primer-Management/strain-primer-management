# Wave 0: lead and team tasks (not code)

These run alongside everything else. "Zone: Lead" means Nour; "Zone: Team" means everyone does it.

## L-1: Verify the setup on every system

```text
Summary: Verify the setup on every operating system the team uses
Zone: Team
Depends on: nothing

In plain words (for beginners)
The setup instructions were written and tested on one Linux machine. Before real work starts we must know they also work on Windows and macOS. Every person follows docs/ONBOARDING.md on their own computer and reports what went wrong.

What
- Each teammate follows docs/ONBOARDING.md (or the PDF handbook) from step 1 to step 6 on their own computer.
- Write down every step that was unclear or failed (system, step number, the error text, a screenshot).
- Nour fixes the docs and scripts (setup.ps1, setup.sh, the winget/brew/apt commands) from the reports.

Acceptance criteria
- [ ] Windows, macOS and Linux each completed steps 1 to 6 at least once.
- [ ] Every reported problem is either fixed in the docs/scripts or has a ticket.
- [ ] The helper menu (tools/git-helper) starts on each system and option 2 ("Is my setup right?") is all green.
```

## L-2: Practice run for every teammate

```text
Summary: Practice run (SCRUM-0) for every teammate
Zone: Team
Depends on: Verify the setup on every operating system

In plain words (for beginners)
Before the first real ticket, everybody does one fake ticket from start to finish: Claude Code creates a branch, a tiny file, a pull request, and we close it. This teaches the whole routine with nothing at stake.

What
- Follow the "Practice run" section of docs/ONBOARDING.md with Claude Code.
- Say "go", look at the changes, say "ship it", ask a teammate to review, watch the checks, then CLOSE the pull request without merging.

Acceptance criteria
- [ ] Each person opened and closed one practice pull request.
- [ ] Each person can explain what "go" and "ship it" mean and what the six checks are.
- [ ] Anything confusing was written down for Nour (feeds the docs).
```

## L-3: Invite everyone and complete CODEOWNERS

```text
Summary: Invite everyone and complete CODEOWNERS
Zone: Lead
Depends on: nothing (run as soon as each username is known)
Files allowed (optional): .github/CODEOWNERS, docs/TEAM.md, docs/LEAD_SETUP.md

In plain words (for beginners)
CODEOWNERS is a file saying who must approve changes to which folders. Each time a person joins we add their GitHub name, and remove the temporary placeholders.

What
- Invite Lina, Zahraa and Judy as collaborators with Write access (Settings > Collaborators). Confirm each accepted. DONE for all (Eya, Lina, Zahraa, Judy).
- /apps/ has Nour and Lina (done). /templates/ and /static/ have Eya, Zahraa and Judy, with Nour and Lina as backup reviewers (done).
- Add the handles to the table in docs/TEAM.md.
- After merging, open GitHub's CODEOWNERS page for the repo: there must be no errors.

Acceptance criteria
- [ ] All five people are collaborators with Write (not Admin).
- [ ] A test pull request touching /templates/ asks for review from the frontend owners (Nour and Lina only as backup).
- [ ] CODEOWNERS shows no errors on GitHub.
```

## L-4: GitHub settings round

```text
Summary: GitHub settings round (alerts, required checks, review of the rules)
Zone: Lead
Depends on: Invite everyone and complete CODEOWNERS

In plain words (for beginners)
Some safety settings can only be switched on in the GitHub website. This ticket is the checklist for them.

What
- Settings > Code security: turn on Dependabot alerts (free). DONE 2026-11-11.
- Settings > Rules > Protect main: add the `docker` job next to `checks` under "Require status checks" once it has passed at least 10 times. DONE 2026-11-11.
- Decide whether to remove the admin bypass from the ruleset now that others can approve (if yes: remember your own PRs then need a teammate's approval).
- Confirm the workflow permissions are read-only (Settings > Actions > General).
- Confirm "Automatically delete head branches" and squash-only merging are still on.

Acceptance criteria
- [ ] Each item done or consciously decided (decision written in docs/DECISIONS.md).
```

## L-5: Jira setup

```text
Summary: Jira setup (template, workflow, board, rhythm)
Zone: Lead (with Eya, who owns the Jira site)
Depends on: nothing

In plain words (for beginners)
Jira is our to-do board. A little setup makes tickets easy to write and easy to follow.

What
- Description template with the lines: Zone, Files allowed (optional), Contract, Acceptance criteria, Out of scope, Depends on (see docs/LEAD_SETUP.md).
- Columns: To Do, In Progress, In Review, Done. Components: Backend, Frontend, Lead.
- Labels per area: accounts, strains, plasmids, primers, search, import, backup, deploy.
- One sprint per wave (Wave 0, Wave 2, ...), as in `docs/tickets/README.md`. Client demos stay every two weeks, whatever sprint is running.
- Optional: try the GitHub-for-Jira link (Eya installs the app, Nour approves on GitHub); if a personal GitHub account is not supported, skip it.
- A rule everyone follows: move your ticket to In Progress when you start and to In Review when the pull request is open.

Acceptance criteria
- [ ] A new ticket created from the template looks right.
- [ ] The board shows the four columns and the components.
```

## L-6: Questions for the client

```text
Summary: Collect the open client questions and record the answers
Zone: Lead
Depends on: nothing

In plain words (for beginners)
Some decisions are not ours: they belong to the client (the lab). We ask them once, in one message, and write the answers down so nobody has to ask again.

What
Send ONE message to the client (Max / Mateusz) with these questions, then record each answer in docs/DECISIONS.md:
1. Primer melting temperature (Tm): which formula should we use?
2. Primer sequences: only A, C, G, T, or also ambiguity letters (N, R, Y, ...)?
3. Should "purpose" (Sequencing, PCR, Cloning, ...) be a fixed list or free text? Which values?
4. Biosafety level: which values do they use (BSL-1, BSL-2, ...)?
5. Backups: answered by the client's e-mail (automatic backups; an admin copies them to another system by hand). Still to ask: how often, how long to keep them, who restores?
6. Import: what format can the Word files be exported to (CSV/Excel)? Can they provide 20-50 anonymised sample records (after asking the professor)? (They already sent excerpts of the three Word files; those stay out of Git.)
7. SnapGene: may we test "click to open" on one lab PC? Is the Hessenbox folder synced on the lab computer that will host the app?
8. Hosting: the group wants its own hardware and suggests a NAS server (bring pros and cons to the next meeting). Which machine (lab computer or NAS), operating system, is it on 24/7, who restarts it, what is its network name?
9. Who may see which data: may students export data? Is any data confidential?
10. Licence and ownership: answered. The client confirmed by e-mail that open source is fine; students keep the rights to their own code (course rules); the team chose AGPL-3.0-or-later (D14).
11. How should demos and change requests be collected (every two weeks)?

Acceptance criteria
- [ ] The message is sent; every answer (or "not decided yet") is in docs/DECISIONS.md.
- [ ] Tickets that were waiting for an answer are updated.
```

## L-7: Claude accounts and access

```text
Summary: Claude accounts: everyone can use Claude Code
Zone: Lead
Depends on: nothing

In plain words (for beginners)
Claude Code needs a Claude account. Sharing one personal account between several people is probably not allowed, so we need a proper plan.

What
- Check Anthropic's terms for team use; decide the plan (individual subscriptions, a team plan, or API access) and who pays.
- Make sure each teammate can run `claude` and sign in.
- Record the decision in docs/DECISIONS.md.

Acceptance criteria
- [ ] All five people can start Claude Code in the project folder.
- [ ] The decision is written down.
```

## L-8: Tune the AI rules after week 1

```text
Summary: Review and trim AGENTS.md after the first week
Zone: Lead
Depends on: Practice run for every teammate (plus about a week of real tickets)
Files allowed (optional): AGENTS.md, docs/PROMPTING_GUIDE.md, docs/SYNC_WITH_MAIN.md

In plain words (for beginners)
AGENTS.md is the rulebook Claude Code follows. It is long. After a week we look at what actually happened and keep only what helps.

What
- Read the docs/ai-log/ files and the closed/merged pull requests. List the rules that were broken, ignored or caused friction.
- Shorten wording, remove rules nobody needs, add rules for real problems.
- Check that all documents still agree with each other.

Acceptance criteria
- [ ] AGENTS.md is shorter (target under 300 lines) with no lost safety rule.
- [ ] A list "what we changed and why" is in the pull request.
```

## L-9: Demo and change-request routine

```text
Summary: Bi-weekly client demo and change-request routine
Zone: Lead (recurring ticket, one per demo)
Depends on: nothing

In plain words (for beginners)
The client wants a demo every two weeks. We prepare the same way each time, and every new wish becomes a ticket we can prioritise.

What (each demo)
- Two days before: pick what to show, run it from a fresh clone on one PC (the demo machine), seed fake data (never real data).
- Write a short demo script (5 to 10 steps) and test it once.
- During the demo: one person drives, one person writes down every wish and question.
- After the demo: turn each wish into a Jira ticket labelled "change-request" and ask the client to order them by priority.

Acceptance criteria
- [ ] Demo ran from a clean setup. Every wish is a ticket or an answered question.
```

## L-10: Working agreements

```text
Summary: Team working agreements
Zone: Team
Depends on: nothing

In plain words (for beginners)
A few simple team promises prevent waiting around and surprises.

What (agree, then write it in docs/TEAM.md)
- Review turnaround: a pull request gets its first review within one working day.
- Who reviews whom (rotation), so nobody is always waiting for the same person.
- A short daily check-in (chat message: what I did, what I will do, where I am stuck).
- When stuck for more than 30 minutes: ask in the team chat, with the report from the helper menu (option 18).
- Definition of done: tests added, six checks green, ticket moved, documentation updated if behaviour changed.

Acceptance criteria
- [ ] Everyone agreed; the text is in docs/TEAM.md (lead PR).
```
