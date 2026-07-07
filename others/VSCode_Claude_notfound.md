# Operator Notes -- Claude CLI PATH Troubleshooting

**Date:** 2026-07-07

## Problem

Running:

``` powershell
claude
```

or

``` powershell
claude --version
```

returned:

``` text
The term 'claude' is not recognized...
```

even though the package was installed globally with npm.

------------------------------------------------------------------------

## Investigation

Verified installation:

``` powershell
npm list -g --depth=0
```

showed:

-   `@anthropic-ai/claude-code@2.1.202`

Checked for launcher files:

``` powershell
Get-ChildItem C:\Users\admin\AppData\Roaming\npm\claude*
```

Found:

-   `claude`
-   `claude.cmd`
-   `claude.ps1`

So installation was correct.

------------------------------------------------------------------------

## Root Cause

`C:\Users\admin\AppData\Roaming\npm` was **not** present in the active
`PATH`.

Temporary fix:

``` powershell
$env:Path += ";C:\Users\admin\AppData\Roaming\npm"
```

After that:

``` powershell
where.exe claude
claude --version
```

worked.

The User PATH was then updated permanently.

------------------------------------------------------------------------

## Secondary Issue

New VS Code terminals still could not find `claude`.

Investigation showed:

-   User PATH contained `C:\Users\admin\AppData\Roaming\npm`
-   Active `$env:Path` inside VS Code did not.

PowerShell profile was inspected and found **not** to be modifying PATH.

The actual issue was that **VS Code had not reloaded the updated
environment variables**.

------------------------------------------------------------------------

## Resolution

Completely restarted VS Code.

After restart:

``` powershell
where.exe claude
```

returned:

``` text
C:\Users\admin\.local\bin\claude.exe
C:\Users\admin\AppData\Roaming\npm\claude
C:\Users\admin\AppData\Roaming\npm\claude.cmd
```

and

``` powershell
claude --version
```

worked successfully.

------------------------------------------------------------------------

## Observation

`npm` reported:

``` text
@anthropic-ai/claude-code@2.1.202
```

while:

``` powershell
claude --version
```

reported:

``` text
2.1.201 (Claude Code)
```

This is because Windows resolves `claude` to:

``` text
C:\Users\admin\.local\bin\claude.exe
```

before the npm shim in:

``` text
C:\Users\admin\AppData\Roaming\npm
```

To use the npm-installed version first, either:

-   move `C:\Users\admin\AppData\Roaming\npm` earlier in PATH, or
-   remove the older `C:\Users\admin\.local\bin\claude.exe` if no longer
    needed.

------------------------------------------------------------------------

## Final Status

-   ✅ Claude CLI is accessible from new VS Code terminals.
-   ✅ PATH includes the npm global bin directory.
-   ✅ Root cause was stale VS Code environment after PATH changes.
-   ⚠️ PATH contains many duplicate entries; optional cleanup is
    recommended.
