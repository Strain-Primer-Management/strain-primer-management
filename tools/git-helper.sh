#!/usr/bin/env bash
# git-helper: every manual Git case of this project in one friendly, coloured menu.
#
#   macOS / Linux:  bash tools/git-helper.sh
#   Windows:        powershell -ExecutionPolicy Bypass -File tools\git-helper.ps1
#
# It explains what it will do, shows the exact Git command, and asks before it changes anything.
# Project rules are built in: never work on main, never force-push, commits start with the ticket.
# Colours: automatic. Turn off with NO_COLOR=1, force on with GITHELPER_COLOR=1.
# LEAD-ONLY FILE. Works with the bash that ships with Git on Windows, and with macOS bash 3.2.

# ------------------------------------------------------------------ colours (plain ANSI, no tput needed)
USE_COLOR=0
if [ -z "${NO_COLOR:-}" ] && { [ "${GITHELPER_COLOR:-}" = 1 ] || { [ -t 1 ] && [ "${TERM:-}" != dumb ]; }; }; then USE_COLOR=1; fi
[ "${GITHELPER_COLOR:-}" = 0 ] && USE_COLOR=0
if [ "$USE_COLOR" = 1 ]; then
  ESC=$(printf '\033')
  BOLD="${ESC}[1m"; DIM="${ESC}[2m"; RED="${ESC}[31m"; GREEN="${ESC}[32m"
  YELLOW="${ESC}[33m"; BLUE="${ESC}[34m"; CYAN="${ESC}[36m"; RESET="${ESC}[0m"
else
  BOLD=""; DIM=""; RED=""; GREEN=""; YELLOW=""; BLUE=""; CYAN=""; RESET=""
fi

say() { printf '%s\n' "$*"; }
title() { printf '\n%s%s== %s ==%s\n' "$BOLD" "$BLUE" "$*" "$RESET"; }
good() { printf '%s%s[OK]%s   %s%s%s\n' "$BOLD" "$GREEN" "$RESET" "$GREEN" "$*" "$RESET"; }
warn() { printf '%s%s[NOTE]%s %s%s%s\n' "$BOLD" "$YELLOW" "$RESET" "$YELLOW" "$*" "$RESET"; }
bad() { printf '%s%s[STOP]%s %s%s%s\n' "$BOLD" "$RED" "$RESET" "$RED" "$*" "$RESET"; }
info() { printf '%s%s[i]%s    %s\n' "$BOLD" "$CYAN" "$RESET" "$*"; }
cmd() { printf '%s  $ %s%s\n' "$CYAN" "$*" "$RESET"; }
run() { cmd "$@"; "$@"; }
pause() { printf '\n%sPress Enter to go back to the menu...%s ' "$DIM" "$RESET"; read -r _ || true; }
trap 'echo; say "Bye!"; exit 0' INT

ask() { # ask "question: "  -> answer in $ANSWER
  printf '%s%s%s' "$BOLD" "$1" "$RESET"
  read -r ANSWER || ANSWER=""
}

yesno() { # yesno "question" [y|n default]
  local default="${2:-n}" a
  if [ "$default" = y ]; then printf '%s%s%s [Y/n] ' "$BOLD" "$1" "$RESET"; else printf '%s%s%s [y/N] ' "$BOLD" "$1" "$RESET"; fi
  read -r a || a=""
  a=$(printf '%s' "$a" | tr 'A-Z' 'a-z')
  [ -z "$a" ] && a=$default
  [ "$a" = y ] || [ "$a" = yes ]
}

typed_confirm() { # typed_confirm WORD "what will happen"
  warn "$2"
  printf 'To go ahead, type %s%s%s and press Enter (anything else cancels): ' "$BOLD" "$1" "$RESET"
  read -r ANSWER || ANSWER=""
  [ "$ANSWER" = "$1" ]
}

# ------------------------------------------------------------------ menu numbers (one place, used in every message)
O_WHERE=1; O_SETUP=2; O_START=3; O_CONTINUE=4; O_SEE=5; O_SAVE=6; O_SEND=7; O_CHECKS=8
O_PR=9; O_NEXT=10; O_CLEAN=11; O_SYNC=12; O_CONFLICT=13; O_APP=14; O_TEAM=15; O_ASIDE=16
O_OOPS=17; O_REPORT=18; O_LEARN=19

# ------------------------------------------------------------------ project checks
command -v git >/dev/null 2>&1 || { bad "Git is not installed. See the handbook, Part 1."; exit 1; }
ROOT=$(git rev-parse --show-toplevel 2>/dev/null) || {
  bad "This folder is not the project. Open a terminal inside Strain-Primer-Management and run me again."
  exit 1
}
cd "$ROOT" || exit 1

# ------------------------------------------------------------------ state helpers
cur() { git branch --show-current 2>/dev/null; }
ticket() { cur | grep -oE 'SCRUM-[0-9]+' | head -1; }
dirty() { [ -n "$(git status --porcelain 2>/dev/null)" ]; }
merging() { git rev-parse -q --verify MERGE_HEAD >/dev/null 2>&1; }
conflicted() { git diff --name-only --diff-filter=U 2>/dev/null; }
has_upstream() { git rev-parse -q --verify '@{u}' >/dev/null 2>&1; }
fetch_quiet() { git fetch -q origin 2>/dev/null; }
have_origin_main() { git rev-parse -q --verify origin/main >/dev/null 2>&1; }
gh_ready() { [ -z "${GITHELPER_NO_GH:-}" ] && command -v gh >/dev/null 2>&1 && gh auth status >/dev/null 2>&1; }

count_ahead() { # commits on this branch that GitHub does not have yet
  if has_upstream; then git rev-list --count '@{u}..HEAD' 2>/dev/null || echo 0
  elif have_origin_main; then git rev-list --count origin/main..HEAD 2>/dev/null || echo 0
  else echo 0; fi
}
count_behind() { have_origin_main && git rev-list --count HEAD..origin/main 2>/dev/null || echo 0; }

suggest() { # sets SUG_OPT and SUG_WHY
  SUG_OPT=""; SUG_WHY=""
  local b ahead behind
  b=$(cur)
  if merging; then SUG_OPT=$O_CONFLICT; SUG_WHY="a merge is waiting for you (conflicts)"; return; fi
  if [ -z "$b" ]; then SUG_OPT=$O_START; SUG_WHY="you are not on a branch"; return; fi
  if [ "$b" = main ]; then
    SUG_OPT=$O_START
    if dirty; then SUG_WHY="you have edits on 'main': move them to your own ticket branch"; else SUG_WHY="start your ticket"; fi
    return
  fi
  if dirty; then SUG_OPT=$O_SAVE; SUG_WHY="you have unsaved changes"; return; fi
  ahead=$(count_ahead)
  if [ "$ahead" -gt 0 ]; then SUG_OPT=$O_SEND; SUG_WHY="$ahead saved commit(s) are not on GitHub yet"; return; fi
  behind=$(count_behind)
  if [ "$behind" -gt 0 ]; then SUG_OPT=$O_SYNC; SUG_WHY="main has $behind newer commit(s) you do not have"; return; fi
  SUG_OPT=$O_PR; SUG_WHY="everything is saved and sent: see how your pull request is doing"
}

