# Syncing with `main` — the only merge an AI may run

**For AI agents. Read this completely before you start, and follow it step by step.**

You may do this **only when the human asks** ("update my branch from main", "my PR has conflicts")
or agrees to your proposal from the freshness check. Never on your own initiative. The **only merge
you may ever run** is `origin/main` into the human's own feature branch.

**Principle:** Git does the work. A clean merge needs **zero edits from you**. You only judge real
conflicts, and only inside the conflict markers. When in doubt, abort and ask. Aborting is always safe.

## 1. Preconditions

- You are on the feature branch (**never** `main`) and `git status` is clean (everything committed).
- Note the starting point: `git rev-parse HEAD`.

## 2. Start the merge without committing

```bash
git fetch origin
git merge --no-commit --no-ff origin/main
```

Nothing is committed yet, so `git merge --abort` returns you to the exact starting point.

## 3. No conflicts?

If the merge succeeded and `git diff --name-only --diff-filter=U` prints nothing: **do not touch any
file.** Go to step 6.

## 4. Conflicts: decide first whether you may touch them

`git diff --name-only --diff-filter=U` lists the conflicted files. Run `git merge --abort`, tell the
human which files and why, and **ask the lead (Nour or Lina)** if **any** of these is true:

- a conflicted file is **outside the approved scope**, or is a **migration** (`*/migrations/*`),
  `requirements/`, `config/`, any other lead-only file, or a binary file;
- there are **more than 3 conflict hunks** in total;
- **both sides changed the same line(s) differently** (a *clash*). That is a decision about how the
  program should behave, not a merge. Example: one side sets `base = 10` to `11`, the other to `12`.

You may resolve only **independent** changes: both sides touched *different* lines that merely sit
next to each other (two new imports, two new URL entries, two new test functions).

## 5. Resolve surgically

For every hunk:

1. Tell the human in plain language what **our side** did and what **their side** did (quote both).
2. Edit **only between the conflict markers** of that file. Not one character elsewhere, in that
   file or any other. No reformatting, no renames, no clean-ups.
3. The resolution may contain **only lines that already exist verbatim** in our version or their
   version of that file. Keep **both sides' intent** (normally both changes, in a sensible order).
   Never drop a side's lines unless the human confirms after seeing them. If the result needs a
   **new line** to work, that is a human decision: abort and ask the lead.
4. Not 100% sure what a hunk means? Stop and ask. Never guess.

## 6. Verify before committing (all must pass)

**a. No invented lines.** For every resolved file `<f>` this must print **nothing**:

```bash
grep -vxFf <(git show HEAD:<f>; git show origin/main:<f>) <f>
```

(No bash? Write the two versions to temporary files **outside the repository** and run the same
`grep -vxFf` against them.) Anything it prints is a line that exists in neither version, so you
invented it: fix it or abort.

**b. No leftover markers or whitespace damage:**

```bash
git add <resolved files>
git diff --cached --check
```

**c. Show the human each resolved file** (`git diff --cached <f>`) and **wait for a yes.**

**d. Run all six checks** (`AGENTS.md` §9) on the uncommitted merge. If they are red because of the
merge and the fix is not inside the approved scope: `git merge --abort` and report. Never "fix" other
people's code. If `makemigrations --check` reports **conflicting migrations**, that is not yours to
fix: `git merge --abort` and follow `CONTRIBUTING.md` → *Migrations* with the lead.

## 7. Commit, then prove the scope did not grow

```bash
git commit -m "SCRUM-<n>: Merge main into <branch>"
git diff --name-only origin/main HEAD      # must list exactly the approved files (plus the ai-log)
git log origin/main..HEAD --format=%s      # every subject starts with SCRUM-<n>:
```

Anything else in the first list: stop and tell the human. Re-run the six checks. **Pushing still needs
its own "Push now?" yes** (`AGENTS.md` §5).

## Why these checks

Each one was tested in a throw-away repository: a clean merge needs no edits; a union of independent
lines passes; an invented line is caught by 6a; a leftover marker is caught by 6b; the scope check
in step 7 lists only the branch's own files; and `git merge --abort` restores the exact starting point.
