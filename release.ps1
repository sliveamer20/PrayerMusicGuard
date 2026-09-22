# PrayerMusicGuard release script (Phase 19 infrastructure)
# Single source of truth for the version: VERSION file (MAJOR.MINOR.PATCH).
#
# Default run = VALIDATION ONLY (no build, no dist changes, no archiving).
# Full release:  .\release.ps1 -Release        (builds EXE + Setup, fills dist\, archives under releases\)
# Bump version:  edit the VERSION file first, then run with -Release.
#
# Layout rules:
#   dist\      = CURRENT build artifacts only (recreated by the build, never archived)
#   releases\  = archived official releases, one folder per version: releases\vX.Y.Z\
#
# The script fails safely: any failed step stops the run, NOTHING is archived,
# and dist\ is left holding only what the successful steps produced.

param(
    [switch]$Release,   # actually build + archive; without it: validation only
    [switch]$SkipSetup  # (-Release only) build EXE but skip the Inno Setup step
)

$ErrorActionPreference = 'Stop'
$PSNativeCommandUseErrorActionPreference = $false
$project = $PSScriptRoot
Set-Location -LiteralPath $project

# ---------- helpers ----------
function Fail($msg) {
    Write-Host ""
    Write-Host "RELEASE ABORTED: $msg" -ForegroundColor Red
    Write-Host "Nothing was archived; dist\ was not modified by the release process beyond any completed build step."
    exit 1
}

function Read-VersionFile {
    $path = Join-Path $project 'VERSION'
    if (-not (Test-Path -LiteralPath $path)) { Fail "VERSION file not found: $path" }
    $raw = (Get-Content -LiteralPath $path -Raw).Trim()
    if ($raw -notmatch '^(\d+)\.(\d+)\.(\d+)$') {
        Fail "VERSION file must contain exactly MAJOR.MINOR.PATCH (e.g. 1.1.0). Found: '$raw'"
    }
    return $raw
}

function Assert-Tool {
    param([string]$Name, [scriptblock]$Test)
    if (-not (& $Test)) { Fail "$Name is not available on this machine." }
}

function Assert-NonEmptyDir {
    param([string]$Path, [string]$What)
    if (-not (Test-Path -LiteralPath $Path)) { Fail "$What not found: $Path" }
    if (-not (Get-ChildItem -LiteralPath $Path -File)) { Fail "$What directory is empty: $Path" }
}

function Get-ToolHashes {
    param([string[]]$Paths)
    $Paths | Where-Object { Test-Path -LiteralPath $_ } | ForEach-Object {
        Get-FileHash -LiteralPath $_ -Algorithm SHA256
    }
}

# ---------- 1. version ----------
$version = Read-VersionFile
Write-Host "PrayerMusicGuard release script"
Write-Host "Version (from VERSION file): $version"
Write-Host "Mode: $(if ($Release) { 'FULL RELEASE (build + archive)' } else { 'VALIDATION ONLY (no build, no changes)' })"

# ---------- 2. preflight checks (always run) ----------
# Phase 46: the release MUST be built only with the pinned Windows 7 toolchain
# (Python 3.8.10 x64 in win7\venv + PyInstaller 5.13.2). Never fall back to the
# modern Python 3.14 in vendor\ — that produced the incompatible v1.2.2 build.
$win7Python = Join-Path $project 'win7\venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $win7Python)) {
    Fail "Win7 Python not found: $win7Python"
}
$win7Version = & $win7Python -c 'import sys; print(sys.version.split()[0], 64 if sys.maxsize > 2**32 else 32)'
if ($LASTEXITCODE -ne 0 -or $win7Version -notmatch '^3\.8\.10 64$') {
    Fail "Win7 Python is not the required Python 3.8.10 x64. Found: $win7Version"
}
$pyInstallerVersion = & $win7Python -c "import PyInstaller; print(PyInstaller.__version__)"
if ($LASTEXITCODE -ne 0 -or $pyInstallerVersion -ne '5.13.2') {
    Fail "Win7 PyInstaller is not the required version 5.13.2. Found: $pyInstallerVersion"
}
$issPath = Join-Path $project 'PrayerMusicGuard.iss'
if (-not (Test-Path -LiteralPath $issPath)) { Fail "Inno Setup script not found: $issPath" }
if (-not $SkipSetup) {
    Assert-Tool 'Inno Setup compiler (ISCC.exe)' {
        [bool](Get-Command ISCC.exe -ErrorAction SilentlyContinue) -or
        (Test-Path 'C:\Program Files (x86)\Inno Setup 6\ISCC.exe')
    }
}
Assert-NonEmptyDir (Join-Path $project 'assets\icons') 'Icon assets'
Assert-NonEmptyDir (Join-Path $project 'assets\images') 'Image assets'
if (-not (Test-Path -LiteralPath (Join-Path $project 'main.py'))) { Fail 'main.py not found.' }
if (-not (Test-Path -LiteralPath (Join-Path $project 'build_exe.bat'))) { Fail 'build_exe.bat not found.' }
Write-Host "Preflight checks: OK"

# ---------- 3. version consistency ----------
$issVersion = (Select-String -LiteralPath $issPath -Pattern 'MyAppVersion\s+"([^"]+)"').Matches[0].Groups[1].Value
if ($issVersion -ne $version) {
    Write-Host ""
    Write-Host "NOTE: PrayerMusicGuard.iss still says version '$issVersion' while VERSION says '$version'."
    if ($Release) {
        Fail "Fix the #define MyAppVersion in PrayerMusicGuard.iss to '$version' before releasing."
    }
    Write-Host "(Validation mode: reported only, nothing changed.)"
}
else { Write-Host "Version consistency (VERSION == .iss MyAppVersion): OK" }