banner() {
  local b t n
  b=$(cur); t=$(ticket)
  n=$(git status --porcelain 2>/dev/null | wc -l | tr -d ' ')
  printf '%sYou are on:%s %s%s%s' "$BOLD" "$RESET" "$GREEN" "${b:-(no branch)}" "$RESET"
  [ -n "$t" ] && printf '   %sticket%s %s' "$BOLD" "$RESET" "$t"
  if [ "$n" -gt 0 ]; then printf '   %sunsaved changes: %s%s' "$YELLOW" "$n" "$RESET"; else printf '   unsaved changes: 0'; fi
  if [ -n "$b" ] && [ "$b" != main ]; then
    n=$(count_ahead)
    [ "$n" -gt 0 ] && printf '   %snot on GitHub yet: %s commit(s)%s' "$YELLOW" "$n" "$RESET"
  fi
  merging && printf '   %s[MERGE IN PROGRESS: option %s]%s' "$RED" "$O_CONFLICT" "$RESET"
  printf '\n'
  suggest
  [ -n "$SUG_OPT" ] && printf '%sSuggestion:%s option %s%s%s, because %s.\n' "$BOLD" "$RESET" "$BOLD$GREEN" "$SUG_OPT" "$RESET" "$SUG_WHY"
}

need_ticket_branch() {
  local b
  b=$(cur)
  if [ -z "$b" ]; then
    bad "You are not on a branch right now."
    say "Option $O_START starts a ticket branch, option $O_CONTINUE goes back to one you already started."
    return 1
  fi
  if [ "$b" = main ]; then
    bad "You are on 'main'. 'main' is the shared line: nobody works on it directly."
    say "Work on your own ticket branch. Option $O_START makes one (your unsaved edits come along)."
    return 1
  fi
  return 0
}

need_clean_tree() { # need_clean_tree "what you wanted to do"
  if dirty; then
    bad "You have unsaved changes, so I will not $1."
    say "Either save them (option $O_SAVE) or set them aside for now (option $O_ASIDE). Nothing was changed."
    return 1
  fi
  return 0
}

ticket_number_or_ask() { # sets TICKET_KEY
  TICKET_KEY=$(ticket)
  if [ -z "$TICKET_KEY" ]; then
    ask "Which ticket number is this for? (digits only, like 12): "
    case "$ANSWER" in
      '' | *[!0-9]*) bad "That is not a number."; return 1 ;;
    esac
    TICKET_KEY="SCRUM-$ANSWER"
  fi
  return 0
}

slugify() { printf '%s' "$1" | tr 'A-Z' 'a-z' | sed -e 's/[^a-z0-9]\{1,\}/-/g' -e 's/^-//' -e 's/-$//'; }

choose_number() { # choose_number MAX  -> sets CHOICE_N, returns 1 if invalid
  case "$ANSWER" in '' | *[!0-9]*) bad "Please type a number."; return 1 ;; esac
  if [ "$ANSWER" -lt 1 ] || [ "$ANSWER" -gt "$1" ]; then bad "There is no number $ANSWER."; return 1; fi
  CHOICE_N=$ANSWER
}

# ------------------------------------------------------------------ 1. where am I
diagnose() {
  title "Where am I? Here is the picture"
  local b staged unstaged untracked n
  b=$(cur)
  fetch_quiet
  if [ -z "$b" ]; then
    bad "You are not on a branch (Git calls this a 'detached HEAD')."
  elif [ "$b" = main ]; then
    warn "You are on 'main' (the shared line). Nobody works here directly."
  else
    good "You are on your own branch: $b"
    [ -n "$(ticket)" ] && say "      It belongs to ticket $(ticket)."
  fi

  staged=$(git diff --cached --name-only | wc -l | tr -d ' ')
  unstaged=$(git diff --name-only | wc -l | tr -d ' ')
  untracked=$(git ls-files -o --exclude-standard | wc -l | tr -d ' ')
  n=$((staged + unstaged + untracked))
  if [ "$n" -eq 0 ]; then
    good "No unsaved changes: everything you did is saved in commits."
  else
    warn "Unsaved changes: $unstaged edited, $staged ready to save, $untracked new file(s)."
    say "      (Edits live only on your computer until you save them: option $O_SAVE.)"
  fi
  merging && bad "A merge is in progress, with $(conflicted | wc -l | tr -d ' ') conflicted file(s): option $O_CONFLICT."

  if [ -n "$b" ] && [ "$b" != main ]; then
    if has_upstream; then
      [ "$(count_ahead)" -gt 0 ] && warn "$(count_ahead) saved commit(s) are not on GitHub yet." || good "Everything saved is on GitHub."
    else
      warn "This branch has never been sent to GitHub."
    fi
    [ "$(count_behind)" -gt 0 ] && warn "main has $(count_behind) newer commit(s) that you do not have yet." || good "You have all the newest changes from main."
  fi
  title "What to do next"
  suggest
  say "Option $SUG_OPT, because $SUG_WHY."
}

# ------------------------------------------------------------------ 2. check my setup
set_identity() {
  info "Your name is shown on everything you save. Use your real name."
  ask "Your real name: "
  local nm="$ANSWER"
  info "Email: your GitHub email, or the no-reply address from github.com/settings/emails (keeps your email private)."
  ask "Your email: "
  if [ -z "$nm" ] || [ -z "$ANSWER" ]; then bad "I need both. Nothing was changed."; return 1; fi
  run git config --global user.name "$nm" && run git config --global user.email "$ANSWER" && good "Saved."
}

setup_check() {
  title "Is my setup right?"
  say "I check the things that cause most 'it does not work for me' problems."
  local nm em hp
  nm=$(git config user.name); em=$(git config user.email)
  if [ -n "$nm" ] && [ -n "$em" ]; then good "Git knows who you are: $nm"; else
    bad "Git does not know your name and email yet (it needs them to save your work)."
    yesno "Set them now?" y && set_identity
  fi
  if command -v gh >/dev/null 2>&1; then
    if gh auth status >/dev/null 2>&1; then good "GitHub CLI (gh) is installed and you are logged in."
    else warn "GitHub CLI is installed but you are not logged in. Run:  gh auth login"; fi
  else
    warn "GitHub CLI (gh) is not installed. Not required, but it lets me open pull requests for you (handbook, Part 1)."
  fi
  hp=$(git config core.hooksPath)
  if [ "$hp" = ".githooks" ]; then good "Safety net is on: committing or pushing straight to 'main' is blocked."
  else
    warn "Safety net is OFF: nothing stops you from committing on 'main' by accident."
    if yesno "Turn it on now? (recommended, only changes this project on your computer)" y; then
      run git config --local core.hooksPath .githooks
      run git config --local pull.ff only
      run git config --local fetch.prune true
      good "Safety net on."
    fi
  fi
  if git remote get-url origin 2>/dev/null | grep -q 'Strain-Primer-Management'; then good "This project is connected to GitHub: $(git remote get-url origin | sed -e 's|//[^@/]*@|//|')"
  else bad "The project is not connected to the right GitHub repository. Ask Nour."; fi
  if command -v docker >/dev/null 2>&1; then
    if docker info >/dev/null 2>&1; then good "Docker is running."; else warn "Docker is installed but not running. Start Docker Desktop."; fi
  else warn "Docker is not installed (handbook, Part 1)."; fi
  if command -v claude >/dev/null 2>&1; then good "Claude Code is installed."; else info "Claude Code is not installed here (handbook, Part 1, step 2)."; fi
}

