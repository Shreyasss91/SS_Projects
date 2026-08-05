<#
.SYNOPSIS
    Safe cleanup + disk-space report for this HP Notebook (i3-4005U / 5400rpm HDD / 8GB RAM).

.DESCRIPTION
    REPORT-ONLY BY DEFAULT. Run it bare to see what it *would* do; nothing is changed.
    Pass -Apply to actually perform the changes marked [APPLY].

    It never touches user documents, never empties the Recycle Bin, and never deletes
    anything outside temp/cache locations. Deletions are limited to files older than
    -TempOlderThanDays (default 7).

.PARAMETER Apply
    Perform the changes. Without this, the script only reports.

.PARAMETER ScanDrives
    Drive letters to scan for large files/folders. Default: C, E
    (D is skipped by default -- it is your largest and least-full volume.)

.PARAMETER TopN
    How many large files / folders to list per drive. Default 20.

.PARAMETER TempOlderThanDays
    Only delete temp files older than this many days. Default 7.

.PARAMETER SkipLargeFileScan
    Skip the recursive large-file scan (it is slow on a 5400rpm HDD -- several minutes).

.PARAMETER Aggressive
    Opt in to the three larger reclaims. Requires -Apply AND admin. Each one prompts
    for confirmation unless -Yes is given. None touches user data.

      * Hibernation file  -- shrink or remove hiberfil.sys (see -HibernateMode)
      * Windows upgrade staging -- clear C:\$Windows.~BT etc. via Disk Cleanup.
        NOTE: this CANCELS any pending Windows feature upgrade.
      * Orphaned search index -- delete Windows.edb, but ONLY when WSearch is
        already Disabled, in which case nothing reads the file. Often the single
        largest reclaim on the disk. Re-enabling search rebuilds it.

.PARAMETER HibernateMode
    What -Aggressive does to hiberfil.sys:
      Reduced (default) -- keeps Fast Startup, drops full hibernate. ~50% smaller.
                           Best choice on a spinning disk: Fast Startup is one of
                           the few things helping boot time.
      Off               -- removes hiberfil.sys entirely. Reclaims more, but you
                           LOSE Fast Startup too.
      None              -- leave hibernation alone.

.PARAMETER Yes
    Skip the interactive confirmation prompts for -Aggressive actions.
    Required when running non-interactively.

.PARAMETER Diagnostics
    Run the full read-only health panel (section 6). This is the scripted form of
    every manual check from the investigation:

      6.1  Drive reliability counters + latency maxima  (Get-StorageReliabilityCounter)
      6.2  True SMART predict-fail                      (MSStorageDriver_FailurePredictStatus)
      6.3  Filesystem dirty flag + fragmentation        (fsutil / defrag /A /V)
      6.4  Battery health                               (powercfg /batteryreport)
      6.5  Unexpected shutdowns, decoded                (Kernel-Power 41 / WHEA / dumps)
      6.6  Thermals                                     (MSAcpi_ThermalZoneTemperature)
      6.7  Power & hibernation state                    (powercfg /a)

    NOTHING here changes the machine. It is unaffected by -Apply. Several checks
    need admin and will say so if unavailable.

.PARAMETER DiagnosticsOnly
    Run section 6 and nothing else. Implies -Diagnostics. Use this for a periodic
    health check without the cleanup passes.

.PARAMETER EventDays
    How far back section 6.5 looks for shutdown / hardware events. Default 120.
    (The original investigation used 60 and UNDERCOUNTED the shutdowns 5x, which is
    why the default here is deliberately wide.)

.PARAMETER DiagnosticsOutDir
    Where to write the generated battery report. Default: alongside this script.
    Never System32 -- powercfg's own default dumps it into the current directory,
    which is a poor place for it.

.EXAMPLE
    .\pc-cleanup.ps1
    Report only. Safe. Start here.

.EXAMPLE
    # Full read-only health panel. ELEVATED gives the complete picture.
    .\pc-cleanup.ps1 -DiagnosticsOnly

.EXAMPLE
    # Cleanup plus health panel, looking back a full year for shutdown events.
    .\pc-cleanup.ps1 -Apply -Diagnostics -EventDays 365

.EXAMPLE
    .\pc-cleanup.ps1 -SkipLargeFileScan
    Fast report, no recursive scan.

.EXAMPLE
    # Run from an ELEVATED PowerShell to include the service changes:
    .\pc-cleanup.ps1 -Apply

.EXAMPLE
    # Everything, including the two big reclaims. ELEVATED. Prompts before each.
    .\pc-cleanup.ps1 -Apply -Aggressive

.EXAMPLE
    # Reclaim the full 3.17GB by killing Fast Startup too, no prompts.
    .\pc-cleanup.ps1 -Apply -Aggressive -HibernateMode Off -Yes

.PARAMETER Help
    Print the built-in usage guide -- every argument with a full explanation, the
    safety model, and worked examples -- then exit without running anything.

    Accepted forms: -Help  -h  --help  /?  -Usage  --usage

    This is richer than Get-Help on this file, so prefer it.

.PARAMETER Usage
    Alias for -Help.
#>

# PositionalBinding=$false is deliberate. By default PowerShell makes parameters
# positional in declaration order, so a bare value like "/?" or "C" would silently
# bind to -ScanDrives instead of being caught as a bad argument. Every option here
# must be named; anything bare falls through to $UnboundArgs and is handled below.
[CmdletBinding(PositionalBinding = $false)]
param(
    [switch]$Apply,
    [string[]]$ScanDrives = @('C', 'E'),
    [int]$TopN = 20,
    [int]$TempOlderThanDays = 7,
    [switch]$SkipLargeFileScan,
    [switch]$Aggressive,
    [ValidateSet('Reduced', 'Off', 'None')]
    [string]$HibernateMode = 'Reduced',
    [switch]$Yes,
    [switch]$Diagnostics,
    [switch]$DiagnosticsOnly,
    [int]$EventDays = 120,
    [string]$DiagnosticsOutDir,

    [Alias('h')]
    [switch]$Help,
    [switch]$Usage,

    # Catches anything that did not bind to a parameter above. Two jobs: accept the
    # GNU-style forms PowerShell itself cannot declare (--help, /?), and refuse a
    # typo'd argument loudly instead of silently ignoring it on a run that DELETES files.
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$UnboundArgs
)

$ErrorActionPreference = 'Continue'

# ------------------------------------------------------------------- usage ----

function Show-Usage {
    $me = if ($PSCommandPath) { Split-Path -Leaf $PSCommandPath } else { 'pc-cleanup.ps1' }

    # Deliberately NOT named W / H / A: single letters collide with built-in aliases
    # (H is Get-History), and aliases outrank functions in PowerShell name resolution.
    function W { param([string]$T = '', [string]$C = 'Gray') Write-Host $T -ForegroundColor $C }
    function UsageHead { param([string]$T) Write-Host ''; Write-Host $T -ForegroundColor Yellow }
    # Argument name, then its wrapped explanation. Kept as one helper so every entry
    # lines up in the same column no matter how long the explanation is.
    function UsageArg {
        param([string]$Name, [string]$Default, [string[]]$Lines)
        Write-Host ''
        Write-Host ("  {0}" -f $Name) -NoNewline -ForegroundColor White
        if ($Default) { Write-Host ("   [default: {0}]" -f $Default) -ForegroundColor DarkGray }
        else { Write-Host '' }
        foreach ($l in $Lines) { Write-Host ("      {0}" -f $l) -ForegroundColor Gray }
    }

    W ('=' * 78) 'DarkCyan'
    W "  $me  --  disk cleanup + hardware health panel" 'Cyan'
    W ('=' * 78) 'DarkCyan'
    W ''
    W '  Two independent jobs in one script:' 'White'
    W '    CLEANUP     (sections 1-5) reclaims disk space. Report-only unless -Apply.'
    W '    DIAGNOSTICS (section 6)     reads drive/battery/thermal/shutdown health.'
    W '                                ALWAYS read-only. Never changes anything.'

    UsageHead 'USAGE'
    W "  pwsh -File .\$me [options]"
    W ''
    W '  With NO options it reports what it would clean and changes nothing.' 'Green'
    W '  That is the safe way to start.' 'Green'

    UsageHead 'SAFETY MODEL  (read this before using -Apply)'
    W '  Three escalating tiers. You have to opt in to each one:'
    W ''
    W '    1. default        Read-only. Prints findings and sizes. Touches nothing.'
    W '    2. -Apply         Deletes temp files/caches, tunes services. Reversible.'
    W '    3. -Aggressive    Adds hibernation resizing, Disk Cleanup handlers, and the
                      orphaned search index.'
    W '                      Requires -Apply AND Administrator AND a per-action prompt.'
    W ''
    W '  Aggressive actions fail CLOSED: if the script cannot prompt you and -Yes was' 'DarkYellow'
    W '  not given, it does nothing rather than guessing.' 'DarkYellow'
    W '  The Recycle Bin is NEVER emptied. Personal files are NEVER deleted.' 'DarkYellow'

    UsageHead 'CLEANUP ARGUMENTS'

    UsageArg '-Apply' 'off' @(
        'Actually perform the cleanup. Without this every destructive step prints'
        '"[WOULD DO]" and is skipped, so a first run can never surprise you.'
        'Covers: user + system temp, Windows Update download cache, thumbnail /'
        'icon / font caches, browser caches, and the Windows Search service.'
        'Non-elevated it still works, but Windows-wide items are reported only.'
    )

    UsageArg '-Aggressive' 'off' @(
        'Unlock the three large reclaims. Requires -Apply and Administrator.'
        '  * hibernation resizing  (see -HibernateMode)'
        '  * cleanmgr /sagerun     (Previous Installations, Setup Logs,'
        '                           Update Cleanup, Temporary Setup Files)'
        '  * Windows.edb           the search index, deleted ONLY when WSearch'
        '                          is already Disabled -- often the biggest'
        '                          single reclaim on a machine with search off'
        'Each one prompts separately unless -Yes. If a STAGED WINDOWS UPGRADE is'
        'detected the script warns in red before touching Previous Installations.'
    )

    UsageArg '-Yes' 'off' @(
        'Auto-confirm every -Aggressive prompt. Use only for unattended runs where'
        'you already know exactly what you are authorising. Ignored without'
        '-Aggressive, so it cannot make a plain -Apply run more destructive.'
    )

    UsageArg '-HibernateMode' 'Reduced' @(
        'What to do with hiberfil.sys when -Aggressive is on.'
        ''
        '  Reduced   Shrink to roughly half size. KEEPS Fast Startup working.'
        '            Recommended. This is the default for a reason.'
        '  Off       Delete hiberfil.sys entirely. Reclaims the most space but'
        '            SILENTLY DISABLES FAST STARTUP -- every boot becomes a cold'
        '            boot, which on a 5400 RPM HDD is a painful trade.'
        '  None      Do not touch hibernation at all.'
    )

    UsageArg '-TempOlderThanDays' '7' @(
        'Age floor for deletion. A file is only removed if its last-write time is'
        'older than this many days. Protects anything an application is actively'
        'using. Set to 0 to delete regardless of age (not recommended).'
    )

    UsageArg '-ScanDrives' 'C, E' @(
        'Which drives to inspect, comma-separated and letter-only: -ScanDrives C,D,E'
        'Used by the large-file scan (section 5) and the filesystem checks (6.3).'
        'A drive that does not exist is skipped silently.'
    )

    UsageArg '-TopN' '20' @(
        'How many entries the largest-files and largest-folders lists print.'
    )

    UsageArg '-SkipLargeFileScan' 'off' @(
        'Skip section 5. That scan walks every file on -ScanDrives, which on a'
        'mechanical disk can take several minutes. Skip it when you only want the'
        'cleanup or the health panel. Implied by -DiagnosticsOnly.'
    )

    UsageHead 'DIAGNOSTICS ARGUMENTS  (section 6 -- always read-only)'

    UsageArg '-Diagnostics' 'off' @(
        'Run the health panel after the cleanup sections. NOT affected by -Apply:'
        'it only reads. Sub-checks, and what each one answers:'
        ''
        '  6.1  Reliability counters   Is the drive erroring, and how long do its'
        '                              slowest operations actually take?'
        '  6.2  SMART predict-fail     Does the drive think it is dying?'
        '  6.3  Filesystem             chkdsk pending? File vs FREE-SPACE'
        '                              fragmentation (they are different problems).'
        '  6.4  Battery                Design vs full-charge capacity -> health %.'
        '  6.5  Shutdowns              Kernel-Power 41 decoded into hangs vs BSODs'
        '                              vs instant power loss, plus WHEA and dumps.'
        '  6.6  Thermals               ACPI zone temperatures, if firmware exposes them.'
        '  6.7  Power state            Hibernate / Fast Startup / Standby availability.'
        ''
        'Several checks need Administrator. Un-elevated they say so and are skipped;'
        'nothing errors out.'
    )

    UsageArg '-DiagnosticsOnly' 'off' @(
        'Run ONLY the health panel, then exit. Implies -Diagnostics and forces'
        '-Apply and -Aggressive off, so it cannot modify anything under any'
        'combination of flags. This is the periodic-checkup mode.'
    )

    UsageArg '-EventDays' '120' @(
        'Lookback window, in days, for the shutdown and hardware-error scan (6.5).'
        'The default is deliberately wide: the original investigation used 60 days'
        'and UNDERCOUNTED the unexpected shutdowns five-fold. Widen further with'
        '-EventDays 365 if the System log goes back that far.'
    )

    UsageArg '-DiagnosticsOutDir' '(this script folder)' @(
        'Where the generated battery-report.html is written. powercfg defaults to'
        'the current directory, which dumps it into System32 on an elevated prompt.'
    )

    UsageHead 'GENERAL'

    UsageArg '-Help, -h, --help, /?' '' @(
        'Show this text and exit. Nothing else runs.'
    )

    UsageArg '-Usage, --usage' '' @(
        'Identical to -Help.'
    )

    UsageArg '-Verbose' '' @(
        'Standard PowerShell switch. Adds per-item detail to the cleanup passes.'
    )

    UsageHead 'EXAMPLES'
    W ''
    W '  # Look first. Changes nothing. Start here.' 'DarkGray'
    W "  pwsh -File .\$me" 'White'
    W ''
    W '  # Same, but skip the slow whole-disk walk.' 'DarkGray'
    W "  pwsh -File .\$me -SkipLargeFileScan" 'White'
    W ''
    W '  # Health panel only. Run this ELEVATED for the complete picture.' 'DarkGray'
    W "  pwsh -File .\$me -DiagnosticsOnly" 'White'
    W ''
    W '  # Apply the safe cleanup.' 'DarkGray'
    W "  pwsh -File .\$me -Apply" 'White'
    W ''
    W '  # Cleanup plus health panel, a full year of shutdown history.' 'DarkGray'
    W "  pwsh -File .\$me -Apply -Diagnostics -EventDays 365" 'White'
    W ''
    W '  # Everything, ELEVATED, prompting before each big reclaim.' 'DarkGray'
    W "  pwsh -File .\$me -Apply -Aggressive" 'White'
    W ''
    W '  # Unattended, keeping Fast Startup.' 'DarkGray'
    W "  pwsh -File .\$me -Apply -Aggressive -Yes -HibernateMode Reduced" 'White'

    UsageHead 'NOTES'
    W '  * To elevate: right-click PowerShell -> Run as administrator, then cd here.'
    W "  * No PowerShell 7? Use: powershell -ExecutionPolicy Bypass -File .\$me"
    W '  * Exit codes:  0 = ran   2 = bad arguments'
    W '  * Full write-up, findings and hardware recommendations: report.md'
    W ''
}

