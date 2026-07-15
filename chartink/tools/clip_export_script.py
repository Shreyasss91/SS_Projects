from pathlib import Path
import subprocess

p = Path(__file__).resolve().parent / "export_dashboard_console.js"
subprocess.run(
    [
        "powershell",
        "-NoProfile",
        "-Command",
        f"Set-Clipboard -Value (Get-Content -Raw -LiteralPath '{p}')",
    ],
    check=True,
)
print("clipboard ok", p.stat().st_size)