# ------------------------------------------------------------------ 3. start a ticket
start_ticket() {
  title "Start a ticket (makes your own branch)"
  say "A branch is your own line of work, so you never change 'main' directly."
  local b
  b=$(cur)
  if dirty && [ -n "$b" ] && [ "$b" != main ]; then
    bad "You have unsaved edits that belong to your current ticket ($b)."
    say "Save them (option $O_SAVE) or set them aside (option $O_ASIDE) first, so they do not end up in the wrong ticket."
    return
  fi
  ask "Ticket number (digits only, like 12): "
  case "$ANSWER" in
    '' | *[!0-9]*) bad "That is not a number. Nothing was changed."; return ;;
  esac
  local num="$ANSWER" slug branch
  ask "Short name, 2 to 5 words (like: strain list page): "
  slug=$(slugify "$ANSWER")
  if [ -z "$slug" ]; then bad "I need a short name. Nothing was changed."; return; fi
  branch="feature/SCRUM-$num-$slug"
  info "I will create the branch: $branch"
  if git rev-parse -q --verify "refs/heads/$branch" >/dev/null 2>&1; then
    bad "That branch already exists on your computer. Use option $O_CONTINUE to go back to it, or pick another name."
    return
  fi
  dirty && warn "You have unsaved edits made on 'main'. They will come along to the new branch (that is what you want here)."
  yesno "Create it?" y || { say "Cancelled. Nothing was changed."; return; }
  fetch_quiet
  if ! have_origin_main; then
    bad "I cannot see origin/main. Check your internet and that you are logged in (handbook, step 3)."
    return
  fi
  run git switch -c "$branch" --no-track origin/main && good "Done. You are on $branch, started from the newest main."
}

# ------------------------------------------------------------------ 4. continue a ticket
continue_ticket() {
  title "Continue a ticket I already started"
  need_clean_tree "switch ticket" || return
  local names=() line n=0 name when subj
  while IFS='|' read -r name when subj; do
    [ "$name" = main ] && continue
    names[${#names[@]}]="$name"
    n=$((n + 1))
    [ "$name" = "$(cur)" ] && mark=" (you are here)" || mark=""
    printf '  %2d) %s%s\n        %slast saved %s: %s%s\n' "$n" "$name" "$mark" "$DIM" "$when" "$subj" "$RESET"
  done < <(git for-each-ref --sort=-committerdate refs/heads --format='%(refname:short)|%(committerdate:relative)|%(subject)')
  if [ "$n" -eq 0 ]; then say "You have no ticket branches yet. Option $O_START starts one."; return; fi
  ask "Which number? "
  choose_number "$n" || return
  run git switch "${names[$((CHOICE_N - 1))]}" && good "You are back on it."
}

# ------------------------------------------------------------------ 5. see my work
see_work() {
  title "What did I change / save?"
  say "  a) My unsaved changes"
  say "  b) What I already saved on this ticket (commits)"
  say "  c) Which files my ticket changes compared to main (what the pull request will contain)"
  printf 'Choose a, b or c: '
  local c
  read -r c || return
  case "$c" in
    a | A)
      say "Legend:  M = edited   A = added   D = deleted   ?? = new file Git does not know yet"
      run git status --short
      dirty || { good "Nothing unsaved."; return; }
      yesno "Show every changed line in detail?" n && git diff
      ;;
    b | B)
      have_origin_main || { warn "I cannot see origin/main. Showing your last 10 saves instead."; git log --oneline --no-decorate -10; return; }
      info "These saves are on your branch but not in main yet:"
      git log --oneline --no-decorate origin/main..HEAD
      [ -z "$(git log --oneline origin/main..HEAD)" ] && say "(none)"
      ;;
    c | C)
      have_origin_main || { bad "I cannot see origin/main."; return; }
      info "Files your ticket changes compared to main. This is exactly what the pull request contains:"
      git -c core.quotepath=false diff --stat origin/main...HEAD
      say "Anything here that does not belong to your ticket? Tell Nour before you send it."
      ;;
    *) warn "Please choose a, b or c." ;;
  esac
}

# ------------------------------------------------------------------ 8. the six checks
CHECK_FAILED=0
chk() { # chk "label" "what it means if it fails" command...
  local label="$1" meaning="$2" out
  shift 2
  printf '\n%s ... ' "$label"
  out=$(docker compose exec -T web "$@" 2>&1)
  if [ $? -eq 0 ]; then
    printf '%s%sOK%s\n' "$BOLD" "$GREEN" "$RESET"
  else
    printf '%s%sFAILED%s\n' "$BOLD" "$RED" "$RESET"
    printf '%s\n' "$out" | tail -n 25
    say "${YELLOW}What it means:${RESET} $meaning"
    CHECK_FAILED=1
  fi
}

run_checks() {
  title "Run the six checks (the same ones GitHub runs)"
  if ! command -v docker >/dev/null 2>&1; then bad "Docker is not installed (handbook, Part 1)."; return 1; fi
  if ! docker info >/dev/null 2>&1; then
    bad "Docker is not running."
    say "Start Docker Desktop (Linux: sudo systemctl start docker), wait, and try again."
    return 1
  fi
  if ! docker compose ps --status running --services 2>/dev/null | grep -qx web; then
    warn "The app is not running yet."
    yesno "Start it now (docker compose up -d)?" y || return 1
    run docker compose up -d || return 1
    info "Giving it a few seconds to wake up..."
    sleep 8
  fi
  CHECK_FAILED=0
  chk "1/6 Django self-check" "something in the settings, models or URLs is broken." python manage.py check
  chk "2/6 Migrations" "a model changed but its migration file is missing (or two collide)." python manage.py makemigrations --check --dry-run
  chk "3/6 Tests" "a test failed: your change broke something (or a test needs updating)." python manage.py test
  chk "4/6 Python lint" "unused imports or likely bugs in Python files." ruff check .
  chk "5/6 Python format" "a Python file is not formatted. Fix with: ruff format <your file>." ruff format --check .
  chk "6/6 Template lint" "an HTML template has a mistake (inline style, unclosed tag...)." djlint templates --lint
  echo
  if [ "$CHECK_FAILED" -eq 0 ]; then good "All six checks passed."; return 0; fi
  bad "At least one check failed. Read the lines above, fix it (or ask Claude Code), and run this again."
  return 1
}