# ---------- 4. VALIDATION-ONLY exit ----------
if (-not $Release) {
    Write-Host ""
    Write-Host "Validation finished. Current dist\ contents were NOT touched:"
    Get-ChildItem -LiteralPath (Join-Path $project 'dist') -File -ErrorAction SilentlyContinue |
        ForEach-Object { Write-Host ("  dist\{0}  ({1:N0} bytes)" -f $_.Name, $_.Length) }
    Write-Host "No EXE or Setup was rebuilt. Run with -Release when you are ready to build and archive."
    exit 0
}

# ---------- 5. FULL RELEASE: build EXE ----------
$dist = Join-Path $project 'dist'
$releases = Join-Path $project 'releases'
$releaseDir = Join-Path $releases ("v$version")
if (Test-Path -LiteralPath $releaseDir) {
    Fail "Release folder already exists: $releaseDir (bump PATCH in VERSION for a new release)."
}

Write-Host ""
Write-Host "[1/5] Building EXE with the pinned Win7 toolchain ..."
# Phase 46: no bare "python", no vendor\ path, no user-site fallback. The
# build runs entirely inside win7\venv (Python 3.8.10 x64, PyInstaller 5.13.2).
$env:PYTHONNOUSERSITE = '1'
$env:PYTHONPATH = $null
& $win7Python -m PyInstaller --noconfirm --clean PrayerMusicGuard.spec
if ($LASTEXITCODE -ne 0 -or -not (Test-Path -LiteralPath (Join-Path $dist 'PrayerMusicGuard.exe'))) {
    Fail "EXE build step failed."
}
Write-Host "EXE build: OK -> dist\PrayerMusicGuard.exe (Python 3.8.10 x64 + PyInstaller 5.13.2)"

# ---------- 6. build Setup ----------
$setupExe = Join-Path $dist 'PrayerMusicGuard-Setup.exe'
if (-not $SkipSetup) {
    Write-Host ""
    Write-Host "[2/5] Building Inno Setup installer ..."
    $iscc = Get-Command ISCC.exe -ErrorAction SilentlyContinue
    if (-not $iscc) { $iscc = Get-Item 'C:\Program Files (x86)\Inno Setup 6\ISCC.exe' }
    # Normalize to the executable path: Get-Command yields CommandInfo (.Source),
    # Get-Item yields FileInfo (.FullName). Both are invoked safely via .FullName.
    $isccPath = if ($iscc -is [string]) { $iscc } elseif ($iscc.FullName) { $iscc.FullName } else { $iscc.Source }
    & $isccPath $issPath
    if ($LASTEXITCODE -ne 0 -or -not (Test-Path -LiteralPath $setupExe)) { Fail "Inno Setup step failed." }
    Write-Host "Setup build: OK -> dist\PrayerMusicGuard-Setup.exe"
}
else {
    Write-Host "[2/5] Skipped (-SkipSetup)."
    if (-not (Test-Path -LiteralPath $setupExe)) { Fail "-SkipSetup used but no existing Setup in dist\ to archive." }
}

# ---------- 7. archive under releases\vX.Y.Z\ ----------
Write-Host ""
Write-Host "[3/5] Archiving release under releases\v$version\ ..."
New-Item -ItemType Directory -Path $releaseDir -Force | Out-Null
Copy-Item -LiteralPath (Join-Path $dist 'PrayerMusicGuard.exe') -Destination $releaseDir
Copy-Item -LiteralPath $setupExe -Destination $releaseDir

# ---------- 8. SHA256 hashes ----------
Write-Host "[4/5] Generating SHA256 hashes ..."
$artifacts = @(
    (Join-Path $releaseDir 'PrayerMusicGuard.exe'),
    $(if (-not $SkipSetup) { Join-Path $releaseDir 'PrayerMusicGuard-Setup.exe' })
) | Where-Object { $_ }
$hashLines = foreach ($a in $artifacts) {
    $h = Get-FileHash -LiteralPath $a -Algorithm SHA256
    '{0}  {1}' -f $h.Hash, (Split-Path -Leaf $a)
}
$hashFile = Join-Path $releaseDir 'SHA256SUMS.txt'
Set-Content -LiteralPath $hashFile -Value $hashLines -Encoding ascii
Write-Host "Hashes written: $hashFile"

# ---------- 9. release manifest ----------
Write-Host "[5/5] Generating release manifest ..."
$manifest = @(
    "release  = PrayerMusicGuard v$version",
    "built    = $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') (local)",
    "mode     = $(if ($SkipSetup) { 'exe-only' } else { 'exe+setup' })",
    "source   = main.py @ $((Get-FileHash -LiteralPath (Join-Path $project 'main.py') -Algorithm SHA256).Hash.Substring(0,12))",
    "",
    "artifacts:"
)
$manifest += $hashLines
Set-Content -LiteralPath (Join-Path $releaseDir 'RELEASE_MANIFEST.txt') -Value $manifest -Encoding utf8
Write-Host "Manifest written: releases\v$version\RELEASE_MANIFEST.txt"

# ---------- 10. final state ----------
Write-Host ""
Write-Host "Release v$version complete."
Write-Host "dist\ (current artifacts only):"
Get-ChildItem -LiteralPath $dist -File | ForEach-Object { Write-Host ("  dist\{0}" -f $_.Name) }
Write-Host "releases\v$version\ (archived):"
Get-ChildItem -LiteralPath $releaseDir -File | ForEach-Object { Write-Host ("  releases\v{0}\{1}" -f $version, $_.Name) }
exit 0