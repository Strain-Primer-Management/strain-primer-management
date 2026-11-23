# Onboarding: from zero to running (about 30 minutes)

Works on **Windows, macOS and Linux**. Do the **6 steps in order**, once. Copy the commands exactly.
After every step, check the **You should see** line before you go on. Steps 2 and 5 have one block per
system: **use only yours**. Everything else is the same for everyone. A printable PDF with the same
steps *and* how to do your job, ticket by ticket, is `docs/TEAM_HANDBOOK.pdf`. Git commands for every
case, without Claude Code: `docs/GIT_BY_HAND.md`.

> **Open a terminal.** Windows: press the Windows key, type `PowerShell`, press Enter. macOS: press
> Cmd+Space, type `Terminal`, press Enter. Linux: any terminal. You do **not** install Python,
> Django or PostgreSQL: Docker does that for you.

## 1. Accounts

Send your **GitHub username** to Nour, accept the **invitation to the GitHub organisation** (it arrives by
email) and turn on **two-factor authentication** on your GitHub account (the organisation requires it). The
Jira invitation is already done. You also need a **Claude** account that includes **Claude Code**: ask
Nour which plan the team uses.

- **You should see:** the organisation **Strain-Primer-Management** under your profile menu, *Your organizations*.
- **If not:** ask Nour to send the invitation again, and check your spam folder.

## 2. Install the programs (including Claude Code)

### Windows (PowerShell)

Copy the whole block and press Enter. Say Yes to any Windows prompt.

```powershell
$flags = "--accept-source-agreements", "--accept-package-agreements"
winget install -e --id Git.Git $flags
winget install -e --id Docker.DockerDesktop $flags
winget install -e --id Microsoft.VisualStudioCode $flags
winget install -e --id GitHub.cli $flags
winget install -e --id Anthropic.ClaudeCode $flags
```

Then **restart your PC**, close PowerShell and open a fresh one. Open **Docker Desktop** from the Start
menu, accept the terms, and wait.

### macOS (Terminal)

1. Install **Homebrew** from <https://brew.sh>: copy the one command shown on that page into Terminal,
   then run the "Next steps" lines it prints.
2. Then:

   ```bash
   brew install git gh
   brew install --cask visual-studio-code claude-code
   ```

3. Download **Docker Desktop for Mac** from <https://www.docker.com/products/docker-desktop> (pick
   **Apple chip** or **Intel chip**), drag it into Applications, open it, accept the terms, and wait.

### Linux

Run the line for your distribution:

```bash
# Debian / Ubuntu
sudo apt update && sudo apt install -y git gh docker.io docker-compose-v2
# Fedora
sudo dnf install -y git gh docker docker-compose
# Arch / CachyOS / Manjaro
sudo pacman -S --needed git github-cli docker docker-compose
```

Then, on every distribution:

```bash
sudo systemctl enable --now docker
sudo usermod -aG docker $USER
curl -fsSL https://claude.ai/install.sh | bash
```

