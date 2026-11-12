#!/usr/bin/env bash
# One-command local setup for Linux, macOS, WSL and Git Bash. Safe to run again at any time.
#   bash setup.sh
# LEAD-ONLY FILE. Windows PowerShell users: use setup.ps1 instead.
set -euo pipefail
cd "$(dirname "$0")"

say() { printf '\n==> %s\n' "$*"; }
fail() { printf '\nERROR: %s\n' "$*" >&2; exit 1; }

say "Checking prerequisites"
command -v git >/dev/null 2>&1 \
  || fail "Git is not installed. Get it from https://git-scm.com/downloads and run this again."
command -v docker >/dev/null 2>&1 \
  || fail "Docker is not installed. Install Docker Desktop: https://www.docker.com/products/docker-desktop/ (Linux: install docker and the compose plugin)."
docker compose version >/dev/null 2>&1 \
  || fail "'docker compose' is missing. Docker Desktop includes it. Linux: Arch 'sudo pacman -S docker-compose', Debian/Ubuntu 'sudo apt install docker-compose-v2'."
docker info >/dev/null 2>&1 \
  || fail "Docker is installed but not reachable. Start Docker Desktop (Linux: 'sudo systemctl enable --now docker'). Linux 'permission denied'? Add yourself to the docker group ('sudo usermod -aG docker \$USER'), log out and in, then run this again."

# Safe Git defaults for THIS clone only: `git pull` can never create a merge commit, and the
# hooks in .githooks/ block commits and pushes directly on main.
if git rev-parse --git-dir >/dev/null 2>&1; then
  git config --local pull.ff only
  git config --local fetch.prune true
  git config --local core.hooksPath .githooks
fi

say "Building and starting the app (first run downloads a few hundred MB, give it a few minutes)"
docker compose up -d --build

say "Waiting for the app to answer"
ready=0
for _ in $(seq 1 60); do
  if docker compose exec -T web python -c \
    "import urllib.request; urllib.request.urlopen('http://localhost:8000/accounts/login/')" \
    >/dev/null 2>&1; then
    ready=1
    break
  fi
  sleep 2
done
if [ "$ready" -ne 1 ]; then
  docker compose logs --tail 40 web || true
  fail "The app did not start within 2 minutes. See the log above."
fi

say "Creating the local dev admin (skipped if it already exists)"
if out=$(docker compose exec -T \
  -e DJANGO_SUPERUSER_USERNAME=admin -e DJANGO_SUPERUSER_PASSWORD=admin \
  -e DJANGO_SUPERUSER_EMAIL=admin@example.com \
  web python manage.py createsuperuser --noinput 2>&1); then
  echo "created"
elif printf '%s' "$out" | grep -qi "already taken"; then
  echo "already exists"
else
  printf '%s\n' "$out" >&2
  fail "Could not create the dev admin (see above)."
fi

cat <<'EOF'

All set.
  Open:   http://localhost:8000
  Login:  admin / admin   (local development only; your database exists only on your PC)
  Next:   read CONTRIBUTING.md before you change anything
  Stop:   docker compose down
EOF
