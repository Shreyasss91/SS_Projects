<#
.SYNOPSIS
    Dev environment bootstrap/check tool for Windows (PowerShell).

.DESCRIPTION
    Checks for: winget, git, python, node, code (VS Code), uv, bash (Git Bash), claude (Claude Code CLI),
    graphify (installed via uv; PyPI package is "graphifyy", CLI command is "graphify").
    pip and npm are verified as part of python/node (they ship bundled, not installed separately).
    winget is bootstrapped first (via Microsoft's Microsoft.WinGet.Client module) since every other
    install below depends on it.

    Fixes applied:
      - PATH is only ever read/written via [Environment]::GetEnvironmentVariable/SetEnvironmentVariable
        against the User scope, never via `setx`. setx silently truncates values over 1024 characters
        and %PATH% expansion is cmd.exe syntax that PowerShell won't expand - both would corrupt PATH.
      - Every PATH write checks for an existing (case-insensitive, trailing-slash-normalized) entry
        first, so re-running this script is safe and won't create duplicates.
      - $PROFILE is edited once, wrapped in a marker block, so re-runs don't duplicate content.
      - VS Code settings.json is only rewritten if a key is actually missing, with a .bak backup made
        first; if the file has comments (jsonc) that break parsing, the script prints the settings to
        add by hand instead of guessing at a text-insertion.
      - git core.editor is reported, not silently overwritten - that's a preference decision, not a bug.

    Deliberately NOT covered (by your earlier choice): codex, opencode. Add winget/npm IDs for those
    to the $tools list or the claude-install block below once you know which packages you want.

.NOTES
    Run from a normal (non-admin) PowerShell 5.1+ session. winget installs are per-user by default;
    if a package insists on machine-scope, re-run that one line as Administrator.
#>

[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'

# ---------------------------------------------------------------------------
# 0. Execution policy - persisted for CurrentUser (your choice), not just this process
# ---------------------------------------------------------------------------
$currentPolicy = Get-ExecutionPolicy -Scope CurrentUser
if ($currentPolicy -notin @('RemoteSigned', 'Unrestricted', 'Bypass')) {
    Write-Host "Setting execution policy (CurrentUser) to Bypass..." -ForegroundColor Cyan
    Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy Bypass -Force
}
else {
    Write-Host "Execution policy already permissive for CurrentUser ($currentPolicy)." -ForegroundColor DarkGray
}

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

function Test-CommandExists {
    param([string]$Name)
    return [bool](Get-Command $Name -ErrorAction SilentlyContinue)
}

function Get-UserPath { [Environment]::GetEnvironmentVariable('Path', 'User') }
function Set-UserPath { param([string]$Value) [Environment]::SetEnvironmentVariable('Path', $Value, 'User') }

function Add-UserPathEntry {
    param([Parameter(Mandatory)][string]$Dir)

    if (-not (Test-Path $Dir)) {
        Write-Host "  (skip - not found: $Dir)" -ForegroundColor DarkGray
        return
    }

    $entries = (Get-UserPath) -split ';' | Where-Object { $_ -ne '' }
    $already = $entries | Where-Object { $_.TrimEnd('\') -ieq $Dir.TrimEnd('\') }

    if ($already) {
        Write-Host "  already on User PATH: $Dir" -ForegroundColor DarkGray
        return
    }

    Set-UserPath (($entries + $Dir) -join ';')
    Write-Host "  added to User PATH: $Dir" -ForegroundColor Green
}

function Remove-DuplicatePathEntries {
    $entries = (Get-UserPath) -split ';' | Where-Object { $_ -ne '' }
    $seen = New-Object System.Collections.Generic.HashSet[string]
    $deduped = @()
    foreach ($e in $entries) {
        if ($seen.Add($e.TrimEnd('\').ToLowerInvariant())) { $deduped += $e }
    }
    if ($deduped.Count -lt $entries.Count) {
        Set-UserPath ($deduped -join ';')
        Write-Host "Removed $($entries.Count - $deduped.Count) duplicate User PATH entrie(s)." -ForegroundColor Yellow
    }
    else {
        Write-Host "No duplicate User PATH entries." -ForegroundColor DarkGray
    }
}

function Sync-SessionPath {
    # SetEnvironmentVariable(...,'User') never touches a running session's $env:Path.
    $machine = [Environment]::GetEnvironmentVariable('Path', 'Machine')
    $user    = [Environment]::GetEnvironmentVariable('Path', 'User')
    $env:Path = "$machine;$user"
}

function Install-WithWinget {
    param([Parameter(Mandatory)][string]$Id, [Parameter(Mandatory)][string]$FriendlyName)
    if (-not (Test-CommandExists 'winget')) {
        Write-Warning "winget not available - can't auto-install $FriendlyName."
        return
    }
    Write-Host "Installing $FriendlyName ($Id) via winget..." -ForegroundColor Cyan
    winget install --id $Id -e --source winget --accept-source-agreements --accept-package-agreements
}

# ---------------------------------------------------------------------------
# 1. winget itself (bootstrap dependency for most of the below - install if missing)
# ---------------------------------------------------------------------------
Write-Host "`n== winget ==" -ForegroundColor Magenta

# winget.exe resolves through an App Execution Alias in this folder. Windows normally puts it on
# PATH by default, but we ensure it explicitly since that's what was asked for.
$wingetAliasDir = "$env:LOCALAPPDATA\Microsoft\WindowsApps"

if (-not (Test-CommandExists 'winget')) {
    Write-Host "winget not found - attempting install..." -ForegroundColor Cyan

    # Cheapest fix first: the App Installer package can be present but unregistered for this user
    # (common on a fresh profile or unattended image) - this needs no download at all.
    try {
        Add-AppxPackage -RegisterByFamilyName -MainPackage Microsoft.DesktopAppInstaller_8wekyb3d8bbwe -ErrorAction Stop
    }
    catch { }

    if (-not (Test-CommandExists 'winget')) {
        # Microsoft's own supported bootstrap path. Deliberately not hand-rolling the old
        # VCLibs/UI.Xaml + .msixbundle dance here - those direct download URLs drift and break
        # (see microsoft/winget-cli discussions #817 and #2890); this module handles dependency
        # resolution itself and is what Microsoft Learn currently documents for this exact case.
        try {
            Write-Host "Bootstrapping via the Microsoft.WinGet.Client module..." -ForegroundColor Cyan
            # Windows PowerShell 5.1 defaults to TLS 1.0/1.1, which PSGallery now rejects - that's
            # what causes "No match was found ... for the provider 'NuGet'" even with a fine network.
            [Net.ServicePointManager]::SecurityProtocol = [Net.ServicePointManager]::SecurityProtocol -bor [Net.SecurityProtocolType]::Tls12
            Install-PackageProvider -Name NuGet -Force -Scope CurrentUser | Out-Null
            Install-Module -Name Microsoft.WinGet.Client -Force -Scope CurrentUser -Repository PSGallery | Out-Null
            Repair-WinGetPackageManager   # no -AllUsers: that needs elevation; this repairs for the current (non-admin) user
        }
        catch {
            Write-Warning "Automated winget bootstrap failed: $_"
            Write-Warning "Manual fallback: install 'App Installer' from the Microsoft Store, or https://aka.ms/getwinget"
        }
    }

    Add-UserPathEntry -Dir $wingetAliasDir
    Sync-SessionPath
}
else {
    Add-UserPathEntry -Dir $wingetAliasDir
}

if (Test-CommandExists 'winget') {
    Write-Host "winget: OK ($(winget --version))" -ForegroundColor Green
}
else {
    Write-Warning "winget still not available after the bootstrap attempt."
    Write-Warning "Try closing and reopening this terminal (or signing out/in) and re-running this script."
    Write-Warning "Skipping winget-dependent installs below until it's present."
}

# ---------------------------------------------------------------------------
# 2. Core tools via winget
# ---------------------------------------------------------------------------
$tools = @(
    @{ Cmd = 'git';  WingetId = 'Git.Git';                    Name = 'Git (also provides Git Bash)' }
    @{ Cmd = 'python'; WingetId = 'Python.Python.3.13';       Name = 'Python' }   # bump version ID as needed
    @{ Cmd = 'node'; WingetId = 'OpenJS.NodeJS.LTS';          Name = 'Node.js (also provides npm)' }
    @{ Cmd = 'code'; WingetId = 'Microsoft.VisualStudioCode'; Name = 'VS Code' }
    @{ Cmd = 'uv';   WingetId = 'astral-sh.uv';                Name = 'uv' }
)

foreach ($t in $tools) {
    Write-Host "`n== $($t.Name) ==" -ForegroundColor Magenta
    if (Test-CommandExists $t.Cmd) {
        $ver = & $t.Cmd --version 2>&1 | Select-Object -First 1
        Write-Host "$($t.Cmd): already installed ($ver)" -ForegroundColor Green
    }
    else {
        Install-WithWinget -Id $t.WingetId -FriendlyName $t.Name
    }
}

# pip - bundled with Python, verify only
Write-Host "`n== pip ==" -ForegroundColor Magenta
if (Test-CommandExists 'python') {
    try {
        Write-Host "pip: $(python -m pip --version 2>&1)" -ForegroundColor Green
    }
    catch {
        Write-Warning "Python found but pip isn't. Run: python -m ensurepip --upgrade"
    }
}
else {
    Write-Warning "pip check skipped - Python not installed yet (open a new terminal after the install above)."
}

# npm - bundled with Node, verify only
Write-Host "`n== npm ==" -ForegroundColor Magenta
if (Test-CommandExists 'npm') {
    Write-Host "npm: $(npm --version)" -ForegroundColor Green
}
else {
    Write-Warning "npm check skipped - Node not installed yet, or PATH needs a refresh (see below)."
}

# bash - Git Bash specifically, per your earlier choice (not WSL)
Write-Host "`n== bash (Git Bash) ==" -ForegroundColor Magenta
$gitBashPath = "$env:ProgramFiles\Git\bin\bash.exe"
if (Test-Path $gitBashPath) {
    Write-Host "Git Bash found: $gitBashPath" -ForegroundColor Green
}
elseif (Test-CommandExists 'bash') {
    Write-Host "bash found on PATH: $((Get-Command bash).Source)" -ForegroundColor Green
}
else {
    Write-Warning "Git Bash not found - it installs alongside Git.Git above. Re-run this script after that install finishes."
}

# claude - Claude Code CLI. Native installer is Anthropic's current recommended method
# (no Node required, auto-updates, installs to %USERPROFILE%\.local\bin).
Write-Host "`n== claude (Claude Code CLI) ==" -ForegroundColor Magenta
if (Test-CommandExists 'claude') {
    Write-Host "claude: already installed ($(claude --version 2>&1))" -ForegroundColor Green
}
else {
    Write-Host "Installing Claude Code via native installer..." -ForegroundColor Cyan
    try {
        Invoke-RestMethod https://claude.ai/install.ps1 | Invoke-Expression
    }
    catch {
        Write-Warning "Native installer failed ($_). Falling back to npm (requires Node)."
        if (Test-CommandExists 'npm') {
            npm install -g @anthropic-ai/claude-code
        }
        else {
            Write-Warning "npm not available either - install Node first, then re-run."
        }
    }
}

# graphify - AI-assistant knowledge-graph CLI (https://graphify.net). Note the PyPI package name
# is "graphifyy" (double y) - other graphify* packages on PyPI are unaffiliated lookalikes; the
# installed command is "graphify". Installed via uv, which puts the shim in %USERPROFILE%\.local\bin
# - the same directory claude's native installer uses, already covered by $knownDirs below.
Write-Host "`n== graphify ==" -ForegroundColor Magenta
if (Test-CommandExists 'graphify') {
    Write-Host "graphify: already installed ($(graphify --version 2>&1))" -ForegroundColor Green
}
elseif (Test-CommandExists 'uv') {
    Write-Host "Installing graphify (package: graphifyy) via uv..." -ForegroundColor Cyan
    uv tool install graphifyy
    uv tool update-shell   # belt-and-suspenders: also registers uv's own tool bin dir + Git Bash's ~/.bashrc
}
else {
    Write-Warning "uv not available - can't install graphify. Install uv above first, then re-run."
}

# ---------------------------------------------------------------------------
# 3. PATH: dedupe, guarantee known install locations, refresh this session
# ---------------------------------------------------------------------------
Write-Host "`n== PATH cleanup ==" -ForegroundColor Magenta
Remove-DuplicatePathEntries

# Covers both possible claude install methods (native vs npm fallback), graphify (via uv), and
# VS Code's bin dir. This replaces the three conflicting `setx PATH ...` lines and the
# `Set-Alias code` from the original spec - if VS Code's bin dir is genuinely on PATH, no alias
# is needed.
$knownDirs = @(
    "$env:LOCALAPPDATA\Programs\Microsoft VS Code\bin"
    "$env:APPDATA\npm"
    "$env:USERPROFILE\.local\bin"     # claude (native installer) + graphify (uv tool)
)
foreach ($d in $knownDirs) { Add-UserPathEntry -Dir $d }

Sync-SessionPath
Write-Host "Session PATH refreshed from User+Machine registry values." -ForegroundColor Green

# Confirm graphify specifically is now callable in *this* running session, not just a future one.
if (Test-CommandExists 'graphify') {
    Write-Host "graphify is live in this session: $(graphify --version 2>&1)" -ForegroundColor Green
}

# ---------------------------------------------------------------------------
# 4. $PROFILE - single consolidated, idempotent edit
# ---------------------------------------------------------------------------
Write-Host "`n== PowerShell profile ==" -ForegroundColor Magenta
if (-not (Test-Path $PROFILE)) {
    New-Item -ItemType File -Path $PROFILE -Force | Out-Null
}

$marker = '# >>> dev-environment-setup >>>'
$endMarker = '# <<< dev-environment-setup <<<'
$existing = Get-Content $PROFILE -Raw -ErrorAction SilentlyContinue

if ($existing -match [regex]::Escape($marker)) {
    Write-Host "Profile block already present - leaving as is." -ForegroundColor DarkGray
}
else {
    $block = @"
$marker
[Console]::InputEncoding = [System.Text.Encoding]::UTF8
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
[Environment]::SetEnvironmentVariable("PYTHONUTF8", "1", "User")

function prompt {
    `$currentFolder = (Get-Location | Split-Path -Leaf)
    Write-Host "PS `$currentFolder> " -NoNewline -ForegroundColor Cyan
    return " "
}
$endMarker
"@
    Add-Content -Path $PROFILE -Value "`n$block"
    Write-Host "Appended setup block to $PROFILE" -ForegroundColor Green
}

# ---------------------------------------------------------------------------
# 5. VS Code settings.json
# ---------------------------------------------------------------------------
Write-Host "`n== VS Code settings ==" -ForegroundColor Magenta
$vscodeSettingsPath = "$env:APPDATA\Code\User\settings.json"

$desiredSettings = [ordered]@{
    'git.useEditorAsCommitInput'                         = $true
    'git.terminalGitEditor'                              = $true
    'terminal.integrated.enablePersistentSessions'       = $true
    'terminal.integrated.persistentSessionReviveProcess' = 'onExitAndWindowClose'
    'terminal.integrated.persistentSessionScrollback'    = 2000
}

if (-not (Test-Path $vscodeSettingsPath)) {
    Write-Warning "settings.json not found at $vscodeSettingsPath - open VS Code once, then re-run this script."
}
else {
    try {
        $json = Get-Content $vscodeSettingsPath -Raw | ConvertFrom-Json
        $changed = $false
        foreach ($key in $desiredSettings.Keys) {
            if (-not $json.PSObject.Properties[$key]) {
                $json | Add-Member -NotePropertyName $key -NotePropertyValue $desiredSettings[$key]
                $changed = $true
            }
        }
        if ($changed) {
            Copy-Item $vscodeSettingsPath "$vscodeSettingsPath.bak" -Force
            ($json | ConvertTo-Json -Depth 10) | Set-Content $vscodeSettingsPath
            Write-Host "Updated $vscodeSettingsPath (backup: .bak)" -ForegroundColor Green
        }
        else {
            Write-Host "All desired settings already present." -ForegroundColor DarkGray
        }
    }
    catch {
        Write-Warning "Couldn't auto-parse settings.json (likely has comments/jsonc, which breaks plain JSON parsing)."
        Write-Host "Add these manually instead:" -ForegroundColor Yellow
        $desiredSettings.GetEnumerator() | ForEach-Object {
            Write-Host "  `"$($_.Key)`": $($_.Value | ConvertTo-Json -Compress)"
        }
    }
}

# git core.editor - reported, not silently overwritten (that's your call, not a bug to auto-fix)
Write-Host "`n== git core.editor ==" -ForegroundColor Magenta
if (Test-CommandExists 'git') {
    $coreEditor = git config --global core.editor 2>$null
    if ($coreEditor) {
        Write-Host "core.editor is set to: $coreEditor" -ForegroundColor Green
    }
    else {
        Write-Host "core.editor is not set. To use VS Code: git config --global core.editor `"code --wait`"" -ForegroundColor Yellow
    }
}
else {
    Write-Warning "git not available - core.editor check skipped."
}

Write-Host "`nDone. Open a new terminal (or run '. `$PROFILE') to pick up profile + PATH changes." -ForegroundColor Cyan