Then **log out and log in again** (or restart), so Docker works without `sudo`. On other or older
distributions, follow <https://docs.docker.com/engine/install/> and make sure `docker compose version`
works. (The last line is Anthropic's official Claude Code installer.)

### On every system

Use VS Code (Linux: <https://code.visualstudio.com>) with the extension **EditorConfig**, or any editor
you like.

- **You should see:** Windows/macOS: Docker Desktop shows **Engine running**. Linux: `docker ps` prints a
  table header and no error. Everywhere, in a **new** terminal: `claude --version` prints a version.
- **If not:** Windows: Fix A or B. Linux: Fix G. macOS: Fix H. `claude` not found: Fix I.

## 3. Sign in to GitHub and to Claude Code

```bash
gh auth login
claude
```

**gh:** answer **GitHub.com**, then **HTTPS**, then **Yes** (authenticate Git), then **Login with a web
browser**; paste the code it shows on the page that opens. **claude:** it opens your browser: sign in
with your Claude account. When **Claude Code** shows its prompt, type `/exit` and press Enter.

- **You should see:** `gh` says you are logged in as your GitHub username, and **Claude Code** shows its
  prompt after you sign in.
- **If not:** GitHub: Fix C. Claude Code: Fix I.

## 4. Tell Git your name

```bash
git config --global user.name "Your Name"
git config --global user.email "you@example.com"
```

Replace **Your Name** with the name you want shown on your work and **you@example.com** with the email you want on your commits. The repository is public, so both are visible to everyone and cannot be removed once pushed. Use your personal email if you are fine with that. If you would rather keep it private, use **GitHub's no-reply address** instead (copy it from <https://github.com/settings/emails>; it looks like `12345678+yourusername@users.noreply.github.com`). **Keep the quotes.**

- **You should see:** nothing is printed. That is normal.

## 5. Download the project and start it

### Windows (PowerShell)

```powershell
mkdir C:\dev
cd C:\dev
git clone https://github.com/Strain-Primer-Management/strain-primer-management.git
cd strain-primer-management
powershell -ExecutionPolicy Bypass -File .\setup.ps1
```

### macOS and Linux (Terminal)

```bash
mkdir -p ~/dev
cd ~/dev
git clone https://github.com/Strain-Primer-Management/strain-primer-management.git
cd strain-primer-management
bash setup.sh
```

The first time takes several minutes (a few hundred MB). Do not close the window. Do not put the
project in OneDrive, iCloud, Desktop or Documents: sync tools fight with Docker.

- **You should see:** **All set.** Then open <http://localhost:8000> and log in with `admin` / `admin`.
  That login exists only on your own computer.
- **If not:** port busy → Fix D. Anything else → Fix E.

The script also switches on a safety net on your computer: `git commit` and `git push` directly on
`main` are blocked. All work goes through a branch and a pull request, which **Claude Code** sets up
for you.

## 6. Check that it works

```bash
docker compose exec web python manage.py test
```

- **You should see:** **OK** at the end of the output.
- **If not:** Fix E.

## Practice run (once, before your first real ticket)

In the project folder, start **Claude Code** (type `claude`), paste the starter message from
`docs/PROMPTING_GUIDE.md`, and use this ticket:

```text
I am <your name>.
Ticket: SCRUM-0 — Practice run. Create only one new file:
docs/ai-log/<today>_SCRUM-0_practice_<yourname>.md, copied from docs/ai-log/_TEMPLATE.md. Touch nothing else.
```

1. Read its plan, say **go**. It creates a branch and the file.
2. Look at the change, say **ship it**. It pushes and opens the pull request.
3. Ask a teammate to review it and watch the `checks` job run.
4. **Close the PR without merging** (the *Close pull request* button on GitHub). Claude Code never
   closes or merges PRs.

## If something goes wrong

| Fix | Problem | What to do |
|---|---|---|
| **A** | Windows: `winget` is not recognized | Install **App Installer** from the Microsoft Store and try again. Or install by hand: git-scm.com/download/win, docker.com/products/docker-desktop (choose **WSL 2**), code.visualstudio.com, cli.github.com, and for **Claude Code** the PowerShell line from code.claude.com/docs/en/setup. |
| **B** | Windows: Docker shows a WSL or virtualization error | PowerShell as administrator: `wsl --install`, restart the PC. Still stuck: enable *Intel VT-x* / *AMD SVM* in the BIOS, then restart. |
| **C** | GitHub login fails, or the wrong account | `gh auth logout`, then `gh auth login` again, signed in to the right account in the browser. "Repository not found" means the invitation (step 1) was not accepted. |
| **D** | Port 8000 is busy | Close the other program that uses it, or ask Nour. Do not change project files for this. |
| **E** | The app does not start, or anything else | `docker compose logs -f web`, copy the last 20 lines into the team chat. To reset: `docker compose down -v`, then repeat step 5. |
| **F** | After a restart the app is gone | Start Docker Desktop (Linux: it starts by itself), wait for it, then run `docker compose up -d` in the project folder. |
| **G** | Linux: `permission denied` on Docker, or the daemon is not running | `sudo systemctl enable --now docker`, then `sudo usermod -aG docker $USER`, then **log out and log in again**. Files in the project owned by root: copy `.env.example` to `.env` and set `UID` and `GID` to the output of `id -u` and `id -g`. |
| **H** | macOS: `brew` or `git` not found, or Docker not running | Install Homebrew from brew.sh and run the "Next steps" lines it prints, then open a new Terminal. For Docker: open Docker Desktop and wait for *Engine running*. |
| **I** | `claude`: command not found, or it will not sign in | Open a **new** terminal and try `claude --version`. Still failing: the troubleshooting page <https://code.claude.com/docs/en/troubleshoot-install>, or ask Nour. Signing in needs a Claude account that includes **Claude Code**. |
| **J** | After a pull the app shows migration errors, or the team reset the migrations | `docker compose restart web` applies new migrations. If the team reset or squashed them (or errors say *already exists* / *does not exist*): `docker compose down -v`, then run the setup script again (step 5). Helper: option 14, d. |

## Every day

Windows: `cd C:\dev\strain-primer-management`. macOS and Linux: `cd ~/dev/strain-primer-management`. Then:

```bash
docker compose up -d            # start the app (Fix F if it was stopped)
claude                          # start Claude Code in the project folder
```

Stuck with Git? Run the helper: `bash tools/git-helper.sh` (Windows:
`powershell -ExecutionPolicy Bypass -File tools\git-helper.ps1`). It explains and asks before it changes anything.

Then: pick your ticket on the Jira board, check no other ticket lists the same files
(`docs/TEAM.md`), and follow `CONTRIBUTING.md`. Stop with `docker compose down`. How to run the tests,
try changes and review a teammate's branch: README → *Run it, test it, review a teammate's branch*.