# Dispatch help BEFORE any work. --help and /? cannot be declared as PowerShell
# parameters, so they arrive via $UnboundArgs and are matched here.
$helpForms = '^(--?help|--?usage|-h|/h|/\?|\?|help|usage)$'
$askedForHelp = $Help -or $Usage -or ($UnboundArgs | Where-Object { $_ -match $helpForms })

if ($askedForHelp) { Show-Usage; exit 0 }

# Anything left unbound is a typo. Refuse rather than proceed -- this script deletes files.
if ($UnboundArgs) {
    Write-Host ''
    Write-Host "ERROR: unrecognised argument(s): $($UnboundArgs -join ' ')" -ForegroundColor Red
    Write-Host "Run '.\$(Split-Path -Leaf $PSCommandPath) -Help' for the full argument list." -ForegroundColor Yellow
    Write-Host ''
    exit 2
}

# -DiagnosticsOnly is a shorthand: turn the panel on, turn everything else off.
if ($DiagnosticsOnly) {
    $Diagnostics = $true
    $Apply = $false
    $Aggressive = $false
    $SkipLargeFileScan = $true
}

if (-not $DiagnosticsOutDir) {
    $DiagnosticsOutDir = if ($PSScriptRoot) { $PSScriptRoot } else { (Get-Location).Path }
}

# ---------------------------------------------------------------- helpers ----

