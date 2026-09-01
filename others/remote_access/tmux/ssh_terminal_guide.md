# Guide: Accessing and Managing Persistent Terminal Sessions Over SSH

This guide covers how to manage your current VS Code terminal session (**PID 4468**) on your **Office PC** and how to set up a robust, persistent terminal workflow using **tmux** so you never lose your terminal state when switching between your **Home PC** and **Office PC**.

---

## Part 1: How to Access Your Current Session (PID 4468)

### Method A: The VS Code Server "Localhost" Re-attachment
When you connected from your **Home PC**, VS Code started a background server instance on your **Office PC**. Connecting to this server locally restores your exact terminal tabs.

* **Where to do this:** On the **Office PC**
* **Step-by-step:**
  1. Open **VS Code** locally.
  2. Open the Command Palette by pressing `Ctrl + Shift + P`.
  3. Type and select `Remote-SSH: Connect to Host...`.
  4. Enter `localhost` (or `127.0.0.1`) and press `Enter`.
  5. Once connected, open the **exact same workspace/folder** that you had open while working from home.
  6. Open your terminal panel (`Ctrl + \``). Your previous terminal tabs, including the one running **PID 4468**, should automatically reappear with their command history.

### Method B: Manage or Monitor via PowerShell
If you only need to inspect or stop the process from your office machine without using VS Code remote windows.

* **Where to do this:** On the **Office PC**
* **Step-by-step:**
  1. Open **PowerShell**.
  2. To check if the process is still running and inspect its details, run:
     ```powershell
     Get-Process -Id 4468 | Format-List *
     ```
  3. To forcefully terminate the process if a script is hung or needs stopping, run:
     ```powershell
     Stop-Process -Id 4468 -Force
     ```

---

## Part 2: Proactive Setup – Persistent Terminals via tmux (WSL)

Windows command-line instances (PowerShell/CMD) natively lack session attachment capabilities. To prevent this issue in the future, configure a terminal multiplexer (`tmux`) inside **WSL (Windows Subsystem for Linux)**.

### Step 1: Install the Multiplexer Environment
* **Where to do this:** On the **Office PC**
* **Step-by-step:**
  1. Search for **PowerShell**, right-click it, and select **Run as Administrator**.
  2. Install WSL and the default Ubuntu Linux distribution by running:
     ```powershell
     wsl --install
     ```
  3. Restart the computer if prompted by Windows. 
  4. Follow the on-screen prompts in the newly opened Linux terminal window to create your Linux username and password.
  5. Update package lists and install `tmux` by running:
     ```bash
     sudo apt update && sudo apt install tmux -y
     ```

### Step 2: Configure Windows OpenSSH to Launch WSL by Default
This ensures that when you connect via SSH from your Home PC, you instantly enter the persistent Linux environment.

* **Where to do this:** On the **Office PC**
* **Step-by-step:**
  1. Open **PowerShell as Administrator**.
  2. Force the default SSH shell configuration to map to WSL by executing:
     ```powershell
     New-ItemProperty -Path "HKLM:\SOFTWARE\OpenSSH" -Name "DefaultShell" -Value "C:\Windows\System32\wsl.exe" -PropertyType String -Force
     ```

### Step 3: Launching a Session from Home
* **Where to do this:** On the **Home PC**
* **Step-by-step:**
  1. Connect to your **Office PC** using VS Code SSH or your standard terminal emulator. You will automatically land inside the WSL Ubuntu shell.
  2. Create a new, explicitly named persistent `tmux` session (e.g., named `work`):
     ```bash
     tmux new -s work
     ```
  3. Execute your long-running processes, scripts, or build commands inside this session.
  4. **To detach safely without stopping your code:** Press `Ctrl + B`, release both keys, and then press `D`. You can now safely close VS Code or shut down your **Home PC**. Your tasks will keep running in the background on the office computer.

### Step 4: Resuming the Session at the Office
* **Where to do this:** On the **Office PC**
* **Step-by-step:**
  1. Walk up to your desk and open the **Ubuntu** application or **PowerShell** (then type `wsl` to enter Linux).
  2. Confirm your session is alive by listing active terminal workspaces:
     ```bash
     tmux ls
     ```
  3. Reattach to your live session and pick up exactly where you left off:
     ```bash
     tmux attach -t work
     ```
