# One-command local setup for Windows PowerShell. Safe to run again at any time.
#   .\setup.ps1
# If Windows blocks the script ("running scripts is disabled"), run it like this instead:
#   powershell -ExecutionPolicy Bypass -File .\setup.ps1
# LEAD-ONLY FILE. Keep this file ASCII-only (Windows PowerShell 5.1 misreads UTF-8 without BOM).

# Continue (not Stop): native commands like docker write progress to stderr, which Windows
# PowerShell 5.1 would treat as errors. We check $LASTEXITCODE explicitly instead.
$ErrorActionPreference = "Continue"
Set-Location $PSScriptRoot

function Say($message) { Write-Host ""; Write-Host "==> $message" -ForegroundColor Cyan }
function Fail($message) { Write-Host ""; Write-Host "ERROR: $message" -ForegroundColor Red; exit 1 }
function Has($name) { return [bool](Get-Command $name -ErrorAction SilentlyContinue) }

Say "Checking prerequisites"
if (-not (Has "git")) { Fail "Git is not installed. Get it from https://git-scm.com/downloads and run this again." }
if (-not (Has "docker")) { Fail "Docker is not installed. Install Docker Desktop: https://www.docker.com/products/docker-desktop/ (choose the WSL 2 backend)." }
docker compose version *> $null
if ($LASTEXITCODE -ne 0) { Fail "'docker compose' is missing. Update Docker Desktop to a current version." }
docker info *> $null
if ($LASTEXITCODE -ne 0) { Fail "Docker is installed but not running. Start Docker Desktop, wait until it says 'running', and run this again." }

# Safe Git defaults for THIS clone only: `git pull` can never create a merge commit, and the
# hooks in .githooks/ block commits and pushes directly on main.
git rev-parse --git-dir *> $null
if ($LASTEXITCODE -eq 0) {
    git config --local pull.ff only
    git config --local fetch.prune true
    git config --local core.hooksPath .githooks
}

Say "Building and starting the app (first run downloads a few hundred MB, give it a few minutes)"
docker compose up -d --build
if ($LASTEXITCODE -ne 0) { Fail "docker compose could not build or start the app (see the messages above)." }

Say "Waiting for the app to answer"
$ready = $false
for ($i = 0; $i -lt 60; $i++) {
    try {
        $response = Invoke-WebRequest -UseBasicParsing -Uri "http://localhost:8000/accounts/login/" -TimeoutSec 3
        if ($response.StatusCode -eq 200) { $ready = $true; break }
    } catch {
        # not up yet
    }
    Start-Sleep -Seconds 2
}
if (-not $ready) {
    docker compose logs --tail 40 web
    Fail "The app did not start within 2 minutes. See the log above."
}

Say "Creating the local dev admin (skipped if it already exists)"
$out = docker compose exec -T -e DJANGO_SUPERUSER_USERNAME=admin -e DJANGO_SUPERUSER_PASSWORD=admin -e DJANGO_SUPERUSER_EMAIL=admin@example.com web python manage.py createsuperuser --noinput 2>&1 | Out-String
if ($LASTEXITCODE -eq 0) {
    Write-Host "created"
} elseif ($out -match "already taken") {
    Write-Host "already exists"
} else {
    Write-Host $out
    Fail "Could not create the dev admin (see above)."
}

Write-Host ""
Write-Host "All set." -ForegroundColor Green
Write-Host "  Open:   http://localhost:8000"
Write-Host "  Login:  admin / admin   (local development only; your database exists only on your PC)"
Write-Host "  Next:   read CONTRIBUTING.md before you change anything"
Write-Host "  Stop:   docker compose down"
