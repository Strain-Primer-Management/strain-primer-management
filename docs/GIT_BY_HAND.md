# Git by hand

Use this when you do not use **Claude Code**, or it cannot reach Git. Every case is a box to copy.
Replace the example `SCRUM-12` and `short-name` with your own. Branch names look like
`feature/SCRUM-12-short-name` (2–5 lowercase words with dashes). Commit messages start with the ticket:
`SCRUM-12: what I did`. Open a terminal in the project folder first.

## The easy way: the Git helper

Everything below is also available as a **menu you can just answer**. It talks in plain language, shows
the exact command, explains it, and **asks before it changes anything**. It already knows our rules: it
refuses to work on `main`, never force-pushes, and starts every commit message with your ticket.

```bash
bash tools/git-helper.sh                                          # macOS / Linux
powershell -ExecutionPolicy Bypass -File tools\git-helper.ps1     # Windows
```

| Menu | What it does |
|---|---|
| 1 Where am I? | Explains your situation in plain words and tells you which option to use next |
| 2 Is my setup right? | Checks your name and email, GitHub login and the safety net, and offers to fix them |
| 3 Start a ticket | Makes your branch (`feature/SCRUM-12-short-name`) from the newest `main` |
| 4 Continue a ticket | Lists the tickets you already started and switches back to one |
| 5 See what I changed / saved | Unsaved changes, what you already saved, and exactly what the pull request will contain |
| 6 Save my work | You pick the files, it adds `SCRUM-12:` to your message, refuses secrets, can run the checks first |
| 7 Send to GitHub | Pushes your branch (never `main`, never forced) and opens the pull request |
| 8 Run the six checks | Same checks as GitHub, with a plain explanation of any failure |
| 9 Where is my pull request? | Shows its checks and review status |
| 10 Next ticket | Back to a fresh `main` after your PR was merged |
| 11 Remove, close or clean up a ticket | Tidies finished tickets automatically, or removes one: *finished*, *never sent* (delete), *back it up to GitHub first*, or *cancel completely* (closes the PR). Asks what happened and confirms before anything is lost |
| 12 Get newest main | Brings `main` into your branch |
| 13 I have a conflict | Step by step, with a safe cancel that restores everything |
| 14 After a pull: migrations / reset my database | Restarts the app to apply new migrations, shows migration status, or resets your local database when the team reset the migrations |
| 15 Teammate's branch | Look at someone else's branch, and go back |
| 16 Set edits aside | Put unsaved edits in a "drawer" to switch branch, and take them out again |
| 17 Oops | Rescue menu: committed on `main`, undo a save, put a file back, wrong file, who-are-you, rejected push… |
| 18 I am lost | Prints a report to paste in the team chat |
| 19 What is the difference between…? | Explains the look-alikes: save vs send, merge vs pull, restore vs undo, finished vs cancelled… |

At the top of the menu it also **suggests your next step** (in colour: green fine, yellow careful, red stop).

The rest of this file is the same thing by hand.

| I want to… | Case |
|---|---|
| Start a ticket | 1 |
| See what I changed | 2 |
| Save my work | 3 |
| Send it to GitHub and open the pull request | 4 |
| Get the newest changes from `main` | 5 |
| Fix conflicts | 6 |
| Change something after a review | 7 |
| Look at a teammate's branch | 8 |
| Start the next ticket | 9 |
| I committed on `main` by mistake | 10 |
| Something else went wrong | the **Oops** table |

## Case 1 — Start a ticket (new branch)

```bash
git fetch origin
git switch -c feature/SCRUM-12-short-name --no-track origin/main
```

You should see: `Switched to a new branch 'feature/SCRUM-12-short-name'`.

## Case 2 — See what I changed

```bash
git branch --show-current     # which branch am I on?
git status                    # which files changed?
git diff                      # what exactly changed (press q to leave)
```

## Case 3 — Save my work (commit)

```bash
git add path/to/file1 path/to/file2
git commit -m "SCRUM-12: Short description of what you did"
```