$script:IsAdmin = ([Security.Principal.WindowsPrincipal] `
        [Security.Principal.WindowsIdentity]::GetCurrent()
).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)

function Write-Head {
    param([string]$Text)
    Write-Host ''
    Write-Host ('=' * 78) -ForegroundColor DarkCyan
    Write-Host "  $Text" -ForegroundColor Cyan
    Write-Host ('=' * 78) -ForegroundColor DarkCyan
}

function Write-Sub {
    param([string]$Text)
    Write-Host ''
    Write-Host "-- $Text" -ForegroundColor Yellow
}

function Write-Act {
    param([string]$Text, [switch]$Done, [switch]$Skipped)
    if ($Done) { Write-Host "   [DONE]    $Text" -ForegroundColor Green }
    elseif ($Skipped) { Write-Host "   [SKIP]    $Text" -ForegroundColor DarkGray }
    else { Write-Host "   [WOULD DO] $Text" -ForegroundColor Magenta }
}

function Format-Size {
    param([double]$Bytes)
    if ($Bytes -ge 1GB) { return ('{0,8:N2} GB' -f ($Bytes / 1GB)) }
    if ($Bytes -ge 1MB) { return ('{0,8:N1} MB' -f ($Bytes / 1MB)) }
    return ('{0,8:N0} KB' -f ($Bytes / 1KB))
}

# Sum sizes under a path without throwing on access-denied / long paths.
function Get-PathSize {
    param([string]$Path, [datetime]$OlderThan = [datetime]::MaxValue)
    $bytes = 0L; $count = 0
    if (-not (Test-Path -LiteralPath $Path)) { return [pscustomobject]@{ Bytes = 0; Count = 0 } }
    Get-ChildItem -LiteralPath $Path -Recurse -File -Force -ErrorAction SilentlyContinue |
        Where-Object { $_.LastWriteTime -lt $OlderThan } |
        ForEach-Object { $bytes += $_.Length; $count++ }
    [pscustomobject]@{ Bytes = $bytes; Count = $count }
}

# Delete files under a path older than a cutoff. Returns bytes freed.
# Uses .NET Delete() so a locked file is skipped rather than aborting the run.
function Remove-StaleFiles {
    param([string]$Path, [datetime]$OlderThan)
    $freed = 0L; $deleted = 0; $locked = 0
    if (-not (Test-Path -LiteralPath $Path)) { return [pscustomobject]@{ Bytes = 0; Deleted = 0; Locked = 0 } }

    Get-ChildItem -LiteralPath $Path -Recurse -File -Force -ErrorAction SilentlyContinue |
        Where-Object { $_.LastWriteTime -lt $OlderThan } |
        ForEach-Object {
            $len = $_.Length
            try {
                [IO.File]::SetAttributes($_.FullName, [IO.FileAttributes]::Normal)
                [IO.File]::Delete($_.FullName)
                $freed += $len; $deleted++
            } catch { $locked++ }
        }

    # Second pass: drop directories that are now empty.
    Get-ChildItem -LiteralPath $Path -Recurse -Directory -Force -ErrorAction SilentlyContinue |
        Sort-Object { $_.FullName.Length } -Descending |
        ForEach-Object {
            try {
                if (-not (Get-ChildItem -LiteralPath $_.FullName -Force -ErrorAction SilentlyContinue)) {
                    [IO.Directory]::Delete($_.FullName, $false)
                }
            } catch { }
        }

    [pscustomobject]@{ Bytes = $freed; Deleted = $deleted; Locked = $locked }
}

# Gate for -Aggressive actions. Returns $true only if the action should proceed.
# Fails CLOSED: if we cannot prompt and -Yes was not given, we do nothing.
function Confirm-Aggressive {
    param([string]$Title, [string[]]$Consequences)

    Write-Host ''
    Write-Host "   >>> $Title" -ForegroundColor Yellow
    foreach ($c in $Consequences) { Write-Host "       - $c" -ForegroundColor DarkYellow }

    if ($Yes) {
        Write-Host '       (auto-confirmed by -Yes)' -ForegroundColor DarkGray
        return $true
    }

    # $Host.UI.RawUI is unavailable in non-interactive hosts; Read-Host would
    # return empty forever, so refuse rather than guess.
    if ([Environment]::UserInteractive -eq $false) {
        Write-Act "$Title -- non-interactive session, pass -Yes to allow." -Skipped
        return $false
    }

    try {
        $answer = Read-Host '       Proceed? [y/N]'
    } catch {
        Write-Act "$Title -- cannot prompt here, pass -Yes to allow." -Skipped
        return $false
    }

    if ($answer -match '^\s*y(es)?\s*$') { return $true }
    Write-Act "$Title -- declined." -Skipped
    return $false
}

function Get-FreeSpaceSnapshot {
    Get-Volume | Where-Object { $_.DriveLetter -and $_.FileSystem } | ForEach-Object {
        [pscustomobject]@{
            Drive   = $_.DriveLetter
            FS      = $_.FileSystem
            SizeGB  = [math]::Round($_.Size / 1GB, 1)
            FreeGB  = [math]::Round($_.SizeRemaining / 1GB, 1)
            PctFree = if ($_.Size) { [math]::Round(100 * $_.SizeRemaining / $_.Size, 1) } else { 0 }
        }
    }
}

# ------------------------------------------------- diagnostics / health panel --

# PowerShell 7 REMOVED Get-WmiObject. Get-CimInstance is the supported replacement and
# behaves identically for the root/wmi storage + ACPI classes, so the panel works on
# both Windows PowerShell 5.1 and pwsh 7 without branching.
function Get-RootWmiClass {
    param([string]$ClassName)
    try { return @(Get-CimInstance -Namespace 'root/wmi' -ClassName $ClassName -ErrorAction Stop) }
    catch { return $null }
}

function Write-Finding {
    param([string]$Text, [ValidateSet('Good', 'Warn', 'Bad', 'Info')][string]$Level = 'Info')
    $c = switch ($Level) { 'Good' { 'Green' } 'Warn' { 'Yellow' } 'Bad' { 'Red' } default { 'Gray' } }
    $t = switch ($Level) { 'Good' { 'OK  ' } 'Warn' { 'WARN' } 'Bad' { 'BAD ' } default { '    ' } }
    Write-Host "   [$t] $Text" -ForegroundColor $c
}

function Write-NeedsAdmin {
    param([string]$What)
    Write-Host "   $What -- needs Administrator; re-run elevated." -ForegroundColor DarkYellow
}

# SMART attribute IDs.
#   ZeroIsGood marks the attributes where a non-zero RAW count is itself the warning,
#   regardless of how healthy the normalised value still looks -- these are the ones
#   that actually correlate with drive death.
#   WearLimit is the manufacturer's RATED design life for a mechanical-cycle counter.
#   These attributes are not errors at all: they count normal wear, and the number only
#   means something against the rating. A drive at 99% of its rated head-park life is
#   worn out even though every error counter reads zero, and nothing else in the panel
#   would tell you. Figures are 2.5" laptop-drive class ratings.
$script:SmartAttrs = @{
    1   = @{ Name = 'Raw Read Error Rate'; ZeroIsGood = $false }
    2   = @{ Name = 'Throughput Performance'; ZeroIsGood = $false }
    3   = @{ Name = 'Spin-Up Time'; ZeroIsGood = $false }
    4   = @{ Name = 'Start/Stop Count'; ZeroIsGood = $false; WearLimit = 50000 }
    5   = @{ Name = 'Reallocated Sectors'; ZeroIsGood = $true }
    7   = @{ Name = 'Seek Error Rate'; ZeroIsGood = $false }
    8   = @{ Name = 'Seek Time Performance'; ZeroIsGood = $false }
    9   = @{ Name = 'Power-On Hours'; ZeroIsGood = $false }
    10  = @{ Name = 'Spin Retry Count'; ZeroIsGood = $true }
    12  = @{ Name = 'Power Cycle Count'; ZeroIsGood = $false; WearLimit = 50000 }
    184 = @{ Name = 'End-to-End Error'; ZeroIsGood = $true }
    187 = @{ Name = 'Reported Uncorrectable'; ZeroIsGood = $true }
    188 = @{ Name = 'Command Timeout'; ZeroIsGood = $true }
    189 = @{ Name = 'High Fly Writes'; ZeroIsGood = $false }
    190 = @{ Name = 'Airflow Temperature'; ZeroIsGood = $false }
    191 = @{ Name = 'G-Sense Error Rate'; ZeroIsGood = $false }
    192 = @{ Name = 'Emergency Unload Count'; ZeroIsGood = $false; WearLimit = 20000 }
    193 = @{ Name = 'Load/Unload Cycle Count'; ZeroIsGood = $false; WearLimit = 600000 }
    194 = @{ Name = 'Temperature'; ZeroIsGood = $false }
    196 = @{ Name = 'Reallocation Event Count'; ZeroIsGood = $true }
    197 = @{ Name = 'Current Pending Sectors'; ZeroIsGood = $true }
    198 = @{ Name = 'Offline Uncorrectable'; ZeroIsGood = $true }
    199 = @{ Name = 'UDMA CRC Error Count'; ZeroIsGood = $true }
    200 = @{ Name = 'Multi-Zone Error Rate'; ZeroIsGood = $false }
    201 = @{ Name = 'Soft Read Error Rate'; ZeroIsGood = $true }
    223 = @{ Name = 'Load Retry Count'; ZeroIsGood = $false }
    225 = @{ Name = 'Load/Unload Cycle Count'; ZeroIsGood = $false; WearLimit = 600000 }
    240 = @{ Name = 'Head Flying Hours'; ZeroIsGood = $false }
    241 = @{ Name = 'Total LBAs Written'; ZeroIsGood = $false }
    242 = @{ Name = 'Total LBAs Read'; ZeroIsGood = $false }
}

function Invoke-HealthPanel {

    Write-Head '6. DIAGNOSTICS  (read-only health panel -- nothing is changed)'

    $since = (Get-Date).AddDays(-$EventDays)
    Write-Host "   Event lookback: $EventDays days (since $($since.ToString('yyyy-MM-dd')))" -ForegroundColor DarkGray

    # -------------------------------------------------- 6.1 reliability counters --
    Write-Sub '6.1  Drive reliability counters & latency maxima'

    $anyCounter = $false
    foreach ($pd in @(Get-PhysicalDisk -ErrorAction SilentlyContinue)) {
        $rc = $pd | Get-StorageReliabilityCounter -ErrorAction SilentlyContinue
        if (-not $rc) { continue }
        $anyCounter = $true

        Write-Host ''
        Write-Host "   Disk $($pd.DeviceId): $($pd.FriendlyName)  [$($pd.MediaType), $($pd.BusType)]" -ForegroundColor White

        if ($null -ne $rc.PowerOnHours) {
            $yrs = [math]::Round($rc.PowerOnHours / 8760, 2)
            $lvl = if ($rc.PowerOnHours -gt 45000) { 'Bad' } elseif ($rc.PowerOnHours -gt 30000) { 'Warn' } else { 'Good' }
            Write-Finding ("PowerOnHours   {0,8}  (~{1} yrs actually spinning)" -f $rc.PowerOnHours, $yrs) $lvl
        }

        # Read-error fields returning a real 0 is positive evidence. Fields returning
        # $null are simply NOT REPORTED by the driver -- never read those as "zero".
        foreach ($f in 'ReadErrorsTotal', 'ReadErrorsUncorrected', 'ReadErrorsCorrected',
                       'WriteErrorsTotal', 'WriteErrorsUncorrected', 'WriteErrorsCorrected') {
            $v = $rc.$f
            if ($null -eq $v) { Write-Finding ("{0,-22} not reported by this driver" -f $f) 'Info' }
            elseif ($v -eq 0) { Write-Finding ("{0,-22} 0" -f $f) 'Good' }
            else { Write-Finding ("{0,-22} {1}" -f $f, $v) 'Bad' }
        }

        if ($null -ne $rc.StartStopCycleCount) {
            Write-Finding ("StartStopCycleCount    {0}   (typical rating ~50,000)" -f $rc.StartStopCycleCount) 'Info'
        }
        if ($null -ne $rc.LoadUnloadCycleCount) {
            Write-Finding ("LoadUnloadCycleCount   {0}   (typical rating ~600,000)" -f $rc.LoadUnloadCycleCount) 'Info'
            # Kept so 6.2 can cross-check it against SMART attribute 193, which reads the
            # drive's own lifetime log rather than what this driver has seen since boot.
            $script:LoadUnloadFromDriver = [int64]$rc.LoadUnloadCycleCount
        }

        # These are milliseconds. Anything in the seconds range is a stall, and with
        # clean read-error counters the stall is in the STORAGE STACK, not the media
        # (dying removable device retrying, or paging storm queue depth).
        foreach ($pair in @(@('ReadLatencyMax', $rc.ReadLatencyMax),
                            @('WriteLatencyMax', $rc.WriteLatencyMax),
                            @('FlushLatencyMax', $rc.FlushLatencyMax))) {
            $name, $ms = $pair
            if ($null -eq $ms) { continue }
            $sec = [math]::Round($ms / 1000, 1)
            $lvl = if ($ms -ge 5000) { 'Bad' } elseif ($ms -ge 1000) { 'Warn' } else { 'Good' }
            Write-Finding ("{0,-18} {1,7} ms  ({2}s)" -f $name, $ms, $sec) $lvl
        }

        if ($rc.Temperature -gt 0) {
            Write-Finding ("Temperature            {0} C  (max {1} C)" -f $rc.Temperature, $rc.TemperatureMax) 'Info'
        } else {
            Write-Finding 'Temperature            not reported (0 means UNSUPPORTED, not cold)' 'Info'
        }
    }
    if (-not $anyCounter) {
        if ($script:IsAdmin) { Write-Host '   No reliability counters exposed by any disk.' -ForegroundColor DarkGray }
        else { Write-NeedsAdmin 'Reliability counters' }
    }

    # ------------------------------------------------------------ 6.2 true SMART --
    Write-Sub '6.2  SMART failure prediction'

    $smart = Get-RootWmiClass 'MSStorageDriver_FailurePredictStatus'
    if (-not $smart) {
        if (-not $script:IsAdmin) { Write-NeedsAdmin 'SMART predict-fail' }
        else {
            Write-Host '   This drive does not expose SMART through the Windows driver' -ForegroundColor DarkYellow
            Write-Host '   (common on older HP/Insyde machines). Use CrystalDiskInfo'    -ForegroundColor DarkYellow
            Write-Host '   (free, portable) to read the real attribute table.'           -ForegroundColor DarkYellow
        }
    } else {
        foreach ($s in $smart) {
            if ($s.PredictFailure) { Write-Finding "$($s.InstanceName): PredictFailure=TRUE  Reason=$($s.Reason)  ** BACK UP NOW **" 'Bad' }
            else { Write-Finding "$($s.InstanceName): PredictFailure=False" 'Good' }
        }

        # PredictFailure is a single pass/fail bit and it only trips once a value has
        # already crossed its threshold -- by then the drive is failing, not "about to".
        # The attribute TABLE shows drift long before that, so decode it.
        $sdata = Get-RootWmiClass 'MSStorageDriver_FailurePredictData'
        $sthr = Get-RootWmiClass 'MSStorageDriver_FailurePredictThresholds'

        foreach ($d in @($sdata)) {
            $bytes = $d.VendorSpecific
            if (-not $bytes -or $bytes.Count -lt 362) { continue }

            # Thresholds live in a parallel structure keyed the same way: 2-byte revision,
            # then 30 records of 12 bytes. Data record = ID, flags(2), value, worst, raw(6), rsvd.
            # Threshold record = ID, threshold, 10 reserved.
            $thrMap = @{}
            $t = @($sthr | Where-Object { $_.InstanceName -eq $d.InstanceName } | Select-Object -First 1)
            if ($t -and $t[0].VendorSpecific) {
                $tb = $t[0].VendorSpecific
                for ($i = 0; $i -lt 30; $i++) {
                    $o = 2 + ($i * 12)
                    if ($o + 1 -ge $tb.Count) { break }
                    if ($tb[$o] -ne 0) { $thrMap[[int]$tb[$o]] = [int]$tb[$o + 1] }
                }
            }

            Write-Host ''
            Write-Host "   SMART attribute table -- $($d.InstanceName)" -ForegroundColor White
            Write-Host '   ID  Attribute                       Cur Wst Thr  Raw' -ForegroundColor DarkGray

            $anyCritical = $false
            $smartRaw = @{}      # id -> raw, for the narrative after the table
            $wornOut = @()       # human-readable "at N% of rated life" lines
            $breached = @()      # attributes whose worst-ever value went past threshold
            for ($i = 0; $i -lt 30; $i++) {
                $o = 2 + ($i * 12)
                if ($o + 11 -ge $bytes.Count) { break }
                $id = [int]$bytes[$o]
                if ($id -eq 0) { continue }

                $cur = [int]$bytes[$o + 3]
                $wst = [int]$bytes[$o + 4]
                # Raw is 6 bytes, little-endian.
                $raw = 0L
                for ($b = 10; $b -ge 5; $b--) { $raw = ($raw * 256) + [int]$bytes[$o + $b] }

                $meta = $script:SmartAttrs[$id]
                $name = if ($meta) { $meta.Name } else { "(vendor attribute $id)" }
                $thr = if ($thrMap.ContainsKey($id)) { $thrMap[$id] } else { $null }

                # The top 2 of the 6 raw bytes being set means the vendor is packing extra
                # fields in there, NOT that the counter reached 2^32. Observed on this HGST:
                # attr 187 decodes to 2.0e14, which is bytes, not a count of errors. Treat
                # such an attribute as unreadable rather than pretending the number means
                # something -- and never let it fire the zero-is-good alarm below.
                $packed = ([int]$bytes[$o + 9] -ne 0 -or [int]$bytes[$o + 10] -ne 0)
                $low32 = $raw -band 0xFFFFFFFFL

                # Mechanical-cycle counters mean nothing as a bare number -- express them
                # as a percentage of the manufacturer's rating so "599407" reads as what
                # it actually is: a drive at the end of its rated head-park life.
                $wearPct = $null
                $wearBogus = $false
                if ($meta -and $meta.WearLimit -and -not $packed -and $raw -gt 0) {
                    # A cycle count an order of magnitude past its rating is not wear, it is
                    # a vendor packing data into a field this decoder cannot interpret. Say
                    # so rather than raising a false end-of-life alarm (HGST attr 192 does
                    # exactly this: ~2e7 "emergency unloads" against a 2e4 rating).
                    if ($raw -gt ($meta.WearLimit * 10)) { $wearBogus = $true }
                    else { $wearPct = [math]::Round(100 * $raw / $meta.WearLimit, 1) }
                }

                $rawTxt = if ($id -in 190, 194) {
                    # Temperature attributes pack current/min/max; the low byte is current C.
                    "$($raw -band 0xFF) C"
                } elseif ($packed) {
                    "$low32  (vendor-packed, upper bytes not a count)"
                } elseif ($null -ne $wearPct) {
                    "$raw  ({0}% of ~{1} rated)" -f $wearPct, $meta.WearLimit
                } elseif ($wearBogus) {
                    "$raw  (implausible vs ~$($meta.WearLimit) rating -- not a plain count)"
                } else {
                    "$raw"
                }

                # Three independent alarms: normalised value at/below threshold (the drive's
                # own verdict), a non-zero raw count on an attribute where ANY count is bad
                # news (reallocations, pending sectors, uncorrectables), and mechanical wear
                # approaching the rated cycle life.
                $belowThr = ($null -ne $thr -and $thr -gt 0 -and $cur -le $thr)
                # Wst is the worst value ever recorded. Wst <= Thr with a healthy Cur means
                # the drive DID breach its own limit at some point and then recovered -- a
                # past excursion that leaves no other trace. Worth surfacing: on attribute
                # 190 it is a historical over-temperature event.
                $everBreached = ($null -ne $thr -and $thr -gt 0 -and $wst -le $thr -and -not $belowThr)
                $rawAlarm = ($meta -and $meta.ZeroIsGood -and $raw -gt 0 -and -not $packed)
                $wearAlarm = ($null -ne $wearPct -and $wearPct -ge 75)

                # A packed attribute gets no verdict either way -- neither OK nor WARN.
                $lvl = if ($belowThr -or ($null -ne $wearPct -and $wearPct -ge 90)) { 'Bad' }
                elseif ($rawAlarm -or $wearAlarm -or $everBreached) { 'Warn' }
                elseif ($meta -and $meta.ZeroIsGood -and -not $packed) { 'Good' }
                else { 'Info' }
                if ($belowThr -or $rawAlarm -or $wearAlarm) { $anyCritical = $true }

                # Stash the raws the narrative below needs, so it does not re-decode.
                if (-not $packed) { $smartRaw[$id] = $raw }
                if ($everBreached) { $breached += ('{0} ({1}): worst-ever {2} vs threshold {3}' -f $id, $name, $wst, $thr) }
                if ($wearAlarm) { $wornOut += ('{0} ({1}) at {2}% of rated life' -f $id, $name, $wearPct) }

                $line = '{0,4}  {1,-30} {2,3} {3,3} {4,3}  {5}' -f `
                    $id, $name, $cur, $wst, $(if ($null -ne $thr) { $thr } else { '--' }), $rawTxt
                Write-Finding $line $lvl
            }

            if ($thrMap.Count -eq 0) {
                Write-Host '          Thr column is blank: the threshold table was not returned (usually' -ForegroundColor DarkGray
                Write-Host '          needs Administrator). Cur/Wst/Raw above are still authoritative.'   -ForegroundColor DarkGray
            }

            # A recovered breach leaves no error count behind, so this is the only place
            # a past excursion shows up at all. On attribute 190 it is specifically a
            # historical over-temperature -- which matters when unexplained power-offs
            # (6.5) are on the table, because it is independent evidence of overheating.
            if ($breached.Count -gt 0) {
                Write-Host ''
                Write-Host '          PAST THRESHOLD BREACH (recovered -- current values are fine):' -ForegroundColor DarkYellow
                foreach ($b in $breached) { Write-Host "            - $b" -ForegroundColor DarkYellow }
                Write-Host '          The drive went outside its own limit at some point and came back.' -ForegroundColor DarkYellow
                if ($breached -match '^190 ') {
                    Write-Host '          Attribute 190 is airflow temperature: this drive HAS overheated'  -ForegroundColor DarkYellow
                    Write-Host '          in the past. Cross-reference 6.5 -- if there are unlogged power'  -ForegroundColor DarkYellow
                    Write-Host '          losses, that is now two independent pointers at cooling.'        -ForegroundColor DarkYellow
                }
            }

            # Mechanical wear is a different failure mode from bad sectors, and the two
            # are routinely confused. Spell it out: zero errors + exhausted cycle life
            # means "replace it because it is worn", not "it is fine".
            if ($wornOut.Count -gt 0) {
                Write-Host ''
                Write-Host '          MECHANICAL WEAR (not a media fault):' -ForegroundColor Yellow
                foreach ($w in $wornOut) { Write-Host "            - $w" -ForegroundColor Yellow }
                Write-Host '          These count normal motion, not errors, so they never trip the' -ForegroundColor Yellow
                Write-Host '          drive PredictFailure flag -- a drive can report perfect health'  -ForegroundColor Yellow
                Write-Host '          right up to the point the actuator stops parking reliably.'      -ForegroundColor Yellow
                Write-Host '          Each head park/unpark also STALLS I/O while the heads reload,'   -ForegroundColor Yellow
                Write-Host '          which is a direct contributor to the latency maxima in 6.1.'     -ForegroundColor Yellow
            }

            # G-sense counts physical shocks the drive detected. On a laptop that is the
            # machine being moved, bumped or vibrated WHILE the platters are spinning --
            # each event can force an emergency head unload, and every unload is a stall.
            if ($smartRaw.ContainsKey(191) -and $smartRaw[191] -gt 1000) {
                Write-Host ''
                Write-Host ("          SHOCK EVENTS: attribute 191 counts {0} detected physical shocks." -f $smartRaw[191]) -ForegroundColor DarkYellow
                Write-Host '          That is the machine being moved or knocked while the disk spins.'  -ForegroundColor DarkYellow
                Write-Host '          Each one can force an emergency head unload -- a multi-second I/O'  -ForegroundColor DarkYellow
                Write-Host '          stall, and cumulative mechanical wear. Until the disk is replaced:' -ForegroundColor DarkYellow
                Write-Host '          keep the machine on a flat surface and do not move it while it is' -ForegroundColor DarkYellow
                Write-Host '          working. An SSD makes this failure mode disappear entirely.'       -ForegroundColor DarkYellow
            }

            # The driver counter and SMART count the same physical event and frequently
            # disagree by orders of magnitude. SMART is read from the drive's own log and
            # is the one to trust; flag the mismatch so the 6.1 number is not believed.
            if ($smartRaw.ContainsKey(193) -and $script:LoadUnloadFromDriver -gt 0) {
                $ratio = $smartRaw[193] / [double]$script:LoadUnloadFromDriver
                if ($ratio -gt 2 -or $ratio -lt 0.5) {
                    Write-Host ''
                    Write-Host ("          NOTE: 6.1 reported LoadUnloadCycleCount = {0}, but the drive's own" -f $script:LoadUnloadFromDriver) -ForegroundColor DarkGray
                    Write-Host ("          SMART log says {0}. SMART is authoritative here -- the storage" -f $smartRaw[193]) -ForegroundColor DarkGray
                    Write-Host '          driver counter only covers what it has observed since it loaded.' -ForegroundColor DarkGray
                }
            }

            # Media health and mechanical wear are separate verdicts. Reporting only the
            # worse of the two would hide the fact that the platters are fine, which is
            # what tells you a clone will succeed.
            $mediaBad = $false
            foreach ($k in 5, 10, 184, 187, 196, 197, 198, 201) {
                if ($smartRaw.ContainsKey($k) -and $smartRaw[$k] -gt 0) { $mediaBad = $true }
            }

            if (-not $mediaBad) {
                Write-Host '          -> No reallocated, pending or uncorrectable sectors. The MEDIA is' -ForegroundColor Green
                Write-Host '             sound, so a clone to a new drive will read cleanly.'            -ForegroundColor Green
            } else {
                Write-Host '          -> Sector-level faults present. Back up before doing anything else.' -ForegroundColor Yellow
            }
            if ($wornOut.Count -gt 0) {
                Write-Host '          -> But it is mechanically WORN (see above). Sound media on a worn' -ForegroundColor Yellow
                Write-Host '             actuator is exactly the profile that goes from "healthy" to'    -ForegroundColor Yellow
                Write-Host '             "will not spin up" with no warning. Replace it, do not wait.'   -ForegroundColor Yellow
            } elseif (-not $mediaBad -and -not $anyCritical) {
                Write-Host '             A drive can still be unbearably SLOW while perfectly healthy.' -ForegroundColor Green
            }
        }
    }

    # ------------------------------------------- 6.3 dirty flag + fragmentation --
    Write-Sub '6.3  Filesystem consistency & fragmentation'

    foreach ($d in $ScanDrives) {
        if (-not (Test-Path -LiteralPath "${d}:\")) { continue }

        $dirty = & fsutil.exe dirty query "${d}:" 2>&1 | Out-String
        if ($dirty -match 'is NOT Dirty') { Write-Finding "${d}: filesystem clean, no chkdsk pending" 'Good' }
        elseif ($dirty -match 'is Dirty') { Write-Finding "${d}: DIRTY -- chkdsk is pending, run it" 'Bad' }
        else { Write-NeedsAdmin "${d}: dirty-flag query" }

        if (-not $script:IsAdmin) { Write-NeedsAdmin "${d}: fragmentation analysis"; continue }

        Write-Host "   ${d}: analysing fragmentation (read-only, slow on an HDD)..." -ForegroundColor DarkGray
        $frag = & defrag.exe "${d}:" /A /V 2>&1 | Out-String

        # File fragmentation and FREE-SPACE fragmentation are different problems.
        # A volume can be perfectly defragmented yet have unusably shattered free space.
        if ($frag -match 'Average fragments per file\s*=\s*([\d.]+)') {
            $apf = [double]$Matches[1]
            $lvl = if ($apf -ge 1.5) { 'Warn' } else { 'Good' }
            Write-Finding ("${d}: average fragments per file = $apf" + $(if ($apf -lt 1.2) { '  (files are contiguous -- do NOT defrag)' } else { '' })) $lvl
        }
        if ($frag -match 'Free space count\s*=\s*([\d,]+)') { $fsCount = [int](($Matches[1]) -replace ',', '') }
        if ($frag -match 'Largest free space size\s*=\s*([\d.]+)\s*(\w+)') { $fsLargest = "$($Matches[1]) $($Matches[2])" }
        if ($fsCount) {
            $lvl = if ($fsCount -gt 20000) { 'Bad' } elseif ($fsCount -gt 5000) { 'Warn' } else { 'Good' }
            Write-Finding ("${d}: free space is in $fsCount fragments, largest contiguous run = $fsLargest") $lvl
            if ($fsCount -gt 20000) {
                Write-Host '          -> A large install (e.g. a Windows feature upgrade, ~20GB) has no' -ForegroundColor Red
                Write-Host '             contiguous room to land in. Defer it until after an SSD swap.'  -ForegroundColor Red
            }
        }
        if ($frag -match 'MFT usage\s*=\s*(\d+)%') {
            $mft = [int]$Matches[1]
            $lvl = if ($mft -ge 100) { 'Warn' } else { 'Good' }
            Write-Finding ("${d}: MFT usage = $mft%" + $(if ($mft -ge 100) { '  (outgrown its reserved zone; further growth fragments)' } else { '' })) $lvl
        }
        Remove-Variable fsCount, fsLargest -ErrorAction SilentlyContinue
    }

    # ------------------------------------------------------------- 6.4 battery --
    Write-Sub '6.4  Battery health'

    $bat = @(Get-CimInstance Win32_Battery -ErrorAction SilentlyContinue)
    if (-not $bat) {
        Write-Host '   No battery detected (desktop, or battery removed/not seen).' -ForegroundColor DarkGray
    } else {
        foreach ($b in $bat) {
            # 1=discharging 2=on AC 3=full 4=low 5=critical 6=charging 11=partially charged
            $stateName = switch ([int]$b.BatteryStatus) {
                1 { 'discharging' } 2 { 'on AC' } 3 { 'fully charged' } 4 { 'LOW' }
                5 { 'CRITICAL' } 6 { 'charging' } 11 { 'partially charged' } default { "code $($b.BatteryStatus)" }
            }
            Write-Finding "$($b.Name): $($b.Status), $stateName, $($b.EstimatedChargeRemaining)% remaining" 'Info'
        }

        $rep = Join-Path $DiagnosticsOutDir 'battery-report.html'
        # powercfg writes to the CURRENT directory by default, which lands the report in
        # System32 when run from an elevated prompt. Always give it an explicit path.
        $null = & powercfg.exe /batteryreport /output $rep 2>&1
        if (Test-Path -LiteralPath $rep) {
            $raw = Get-Content -LiteralPath $rep -Raw
            $flat = ($raw -replace '(?s)<style.*?</style>', '' -replace '(?s)<script.*?</script>', '' `
                          -replace '<[^>]+>', ' ' -replace '&nbsp;', ' ') -replace '\s+', ' '
            $design = if ($flat -match 'DESIGN CAPACITY\s*([\d,]+)\s*mWh') { [int](($Matches[1]) -replace ',', '') }
            $full = if ($flat -match 'FULL CHARGE CAPACITY\s*([\d,]+)\s*mWh') { [int](($Matches[1]) -replace ',', '') }
            if ($design -gt 0 -and $full -gt 0) {
                $health = [math]::Round(100 * $full / $design, 1)
                $lvl = if ($health -lt 50) { 'Bad' } elseif ($health -lt 70) { 'Warn' } else { 'Good' }
                Write-Finding ("Capacity {0} / {1} mWh  ->  {2}% health" -f $full, $design, $health) $lvl
                if ($health -ge 60) {
                    Write-Host '          -> A functional battery rides through AC flicker, so mains blips' -ForegroundColor DarkGray
                    Write-Host '             CANNOT explain sudden power-off events. See 6.5.'              -ForegroundColor DarkGray
                }
            }
            Write-Host "   Full report: $rep" -ForegroundColor DarkGray
        } else {
            Write-NeedsAdmin 'Battery report generation'
        }
    }

    # -------------------------------------------- 6.5 unexpected shutdowns etc. --
    Write-Sub "6.5  Unexpected shutdowns & hardware errors (last $EventDays days)"

    $k41 = @(Get-WinEvent -FilterHashtable @{
            LogName = 'System'; ProviderName = 'Microsoft-Windows-Kernel-Power'
            Id = 41; StartTime = $since
        } -ErrorAction SilentlyContinue)

    if (-not $k41) {
        Write-Finding "No Kernel-Power 41 events in $EventDays days -- no unexpected shutdowns" 'Good'
    } else {
        $decoded = $k41 | ForEach-Object {
            $x = [xml]$_.ToXml()
            $d = @{}
            foreach ($n in $x.Event.EventData.Data) { $d[$n.Name] = $n.'#text' }
            [pscustomobject]@{
                Time     = $_.TimeCreated
                Bugcheck = [string]$d['BugcheckCode']
                PowerBtn = [string]$d['PowerButtonTimestamp']
            }
        }
        # PowerButtonTimestamp != 0 means the user HELD THE POWER BUTTON -- the machine
        # had hung. That is a different failure from an instant unlogged power loss.
        $hangs = @($decoded | Where-Object { $_.PowerBtn -and $_.PowerBtn -ne '0' })
        $bsods = @($decoded | Where-Object { $_.Bugcheck -and $_.Bugcheck -ne '0' })
        $sudden = @($decoded | Where-Object { (-not $_.PowerBtn -or $_.PowerBtn -eq '0') -and ($_.Bugcheck -eq '0' -or -not $_.Bugcheck) })

        $lvl = if ($k41.Count -gt 10) { 'Bad' } elseif ($k41.Count -gt 2) { 'Warn' } else { 'Info' }
        Write-Finding ("Kernel-Power 41 total: {0}   (newest {1:yyyy-MM-dd}, oldest {2:yyyy-MM-dd})" -f `
                $k41.Count, $decoded[0].Time, $decoded[-1].Time) $lvl
        Write-Finding ("  forced by power button (machine had HUNG) : {0}" -f $hangs.Count) $(if ($hangs.Count) { 'Warn' } else { 'Good' })
        Write-Finding ("  with a bugcheck/BSOD code                 : {0}" -f $bsods.Count) $(if ($bsods.Count) { 'Warn' } else { 'Good' })
        Write-Finding ("  instant, unlogged power loss             : {0}" -f $sudden.Count) $(if ($sudden.Count) { 'Bad' } else { 'Good' })

        $quietDays = [math]::Round(((Get-Date) - $decoded[0].Time).TotalDays, 0)
        if ($quietDays -ge 7) {
            Write-Host "          -> None for $quietDays days. Whatever changed around" -ForegroundColor Green
            Write-Host "             $($decoded[0].Time.ToString('yyyy-MM-dd')) may already have fixed it." -ForegroundColor Green
        }
        if ($sudden.Count -gt 0) {
            Write-Host '          -> Instant deaths with a healthy battery and clean WHEA point at a' -ForegroundColor Yellow
            Write-Host '             board-level THERMAL TRIP. Clean the fan/heatsink and repaste.'   -ForegroundColor Yellow
        }
    }

    $whea = @(Get-WinEvent -FilterHashtable @{
            LogName = 'System'; ProviderName = 'Microsoft-Windows-WHEA-Logger'; StartTime = $since
        } -ErrorAction SilentlyContinue)
    if ($whea) {
        Write-Finding "WHEA hardware errors: $($whea.Count) -- CPU/RAM/PCIe IS faulting, investigate" 'Bad'
        $whea | Group-Object Id | ForEach-Object { Write-Host "          Event $($_.Name): $($_.Count)x" -ForegroundColor Red }
    } else {
        Write-Finding 'WHEA hardware errors: 0 -- no CPU/RAM/cache/PCIe machine checks' 'Good'
    }

    $dirtyShut = @(Get-WinEvent -FilterHashtable @{
            LogName = 'System'; ProviderName = 'EventLog'; Id = 6008; StartTime = $since
        } -ErrorAction SilentlyContinue)
    Write-Finding "Unclean-shutdown records (EventLog 6008): $($dirtyShut.Count)" $(if ($dirtyShut.Count -gt 10) { 'Bad' } elseif ($dirtyShut.Count) { 'Warn' } else { 'Good' })

    $dumps = @(Get-ChildItem 'C:\Windows\Minidump' -ErrorAction SilentlyContinue)
    $bigDump = Test-Path 'C:\Windows\MEMORY.DMP'
    if ($dumps.Count -or $bigDump) {
        Write-Finding "Crash dumps present: $($dumps.Count) minidump(s)$(if ($bigDump) { ' + MEMORY.DMP' })" 'Warn'
        $dumps | Sort-Object LastWriteTime -Descending | Select-Object -First 5 |
            ForEach-Object { Write-Host "          $($_.LastWriteTime.ToString('yyyy-MM-dd HH:mm'))  $($_.Name)" -ForegroundColor DarkYellow }
    } else {
        Write-Finding 'Crash dumps: none -- consistent with bugcheck 0 (nothing could be written)' 'Info'
    }

    # ------------------------------------------------------------ 6.6 thermals --
    Write-Sub '6.6  Thermals'

    $tz = Get-RootWmiClass 'MSAcpi_ThermalZoneTemperature'
    $liveZones = 0
    if ($tz) {
        foreach ($z in $tz) {
            $k = [int]$z.CurrentTemperature
            # A zone that reports 0 deci-Kelvin decodes to -273.2 C. That is not a reading,
            # it is an UNPOPULATED zone -- never present it as a healthily cool temperature.
            if ($k -le 0) {
                Write-Finding ("{0}: not populated (reports absolute zero -- ignore)" -f $z.InstanceName) 'Info'
                continue
            }
            $liveZones++
            $c = [math]::Round(($k - 2732) / 10, 1)
            $lvl = if ($c -ge 90) { 'Bad' } elseif ($c -ge 75) { 'Warn' } else { 'Good' }
            Write-Finding ("{0}: {1} C" -f $z.InstanceName, $c) $lvl
        }
    }
    if ($liveZones -gt 0) {
        Write-Host ''
        Write-Host '   IMPORTANT: ACPI zones are chassis/board sensors, NOT the CPU core.'    -ForegroundColor DarkYellow
        Write-Host '   A cool zone reading does NOT rule out a CPU thermal trip -- cores can' -ForegroundColor DarkYellow
        Write-Host '   hit 100 C while the zone sensor a few cm away still reads under 40 C,' -ForegroundColor DarkYellow
        Write-Host '   and these are idle readings regardless.'                               -ForegroundColor DarkYellow
        Write-Host '   To actually settle it: HWiNFO64 or Core Temp, watching CPU PACKAGE'    -ForegroundColor DarkYellow
        Write-Host '   temperature under sustained load.'                                     -ForegroundColor DarkYellow
    } elseif ($tz) {
        Write-Host ''
        Write-Host '   Every ACPI zone is unpopulated -- this firmware exposes no usable'  -ForegroundColor DarkYellow
        Write-Host '   temperature. Use HWiNFO64 or Core Temp instead.'                    -ForegroundColor DarkYellow
    } else {
        Write-Host '   ACPI thermal zones unavailable (common on Insyde firmware, and needs admin).' -ForegroundColor DarkYellow
        Write-Host '   Install HWiNFO64 or Core Temp and watch CPU package temp under load.'        -ForegroundColor DarkYellow
        Write-Host '   Sustained 90C+, or a spike toward 100C, confirms a thermal-trip cause'       -ForegroundColor DarkYellow
        Write-Host '   for the unlogged shutdowns in 6.5.'                                          -ForegroundColor DarkYellow
    }

    # ------------------------------------------------- 6.7 power / hibernation --
    Write-Sub '6.7  Power & hibernation state'

    $pa = & powercfg.exe /a 2>&1 | Out-String
    foreach ($state in 'Hibernate', 'Fast Startup', 'Hybrid Sleep', 'Standby') {
        # powercfg lists UNavailable states under a separate heading, so a plain
        # "does the word appear" test is useless -- check which section it sits in.
        $available = $false
        $inUnavailable = $false
        foreach ($line in ($pa -split "`r?`n")) {
            if ($line -match 'The following sleep states are not available') { $inUnavailable = $true; continue }
            if ($line -match 'The following sleep states are available') { $inUnavailable = $false; continue }
            if ($line -match [regex]::Escape($state)) { if (-not $inUnavailable) { $available = $true } }
        }
        Write-Finding ("{0,-14} {1}" -f $state, $(if ($available) { 'available' } else { 'NOT available' })) `
            $(if ($available) { 'Good' } else { 'Warn' })
    }

    $hib = "$env:SystemDrive\hiberfil.sys"
    try {
        $hf = Get-Item -LiteralPath $hib -Force -ErrorAction Stop
        Write-Finding ("hiberfil.sys   {0}" -f (Format-Size $hf.Length)) 'Info'
        Write-Host '          -> "powercfg /hibernate /type reduced" keeps Fast Startup at ~half the size.' -ForegroundColor DarkGray
    } catch [System.UnauthorizedAccessException] {
        # Access-denied is NOT evidence of absence -- powercfg /a above is the authority.
        Write-Finding 'hiberfil.sys   access denied (re-run elevated to read its size)' 'Info'
    } catch {
        Write-Finding 'hiberfil.sys   absent -- hibernation is off, so Fast Startup is off too' 'Info'
        Write-Host '          -> If you ran "powercfg /hibernate on" and still see this, the change' -ForegroundColor Yellow
        Write-Host '             did NOT stick. Re-run it from an ELEVATED prompt and re-check.'     -ForegroundColor Yellow
    }

    Write-Host ''
    Write-Host '   Panel complete. Nothing above changed the machine.' -ForegroundColor DarkGray
}

# ------------------------------------------------------------------ intro ----

Write-Head 'PC CLEANUP  --  safe maintenance'

Write-Host ("  Mode          : " + $(if ($Apply) { 'APPLY (changes will be made)' } else { 'REPORT ONLY (nothing will change)' })) `
    -ForegroundColor $(if ($Apply) { 'Green' } else { 'White' })
Write-Host  "  Elevated      : $script:IsAdmin"
Write-Host ("  Aggressive    : " + $(if ($Aggressive) { "ON  (hibernate=$HibernateMode, prompts=$(if($Yes){'auto-yes'}else{'interactive'}))" } else { 'off' })) `
    -ForegroundColor $(if ($Aggressive) { 'Yellow' } else { 'White' })
Write-Host  "  Temp cutoff   : files older than $TempOlderThanDays days"
Write-Host  "  Scan drives   : $($ScanDrives -join ', ')"

if (-not $script:IsAdmin) {
    Write-Host ''
    Write-Host '  NOTE: not running as Administrator. Service changes and Windows-wide' -ForegroundColor DarkYellow
    Write-Host '        caches will be reported but cannot be applied. Re-run from an'    -ForegroundColor DarkYellow
    Write-Host '        elevated PowerShell to include them.'                             -ForegroundColor DarkYellow
}

$before = Get-FreeSpaceSnapshot

Write-Sub 'Free space BEFORE'
$before | Format-Table -AutoSize | Out-String | Write-Host

# A percentage in a table is easy to skim past. NTFS picks extents out of whatever
# free space it can find, so once a volume drops under ~15% free the allocator starts
# scattering new files -- on a 5400rpm platter that scattering IS the slowness. Call
# it out explicitly rather than leaving the reader to notice the column.
$tight = $before | Where-Object { $_.PctFree -lt 15 }
if ($tight) {
    foreach ($v in $tight) {
        $lvl = if ($v.PctFree -lt 10) { 'Red' } else { 'DarkYellow' }
        Write-Host ("   LOW FREE SPACE: {0}: is {1}% free ({2} GB of {3} GB)." -f `
                $v.Drive, $v.PctFree, $v.FreeGB, $v.SizeGB) -ForegroundColor $lvl
    }
    Write-Host '   NTFS fragments new allocations badly below ~15% free, and Windows'  -ForegroundColor DarkYellow
    Write-Host '   needs headroom for the pagefile, temp files and update staging.'    -ForegroundColor DarkYellow
    Write-Host '   Nothing this script deletes lives on a data volume -- freeing these' -ForegroundColor DarkYellow
    Write-Host '   means moving or removing your own files (see section 5).'           -ForegroundColor DarkYellow
    Write-Host ''
}

# -DiagnosticsOnly short-circuits the cleanup passes entirely: run the panel and stop.
if ($DiagnosticsOnly) {
    Invoke-HealthPanel
    Write-Host ''
    Write-Host 'Diagnostics-only run finished. No cleanup was attempted.' -ForegroundColor Cyan
    Write-Host 'Run without -DiagnosticsOnly to include the cleanup sections.' -ForegroundColor DarkGray
    exit 0
}

# ------------------------------------------------- 1. removable media check --

Write-Head '1. REMOVABLE MEDIA  (the failing SD card)'

$badBlocks = @(Get-WinEvent -FilterHashtable @{
        LogName = 'System'; ProviderName = 'disk'; Id = 7; StartTime = (Get-Date).AddDays(-30)
    } -ErrorAction SilentlyContinue)

$presentDisks = @(Get-Disk -ErrorAction SilentlyContinue)

if ($badBlocks.Count) {
    Write-Host "   $($badBlocks.Count) bad-block error(s) in the last 30 days:" -ForegroundColor Red
    Write-Host ''

    # Attribute each error to a physical disk, then say whether that disk is
    # still attached -- a card that has vanished from Get-Disk has effectively
    # failed off the bus, which is worse news than the errors themselves.
    $badBlocks |
        Group-Object { ($_.Message -replace '.*\\Device\\Harddisk(\d+)\\DR\d+.*', '$1') } |
        Sort-Object Count -Descending |
        ForEach-Object {
            $diskNo = $_.Name
            $last   = ($_.Group | Sort-Object TimeCreated -Descending | Select-Object -First 1).TimeCreated
            $disk   = $presentDisks | Where-Object { $_.Number -eq [int]$diskNo }

            if ($disk) {
                $where = "STILL ATTACHED -> Disk $diskNo : $($disk.FriendlyName) [$($disk.BusType)]"
            } else {
                $where = "NO LONGER ATTACHED (Disk $diskNo has dropped off the bus)"
            }
            Write-Host ("     {0,4} error(s), last {1:yyyy-MM-dd HH:mm}" -f $_.Count, $last) -ForegroundColor Red
            Write-Host  "           $where" -ForegroundColor Red
        }

    Write-Host ''
    Write-Host '   Bad blocks cause driver-level I/O retries that BLOCK the calling' -ForegroundColor Red
    Write-Host '   thread -- this is what makes Explorer freeze for seconds.'        -ForegroundColor Red
    Write-Host '   A device that dropped off the bus is failing outright. Do not'    -ForegroundColor Red
    Write-Host '   trust it with data; copy anything you still need off it.'         -ForegroundColor Red
} else {
    Write-Host '   No bad-block events in the last 30 days.' -ForegroundColor Green
}

Write-Sub 'Physical disks currently attached'
$presentDisks | Select-Object Number, FriendlyName, BusType, HealthStatus,
@{n = 'SizeGB'; e = { [math]::Round($_.Size / 1GB, 1) } } |
    Format-Table -AutoSize | Out-String | Write-Host

# Card readers often present as DriveType 'Fixed', so DriveType alone is not a
# reliable removable test -- flag anything that is not on an internal SATA disk.
Write-Sub 'Volumes not backed by an internal SATA disk'
$internal = @($presentDisks | Where-Object { $_.BusType -eq 'SATA' } | Select-Object -ExpandProperty Number)
$suspect = Get-Partition -ErrorAction SilentlyContinue |
    Where-Object { $_.DriveLetter -and $_.DiskNumber -notin $internal }

if ($suspect) {
    $suspect | ForEach-Object {
        $v = Get-Volume -DriveLetter $_.DriveLetter -ErrorAction SilentlyContinue
        [pscustomobject]@{
            Drive  = $_.DriveLetter
            Disk   = $_.DiskNumber
            FS     = $v.FileSystem
            Type   = $v.DriveType
            SizeGB = [math]::Round($v.Size / 1GB, 1)
            FreeGB = [math]::Round($v.SizeRemaining / 1GB, 1)
        }
    } | Format-Table -AutoSize | Out-String | Write-Host
    Write-Host '   ACTION (manual, by hand): copy anything you need off these, then' -ForegroundColor Magenta
    Write-Host '   eject them. This script will NOT touch removable media.'          -ForegroundColor Magenta
} else {
    Write-Host '   None. Only internal SATA volumes are mounted -- good.' -ForegroundColor Green
}

# ------------------------------------------------------ 2. search indexing --

Write-Head '2. WINDOWS SEARCH INDEXING  [APPLY]'

Write-Host '   Why: WSearch continuously crawls the filesystem. On a 5400rpm HDD'
Write-Host '   this is a constant background seek load. Disabling it is reversible.'
Write-Host ''
Write-Host '   TRADE-OFF: Start-menu file search and Outlook search become slow /'  -ForegroundColor DarkYellow
Write-Host '   non-instant. App and setting search still work. To undo:'            -ForegroundColor DarkYellow
Write-Host '     Set-Service WSearch -StartupType Automatic; Start-Service WSearch' -ForegroundColor DarkYellow

$ws = Get-Service WSearch -ErrorAction SilentlyContinue
if (-not $ws) {
    Write-Act 'WSearch service not present -- nothing to do.' -Skipped
} else {
    Write-Host ''
    Write-Host "   Current: Status=$($ws.Status)  StartType=$($ws.StartType)"

    # ACLs on the Search data dir deny non-admin reads, so probe defensively --
    # an access-denied Test-Path throws rather than returning $false.
    $edb = 'C:\ProgramData\Microsoft\Search\Data\Applications\Windows\Windows.edb'
    $script:EdbPath = $edb
    $script:EdbBytes = 0L
    try {
        $edbItem = Get-Item -LiteralPath $edb -Force -ErrorAction Stop
        $script:EdbBytes = [int64]$edbItem.Length
        Write-Host "   Index database: $(Format-Size $edbItem.Length)  ($edb)"
        # Once WSearch is disabled the .edb is orphaned -- nothing reads it, and it is
        # frequently the single largest reclaim on the disk. Flag it here; 4b.3 offers it.
        if ($ws.StartType -eq 'Disabled' -and $edbItem.Length -gt 1GB) {
            Write-Host "   NOTE: search is disabled, so this $(Format-Size $edbItem.Length) index is dead" -ForegroundColor Yellow
            Write-Host '         weight. See section 4b.3 to reclaim it (-Aggressive).'  -ForegroundColor Yellow
        }
    } catch [System.UnauthorizedAccessException] {
        Write-Host '   Index database: present, size unreadable without admin.'
    } catch {
        Write-Host '   Index database: not found.'
    }

    if ($ws.Status -eq 'Running' -or $ws.StartType -ne 'Disabled') {
        if ($Apply -and $script:IsAdmin) {
            try {
                if ($ws.Status -eq 'Running') { Stop-Service WSearch -Force -ErrorAction Stop }
                Set-Service WSearch -StartupType Disabled -ErrorAction Stop
                Write-Act 'Stopped WSearch and set startup to Disabled.' -Done
            } catch {
                Write-Host "   [FAIL]    $($_.Exception.Message)" -ForegroundColor Red
            }
        } elseif ($Apply -and -not $script:IsAdmin) {
            Write-Act 'Stop WSearch + set startup Disabled -- NEEDS ADMIN.' -Skipped
        } else {
            Write-Act 'Stop WSearch and set its startup type to Disabled.'
        }
    } else {
        Write-Act 'WSearch already stopped and disabled.' -Skipped
    }
}

# ------------------------------------------------------- 3. temp / caches ---

Write-Head "3. TEMP & CACHE CLEANUP  [APPLY]  (only files older than $TempOlderThanDays days)"

$cutoff = (Get-Date).AddDays(-$TempOlderThanDays)

$targets = @(
    [pscustomobject]@{ Name = 'User temp';            Path = $env:TEMP;                                     Admin = $false }
    [pscustomobject]@{ Name = 'Windows temp';         Path = "$env:SystemRoot\Temp";                         Admin = $true  }
    [pscustomobject]@{ Name = 'Windows Update cache'; Path = "$env:SystemRoot\SoftwareDistribution\Download"; Admin = $true  }
    [pscustomobject]@{ Name = 'CBS logs';             Path = "$env:SystemRoot\Logs\CBS";                      Admin = $true  }
    [pscustomobject]@{ Name = 'Delivery Optimization'; Path = "$env:SystemRoot\SoftwareDistribution\DeliveryOptimization"; Admin = $true }
    [pscustomobject]@{ Name = 'Thumbnail cache';      Path = "$env:LOCALAPPDATA\Microsoft\Windows\Explorer";  Admin = $false }
    [pscustomobject]@{ Name = 'INetCache';            Path = "$env:LOCALAPPDATA\Microsoft\Windows\INetCache"; Admin = $false }
    [pscustomobject]@{ Name = 'CrashDumps';           Path = "$env:LOCALAPPDATA\CrashDumps";                  Admin = $false }
    [pscustomobject]@{ Name = 'pip cache';            Path = "$env:LOCALAPPDATA\pip\Cache";                   Admin = $false }
    [pscustomobject]@{ Name = 'npm cache (_cacache)'; Path = "$env:LOCALAPPDATA\npm-cache\_cacache";          Admin = $false }
    [pscustomobject]@{ Name = 'uv cache';             Path = "$env:LOCALAPPDATA\uv\cache";                    Admin = $false }
    [pscustomobject]@{ Name = 'NuGet http cache';     Path = "$env:LOCALAPPDATA\NuGet\v3-cache";              Admin = $false }
)

$totalReclaimable = 0L
$totalFreed = 0L

foreach ($t in $targets) {
    if (-not (Test-Path -LiteralPath $t.Path)) {
        Write-Host ("   {0,-24} {1}" -f $t.Name, '(not present)') -ForegroundColor DarkGray
        continue
    }

    $size = Get-PathSize -Path $t.Path -OlderThan $cutoff
    $totalReclaimable += $size.Bytes
    Write-Host ("   {0,-24} {1}   {2,6} files" -f $t.Name, (Format-Size $size.Bytes), $size.Count)

    if ($size.Bytes -eq 0) { continue }

    if ($Apply) {
        if ($t.Admin -and -not $script:IsAdmin) {
            Write-Act "$($t.Name): needs admin." -Skipped
            continue
        }
        $r = Remove-StaleFiles -Path $t.Path -OlderThan $cutoff
        $totalFreed += $r.Bytes
        Write-Act ("$($t.Name): freed $(Format-Size $r.Bytes), $($r.Deleted) deleted, $($r.Locked) in use/skipped.") -Done
    }
}

Write-Host ''
Write-Host ("   TOTAL reclaimable: {0}" -f (Format-Size $totalReclaimable)) -ForegroundColor Cyan
if ($Apply) {
    Write-Host ("   TOTAL freed      : {0}" -f (Format-Size $totalFreed)) -ForegroundColor Green
}

# ------------------------------------------ 4. report-only: user data areas --

Write-Head '4. REPORT ONLY  --  never auto-deleted (your data / your call)'

Write-Sub 'Recycle Bin'
$rbTotal = 0L
foreach ($d in (Get-Volume | Where-Object { $_.DriveLetter -and $_.FileSystem -eq 'NTFS' }).DriveLetter) {
    $rb = "${d}:\`$Recycle.Bin"
    if (Test-Path -LiteralPath $rb) {
        $s = Get-PathSize -Path $rb
        $rbTotal += $s.Bytes
        if ($s.Bytes -gt 0) { Write-Host ("   {0}:  {1}   {2} files" -f $d, (Format-Size $s.Bytes), $s.Count) }
    }
}
Write-Host ("   Total in Recycle Bin: {0}" -f (Format-Size $rbTotal))
Write-Host '   To empty (your decision):  Clear-RecycleBin -Force' -ForegroundColor DarkYellow

# ------------------------------------------------ 4b. AGGRESSIVE reclaims ----

Write-Head '4b. LARGER RECLAIMS  [APPLY + AGGRESSIVE]'

$aggressiveAllowed = $Apply -and $Aggressive -and $script:IsAdmin

if (-not $Aggressive) {
    Write-Host '   Not requested. Add -Aggressive to enable these (they will still prompt).' -ForegroundColor DarkGray
} elseif (-not $Apply) {
    Write-Host '   -Aggressive given but not -Apply: showing what WOULD happen only.' -ForegroundColor Magenta
} elseif (-not $script:IsAdmin) {
    Write-Host '   -Aggressive requires Administrator. Re-run from an elevated PowerShell.' -ForegroundColor Red
}

# --- 4b.1 hibernation --------------------------------------------------------

Write-Sub 'Hibernation file (hiberfil.sys)'

$hib = "$env:SystemDrive\hiberfil.sys"
$hibSize = 0L
if (Test-Path -LiteralPath $hib) {
    try { $hibSize = (Get-Item -LiteralPath $hib -Force).Length } catch { }
}

if ($hibSize -eq 0 -and -not (Test-Path -LiteralPath $hib)) {
    Write-Host '   Not present (hibernation already off).' -ForegroundColor Green
} else {
    $ramBytes = (Get-CimInstance Win32_ComputerSystem).TotalPhysicalMemory
    if ($hibSize) {
        $pct = [math]::Round(100 * $hibSize / $ramBytes)
        Write-Host ("   Current: {0}  ({1}% of RAM -> '{2}' type)" -f (Format-Size $hibSize), $pct,
            $(if ($pct -ge 35) { 'full' } else { 'reduced' }))
    } else {
        Write-Host '   Present (size not readable without admin).'
    }

    # Fast Startup is implemented ON TOP of hibernation -- turning hibernation
    # fully off silently removes it too. On a 5400rpm HDD that is a bad trade,
    # which is why 'Reduced' is the default rather than 'Off'.
    $fastStartup = (Get-ItemProperty 'HKLM:\SYSTEM\CurrentControlSet\Control\Session Manager\Power' `
            -ErrorAction SilentlyContinue).HiberbootEnabled
    Write-Host ("   Fast Startup: {0}" -f $(if ($fastStartup -eq 1) { 'ON' } else { 'off' }))

    switch ($HibernateMode) {
        'None' {
            Write-Act 'Hibernation: -HibernateMode None, leaving untouched.' -Skipped
        }
        'Reduced' {
            if (-not $aggressiveAllowed) {
                Write-Act 'Shrink hiberfil.sys to "reduced" (powercfg /hibernate /type reduced).'
            } elseif (Confirm-Aggressive -Title 'Shrink hiberfil.sys to reduced' -Consequences @(
                    'KEEPS Fast Startup (good on a spinning disk).',
                    'LOSES full hibernate (S4). You still have S3 standby.',
                    "Expect to reclaim roughly $(Format-Size ($hibSize / 2)).",
                    'Undo: powercfg /hibernate /type full')) {

                $out = & powercfg.exe /hibernate /type reduced 2>&1
                if ($LASTEXITCODE -eq 0) {
                    Start-Sleep -Seconds 2
                    $newSize = 0L
                    try { $newSize = (Get-Item -LiteralPath $hib -Force).Length } catch { }
                    Write-Act ("Hibernation set to reduced. hiberfil.sys now $(Format-Size $newSize) (was $(Format-Size $hibSize)).") -Done
                } else {
                    Write-Host "   [FAIL]    powercfg: $out" -ForegroundColor Red
                }
            }
        }
        'Off' {
            if (-not $aggressiveAllowed) {
                Write-Act 'Delete hiberfil.sys entirely (powercfg /hibernate off).'
            } elseif (Confirm-Aggressive -Title 'Disable hibernation entirely' -Consequences @(
                    'REMOVES hiberfil.sys completely.',
                    'ALSO DISABLES Fast Startup -- every boot becomes a cold boot.',
                    'On a 5400rpm HDD that noticeably slows startup. Reduced is usually better.',
                    "Expect to reclaim $(Format-Size $hibSize).",
                    'Undo: powercfg /hibernate on')) {

                $out = & powercfg.exe /hibernate off 2>&1
                if ($LASTEXITCODE -eq 0) {
                    Write-Act ("Hibernation disabled. Reclaimed $(Format-Size $hibSize).") -Done
                } else {
                    Write-Host "   [FAIL]    powercfg: $out" -ForegroundColor Red
                }
            }
        }
    }
}

# --- 4b.2 Windows upgrade staging -------------------------------------------

Write-Sub 'Windows upgrade staging folders'

$stagePaths = @(
    "$env:SystemDrive\Windows.old"
    "$env:SystemDrive\`$Windows.~BT"
    "$env:SystemDrive\`$Windows.~WS"
    "$env:SystemDrive\`$GetCurrent"
    "$env:SystemDrive\ESD"
)

$stageFound = @()
foreach ($p in $stagePaths) {
    if (Test-Path -LiteralPath $p) {
        $s = Get-PathSize -Path $p
        # A recent write time means an upgrade is STAGED, not merely leftover --
        # clearing it cancels that pending upgrade, so surface the distinction.
        $newest = (Get-ChildItem -LiteralPath $p -Force -ErrorAction SilentlyContinue |
                Sort-Object LastWriteTime -Descending | Select-Object -First 1).LastWriteTime
        $stageFound += [pscustomobject]@{ Path = $p; Bytes = $s.Bytes; Newest = $newest }
        Write-Host ("   {0,-28} {1}   newest content: {2:yyyy-MM-dd}" -f
            (Split-Path $p -Leaf), (Format-Size $s.Bytes), $newest) -ForegroundColor Yellow
    }
}

if (-not $stageFound) {
    Write-Host '   None present. Nothing to reclaim.' -ForegroundColor Green
} else {
    $stageTotal = ($stageFound | Measure-Object Bytes -Sum).Sum
    $recent = $stageFound | Where-Object { $_.Newest -gt (Get-Date).AddDays(-30) }
    if ($recent) {
        Write-Host ''
        Write-Host '   WARNING: content written in the last 30 days -- a Windows feature' -ForegroundColor Red
        Write-Host '   upgrade is STAGED and pending. Clearing this CANCELS that upgrade.' -ForegroundColor Red
        Write-Host '   (It can be re-downloaded later; nothing is permanently lost.)'      -ForegroundColor Red
    }

    if (-not $aggressiveAllowed) {
        Write-Act ("Clear upgrade staging via Disk Cleanup, reclaiming $(Format-Size $stageTotal).")
        Write-Host '   Manual route: Settings > System > Storage > Temporary files' -ForegroundColor DarkYellow
    } elseif (Confirm-Aggressive -Title 'Clear Windows upgrade staging folders' -Consequences @(
            "Reclaims about $(Format-Size $stageTotal).",
            'CANCELS any pending Windows feature upgrade (re-downloadable).',
            'Removes the ability to roll back a recent upgrade.',
            'Runs the built-in Disk Cleanup handler -- not a raw delete.')) {

        # Drive Disk Cleanup by its documented StateFlags mechanism rather than
        # force-deleting TrustedInstaller-owned trees, which can desync WU state.
        $vc = 'HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Explorer\VolumeCaches'
        $handlers = @(
            'Temporary Setup Files'
            'Previous Installations'
            'Setup Log Files'
            'Windows Upgrade Log Files'
            'Update Cleanup'
        )
        $tag = 65
        $flag = "StateFlags{0:D4}" -f $tag
        $touched = @()

        foreach ($h in $handlers) {
            $key = Join-Path $vc $h
            if (Test-Path -LiteralPath $key) {
                try {
                    New-ItemProperty -LiteralPath $key -Name $flag -Value 2 -PropertyType DWord -Force -EA Stop | Out-Null
                    $touched += $key
                } catch {
                    Write-Host "   [WARN]    could not stage handler '$h': $($_.Exception.Message)" -ForegroundColor DarkYellow
                }
            }
        }

        if (-not $touched) {
            Write-Host '   [FAIL]    no Disk Cleanup handlers available.' -ForegroundColor Red
        } else {
            Write-Host "   Running cleanmgr /sagerun:$tag -- a progress window may appear." -ForegroundColor DarkGray
            Write-Host '   This can take several minutes on a spinning disk. Waiting...'   -ForegroundColor DarkGray
            try {
                $proc = Start-Process -FilePath 'cleanmgr.exe' -ArgumentList "/sagerun:$tag" -PassThru -Wait -EA Stop
                Write-Host "   cleanmgr exited with code $($proc.ExitCode)." -ForegroundColor DarkGray
            } catch {
                Write-Host "   [FAIL]    could not run cleanmgr: $($_.Exception.Message)" -ForegroundColor Red
            }

            # Leave no persistent StateFlags behind for the next manual cleanmgr run.
            foreach ($key in $touched) {
                Remove-ItemProperty -LiteralPath $key -Name $flag -ErrorAction SilentlyContinue
            }

            $left = @($stagePaths | Where-Object { Test-Path -LiteralPath $_ })
            if (-not $left) {
                Write-Act ("Upgrade staging cleared. Reclaimed about $(Format-Size $stageTotal).") -Done
            } else {
                $leftBytes = 0L
                foreach ($p in $left) { $leftBytes += (Get-PathSize -Path $p).Bytes }
                Write-Act ("Partially cleared; $(Format-Size $leftBytes) still present.") -Done
                Write-Host '   Disk Cleanup would not release these:' -ForegroundColor DarkYellow
                $left | ForEach-Object { Write-Host "     $_" -ForegroundColor DarkYellow }
                Write-Host '   They are owned by TrustedInstaller. Forcing them with takeown/rmdir' -ForegroundColor DarkYellow
                Write-Host '   is possible but can desync Windows Update, so this script will not'  -ForegroundColor DarkYellow
                Write-Host '   do it. Try: Settings > System > Storage > Temporary files.'          -ForegroundColor DarkYellow
            }
        }
    }
}

# --- 4b.3 orphaned Windows Search index -------------------------------------

Write-Sub 'Windows Search index database (Windows.edb)'

if (-not $script:EdbBytes -or $script:EdbBytes -le 0) {
    if (-not $script:IsAdmin) {
        Write-Host '   Size unreadable without admin -- re-run elevated to evaluate.' -ForegroundColor DarkGray
    } else {
        Write-Host '   Not present -- nothing to reclaim.' -ForegroundColor DarkGray
    }
} else {
    $edbSvc = Get-Service -Name WSearch -ErrorAction SilentlyContinue

    Write-Host "   $($script:EdbPath)"
    Write-Host "   Size: $(Format-Size $script:EdbBytes)"

    # Deleting the index while the service can still start is pointless -- WSearch
    # simply rebuilds it, costing hours of seek load on a 5400rpm disk for no gain.
    if (-not $edbSvc -or $edbSvc.StartType -ne 'Disabled') {
        Write-Host '   WSearch is NOT disabled, so this index is live and in use.' -ForegroundColor DarkYellow
        Write-Host '   Deleting it now would only make Windows rebuild it. Disable the' -ForegroundColor DarkYellow
        Write-Host '   service first (section 2), then re-run.'                          -ForegroundColor DarkYellow
    } elseif (-not $aggressiveAllowed) {
        Write-Act ("Delete the orphaned search index, reclaiming $(Format-Size $script:EdbBytes).")
        Write-Host '   Safe because search is already disabled: nothing reads this file.'  -ForegroundColor DarkYellow
        Write-Host '   Windows regenerates it automatically if you ever re-enable search.' -ForegroundColor DarkYellow
    } elseif (-not $script:IsAdmin) {
        Write-Act 'Delete orphaned search index -- NEEDS ADMIN.' -Skipped
    } elseif (Confirm-Aggressive -Title 'Delete the orphaned Windows Search index' -Consequences @(
            "Reclaims about $(Format-Size $script:EdbBytes) on C:.",
            'Safe only because WSearch is already Disabled -- nothing reads this file.',
            'If you ever re-enable search, Windows rebuilds the index from scratch.',
            'That rebuild is a multi-hour background crawl on a 5400rpm disk.')) {

        # The service is Disabled, but a stale worker can still hold the handle open;
        # stop it explicitly rather than letting the delete fail on a sharing violation.
        try {
            if ($edbSvc.Status -ne 'Stopped') { Stop-Service WSearch -Force -ErrorAction Stop }
        } catch {
            Write-Host "   [WARN]    could not stop WSearch: $($_.Exception.Message)" -ForegroundColor DarkYellow
        }

        try {
            [IO.File]::Delete($script:EdbPath)
            Write-Act ("Deleted the search index. Reclaimed $(Format-Size $script:EdbBytes).") -Done
        } catch {
            Write-Host "   [FAIL]    $($_.Exception.Message)" -ForegroundColor Red
            Write-Host '   The file is still locked. Reboot and re-run -- with the service' -ForegroundColor DarkYellow
            Write-Host '   Disabled it will not come back up to re-open it.'                -ForegroundColor DarkYellow
        }
    }
}

# ------------------------------------------------- 5. large files & folders --

Write-Head '5. LARGE FILES & FOLDERS  (report only -- nothing is deleted)'

if ($SkipLargeFileScan) {
    Write-Host '   Skipped (-SkipLargeFileScan).' -ForegroundColor DarkGray
} else {
    foreach ($d in $ScanDrives) {
        $root = "${d}:\"
        if (-not (Test-Path -LiteralPath $root)) {
            Write-Host "   $root not available -- skipping." -ForegroundColor DarkGray
            continue
        }

        Write-Sub "Drive ${d}:  --  scanning (slow on a 5400rpm HDD, please wait)"
        $sw = [Diagnostics.Stopwatch]::StartNew()

        $files = Get-ChildItem -LiteralPath $root -Recurse -File -Force -ErrorAction SilentlyContinue

        Write-Host "   Top $TopN largest FILES:" -ForegroundColor White
        $files | Sort-Object Length -Descending | Select-Object -First $TopN | ForEach-Object {
            Write-Host ("     {0}   {1}" -f (Format-Size $_.Length), $_.FullName)
        }

        Write-Host ''
        Write-Host "   Top $TopN largest TOP-LEVEL FOLDERS:" -ForegroundColor White
        Get-ChildItem -LiteralPath $root -Directory -Force -ErrorAction SilentlyContinue | ForEach-Object {
            $dir = $_.FullName
            $sum = ($files | Where-Object { $_.FullName.StartsWith($dir, 'OrdinalIgnoreCase') } |
                    Measure-Object Length -Sum).Sum
            [pscustomobject]@{ Folder = $dir; Bytes = [double]($sum ?? 0) }
        } | Sort-Object Bytes -Descending | Select-Object -First $TopN | ForEach-Object {
            Write-Host ("     {0}   {1}" -f (Format-Size $_.Bytes), $_.Folder)
        }

        $sw.Stop()
        Write-Host ("   (scanned $($files.Count) files in $([math]::Round($sw.Elapsed.TotalSeconds,1))s)") -ForegroundColor DarkGray
    }
}

# --------------------------------------------------------- 6. diagnostics ----

# Strictly read-only, so it is gated on -Diagnostics alone and ignores -Apply.
if ($Diagnostics) { Invoke-HealthPanel }

# ----------------------------------------------------------------- summary ---

Write-Head 'SUMMARY'

if ($Apply) {
    Write-Sub 'Free space AFTER'
    $after = Get-FreeSpaceSnapshot
    $after | ForEach-Object {
        $b = $before | Where-Object Drive -eq $_.Drive
        $delta = if ($b) { [math]::Round($_.FreeGB - $b.FreeGB, 2) } else { 0 }
        [pscustomobject]@{
            Drive = $_.Drive; SizeGB = $_.SizeGB; FreeGB = $_.FreeGB
            PctFree = $_.PctFree; GainedGB = $delta
        }
    } | Format-Table -AutoSize | Out-String | Write-Host
} else {
    Write-Host ''
    Write-Host '  Nothing was changed. Re-run with -Apply to perform the [APPLY] items.'  -ForegroundColor Magenta
    Write-Host '  For the admin-only items, launch PowerShell as Administrator first.'    -ForegroundColor Magenta
    if (-not $Aggressive) {
        Write-Host '  Add -Aggressive for the three larger reclaims (hiberfil.sys, upgrade' -ForegroundColor Magenta
        Write-Host '  staging, orphaned search index). Each prompts before doing anything.' -ForegroundColor Magenta
    }
}

Write-Host ''
Write-Host '  Reminder: cleanup buys you free space and removes background seek load.' -ForegroundColor White
Write-Host '  It does NOT fix the root cause. On this machine the ranked fixes are:'   -ForegroundColor White
Write-Host '    1. Eject the failing SD card       (free, biggest anti-freeze win)'    -ForegroundColor White
Write-Host '    2. 2.5" SATA SSD, ~500GB           (biggest overall speed win)'        -ForegroundColor White
Write-Host '    3. 2 x 8GB DDR3L SO-DIMM = 16GB    (if still tight after the SSD)'     -ForegroundColor White
Write-Host ''
