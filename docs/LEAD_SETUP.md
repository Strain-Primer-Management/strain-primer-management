# One-time setup (lead only)

Do this once, before the team starts. Items marked ✅ are already done.

## 1. Where the repository lives

The repository is in the GitHub organisation **Strain-Primer-Management** as `strain-primer-management`
(<https://github.com/Strain-Primer-Management/strain-primer-management>), public, AGPL-3.0-or-later. It starts from one clean commit and was
created and protected by the lead's setup script (kept outside the repository), so there is nothing to do
here. A lead push to `main` needs the ruleset bypass **and** `ALLOW_MAIN_PUSH=1` (PowerShell:
`$env:ALLOW_MAIN_PUSH=1; git push`); everybody else works through branches and pull requests.

## 2. First real test (Docker was not available when this base was created)

```bash
bash setup.sh                       # Windows: powershell -ExecutionPolicy Bypass -File .\setup.ps1
```

Expected: the script finishes with "All set", and <http://localhost:8000> shows the login page;
`admin` / `admin` logs in, and Strains / Plasmids / Primers open. Then run the six checks from the
README. If anything fails, fix it before inviting the team. **Test on every system the team uses:**
`setup.ps1` on Windows, `setup.sh` on macOS and Linux, and try the install commands in
`docs/ONBOARDING.md` for that system. `setup.sh` has been run for real on Linux with real Docker (Nour, 2026-11-10: it works). None of
the install blocks (winget, brew, apt/dnf/pacman) or `setup.ps1` have been run yet. On Linux, `docker compose` needs the compose plugin and a running daemon you are allowed
to use (`sudo systemctl enable --now docker`, and your user in the `docker` group).

## 3. GitHub settings (organisation `Strain-Primer-Management`)

All of this was applied by the lead's setup script and checked through the API on 2026-11-12.

- **Plan:** the organisation is on GitHub **Free** and the repository is **public**, which is what makes the
  rules enforceable. **Never make the repository private** while the plan is Free: the ruleset would still
  say *Active* but enforce nothing. The setup ended with the safe test below (a push that must be rejected).
- **Merge button:** only *Squash and merge*; merged branches are deleted automatically.
- **Security:** secret scanning with push protection, Dependabot alerts and security updates, CodeQL (default
  setup), private vulnerability reporting (`SECURITY.md`).
- **Actions:** only GitHub-owned actions, a read-only token, and approval for every outside contributor.
  Issues, wiki and projects are off; issues and PRs are limited to collaborators for six months at a time
  (renew it before it expires).
- ✅ **Lead-only files guard (automatic, nothing to switch on).** The first step of the `checks` job runs
  `.github/scripts/check_lead_only.sh` on every pull request: if the author is not in `ALLOWED_AUTHORS`
  (in `ci.yml`: `Nour833` and `dependabot[bot]`) and the PR changes a lead-only path (list: `AGENTS.md`
  §3), the check turns red and prints which files and what to do. A *new* file in `docs/ai-log/` is the
  only exception. It is part of `checks`, so it is already required by the ruleset. **When the lead-only
  list in `AGENTS.md` §3 changes, update the `lead_only` pattern in the script too.** If you add a
  co-lead, add their login to `ALLOWED_AUTHORS`.
- ✅ **Other automatic guards on every PR:** `check_ai_log.sh` (short, general AI logs), `check_sensitive.sh`
  (no secrets or real e-mails) and `check_no_ai_credit.sh` (no AI tool as author or co-author). The local
  hooks in `.githooks/` run the same checks.
- ✅ **Ruleset "Protect main"** (Settings → Rules): pull request required with **1 approval**, stale approvals
  dismissed on new pushes, conversations resolved, **code-owner review**, status checks **`checks`** and
  **`docker`**, squash only, no force-push, no deletion. **Only the lead can bypass it**: the one-person team
  `lead-bypass` is the only entry in the bypass list. The lead's AI still asks before every push and PR
  (`AGENTS.md` §5).
  - **Prove the rules are enforced** (done at setup; repeat after any change to the ruleset; *Active* alone
    proves nothing). Safe test, never on `main`: create a second ruleset targeting the branch
    `enforcement-test` with only *Restrict creations* and an empty bypass list, then run
    `git push origin HEAD:enforcement-test`. **Rejected = enforced.** Delete the test ruleset afterwards.
  - The `docker` job builds the image and starts the real stack. If it fails for a reason unrelated to the
    PR (for example a network problem), re-run it.
- ✅ **Code owners:** CODEOWNERS names only people who have joined the organisation; add each new
  teammate's handle to `.github/CODEOWNERS` and `docs/TEAM.md` when they join.
- **People:** the `developers` team (Write access) holds the four teammates; the organisation's default
  permission is none and members cannot create repositories. The lead is the only owner for now; a second
  owner (for example Lina) is a good idea for emergencies and does **not** get the ruleset bypass unless
  added to `lead-bypass`.
- **Require two-factor authentication** for the organisation (Org settings → Authentication security).

## 4. Jira

- ✅ Project key is **`SCRUM`**; the docs already use it.
- The Jira site belongs to Eya's account. ✅ Everyone has accepted the Jira
  invitation. (Previously: make sure Nour, Lina, Zahraa and
  Judy are invited to the site.
- **GitHub autolink** (create it once in the new repository; the setup script does not know the Jira
  site): `SCRUM-<n>` in PR text and commit messages becomes a clickable link to Jira. One command, run by
  the lead: `gh api -X POST repos/<org>/<repo>/autolinks -f key_prefix='SCRUM-'
  -f url_template='https://<jira-site>.atlassian.net/browse/SCRUM-<num>' -F is_alphanumeric=false`.
  One-way only: it links to Jira but does not update tickets.
- **Link GitHub to Jira** (the "GitHub for Atlassian" app; the organisation makes this fully supported):
  **Eya** (Jira site admin) installs the app in Jira and, since she is not an owner of the GitHub
  organisation, chooses *Send them a link*; **Nour** (organisation owner) opens that link and approves the
  connection for **this repository only**. After that, branches, PRs and commits containing `SCRUM-<n>`
  show on the ticket (the app also syncs what already exists). It matches branch names
  `feature/SCRUM-<n>-slug` and PR titles starting with `SCRUM-<n>`.
- **Jira automation (optional):** "PR opened -> In Review" and "PR merged -> Done". Do **not** turn on
  "work item moved to In Progress -> create a branch in GitHub": the AI creates the branch after the plan
  is approved (`AGENTS.md` section 5), so that rule would make duplicates.
- Workflow: `To Do → In Progress → In Review → Done`. Components: `Backend`, `Frontend`.
- Make this the **ticket template**. Only *Zone* and *Acceptance criteria* are required. **"Files allowed"
  is optional and will usually be empty**: Claude Code then proposes the files from the acceptance
  criteria and the developer approves them at the "go" (nothing is blocked):

```text
Zone: Backend | Frontend
Files allowed (optional): apps/strains/models.py, apps/strains/migrations/
   → if given: no other ticket in In Progress / In Review lists the same files
Contract (cross-zone tickets): URL name + template variables, or JSON endpoint URL + JSON shape
Acceptance criteria:
- [ ] ...
Out of scope: ...
Depends on: SCRUM-<n>
```

## 5. Suggested start order (keeps people from blocking each other)

1. **Everyone:** first make sure each person has a **Claude account that includes Claude Code**, then
   read `docs/TEAM_HANDBOOK.pdf` (setup plus how to do the job; send it to the team),
   `CONTRIBUTING.md` and `docs/TEAM.md` (especially the four sharing rules).
2. **Backend, in order:** Primer model → Plasmid model (+ Primer link) → Strain model (+ Plasmid
   link). One open migration PR per app, small PRs, merged fast.
3. **Frontend, in parallel from day one** (no backend needed): design tokens, base layout, shared
   components, each as its own small ticket announced in chat (shared files); then page templates
   as each backend view lands.
4. **Later tickets:** roles & permissions (`setup_roles`), search/filter, backups, SnapGene link,
   CSV import script (bonus), deployment.

The handbook PDF is built by `docs/handbook/build_handbook.py` (needs `pip install reportlab`, which
is not a project dependency). It is a snapshot: when the workflow docs change, update the text in
that script and rebuild with `python docs/handbook/build_handbook.py`.

## 6. How the repository moved to the public organisation (decision D14, reference)

The final repository is public, in a **free GitHub organisation**. A free organisation enforces rulesets
on **public** repositories only, so the repo must be public from its first push, and everything in it must
already be clean. Going back to private later switches the protection off silently.

1. **Before anything:** merge or close open PRs and tell the team to stop working. The old private repo
   (PRs #1 to #12) simply stays where it is on GitHub, unchanged (give the teaching assistant read access
   there if they want the original review record), and the lead keeps the old laptop folder under another
   name. The new repository then re-creates the three ticket PRs (SCRUM-1 to 3, as #1 to #3, which the AI-log entries
   cite) and two small follow-ups in order, so its `main` ends exactly as the cleaned code.
2. **One commit, no history.** Build it locally from the cleaned tree with the GitHub noreply address as
   author. Check that `git log` shows one commit and no real email or full name.
3. **Create the organisation** on the web (GitHub has no API for it), then the teaching assistant's access
   and the Jira app. The **only manual settings**: *Require two-factor authentication* (Org Settings →
   Authentication security; the API cannot set it) and each member accepting their invitation.
4. **Run the setup script** (kept outside the repository until proven; it creates the empty public repo, turns
   on secret scanning with push protection, Dependabot, code scanning and private vulnerability reporting,
   restricts Actions to GitHub-owned actions with a read-only token and approval for every outside
   contributor, limits interactions to collaborators, pushes the single commit, creates the ruleset "Protect
   main", and invites the team). **Only the lead can bypass** the ruleset (a one-person team is the only entry in the
   bypass list); everyone else, including future admins, follows it. The local `pre-commit` hook and the CI step run the same
   `check_sensitive.sh`: no secrets or keys (e-mail addresses are allowed on purpose; override
   `ALLOW_SENSITIVE=1`, lead only, false alarms only).
5. **Prove it:** the script ends with the safe test (a second ruleset on `enforcement-test` with no bypass; the
   push must be **rejected**). `Active` alone proves nothing. Still to see once with your own eyes: the first
   real PR must show *review required* and, for you, the bypass must work.
   **Renew the interaction limit** before it expires (maximum six months; it limits issues, PRs and
   comments to collaborators): `PUT repos/<org>/<repo>/interaction-limits`.
6. **The new address is already in the docs** (`README.md`, `ONBOARDING.md`, `TEAM.md`, the handbook script
   and PDF) before the first push, so there is nothing to update afterwards.
7. **Everyone makes a fresh clone** of the new repository and re-applies unmerged work. Old clones keep
   pointing at the old repository.
8. A second owner (for example Lina) lets the lead remove the admin bypass later.

