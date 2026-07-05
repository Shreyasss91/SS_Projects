# VS Code Remote Development using Tailscale (Office-PC ↔ Home-PC)

## Objective

Develop and edit your **OpenAlgo** project running on the **Office-PC** from the **Home-PC** using **VS Code Remote SSH**.

This approach allows you to:

* Edit source code directly on the Office-PC
* Run terminals on the Office-PC
* Execute `uv run app.py` on the Office-PC
* Debug Python remotely
* Use Git on the Office-PC
* Avoid copying files between computers

All communication occurs securely over **Tailscale**.

---

# Final Architecture

```
                 Internet

        ┌────────────────────────┐
        │      Tailscale VPN     │
        └───────────┬────────────┘
                    │
         ┌──────────┴──────────┐
         │                     │
     Home-PC              Office-PC
     VS Code             OpenAlgo Source
                           SSH Server
                           Python
                           uv
```

VS Code runs on the Home-PC.

All code execution happens on the Office-PC.

---

# Prerequisites

## Office-PC

* Windows
* OpenAlgo project
* Python
* uv
* Tailscale installed
* Logged into Tailscale

## Home-PC

* Windows
* VS Code
* Tailscale installed
* Logged into the same Tailscale account

---

# Information to Note

## Office-PC

Computer Name

```
DESKTOP-MBO33IR
```

Windows Username

```
admin
```

This was obtained using

```powershell
echo $env:USERNAME
```

Output

```
admin
```

> **Important**
>
> `admin` is **your actual Windows account username**, obtained from:
>
> ```powershell
> echo $env:USERNAME
> ```
>
> It is **not** a generic placeholder or example username.
>
> On another Windows installation this value could be different (for example `john`, `administrator`, or `shreyas`). Always use the value returned by **your own** Office-PC.

Tailscale IP

```
100.108.179.50
```

Obtained using

```powershell
tailscale status
```

---

# Step 1 — Verify Tailscale

## Office-PC

Run

```powershell
tailscale status
```

Expected

```
100.108.179.50    desktop-mbo33ir
```

---

## Home-PC

Run

```powershell
tailscale status
```

You should see the Office-PC listed.

---

# Step 2 — Install OpenSSH Server (Office-PC)

Open **PowerShell as Administrator**

Check whether OpenSSH Server is installed

```powershell
Get-Service sshd
```

---

## If Installed

Expected

```
Status   Name   DisplayName

Running  sshd   OpenSSH SSH Server
```

Proceed to Step 4.

---

## If NOT Installed

Run

```powershell
Add-WindowsCapability -Online -Name OpenSSH.Server~~~~0.0.1.0
```

---

Start the service

```powershell
Start-Service sshd
```

---

Enable automatic startup

```powershell
Set-Service -Name sshd -StartupType Automatic
```

---

# Step 3 — Configure Windows Firewall

Open PowerShell as Administrator

Run

```powershell
New-NetFirewallRule `
    -Name sshd `
    -DisplayName "OpenSSH Server" `
    -Enabled True `
    -Direction Inbound `
    -Protocol TCP `
    -Action Allow `
    -LocalPort 22
```

---

Verify

```powershell
Get-NetFirewallRule sshd
```

---

# Step 4 — Verify SSH Server

Run

```powershell
netstat -ano | findstr :22
```

Expected

```
TCP    0.0.0.0:22    LISTENING
```

If you do not see this,

SSH is not running.

---

# Step 5 — Test SSH Connection

From the Home-PC

Open PowerShell

Run

```bash
ssh admin@100.108.179.50
```

where

```
admin
```

is the value returned by

```powershell
echo $env:USERNAME
```

on the Office-PC.

---

## First Connection

You will see

```
The authenticity of host cannot be established.

Are you sure you want to continue connecting?
```

Type

```
yes
```

---

Enter the Windows password for the Office-PC user.

> Windows SSH uses the **Windows account password**, **not** the Windows Hello PIN.

---

Expected prompt

```
admin@DESKTOP-MBO33IR
```

SSH is now working.

---

# Step 6 — Install VS Code Extension

On Home-PC

Open VS Code

Install extension

```
Remote - SSH
```

Published by Microsoft.

---

# Step 7 — Configure SSH Host

Open Command Palette

```
Ctrl + Shift + P
```

Select

```
Remote-SSH: Open SSH Configuration File
```

Open

```
~/.ssh/config
```

Add

```text
Host office-pc

    HostName 100.108.179.50

    User admin
