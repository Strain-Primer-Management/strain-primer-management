# Starts tools/git-helper.sh with the bash that comes with Git for Windows.
#   powershell -ExecutionPolicy Bypass -File tools\git-helper.ps1
# LEAD-ONLY FILE. Keep this file ASCII-only (Windows PowerShell 5.1 misreads UTF-8 without BOM).

$script = Join-Path $PSScriptRoot "git-helper.sh"
$candidates = @(
    (Join-Path $env:ProgramFiles "Git\bin\bash.exe"),
    (Join-Path ${env:ProgramFiles(x86)} "Git\bin\bash.exe"),
    (Join-Path $env:LOCALAPPDATA "Programs\Git\bin\bash.exe")
)
$git = Get-Command git -ErrorAction SilentlyContinue
if ($git) {
    # git.exe is usually ...\Git\cmd\git.exe, so bash is in ...\Git\bin
    $candidates += (Join-Path (Split-Path (Split-Path $git.Source)) "bin\bash.exe")
}
$bash = $candidates | Where-Object { $_ -and (Test-Path $_) } | Select-Object -First 1
if (-not $bash) {
    Write-Host "I could not find Git's bash. Install Git for Windows (handbook, Part 1) and try again." -ForegroundColor Red
    exit 1
}
& $bash $script
