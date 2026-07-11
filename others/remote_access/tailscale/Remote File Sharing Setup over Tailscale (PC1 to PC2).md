# Remote File Sharing Setup over Tailscale (PC1 to PC2)

This guide details how to securely share multiple distinct folders on **PC2** and access them from **PC1** using Tailscale. Since you only have SSH access to PC2, all server-side steps are executed via the terminal.

### 🌐 Environment Architecture
*   **PC1:** Your current local machine.
*   **PC2 (Remote Machine):** Windows PC accessible via VS Code Remote SSH.
*   **PC2 Tailscale IP:** `100.108.179.50`

### 📂 Target Folders & Share Names
Windows requires a **unique Share Name for every unique folder path**. We will map two separate folders:
1.  **Folder 1 (Strategies Workspace):** 
    *   Path: `C:\Users\admin\Downloads\ai tools\openalgo_platform\openalgo\strategies\SS_Projects`
    *   Share Name: `TailscaleShare`
2.  **Folder 2 (Claude Configurations):** 
    *   Path: `$home\.claude` (Dynamically resolves to your user home profile)
    *   Share Name: `ClaudeShare`

---

## 🛠️ Phase 1: Configuration on PC2 (Via VS Code SSH Terminal)

Perform these steps inside your active VS Code Remote SSH terminal connected to PC2. Ensure your terminal profile is set to **PowerShell** (indicated by `PS` at the start of your command line).

### Step 1: Enable Windows Firewall for Sharing
Allow incoming File and Printer sharing traffic over your network adapters (including the Tailscale adapter).
```powershell
Set-NetFirewallRule -DisplayGroup "File and Printer Sharing" -Enabled True
```

### Step 2: Create Share #1 (Strategies Folder)
Run the following command to register your coding project workspace under the name `TailscaleShare`:
```powershell
New-SmbShare -Name "TailscaleShare" -Path "C:\Users\admin\Downloads\ai tools\openalgo_platform\openalgo\strategies\SS_Projects" -FullAccess "Everyone"
```

### Step 3: Create Share #2 (Claude Profile Folder)
Run this block to dynamically resolve your current user's `$home` path and register the hidden configuration directory under the name `ClaudeShare`:
```powershell
$ClaudePath = Join-Path $home ".claude"
New-SmbShare -Name "ClaudeShare" -Path $ClaudePath -FullAccess "Everyone"
```

### Step 4: Verify Both Network Shares are Active
Ensure Windows acknowledges both shares by running:
```powershell
Get-SmbShare | Where-Object { $_.Name -in "TailscaleShare", "ClaudeShare" }
```
*Expected Terminal Output:*
```text
Name           ScopeName Path                                                                                    Description
----           --------- ----                                                                                    -----------
ClaudeShare    *         C:\Users\admin\.claude
TailscaleShare *         C:\Users\admin\Downloads\ai tools\openalgo_platform\openalgo\strategies\SS_Projects
```

---

## 💻 Phase 2: Accessing the Folders from PC1

Once Phase 1 is complete, switch back to your physical local machine (**PC1**). You can open or mount either folder using these options:

### Method A: Quick Access via Windows File Explorer
1. Press the keyboard shortcut **`Windows Key + R`** to launch the Run dialogue box.
2. To open your strategies project, paste:
   ```text
   \\100.108.179.50\TailscaleShare
   ```
3. To open your Claude configurations, paste:
   ```text
   \\100.108.179.50\ClaudeShare
   ```
4. Press **Enter**. When prompted by Windows Security, log in using **PC2's local Windows username and password**.

### Method B: Mount as Permanent Network Drives via Terminal
If you prefer dedicated drive letters inside "This PC", open a standard Command Prompt or PowerShell window on **PC1** and run:

```cmd
:: Map Folder 1 to Drive X:
net use X: \\100.108.179.50\TailscaleShare /user:PC2_Username PC2_Password

:: Map Folder 2 to Drive Y:
net use Y: \\100.108.179.50\ClaudeShare /user:PC2_Username PC2_Password
```
*Replace `PC2_Username` and `PC2_Password` with the actual OS-level credentials of PC2.*

---

## 🚨 Troubleshooting & Cleanup

*   **Showing Hidden Dotfiles on PC1:** Because `.claude` is a hidden directory, ensure you have enabled hidden items in PC1's File Explorer (`View > Show > Hidden items`) if you don't see your configuration files right away.
*   **Authentication Issues:** If you use a Microsoft account email on PC2, use your full email address as the username and your master account password. **Windows Hello PIN codes will not work for network sharing.**
*   **Removing / Resetting Shares:** If you ever need to stop sharing or want to rename them later, execute these commands inside your PC2 SSH terminal:
    ```powershell
    Remove-SmbShare -Name "TailscaleShare" -Force
    Remove-SmbShare -Name "ClaudeShare" -Force
    ```