```

where

```
admin
```

is the Office-PC Windows username returned by

```powershell
echo $env:USERNAME
```

---

Save the file.

---

# Step 8 — Connect from VS Code

Press

```
Ctrl + Shift + P
```

Select

```
Remote-SSH: Connect to Host
```

Choose

```
office-pc
```

---

VS Code will

* connect over SSH
* install the VS Code Server on the Office-PC (first time only)
* reconnect automatically

---

# Step 9 — Open OpenAlgo

Inside VS Code

```
File

Open Folder
```

Browse to

```
C:\Users\admin\Downloads\ai tools\openalgo_platform\openalgo
```

(or wherever your OpenAlgo project resides)

---

Now

* Explorer shows Office-PC files.
* Terminal runs on Office-PC.
* Python executes on Office-PC.

---

# Verify Everything

## Verify SSH

From Home-PC

```bash
ssh admin@100.108.179.50
```

Expected

```
admin@DESKTOP-MBO33IR
```

---

## Verify VS Code

Open terminal

Run

```powershell
hostname
```

Expected

```
DESKTOP-MBO33IR
```

---

Run

```powershell
whoami
```

Expected

```
desktop-mbo33ir\admin
```

---

Run

```powershell
pwd
```

Should show the OpenAlgo project directory on the Office-PC.

---

Run

```powershell
python --version
```

Should display the Python installed on the Office-PC.

---

Run

```powershell
uv --version
```

Should display the Office-PC's `uv` version.

---

# Starting OpenAlgo

Inside the VS Code terminal

```powershell
uv run app.py
```

OpenAlgo now runs entirely on the Office-PC.

---

# Accessing the Dashboard

Since the Office-PC is already configured with Tailscale,

you can open

```
http://100.108.179.50:5000
```

from

* Home-PC
* Mobile

while developing inside VS Code.

---

# Workflow

```
Start Office-PC

↓

Tailscale starts

↓

OpenSSH starts

↓

OpenAlgo project available

↓

Home-PC

↓

Open VS Code

↓

Remote SSH

↓

Connect to office-pc

↓

Open OpenAlgo folder

↓

Edit Code

↓

Run

uv run app.py

↓

Test

http://100.108.179.50:5000

↓

Continue development
```

---

# Troubleshooting

## SSH Connection Refused

Check

```powershell
Get-Service sshd
```

Service should be

```
Running
```

---

## SSH Times Out

Verify

```powershell
tailscale status
```

Both Office-PC and Home-PC should be online.

---

Verify firewall

```powershell
netstat -ano | findstr :22
```

Should show

```
0.0.0.0:22 LISTENING
```

---

## VS Code Cannot Connect

Verify SSH manually

```bash
ssh admin@100.108.179.50
```

If SSH works,

VS Code will also work.

---

## Authentication Failed

Remember

SSH uses the

**Windows account password**

NOT

Windows Hello PIN.

---

# Useful Commands

## Office-PC

Current Username

```powershell
echo $env:USERNAME
```

Current Computer Name

```powershell
echo $env:COMPUTERNAME
```

Current Logged-in User

```powershell
whoami
```

Verify SSH Service

```powershell
Get-Service sshd
```

Verify SSH Port

```powershell
netstat -ano | findstr :22
```

Verify Tailscale

```powershell
tailscale status
```

---

## Home-PC

SSH Test

```bash
ssh admin@100.108.179.50
```

Open VS Code

```
code .
```

Connect

```
Remote-SSH → office-pc
```

---

# Advantages of This Setup

* No file synchronization required.
* Source code remains only on the Office-PC.
* Full IntelliSense and debugging.
* Terminal executes on the Office-PC.
* Git operations occur on the Office-PC.
* Secure encrypted communication via Tailscale.
* No port forwarding.
* No public IP.
* No domain name required.
* Accessible from anywhere with Tailscale connectivity.
