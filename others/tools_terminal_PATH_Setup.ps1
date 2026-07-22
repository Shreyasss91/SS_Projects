<#
.SYNOPSIS
Dev environment bootstrap/check tool for Windows (PowerShell).
.DESCRIPTION
Checks for: winget, git, python, node, code (VS Code), uv, bash (Git Bash), notepad++ (Notepad++),
claude (Claude Code CLI), grok (Grok CLI / xAI), codex (OpenAI Codex CLI), agy (Google Antigravity CLI),
cursor (Cursor CLI / agent), graphify (installed via uv; PyPI package is "graphifyy", CLI command is "graphify").
pip and npm are verified as part of python/node (they ship bundled, not installed separately).
winget is bootstrapped first (via Microsoft's Microsoft.WinGet.Client module) since every other
install below depends on it.
AI coding CLIs (claude, grok, codex, agy, cursor): install if missing. By default, already-installed
 tools are only reported (no update/reinstall on every run). Pass -UpdateClis to run each tool's
 own self-update command. Self-update never falls back to a full reinstall when the CLI is already
 on PATH - that was re-downloading npm packages / re-running installers every run when exit codes
 were non-zero or when `codex update` always re-ran `npm install -g`.
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
   - git Credential Manager store: prefer DPAPI over wincredman. On some Windows setups GCM's
     default 'wincredman' store fails with:
       fatal: Unable to persist credentials with the 'wincredman' credential store.
       See https://aka.ms/gcm/credstores for more information.
     That blocks git fetch/pull/push even when auth is fine. Setting
       git config --global credential.credentialStore dpapi
     uses encrypted DPAPI-backed storage instead (usual reliable fix). Also normalizes a messy
     global credential.helper list (empty/duplicate helpers) down to a single 'manager' entry.
 Deliberately NOT covered (by earlier choice): opencode. Add an install/update block for it when needed.
.NOTES
Run from a normal (non-admin) PowerShell 5.1+ session. winget installs are per-user by default;
if a package insists on machine-scope, re-run that one line as Administrator.
#>
[CmdletBinding()]
param(
# When set, run each installed AI CLI's built-in self-update (`claude update`, etc.).
# Default is install-if-missing only: already-present tools are reported and left alone.
# Self-update is never followed by a reinstall fallback when the CLI is already callable.
[switch]$UpdateClis
)
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

function Get-CliVersionLine {
    param([Parameter(Mandatory)][string]$Cmd)
    try {
        return (& $Cmd --version 2>&1 | Select-Object -First 1 | Out-String).Trim()
    }
    catch {
        return '(version unknown)'
    }
}

# Report an already-installed CLI without downloading or reinstalling.
function Show-CliInstalled {
    param(
        [Parameter(Mandatory)][string]$Cmd,
        [Parameter(Mandatory)][string]$FriendlyName
    )
    $ver = Get-CliVersionLine -Cmd $Cmd
    $src = (Get-Command $Cmd -ErrorAction SilentlyContinue).Source
    Write-Host "${Cmd}: already installed ($ver)" -ForegroundColor Green
    if ($src) {
        Write-Host "  $src" -ForegroundColor DarkGray
    }
    Write-Host "  (skip update; re-run with -UpdateClis to check for newer releases)" -ForegroundColor DarkGray
}

# Run "<cmd> update" only. Built-in update commands should upgrade when a newer release exists
# (no-op / "already latest" when current). Does NOT reinstall via npm/installer when self-update
# fails or returns a non-zero exit - that used to re-download on every bootstrap run.
# Uses Start-Process + WaitForExit so a hung interactive CLI cannot block the rest of the bootstrap.
function Update-CliIfAvailable {
    param(
        [Parameter(Mandatory)][string]$Cmd,
        [Parameter(Mandatory)][string]$FriendlyName,
        [int]$TimeoutSec = 180
    )
    $resolved = Get-Command $Cmd -ErrorAction SilentlyContinue
    if (-not $resolved) {
        Write-Warning "Cannot update $FriendlyName - '$Cmd' not on PATH."
        return
    }
    $before = Get-CliVersionLine -Cmd $Cmd
    Write-Host "Checking $FriendlyName for updates (current: $before)..." -ForegroundColor Cyan
    
    # Native .exe can be launched directly. npm global shims are .cmd/.ps1 - run via cmd.exe so
    # PATH resolution matches an interactive shell (Start-Process cannot run .ps1 as an exe).
    $source = $resolved.Source
    if ($source -like '*.exe') {
        $filePath = $source
        $argList  = @('update')
    }
    else {
        $filePath = "$env:ComSpec"
        $argList  = @('/d', '/c', "$Cmd update")
    }
    
    $tmpOut = [System.IO.Path]::GetTempFileName()
    $tmpErr = [System.IO.Path]::GetTempFileName()
    $exitCode = $null
    $combined = ''
    try {
        $proc = Start-Process -FilePath $filePath -ArgumentList $argList `
            -NoNewWindow -PassThru `
            -RedirectStandardOutput $tmpOut -RedirectStandardError $tmpErr
        if (-not $proc.WaitForExit($TimeoutSec * 1000)) {
            try { $proc.Kill() } catch { }
            Write-Host "  self-update timed out after ${TimeoutSec}s - leaving installed version as-is." -ForegroundColor Yellow
            return
        }
        # Ensure ExitCode is populated (some hosts leave it null until a final WaitForExit).
        if (-not $proc.HasExited) { $null = $proc.WaitForExit(5000) }
        try { $exitCode = $proc.ExitCode } catch { $exitCode = $null }
        
        $stdout = (Get-Content $tmpOut -Raw -ErrorAction SilentlyContinue)
        $stderr = (Get-Content $tmpErr -Raw -ErrorAction SilentlyContinue)
        $combined = (@($stdout, $stderr) | Where-Object { $_ } | ForEach-Object { $_.Trim() }) -join "`n"
        if ($combined) {
            # Keep noise down: print a short preview, not multi-page npm trees.
            $preview = if ($combined.Length -gt 500) { $combined.Substring(0, 500) + '...' } else { $combined }
            Write-Host $preview -ForegroundColor DarkGray
        }
    }
    catch {
        Write-Host "  self-update not available ($($_.Exception.Message)). Leaving installed version as-is." -ForegroundColor DarkGray
        return
    }
    finally {
        Remove-Item $tmpOut, $tmpErr -Force -ErrorAction SilentlyContinue
    }
    
    # Success if exit 0, or output clearly says already current (some CLIs exit non-zero / null
    # even when up to date; we must not reinstall in that case).
    $alreadyCurrent = $combined -match '(?i)(already up to date|up to date|is up to date|already latest|no updates? available)'
    if ($null -ne $exitCode -and $exitCode -ne 0 -and -not $alreadyCurrent) {
        Write-Host "  self-update exit code $exitCode - leaving installed version as-is (no reinstall fallback)." -ForegroundColor DarkGray
    }
    
    Sync-SessionPath
    $after = Get-CliVersionLine -Cmd $Cmd
    if ($after -and $before -and ($after -ne $before)) {
        Write-Host "${Cmd}: updated $before -> $after" -ForegroundColor Green
    }
    else {
        Write-Host "${Cmd}: up to date ($after)" -ForegroundColor Green
    }
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
    # notepad++: winget id Notepad++.Notepad++; command is notepad++.exe (PATH dir added in section 3).
    # Do not run it for a version string - it's a GUI app and can open a window.
    @{ Cmd = 'notepad++'; WingetId = 'Notepad++.Notepad++';   Name = 'Notepad++'; ReportSourceOnly = $true }
)

foreach ($t in $tools) {
    Write-Host "`n== $($t.Name) == " -ForegroundColor Magenta
    # Notepad++ is often installed under Program Files but not on PATH yet. Treat a known
    # install location as "present" so we only fix PATH later (section 3) instead of re-running winget.
    $alreadyPresent = Test-CommandExists $t.Cmd
    if (-not $alreadyPresent -and $t.Cmd -eq 'notepad++') {
        $nppCandidates = @(
            "$env:ProgramFiles\Notepad++\notepad++.exe"
            "${env:ProgramFiles(x86)}\Notepad++\notepad++.exe"
        )
        $alreadyPresent = [bool]($nppCandidates | Where-Object { Test-Path $_ } | Select-Object -First 1)
    }
    
    if ($alreadyPresent) {
        if ($t.ReportSourceOnly) {
            $src = $null
            if (Test-CommandExists $t.Cmd) {
                $src = (Get-Command $t.Cmd).Source
            }
            else {
                $src = @(
                    "$env:ProgramFiles\Notepad++\notepad++.exe"
                    "${env:ProgramFiles(x86)}\Notepad++\notepad++.exe"
                ) | Where-Object { Test-Path $_ } | Select-Object -First 1
            }
            Write-Host "$($t.Cmd): already installed ($src)" -ForegroundColor Green
        }
        else {
            $ver = & $t.Cmd --version 2>&1 | Select-Object -First 1
            Write-Host "$($t.Cmd): already installed ($ver)" -ForegroundColor Green
        }
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

# ---------------------------------------------------------------------------
# AI coding CLIs: install if missing. Default re-runs only report version.
# Pass -UpdateClis to run each tool's self-update (no reinstall fallback).
# ---------------------------------------------------------------------------

# claude - Claude Code CLI. Native installer is Anthropic's current recommended method
# (no Node required; installs to %USERPROFILE%\.local\bin). Optional update: `claude update`.
Write-Host "`n== claude (Claude Code CLI) ==" -ForegroundColor Magenta
$claudeBinDir = "$env:USERPROFILE\.local\bin"
$claudeExe    = Join-Path $claudeBinDir 'claude.exe'
if (-not (Test-CommandExists 'claude') -and (Test-Path $claudeExe)) {
    Write-Host "claude found at $claudeExe but not on PATH - adding bin dir only (no reinstall)." -ForegroundColor Cyan
    Add-UserPathEntry -Dir $claudeBinDir
    Sync-SessionPath
}
if (Test-CommandExists 'claude') {
    if ($UpdateClis) { Update-CliIfAvailable -Cmd 'claude' -FriendlyName 'Claude Code' }
    else { Show-CliInstalled -Cmd 'claude' -FriendlyName 'Claude Code' }
}
else {
    Write-Host "Installing Claude Code via native installer..." -ForegroundColor Cyan
    try {
        Invoke-RestMethod https://claude.ai/install.ps1 | Invoke-Expression
        Add-UserPathEntry -Dir $claudeBinDir
        Sync-SessionPath
        if (Test-CommandExists 'claude') {
            Write-Host "claude: installed ($(Get-CliVersionLine -Cmd 'claude'))" -ForegroundColor Green
        }
        else {
            Write-Warning "Native installer finished but claude not on PATH. Falling back to npm if available."
            if (Test-CommandExists 'npm') {
                npm install -g @anthropic-ai/claude-code
                Sync-SessionPath
            }
        }
    }
    catch {
        Write-Warning "Native installer failed ($_). Falling back to npm (requires Node)."
        if (Test-CommandExists 'npm') {
            npm install -g @anthropic-ai/claude-code
            Sync-SessionPath
        }
        else {
            Write-Warning "npm not available either - install Node first, then re-run."
        }
    }
}

# grok - Grok CLI (xAI). Official installer; binary at %USERPROFILE%\.grok\bin.
# Install ONLY when missing from PATH and that known path - never reinstall just because PATH is stale.
# Optional update: `grok update`.
Write-Host "`n== grok (Grok CLI / xAI) ==" -ForegroundColor Magenta
$grokBinDir = "$env:USERPROFILE\.grok\bin"
$grokExe    = Join-Path $grokBinDir 'grok.exe'
if (-not (Test-CommandExists 'grok') -and (Test-Path $grokExe)) {
    # Installed but not on this session's PATH - fix PATH only, do not reinstall.
    Write-Host "grok found at $grokExe but not on PATH - adding bin dir only (no reinstall)." -ForegroundColor Cyan
    Add-UserPathEntry -Dir $grokBinDir
    Sync-SessionPath
}
if (Test-CommandExists 'grok') {
    if ($UpdateClis) { Update-CliIfAvailable -Cmd 'grok' -FriendlyName 'Grok CLI' }
    else { Show-CliInstalled -Cmd 'grok' -FriendlyName 'Grok CLI' }
}
elseif (Test-Path $grokExe) {
    Write-Warning "grok.exe exists but still not callable. Open a new terminal and re-check."
}
else {
    Write-Host "Installing Grok CLI via official installer (irm https://x.ai/cli/install.ps1 | iex)..." -ForegroundColor Cyan
    try {
        Invoke-RestMethod https://x.ai/cli/install.ps1 | Invoke-Expression
        Add-UserPathEntry -Dir $grokBinDir
        Sync-SessionPath
        if (Test-CommandExists 'grok') {
            Write-Host "grok: installed ($(Get-CliVersionLine -Cmd 'grok'))" -ForegroundColor Green
        }
        elseif (Test-Path $grokExe) {
            Write-Warning "Installer finished; grok.exe is at $grokExe but not on PATH yet. Open a new terminal."
        }
        else {
            Write-Warning "Installer finished but grok was not found on PATH or at $grokExe."
        }
    }
    catch {
        Write-Warning "Grok CLI install failed: $_"
        Write-Warning "Manual: irm https://x.ai/cli/install.ps1 | iex"
    }
}

# codex - OpenAI Codex CLI. Prefer native Windows installer; npm (@openai/codex) is a supported
# fallback. Note: `codex update` re-runs `npm install -g @openai/codex` even when already current,
# so it is only invoked when -UpdateClis is passed (never on a plain re-run).
Write-Host "`n== codex (OpenAI Codex CLI) ==" -ForegroundColor Magenta
$codexNativeBinDir = "$env:LOCALAPPDATA\Programs\OpenAI\Codex\bin"
$codexNativeExe    = Join-Path $codexNativeBinDir 'codex.exe'
if (-not (Test-CommandExists 'codex') -and (Test-Path $codexNativeExe)) {
    Write-Host "codex found at $codexNativeExe but not on PATH - adding bin dir only (no reinstall)." -ForegroundColor Cyan
    Add-UserPathEntry -Dir $codexNativeBinDir
    Sync-SessionPath
}
if (Test-CommandExists 'codex') {
    if ($UpdateClis) { Update-CliIfAvailable -Cmd 'codex' -FriendlyName 'Codex CLI' }
    else { Show-CliInstalled -Cmd 'codex' -FriendlyName 'Codex CLI' }
}
else {
    Write-Host "Installing Codex CLI via official installer..." -ForegroundColor Cyan
    try {
        Invoke-RestMethod https://chatgpt.com/codex/install.ps1 | Invoke-Expression
        Add-UserPathEntry -Dir $codexNativeBinDir
        Sync-SessionPath
        if (Test-CommandExists 'codex') {
            Write-Host "codex: installed ($(Get-CliVersionLine -Cmd 'codex'))" -ForegroundColor Green
        }
        elseif (Test-CommandExists 'npm') {
            Write-Warning "Native installer finished but codex not on PATH - falling back to npm."
            npm install -g @openai/codex
            Sync-SessionPath
            if (Test-CommandExists 'codex') {
                Write-Host "codex: installed via npm ($(Get-CliVersionLine -Cmd 'codex'))" -ForegroundColor Green
            }
        }
        else {
            Write-Warning "Installer finished but codex not found. Manual: irm https://chatgpt.com/codex/install.ps1 | iex"
        }
    }
    catch {
        Write-Warning "Native Codex install failed ($_). Falling back to npm if available."
        if (Test-CommandExists 'npm') {
            npm install -g @openai/codex
            Sync-SessionPath
            if (Test-CommandExists 'codex') {
                Write-Host "codex: installed via npm ($(Get-CliVersionLine -Cmd 'codex'))" -ForegroundColor Green
            }
        }
        else {
            Write-Warning "npm not available either - install Node first, then re-run."
            Write-Warning "Manual: irm https://chatgpt.com/codex/install.ps1 | iex"
        }
    }
}

# agy - Google Antigravity CLI. Official installer; binary under %LOCALAPPDATA%\agy\bin.
# Optional update: `agy update`.
Write-Host "`n== agy (Google Antigravity CLI) ==" -ForegroundColor Magenta
$agyBinDir = "$env:LOCALAPPDATA\agy\bin"
$agyExe    = Join-Path $agyBinDir 'agy.exe'
if (-not (Test-CommandExists 'agy') -and (Test-Path $agyExe)) {
    Write-Host "agy found at $agyExe but not on PATH - adding bin dir only (no reinstall)." -ForegroundColor Cyan
    Add-UserPathEntry -Dir $agyBinDir
    Sync-SessionPath
}
if (Test-CommandExists 'agy') {
    if ($UpdateClis) { Update-CliIfAvailable -Cmd 'agy' -FriendlyName 'Antigravity CLI (agy)' }
    else { Show-CliInstalled -Cmd 'agy' -FriendlyName 'Antigravity CLI (agy)' }
}
elseif (Test-Path $agyExe) {
    Write-Warning "agy.exe exists but still not callable. Open a new terminal and re-check."
}
else {
    Write-Host "Installing Antigravity CLI via official installer (irm https://antigravity.google/cli/install.ps1 | iex)..." -ForegroundColor Cyan
    try {
        Invoke-RestMethod https://antigravity.google/cli/install.ps1 | Invoke-Expression
        Add-UserPathEntry -Dir $agyBinDir
        Sync-SessionPath
        if (Test-CommandExists 'agy') {
            Write-Host "agy: installed ($(Get-CliVersionLine -Cmd 'agy'))" -ForegroundColor Green
        }
        elseif (Test-Path $agyExe) {
            Write-Warning "Installer finished; agy.exe is at $agyExe but not on PATH yet. Open a new terminal."
        }
        else {
            Write-Warning "Installer finished but agy was not found on PATH or at $agyExe."
        }
    }
    catch {
        Write-Warning "Antigravity CLI (agy) install failed: $_"
        Write-Warning "Manual: irm https://antigravity.google/cli/install.ps1 | iex"
    }
}

# cursor - Cursor CLI (agent). Official installer; binary at %LOCALAPPDATA%\cursor-agent.
# We alias 'cursor' to call agent.cmd with all arguments.
Write-Host "`n== cursor (Cursor CLI) ==" -ForegroundColor Magenta
$cursorBinDir = "$env:LOCALAPPDATA\cursor-agent"
$cursorAgentCmd = Join-Path $cursorBinDir 'agent.cmd'

if (-not (Test-CommandExists 'agent') -and (Test-Path $cursorAgentCmd)) {
    Write-Host "cursor agent found at $cursorAgentCmd but not on PATH - adding bin dir only (no reinstall)." -ForegroundColor Cyan
    Add-UserPathEntry -Dir $cursorBinDir
    Sync-SessionPath
}

if (Test-CommandExists 'agent') {
    if ($UpdateClis) {
        Write-Host "Checking Cursor CLI for updates..." -ForegroundColor Cyan
        Show-CliInstalled -Cmd 'agent' -FriendlyName 'Cursor CLI'
    }
    else {
        Show-CliInstalled -Cmd 'agent' -FriendlyName 'Cursor CLI'
    }
}
elseif (Test-Path $cursorAgentCmd) {
    Write-Warning "agent.cmd exists but still not callable. Open a new terminal and re-check."
}
else {
    Write-Host "Installing Cursor CLI via official installer..." -ForegroundColor Cyan
    try {
        Invoke-RestMethod 'https://cursor.com/install?win32=true' | Invoke-Expression
        Add-UserPathEntry -Dir $cursorBinDir
        Sync-SessionPath
        if (Test-CommandExists 'agent') {
            Write-Host "cursor (agent): installed ($(Get-CliVersionLine -Cmd 'agent'))" -ForegroundColor Green
        }
        else {
            Write-Warning "Installer finished but agent not found on PATH. Manual: irm 'https://cursor.com/install?win32=true' | iex"
        }
    }
    catch {
        Write-Warning "Cursor CLI install failed: $_"
        Write-Warning "Manual: irm 'https://cursor.com/install?win32=true' | iex"
    }
}

# Ensure 'cursor' alias/function is available in the current session immediately
if (Test-Path $cursorAgentCmd) {
    if (-not (Test-CommandExists 'cursor')) {
        function global:cursor {
            & "$env:LOCALAPPDATA\cursor-agent\agent.cmd" @args
        }
    }
}

# graphify - AI-assistant knowledge-graph CLI (https://graphify.net). Note the PyPI package name
# is "graphifyy" (double y) - other graphify* packages on PyPI are unaffiliated lookalikes; the
# installed command is "graphify". Installed via uv, which puts the shim in %USERPROFILE%\.local\bin
# - the same directory claude/grok native installers use, already covered by $knownDirs below.
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

# Covers claude (native vs npm fallback), grok (xAI), codex (native / npm), agy (Antigravity),
# cursor (Cursor CLI agent), graphify (via uv), VS Code's bin dir, and Notepad++. 
# Replaces the old conflicting setx PATH lines and the Set-Alias code from the original spec.
$knownDirs = @(
    "$env:LOCALAPPDATA\Programs\Microsoft VS Code\bin"
    "$env:APPDATA\npm"                                      # npm global shims (codex/claude fallback)
    "$env:USERPROFILE\.local\bin"                           # claude (native) + graphify (uv tool)
    "$env:USERPROFILE\.grok\bin"                            # grok (xAI CLI installer)
    "$env:LOCALAPPDATA\Programs\OpenAI\Codex\bin"           # codex (native Windows installer)
    "$env:LOCALAPPDATA\agy\bin"                             # agy (Google Antigravity CLI)
    "$env:LOCALAPPDATA\cursor-agent"                        # cursor (Cursor CLI agent)
    "$env:ProgramFiles\Notepad++"                           # notepad++ (64-bit default install)
    "${env:ProgramFiles(x86)}\Notepad++"                    # notepad++ (32-bit install)
)
foreach ($d in $knownDirs) { Add-UserPathEntry -Dir $d }

Sync-SessionPath
Write-Host "Session PATH refreshed from User+Machine registry values." -ForegroundColor Green

# Confirm AI CLIs / graphify / notepad++ are callable in this running session, not just a future one.
foreach ($cli in @('claude', 'grok', 'codex', 'agy', 'graphify', 'cursor')) {
    if (Test-CommandExists $cli) {
        Write-Host "$cli is live in this session: $(Get-CliVersionLine -Cmd $cli)" -ForegroundColor Green
    }
}
if (Test-CommandExists 'notepad++') {
    Write-Host "notepad++ is live in this session: $((Get-Command notepad++).Source)" -ForegroundColor Green
}
else {
    Write-Warning "notepad++ not on PATH yet. Install Notepad++ (winget id Notepad++.Notepad++) and re-run, or open a new terminal after PATH was updated."
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
    Write-Host "PS`$currentFolder> " -NoNewline -ForegroundColor Cyan
    return " "
}
function global:cursor {
    & "`$env:LOCALAPPDATA\cursor-agent\agent.cmd" @args
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
            Write-Host "   `"$($_.Key)`": $($_.Value | ConvertTo-Json -Compress)"
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

# git credential store - GCM default 'wincredman' can fail to persist on some Windows setups:
# fatal: Unable to persist credentials with the 'wincredman' credential store.
# Prefer DPAPI (encrypted file-backed store). Also collapse empty/duplicate global helpers to a
# single 'manager' entry so GCM is the only helper consulted.
Write-Host "`n== git credential store (GCM / dpapi) ==" -ForegroundColor Magenta
if (Test-CommandExists 'git') {
    $helpers = @(git config --global --get-all credential.helper 2>$null)
    $store   = git config --global --get credential.credentialStore 2>$null
    
    # Empty helper lines and multiple manager entries both cause confusing GCM behavior.
    $needsHelperCleanup = ($helpers.Count -eq 0) -or
        ($helpers | Where-Object { [string]::IsNullOrWhiteSpace($_) }) -or
        (($helpers | Where-Object { $_ -match 'manager' }).Count -ne 1) -or
        ($helpers.Count -gt 1)
        
    if ($needsHelperCleanup) {
        Write-Host "Normalizing global credential.helper -> single 'manager' (was: $($helpers -join ' | '))" -ForegroundColor Cyan
        git config --global --unset-all credential.helper 2>$null
        git config --global credential.helper manager
    }
    else {
        Write-Host "credential.helper already clean: $($helpers -join ', ')" -ForegroundColor DarkGray
    }
    
    if ($store -ieq 'dpapi') {
        Write-Host "credential.credentialStore already dpapi (avoids wincredman persist failures)." -ForegroundColor Green
    }
    else {
        # wincredman is the GCM Windows default; when it can't write to Credential Manager you get
        # fatal errors on fetch/pull/push. dpapi is the documented alternative store for that case.
        if ($store) {
            Write-Host "credential.credentialStore was '$store' - switching to dpapi..." -ForegroundColor Cyan
        }
        else {
            Write-Host "credential.credentialStore not set - setting dpapi (avoids wincredman persist failures)..." -ForegroundColor Cyan
        }
        git config --global credential.credentialStore dpapi
        Write-Host "Set: git config --global credential.credentialStore dpapi" -ForegroundColor Green
    }
    
    Write-Host "  helper = $(git config --global --get-all credential.helper 2>$null)" -ForegroundColor DarkGray
    Write-Host "  credentialStore = $(git config --global --get credential.credentialStore 2>$null)" -ForegroundColor DarkGray
    Write-Host "  (If auth is still needed: run git fetch in an interactive terminal and complete the GCM login once.)" -ForegroundColor DarkGray
}
else {
    Write-Warning "git not available - credential store check skipped."
}

Write-Host "`nDone. Open a new terminal (or run '. `$PROFILE') to pick up profile + PATH changes." -ForegroundColor Cyan
if (-not $UpdateClis) {
    Write-Host "Tip: installed AI CLIs were left as-is. To check for newer releases: .\tools_terminal_PATH_Setup.ps1 -UpdateClis" -ForegroundColor DarkGray
}