# ------------------------------------------------------------------ 6. save my work (commit)
is_sensitive() {
  case "$1" in
    .env | */.env | *.sqlite3 | *.pyc | */__pycache__/* | *.pem | *.key | *id_rsa* | data/private/*) return 0 ;;
  esac
  return 1
}

save_work() {
  title "Save my work (commit)"
  say "Saving puts your edits into a commit on YOUR branch. It stays on your computer until you send it (option $O_SEND)."
  need_ticket_branch || return
  merging && { bad "A merge is in progress. Finish or cancel it first (option $O_CONFLICT)."; return; }

  FILES=()
  while IFS= read -r f; do
    [ -n "$f" ] && FILES[${#FILES[@]}]="$f"
  done < <({ git -c core.quotepath=false diff --name-only; git -c core.quotepath=false diff --cached --name-only; git -c core.quotepath=false ls-files -o --exclude-standard; } 2>/dev/null | sort -u)
  if [ "${#FILES[@]}" -eq 0 ]; then good "Nothing to save: no changes."; return; fi

  say "These files have changes:"
  local i=0 label f
  for f in "${FILES[@]}"; do
    i=$((i + 1))
    if ! git ls-files --error-unmatch -- "$f" >/dev/null 2>&1; then label="${GREEN}new${RESET}    "
    elif [ ! -e "$f" ]; then label="${RED}deleted${RESET} "
    else label="${YELLOW}edited${RESET}  "; fi
    printf '  %2d) %s %s\n' "$i" "$label" "$f"
  done
  [ "${#FILES[@]}" -gt 10 ] && warn "More than 10 files: is the ticket too big? Consider splitting it."
  ask "Which files belong to this ticket? (numbers like 1 3 4, a = all, q = cancel): "
  local sel="$ANSWER" CHOSEN=() tok
  case "$sel" in
    q | Q | '') say "Cancelled. Nothing was changed."; return ;;
    a | A) for f in "${FILES[@]}"; do CHOSEN[${#CHOSEN[@]}]="$f"; done ;;
    *)
      for tok in $sel; do
        case "$tok" in *[!0-9]* | '') bad "'$tok' is not a number. Nothing was changed."; return ;; esac
        if [ "$tok" -lt 1 ] || [ "$tok" -gt "${#FILES[@]}" ]; then bad "There is no file number $tok. Nothing was changed."; return; fi
        CHOSEN[${#CHOSEN[@]}]="${FILES[$((tok - 1))]}"
      done
      ;;
  esac
  for f in "${CHOSEN[@]}"; do
    if is_sensitive "$f"; then
      bad "I will not save '$f': it looks like a secret, a database or a generated file."
      say "Leave it out. If you are sure it belongs, ask Nour. Nothing was changed."
      return
    fi
  done

  if yesno "Run the six checks first? (recommended)" y; then
    run_checks || { yesno "Checks did not pass. Save anyway?" n || { say "Cancelled. Nothing was saved."; return; }; }
  fi

  ticket_number_or_ask || return
  ask "In a few words, what did you do? "
  [ -z "$ANSWER" ] && { bad "I need a short description. Nothing was saved."; return; }
  local msg="$TICKET_KEY: $ANSWER"
  info "Message that will be saved:  $msg"
  yesno "Save these ${#CHOSEN[@]} file(s)?" y || { say "Cancelled. Nothing was changed."; return; }
  run git add -- "${CHOSEN[@]}" || return
  run git commit -m "$msg" || { bad "Git refused to commit. Read the message above."; return; }
  good "Saved on your computer. It is NOT on GitHub yet: option $O_SEND sends it."
}

# ------------------------------------------------------------------ 7. send to GitHub, open the PR
repo_web_url() {
  local url
  url=$(git remote get-url origin 2>/dev/null) || return 1
  url=${url%.git}
  case "$url" in
    git@github.com:*) url="https://github.com/${url#git@github.com:}" ;;
    ssh://git@github.com/*) url="https://github.com/${url#ssh://git@github.com/}" ;;
  esac
  printf '%s' "$url" | sed -e 's|//[^@/]*@|//|'
}

send_work() {
  title "Send my work to GitHub and open the pull request"
  say "This uploads your branch (never main) so a teammate can review it."
  need_ticket_branch || return
  merging && { bad "A merge is in progress. Finish or cancel it first (option $O_CONFLICT)."; return; }
  local b
  b=$(cur)
  dirty && warn "You have unsaved changes. They are NOT included. Save them first (option $O_SAVE) if they belong here."
  if has_upstream && [ "$(count_ahead)" -eq 0 ]; then good "Nothing new to send: GitHub already has all your saved work."; fi
  yesno "Send branch '$b' to GitHub now?" y || { say "Cancelled. Nothing was sent."; return; }
  if has_upstream; then run git push; else run git push -u origin "$b"; fi
  if [ $? -ne 0 ]; then
    bad "GitHub did not accept the push. I will NOT force it (forcing can destroy teammates' work)."
    say "Common reason: the branch changed on GitHub. Option $O_REPORT makes a report: paste it in the team chat and ask Nour."
    return
  fi
  good "Your branch is on GitHub."

  local slug title_text key web
  key=$(ticket)
  slug=$(printf '%s' "$b" | sed -e 's|^feature/||' -e 's|^fix/||' -e "s|^$key-||" -e 's/-/ /g')
  title_text="$key $slug"
  info "Pull request title suggestion:  $title_text"
  yesno "Open the pull request now?" y || { say "Later: option $O_PR, or open the link GitHub printed above."; return; }
  if gh_ready; then
    run gh pr create --web --base main --title "$title_text" --body-file .github/pull_request_template.md
  else
    web=$(repo_web_url) && {
      say "Open this link in your browser and click 'Create pull request':"
      say "  ${BOLD}$web/pull/new/$b${RESET}"
    }
  fi
  title "What happens next"
  say "1. Fill in the template and create the pull request."
  say "2. Ask a teammate to review it."
  say "3. When the checks are green and it has one approval, YOU click 'Squash and merge' on GitHub."
}

# ------------------------------------------------------------------ 9. where is my pull request
pr_status() {
  title "Where is my pull request?"
  need_ticket_branch || return
  if gh_ready; then
    if gh pr view >/dev/null 2>&1; then
      run gh pr view
      echo
      cmd gh pr checks
      gh pr checks
      echo
      info "green/pass = good.  pending = still running, wait a minute.  fail = open the link, read why, fix it, save (option $O_SAVE) and send (option $O_SEND) again."
      info "You can merge when the checks are green AND one teammate approved. Then click 'Squash and merge' on GitHub."
      info "After it is merged: option $O_NEXT starts the next ticket."
    else
      warn "There is no pull request for this branch yet. Option $O_SEND sends your work and opens one."
    fi
  else
    warn "I need the GitHub CLI (gh) logged in to look this up. Without it, open the list yourself:"
    say "  ${BOLD}$(repo_web_url)/pulls${RESET}"
  fi
}

# ------------------------------------------------------------------ 10. get newest main
sync_main() {
  title "Get the newest changes from main"
  say "This brings what others added to 'main' into YOUR branch. It never changes 'main'."
  need_ticket_branch || return
  merging && { bad "A merge is already in progress. Use option $O_CONFLICT."; return; }
  need_clean_tree "update your branch" || return
  fetch_quiet
  have_origin_main || { bad "I cannot see origin/main. Check your internet and login."; return; }
  local behind
  behind=$(count_behind)
  if [ "$behind" -eq 0 ]; then good "Already up to date: main has nothing new for you."; return; fi
  info "main has $behind newer commit(s)."
  ticket_number_or_ask || return
  yesno "Bring them into '$(cur)'?" y || { say "Cancelled. Nothing was changed."; return; }
  if run git merge origin/main -m "$TICKET_KEY: Merge main into my branch"; then
    good "Done, with no conflict. Now run the checks (option $O_CHECKS), then send (option $O_SEND)."
  else
    bad "Git found a CONFLICT: you and someone else changed the same place."
    say "Do not panic: nothing is lost. Option $O_CONFLICT guides you step by step."
  fi
}

# ------------------------------------------------------------------ 11. conflict guide
conflict_help() {
  title "Fix a conflict, step by step"
  if ! merging && [ -z "$(conflicted)" ]; then
    good "There is no conflict right now."
    say "Conflicts appear after option $O_SYNC when you and a teammate changed the same lines."
    return
  fi
  local files=() f n c choice
  while IFS= read -r f; do [ -n "$f" ] && files[${#files[@]}]="$f"; done < <(conflicted)
  say "Files in conflict:"
  n=0
  for f in "${files[@]}"; do
    n=$((n + 1))
    c=$(grep -c '^<<<<<<<' "$f" 2>/dev/null || echo 0)
    printf '  %d) %s   (%s conflict block(s))\n' "$n" "$f" "$c"
    case "$f" in
      */migrations/*) bad "     This is a migration. Do not fix it yourself: choose d (cancel) and ask Nour or Lina." ;;
    esac
  done
  warn "Choose d (cancel) and ask Nour or Lina if: a file is not one of your ticket's files, it is a migration, you do not understand it, or both sides changed the very same line."
  while true; do
    echo
    say "  ${BOLD}a)${RESET} Show me how to fix a file"
    say "  ${BOLD}b)${RESET} I fixed a file: mark it as done"
    say "  ${BOLD}c)${RESET} All fixed: finish the merge"
    say "  ${BOLD}d)${RESET} Cancel everything ${DIM}(safe: back to how it was before option $O_SYNC)${RESET}"
    say "  ${BOLD}e)${RESET} Back to the main menu"
    printf 'Choose a, b, c, d or e: '
    read -r choice || return
    case "$choice" in
      a | A)
        say ""
        say "1. Open the file in your editor. Find blocks like this:"
        say "     ${RED}<<<<<<< HEAD${RESET}"
        say "     your version of the lines"
        say "     ${RED}=======${RESET}"
        say "     their version of the lines (from main)"
        say "     ${RED}>>>>>>> origin/main${RESET}"
        say "2. Keep what BOTH sides need (usually both sets of lines)."
        say "3. Delete the three marker lines (<<<<<<<, =======, >>>>>>>)."
        say "4. Save the file, come back here and choose b."
        ;;
      b | B)
        ask "Which file number did you fix? "
        choose_number "${#files[@]}" || continue
        f="${files[$((CHOICE_N - 1))]}"
        if grep -nE '^(<<<<<<<|=======|>>>>>>>)' "$f" >/dev/null 2>&1; then
          bad "'$f' still contains conflict marker lines:"
          grep -nE '^(<<<<<<<|=======|>>>>>>>)' "$f" | head -n 10
          say "Delete those lines, save, and try again."
        else
          run git add -- "$f" && good "Marked as done: $f"
        fi
        ;;
      c | C)
        if [ -n "$(conflicted)" ]; then bad "These files are still in conflict:"; conflicted | sed 's/^/   /'; continue; fi
        ticket_number_or_ask || continue
        run git commit -m "$TICKET_KEY: Merge main into my branch" && good "Merge finished. Run the checks (option $O_CHECKS), then send (option $O_SEND)." && return
        ;;
      d | D)
        yesno "Cancel the merge and go back to how everything was before?" y || continue
        run git merge --abort && good "Cancelled. Your branch is exactly as it was. Ask Nour or Lina for help with this conflict."
        return
        ;;
      e | E | q | Q) return ;;
      *) warn "Please choose a, b, c, d or e." ;;
    esac
  done
}

# ------------------------------------------------------------------ 12. next ticket
next_ticket() {
  title "Start the next ticket"
  say "Do this AFTER your pull request was merged. It moves you back to a fresh 'main'."
  need_clean_tree "switch away" || return
  yesno "Has your pull request been merged on GitHub?" n || { say "Then keep working on your branch for now (option $O_PR shows its status). Nothing was changed."; return; }
  run git switch main || return
  run git pull --ff-only || { bad "Could not update main. Ask Nour."; return; }
  good "main is up to date."
  yesno "Start the next ticket now?" y && start_ticket
}

# ------------------------------------------------------------------ 13. teammate's branch
teammate_branch() {
  title "Look at a teammate's branch"
  say "  ${BOLD}1)${RESET} Switch to a teammate's branch (to review it)"
  say "  ${BOLD}2)${RESET} Go back to the branch I was on before"
  printf 'Choose 1 or 2: '
  local choice
  read -r choice || return
  case "$choice" in
    2) need_clean_tree "switch branches" || return; run git switch - ;;
    1)
      need_clean_tree "switch branches" || return
      fetch_quiet
      local list=() b n=0
      while IFS= read -r b; do
        b=${b#origin/}
        case "$b" in main | HEAD* | '' | origin) continue ;; esac
        list[${#list[@]}]="$b"
      done < <(git branch -r --format='%(refname:short)' 2>/dev/null)
      if [ "${#list[@]}" -eq 0 ]; then say "No other branches on GitHub right now."; return; fi
      for b in "${list[@]}"; do n=$((n + 1)); printf '  %d) %s\n' "$n" "$b"; done
      ask "Which number? "
      choose_number "${#list[@]}" || return
      run git switch "${list[$((CHOICE_N - 1))]}" || return
      good "You are looking at it. Do not edit here: this is their work."
      if command -v docker >/dev/null 2>&1 && docker info >/dev/null 2>&1; then
        yesno "Restart the app so it shows this branch? (docker compose restart web)" y && run docker compose restart web
      fi
      say "When you are done, choose option $O_TEAM again, then 2."
      ;;
    *) warn "Please choose 1 or 2." ;;
  esac
}

# ------------------------------------------------------------------ 14. set edits aside
aside() {
  title "Set my unsaved edits aside / bring them back"
  info "Like putting your edits in a drawer: you can switch branch, then take them out again. Nothing is lost."
  say "  ${BOLD}a)${RESET} Put my unsaved edits in the drawer"
  say "  ${BOLD}b)${RESET} Take them out of the drawer again"
  say "  ${BOLD}c)${RESET} What is in the drawer?"
  printf 'Choose a, b or c: '
  local c
  read -r c || return
  case "$c" in
    a | A)
      dirty || { good "You have no unsaved edits to put away."; return; }
      yesno "Put all unsaved edits (including new files) in the drawer?" y || { say "Cancelled."; return; }
      run git stash push -u -m "git-helper $(date '+%Y-%m-%d %H:%M')" && good "Done. Your files are clean now. Option $O_ASIDE, b brings the edits back."
      ;;
    b | B)
      [ -z "$(git stash list)" ] && { good "The drawer is empty."; return; }
      dirty && { bad "You have unsaved edits right now. Save them (option $O_SAVE) or put them in the drawer first."; return; }
      info "I will take out the newest thing in the drawer:"
      git stash list | head -n 1
      yesno "Take it out now?" y || { say "Cancelled."; return; }
      run git stash pop && good "Your edits are back." || warn "Git could not put everything back cleanly (a conflict). Your edits are still in the drawer. Ask Nour or Lina."
      ;;
    c | C) [ -z "$(git stash list)" ] && say "The drawer is empty." || git stash list ;;
    *) warn "Please choose a, b or c." ;;
  esac
}

# ------------------------------------------------------------------ 15. oops
oops() {
  title "Oops! Pick what happened"
  say "  ${BOLD}a)${RESET} I edited or saved files on 'main' by mistake"
  say "  ${BOLD}b)${RESET} Undo my last save (commit) but keep my changes   ${DIM}(only if not on GitHub yet)${RESET}"
  say "  ${BOLD}c)${RESET} Put ONE file back exactly as in my last save      ${DIM}(loses my edits to it)${RESET}"
  say "  ${BOLD}d)${RESET} I picked the wrong file to save (take it back out, keeps my edits)"
  say "  ${BOLD}e)${RESET} I saved or sent something wrong on my branch"
  say "  ${BOLD}f)${RESET} Git says 'Please tell me who you are'"
  say "  ${BOLD}g)${RESET} GitHub rejected my push"
  say "  ${BOLD}h)${RESET} I pushed to 'main' by mistake"
  say "  ${BOLD}i)${RESET} Throw away ALL my unsaved edits                   ${RED}(dangerous)${RESET}"
  say "  ${BOLD}q)${RESET} Back"
  printf 'Choose a letter: '
  local choice f i n
  read -r choice || return
  case "$choice" in
    a | A)
      local b ahead
      b=$(cur)
      if [ "$b" != main ]; then
        good "You are not on 'main' (you are on '${b:-no branch}'). Nothing to rescue."
        return
      fi
      fetch_quiet
      ahead=$(git rev-list --count origin/main..main 2>/dev/null || echo 0)
      if [ "$ahead" -eq 0 ]; then
        say "You have only unsaved edits on main (nothing saved there). Easy: start your ticket branch; the edits come along."
        yesno "Start the ticket branch now?" y && start_ticket
        return
      fi
      warn "You saved $ahead commit(s) on 'main' that are not on GitHub. I will move them to a new ticket branch and put 'main' back to normal."
      dirty && { bad "You also have unsaved edits. Save or set them aside first (option $O_ASIDE). Nothing was changed."; return; }
      ask "Ticket number (digits only): "
      case "$ANSWER" in '' | *[!0-9]*) bad "That is not a number. Nothing was changed."; return ;; esac
      n="$ANSWER"
      ask "Short name, 2 to 5 words: "
      local slug branch
      slug=$(slugify "$ANSWER")
      [ -z "$slug" ] && { bad "I need a short name. Nothing was changed."; return; }
      branch="feature/SCRUM-$n-$slug"
      info "Plan: 1) new branch $branch keeps your work  2) main goes back to GitHub's version  3) you end up on $branch"
      typed_confirm YES "Your work is safe because it is saved on the new branch first." || { say "Cancelled. Nothing was changed."; return; }
      run git switch -c "$branch" && run git switch main && run git reset --hard origin/main && run git switch "$branch" \
        && good "Rescued. You are on $branch with your work, and main is back to normal."
      ;;
    b | B)
      need_ticket_branch || return
      if git branch -r --contains HEAD 2>/dev/null | grep -q .; then
        bad "That commit is already on GitHub. Do not undo it. Fix the files and save a NEW commit instead (option $O_SAVE), then send it (option $O_SEND)."
        return
      fi
      info "Your last commit will be undone, and all its changes stay in your files (ready to save again)."
      yesno "Do it?" n || { say "Cancelled. Nothing was changed."; return; }
      run git reset --soft HEAD~1 && good "Undone. Your changes are still here."
      ;;
    c | C)
      FILES=()
      while IFS= read -r f; do [ -n "$f" ] && FILES[${#FILES[@]}]="$f"; done < <({ git -c core.quotepath=false diff --name-only; git -c core.quotepath=false diff --cached --name-only; } 2>/dev/null | sort -u)
      [ "${#FILES[@]}" -eq 0 ] && { good "No edited files to put back."; return; }
      i=0
      for f in "${FILES[@]}"; do i=$((i + 1)); printf '  %d) %s\n' "$i" "$f"; done
      ask "Which file number? "
      choose_number "${#FILES[@]}" || return
      f="${FILES[$((CHOICE_N - 1))]}"
      typed_confirm DELETE "ALL your edits to '$f' will be thrown away and cannot be recovered." || { say "Cancelled. Nothing was changed."; return; }
      run git restore --source=HEAD --staged --worktree -- "$f" && good "Done: '$f' is exactly as in your last save."
      ;;
    d | D)
      FILES=()
      while IFS= read -r f; do [ -n "$f" ] && FILES[${#FILES[@]}]="$f"; done < <(git -c core.quotepath=false diff --cached --name-only 2>/dev/null)
      [ "${#FILES[@]}" -eq 0 ] && { good "Nothing is waiting to be saved, so there is nothing to take out."; return; }
      i=0
      for f in "${FILES[@]}"; do i=$((i + 1)); printf '  %d) %s\n' "$i" "$f"; done
      ask "Which file number should NOT be saved? "
      choose_number "${#FILES[@]}" || return
      run git restore --staged -- "${FILES[$((CHOICE_N - 1))]}" && good "Taken out. Your edits in that file are untouched."
      ;;
    e | E)
      info "Never undo history that is already on GitHub. Do this instead:"
      say "1. Fix the files so they are right.  2. Option $O_SAVE: save a NEW commit.  3. Option $O_SEND: send it."
      say "The pull request updates by itself, and the old mistake simply disappears at 'Squash and merge'."
      ;;
    f | F) set_identity ;;
    g | G)
      info "GitHub says your branch is behind or changed. NEVER force the push (it can destroy teammates' work)."
      say "1. Option $O_SYNC (get the newest changes), then option $O_SEND again."
      say "2. Still rejected? Option $O_REPORT makes a report: paste it in the team chat and ask Nour."
      ;;
    h | H) bad "Do NOT try to fix this yourself. Tell Nour right now, with the report from option $O_REPORT." ;;
    i | I)
      dirty || { good "You have no unsaved edits."; return; }
      typed_confirm "DELETE MY EDITS" "ALL unsaved edits in tracked files will be thrown away. New files stay. This cannot be undone." || { say "Cancelled. Nothing was changed."; return; }
      run git restore --source=HEAD --staged --worktree . && good "Done. Your files are exactly as in your last save."
      ;;
    q | Q | '') return ;;
    *) warn "Please choose one of the letters." ;;
  esac
}

# ------------------------------------------------------------------ 16. report
report() {
  title "Report for the team chat"
  say "Copy everything between the two lines and paste it in the team chat."
  echo "------------------------------------------------------------"
  echo "when:       $(date '+%Y-%m-%d %H:%M')"
  echo "system:     $(uname -s 2>/dev/null) $(uname -r 2>/dev/null)"
  echo "git:        $(git --version)"
  echo "branch:     $(cur)"
  echo "ticket:     $(ticket)"
  echo "merging:    $(merging && echo yes || echo no)"
  echo "hooks:      $(git config core.hooksPath || echo 'not enabled')"
  echo "upstream:   $(git rev-parse --abbrev-ref '@{u}' 2>/dev/null || echo 'none')"
  echo "remote:     $(git remote get-url origin 2>/dev/null | sed -e 's|//[^@/]*@|//|')"
  echo "status:"
  git status --short | head -n 25 | sed 's/^/  /'
  echo "last commits:"
  git log --oneline -5 2>/dev/null | sed 's/^/  /'
  echo "------------------------------------------------------------"
}

# ------------------------------------------------------------------ 17. learn
learn() {
  title "What is the difference between...?"
  cat <<'TXT'
 SAVE vs SEND            Save (commit) = a snapshot on YOUR computer.  Send (push) = upload it to GitHub.
                         Nobody sees your work until you send it.
 BRANCH vs main          'main' is the shared, finished line. A branch is your private copy to work on.
                         Your work reaches main only through a pull request.
 GET NEWEST (merge main) Copies what others added to main INTO your branch. It never changes main.
                         (Different from the green 'Squash and merge' button, which adds your branch to main.)
 pull vs fetch           fetch = look at what is new on GitHub, change nothing.  pull = fetch + update.
                         On 'main' we only use 'pull --ff-only', which can never create a mess.
 CONFLICT vs ERROR       A conflict is normal: you and a teammate changed the same lines. Nothing is lost.
                         Conflict option -> d cancels everything safely.
 SET ASIDE vs SAVE       Set aside (stash) = put unsaved edits in a drawer to switch branches. Not part of any ticket.
                         Save (commit) = a real part of your ticket's history.
 PUT A FILE BACK vs      'Put one file back' (Oops c) throws away your edits to ONE file.
 UNDO LAST SAVE          'Undo last save' (Oops b) keeps all your edits and only removes the commit.
                         'Take a file out' (Oops d) just un-picks a file from the next save. Nothing is lost.
 UNSAVED vs SAVED        Edits you have not saved exist only in your files. Save often.
 PULL REQUEST            A request to add your branch to main. A teammate reviews it, the checks run,
                         then you click 'Squash and merge' on GitHub.
 FINISHED vs CANCELLED   Finished = your pull request was merged: only leftovers to tidy (option 11, a).
 TICKET                  Cancelled = you give up: option 11, b asks if it was ever sent to GitHub, and whether to
                         back it up first, delete it, or close the pull request too.
 MIGRATION vs RESET      A migration is a database change a teammate made. After a pull, restart the app to apply it.
                         Reset = empty your LOCAL database and rebuild it (option 14, d). Your code stays untouched.
 force-push              Overwrites GitHub's history. NEVER do it here: this helper will never offer it.
TXT
}

# ------------------------------------------------------------------ remove / close / clean up a ticket
remote_has() { git ls-remote --exit-code --heads origin "$1" >/dev/null 2>&1; }

delete_local_branch() { # delete_local_branch NAME
  if [ "$1" = main ]; then bad "I never delete main."; return 1; fi
  if [ "$(cur)" = "$1" ]; then
    need_clean_tree "leave this branch" || return 1
    info "You are on this branch, so I move you back to 'main' first."
    run git switch main || return 1
  fi
  info "I use 'branch -D' because a squash-merged branch looks 'unmerged' to Git. That is why I ask first."
  run git branch -D "$1" && good "Removed '$1' from your computer."
}

delete_remote_branch() { # delete_remote_branch NAME
  if [ "$1" = main ]; then bad "I never delete main."; return 1; fi
  run git push origin --delete "$1" && good "Removed '$1' from GitHub (an open pull request for it closes by itself)."
}

tidy_auto() {
  title "Tidy up automatically"
  info "After a pull request is merged, GitHub deletes the branch. Your computer keeps a stale copy. I find those."
  git fetch -q --prune origin 2>/dev/null
  local gone=() b
  while IFS= read -r b; do
    [ -n "$b" ] && [ "$b" != main ] && gone[${#gone[@]}]="$b"
  done < <(git for-each-ref --format='%(refname:short) %(upstream:track)' refs/heads | awk '$2=="[gone]"{print $1}')
  if [ "${#gone[@]}" -eq 0 ]; then good "Nothing to tidy: no finished ticket is left over."; return; fi
  say "These tickets are gone from GitHub (normally because they were merged):"
  for b in "${gone[@]}"; do printf '  - %s   %s(last save: %s)%s\n' "$b" "$DIM" "$(git log -1 --format=%s "$b")" "$RESET"; done
  yesno "Remove them from your computer?" n || { say "Cancelled. Nothing was changed."; return; }
  for b in "${gone[@]}"; do delete_local_branch "$b"; done
}

clean_one() {
  title "Remove ONE ticket"
  fetch_quiet
  local names=() b n=0 where unsent
  while IFS= read -r b; do
    [ -n "$b" ] && [ "$b" != main ] && names[${#names[@]}]="$b"
  done < <(git for-each-ref --format='%(refname:short)' refs/heads)
  if [ "${#names[@]}" -eq 0 ]; then say "You have no ticket branches."; return; fi
  for b in "${names[@]}"; do
    n=$((n + 1))
    if git rev-parse -q --verify "refs/remotes/origin/$b" >/dev/null 2>&1; then
      where="${GREEN}on GitHub${RESET}"; unsent=$(git rev-list --count "origin/$b..$b" 2>/dev/null || echo 0)
    else
      where="${YELLOW}NOT on GitHub${RESET}"; unsent=$(git rev-list --count "origin/main..$b" 2>/dev/null || echo 0)
    fi
    printf '  %2d) %s   [%s, %s unsent commit(s)]\n' "$n" "$b" "$where" "$unsent"
  done
  ask "Which ticket? (number, or Enter to cancel) "
  [ -z "$ANSWER" ] && { say "Cancelled."; return; }
  choose_number "${#names[@]}" || return
  b="${names[$((CHOICE_N - 1))]}"
  local has_remote=0 unsent_n
  remote_has "$b" && has_remote=1
  if [ "$has_remote" -eq 1 ]; then unsent_n=$(git rev-list --count "origin/$b..$b" 2>/dev/null || echo 0); else unsent_n=$(git rev-list --count "origin/main..$b" 2>/dev/null || echo 0); fi

  title "What is the situation with $b?"
  say "  ${BOLD}1)${RESET} It is FINISHED: my pull request was merged                 ${DIM}(clean up the leftovers)${RESET}"
  say "  ${BOLD}2)${RESET} I gave up and NEVER sent it to GitHub: just delete it       ${DIM}(the work is gone for good)${RESET}"
  say "  ${BOLD}3)${RESET} Send it to GitHub FIRST as a backup, then remove it from my computer"
  say "  ${BOLD}4)${RESET} It is already on GitHub and I want to CANCEL it completely  ${DIM}(close the pull request, delete everywhere)${RESET}"
  say "  ${BOLD}5)${RESET} Cancel, keep everything"
  printf 'Choose 1 to 5: '
  local choice
  read -r choice || return
  case "$choice" in
    1)
      if gh_ready; then
        local state
        state=$(gh pr list --head "$b" --state all --json state --jq '.[0].state' 2>/dev/null)
        if [ "$state" != MERGED ]; then
          warn "GitHub does not show a merged pull request for this branch (state: ${state:-no pull request found})."
          yesno "Remove it anyway?" n || { say "Cancelled. Nothing was changed."; return; }
        else
          good "GitHub confirms: the pull request was merged."
        fi
      else
        yesno "Are you SURE the pull request was merged? (I cannot check without the GitHub CLI)" n || { say "Cancelled. Nothing was changed."; return; }
      fi
      delete_local_branch "$b" || return
      if remote_has "$b"; then
        yesno "The branch is still on GitHub. Remove it there too?" y && delete_remote_branch "$b"
      fi
      ;;
    2)
      if [ "$has_remote" -eq 1 ]; then
        bad "This ticket IS on GitHub. Choose 3 (keep a backup) or 4 (cancel it completely) instead. Nothing was changed."
        return
      fi
      if [ "$unsent_n" -gt 0 ]; then
        typed_confirm DELETE "$unsent_n saved commit(s) exist ONLY on your computer. They will be lost forever." || { say "Cancelled. Nothing was changed."; return; }
      else
        yesno "Delete '$b'? It has nothing that is not already in main." y || { say "Cancelled."; return; }
      fi
      delete_local_branch "$b"
      ;;
    3)
      if [ "$(cur)" = "$b" ]; then need_clean_tree "send and leave this branch" || return; fi
      if [ "$has_remote" -eq 1 ] && [ "$unsent_n" -eq 0 ]; then
        good "GitHub already has all of it."
      else
        yesno "Send '$b' to GitHub now as a backup?" y || { say "Cancelled. Nothing was changed."; return; }
        run git push -u origin "$b" || { bad "GitHub did not accept it. I will NOT remove anything."; return; }
      fi
      if yesno "Now remove it from your computer? (You can bring it back later: option $O_TEAM lists it and switches to it.)" y; then
        delete_local_branch "$b"
      fi
      ;;
    4)
      if [ "$has_remote" -eq 0 ]; then
        bad "This ticket is not on GitHub, so there is nothing to cancel there. Choose 2 instead. Nothing was changed."
        return
      fi
      typed_confirm DELETE "The pull request (if any) will be CLOSED and the branch deleted on GitHub AND on your computer. Unsent work is lost." || { say "Cancelled. Nothing was changed."; return; }
      if gh_ready; then
        local pr
        pr=$(gh pr list --head "$b" --state open --json number --jq '.[0].number' 2>/dev/null)
        [ -n "$pr" ] && run gh pr close "$pr" --comment "Closed by the author: this ticket was cancelled."
      else
        info "Without the GitHub CLI I cannot close the pull request myself, but deleting its branch closes it automatically."
      fi
      delete_remote_branch "$b" && delete_local_branch "$b"
      ;;
    *) say "Cancelled. Nothing was changed." ;;
  esac
}

clean_ticket() {
  title "Remove, close or clean up a ticket"
  say "  ${BOLD}a)${RESET} Tidy up automatically: remove all my finished tickets ${DIM}(merged and gone from GitHub)${RESET}"
  say "  ${BOLD}b)${RESET} Remove ONE ticket: I choose it, and tell you what happened to it"
  printf 'Choose a or b: '
  local c
  read -r c || return
  case "$c" in
    a | A) tidy_auto ;;
    b | B) clean_one ;;
    *) warn "Please choose a or b." ;;
  esac
}

# ------------------------------------------------------------------ the app after a pull / reset the database
app_ready_wait() {
  local i
  info "Waiting for the app to answer..."
  for i in $(seq 1 45); do
    if docker compose exec -T web python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/accounts/login/')" >/dev/null 2>&1; then
      good "The app is up."; return 0
    fi
    sleep 2
  done
  bad "The app did not answer in time. The last lines of its log:"
  docker compose logs --no-color --tail 15 web 2>&1 | sed 's/^/   | /'
  info "Errors like 'already exists' or 'does not exist' mean your database does not match the code (for example the team reset the migrations): choose d (reset my database) in option $O_APP."
  return 1
}

app_help() {
  title "The app after a pull / reset my database"
  info "Migrations are database changes your teammates made. The app applies them only when it STARTS."
  info "So after you pull or switch to a branch with new migrations, restart the app (choice a)."
  if ! command -v docker >/dev/null 2>&1; then bad "Docker is not installed (handbook, Part 1)."; return; fi
  if ! docker info >/dev/null 2>&1; then bad "Docker is not running. Start Docker Desktop (Linux: sudo systemctl start docker) and try again."; return; fi
  say "  ${BOLD}a)${RESET} Apply new migrations ${DIM}(restarts the app)${RESET}"
  say "  ${BOLD}b)${RESET} Start the app ${DIM}(if it is stopped)${RESET}"
  say "  ${BOLD}c)${RESET} Show which migrations are applied"
  say "  ${BOLD}d)${RESET} RESET my local database ${DIM}(empty, rebuilt from scratch: use it when the team reset or squashed the migrations, or the app shows migration errors)${RESET}"
  say "  ${BOLD}e)${RESET} Back"
  printf 'Choose a, b, c, d or e: '
  local c
  read -r c || return
  case "$c" in
    a | A)
      if docker compose ps --status running --services 2>/dev/null | grep -qx web; then
        run docker compose restart web && app_ready_wait && good "New migrations are applied."
      else
        run docker compose up -d && app_ready_wait && good "The app started, and new migrations are applied."
      fi
      ;;
    b | B) run docker compose up -d && app_ready_wait ;;
    c | C)
      if docker compose ps --status running --services 2>/dev/null | grep -qx web; then
        info "[X] = applied, [ ] = waiting. Waiting ones are applied when you choose a."
        docker compose exec -T web python manage.py showmigrations
      else warn "The app is not running. Choose b first."; fi
      ;;
    d | D)
      warn "This deletes ONLY your local database (the data on your computer, which is disposable). Your code and your branches are not touched."
      info "Afterwards the database is rebuilt from the migrations in your current files, and the dev login admin / admin is created again."
      typed_confirm "RESET MY DATABASE" "Everything in your local database will be erased." || { say "Cancelled. Nothing was changed."; return; }
      run docker compose down -v || return
      run docker compose up -d || return
      app_ready_wait || return
      info "Creating the dev login (admin / admin, only on your computer)..."
      docker compose exec -T -e DJANGO_SUPERUSER_USERNAME=admin -e DJANGO_SUPERUSER_PASSWORD=admin -e DJANGO_SUPERUSER_EMAIL=admin@example.com web python manage.py createsuperuser --noinput >/dev/null 2>&1
      good "Done. Fresh database. Open http://localhost:8000 and log in with admin / admin."
      ;;
    e | E | '') return ;;
    *) warn "Please choose a, b, c, d or e." ;;
  esac
}

# ------------------------------------------------------------------ menu
mi() { printf ' %s%2s)%s %s' "$BOLD$CYAN" "$1" "$RESET" "$2"; [ -n "${3:-}" ] && printf '  %s%s%s' "$DIM" "$3" "$RESET"; printf '\n'; }
group() { printf '\n %s%s%s\n' "$BOLD" "$1" "$RESET"; }

menu() {
  echo
  banner
  group "START HERE"
  mi $O_WHERE "Where am I? What should I do next?" "(a plain picture of your situation)"
  mi $O_SETUP "Is my setup right?" "(name, GitHub login, safety net)"
  group "WORK ON A TICKET"
  mi $O_START "Start a ticket" "(makes your own branch)"
  mi $O_CONTINUE "Continue a ticket I already started"
  mi $O_SEE "See what I changed / what I saved"
  mi $O_SAVE "Save my work" "(commit, on your computer)"
  mi $O_SEND "Send my work to GitHub / open the pull request"
  mi $O_CHECKS "Run the six checks" "(the same ones GitHub runs)"
  group "AFTER SENDING"
  mi $O_PR "Where is my pull request?" "(checks, review)"
  mi $O_NEXT "Start the next ticket" "(after my pull request was merged)"
  mi $O_CLEAN "Remove, close or clean up a ticket" "(finished, cancelled, or tidy everything)"
  group "STAY UP TO DATE"
  mi $O_SYNC "Get the newest changes from main"
  mi $O_CONFLICT "I have a conflict" "(guided, step by step, with a safe cancel)"
  group "THE APP"
  mi $O_APP "After a pull: apply new migrations / reset my database"
  group "OTHER PEOPLE'S WORK"
  mi $O_TEAM "Look at a teammate's branch"
  group "PROBLEMS"
  mi $O_ASIDE "Set my unsaved edits aside / bring them back"
  mi $O_OOPS "Oops! Something went wrong" "(undo and rescue)"
  mi $O_REPORT "I am lost: make a report for the team chat"
  group "LEARN"
  mi $O_LEARN "What is the difference between...?"
  printf ' %s%s q)%s Quit\n' "$BOLD" "$CYAN" "$RESET"
}

printf '%sGit helper for Strain-Primer-Management%s: pick what you want. I explain, and ask before I change anything.\n' "$BOLD" "$RESET"
while true; do
  menu
  printf '\n%sType a number (or q to quit):%s ' "$BOLD" "$RESET"
  read -r choice || { echo; exit 0; }
  case "$choice" in
    "$O_WHERE") diagnose ;;
    "$O_SETUP") setup_check ;;
    "$O_START") start_ticket ;;
    "$O_CONTINUE") continue_ticket ;;
    "$O_SEE") see_work ;;
    "$O_SAVE") save_work ;;
    "$O_SEND") send_work ;;
    "$O_CHECKS") run_checks ;;
    "$O_PR") pr_status ;;
    "$O_SYNC") sync_main ;;
    "$O_CONFLICT") conflict_help ;;
    "$O_NEXT") next_ticket ;;
    "$O_CLEAN") clean_ticket ;;
    "$O_APP") app_help ;;
    "$O_TEAM") teammate_branch ;;
    "$O_ASIDE") aside ;;
    "$O_OOPS") oops ;;
    "$O_REPORT") report ;;
    "$O_LEARN") learn ;;
    q | Q | quit | exit) say "Bye!"; exit 0 ;;
    *) warn "Please type one of the numbers in the list." ;;
  esac
  pause
done