Name every file. **Never `git add .`** Run the six checks (README) before you commit. If Git says
`Blocked: you are on 'main'`, see the Oops table.

## Case 4 — Send it to GitHub and open the pull request

```bash
git push -u origin feature/SCRUM-12-short-name
```

The output contains a link ("Create a pull request for…"): open it, fill in the template, click
**Create pull request**. With the GitHub CLI you can use
`gh pr create --base main --title "SCRUM-12 Short description"` instead. Then ask a teammate to review.
When the checks are green and it has one approval, click **Squash and merge**. Later pushes on the same
branch are just `git push`.

## Case 5 — Get the newest changes from `main`

```bash
git fetch origin
git merge origin/main -m "SCRUM-12: Merge main into my branch"
```

No conflict: done (run the checks, then `git push`). Conflict: Case 6. Want to cancel: `git merge --abort`.

## Case 6 — Fix conflicts (Git says `CONFLICT`)

1. `git status` lists the conflicted files under *Unmerged paths*.
2. **Stop and ask Nour or Lina, then run `git merge --abort`,** if a conflicted file is not one of your
   ticket's files, is a migration, or you do not understand it, or both sides changed the same line.
3. Otherwise open the file and find the blocks:

   ```text
   <<<<<<< HEAD
   your version of the lines
   =======
   their version of the lines (from main)
   >>>>>>> origin/main
   ```

4. Keep what both sides need (usually both sets of lines) and delete the three marker lines. Do not
   guess: unsure means ask.
5. Save, then:

   ```bash
   git add path/to/the-file
   git commit -m "SCRUM-12: Merge main into my branch"
   ```

6. Run the six checks, then `git push`.

## Case 7 — Change something after a review

```bash
git add path/to/file
git commit -m "SCRUM-12: Address review comments"
git push
```

The pull request updates by itself.

## Case 8 — Look at a teammate's branch

```bash
git fetch origin
git switch their-branch-name
docker compose restart web
```

Commit your own work first. When you are done: `git switch main` (or back to your own branch).

## Case 9 — Start the next ticket

```bash
git switch main
git pull --ff-only
```

Then Case 1. (`--ff-only` is safe: it can never create a mess.) Leave old branches alone.

## Case 10 — I committed on `main` by mistake (not pushed yet)

```bash
git switch -c feature/SCRUM-12-short-name   # your commit now lives on this branch
git switch main
git reset --hard origin/main              # main is back to normal; your work is safe on the new branch
git switch feature/SCRUM-12-short-name
```

This is safe **only** because the commit is saved on the new branch first. Unsure? Ask Nour.

## Oops table

| Situation | Do this |
|---|---|
| `Blocked: you are on 'main'`, or I edited files on `main` | `git switch -c feature/SCRUM-12-short-name` (your edits come along) |
| I pushed to `main` by mistake | **Do not fix it yourself. Tell Nour right now.** |
| Undo my last commit, keep my changes (not pushed) | `git reset --soft HEAD~1` |
| Put a file back exactly as in my last commit (**loses** my edits to it) | `git restore --source=HEAD --staged --worktree path/to/file` |
| I staged the wrong file (before committing) | `git restore --staged path/to/file` |
| I committed or pushed something wrong on my branch | Fix it, make a **new** commit, `git push`. Never force-push. |
| "Please tell me who you are" | `git config --global user.name "Your Name"` and `git config --global user.email "you@example.com"` (name = your real name; email = your GitHub email, or its no-reply address from github.com/settings/emails) |
| `git status` shows files I never touched | Do not add them. Ask Nour. |
| Push rejected (non-fast-forward) | Do not force. `git fetch origin`, then ask Nour. |
| I am lost | `git status`, copy the output into the team chat. Do not type commands you do not understand. |

**Never:** `git push --force`, `git add .`, `git rebase`, `git reset --hard` (except Case 10), `git pull`
on your own branch (use Case 5), or deleting branches.
