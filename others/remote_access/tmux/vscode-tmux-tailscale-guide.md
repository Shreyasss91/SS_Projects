# Comprehensive Guide: Using tmux in VS Code via Tailscale & Remote-SSH
**Environment:** Windows 11/10 Client (`home-pc`) to Windows 11/10 Host (`office-pc`)

This guide walks you through setting up a persistent developmental environment using **VS Code**, **Tailscale**, **Remote-SSH**, and **tmux**. Because `tmux` is natively built for Unix-like environments, this setup routes your SSH connection directly into **WSL (Windows Subsystem for Linux)** on your office machine.

---

## Architecture Overview
* **home-pc (Client):** Windows machine running VS Code and the Remote-SSH extension.
* **Tailscale:** Provides a secure, encrypted mesh VPN tunnel between both PCs across separate networks.
* **office-pc (Host):** Windows machine running Windows OpenSSH Server and WSL (Ubuntu), where your workflows and `tmux` sessions will persist.

---

## Step 1: Prepare the Office PC (`office-pc`)

### 1.1 Install WSL and tmux
1. Right-click the **Start menu** and open **PowerShell (Admin)** or **Windows Terminal (Admin)**.
2. Execute the installation command:
   ```powershell
   wsl --install
   ```
3. **Restart your PC** when prompted to complete the installation.
4. After restarting, a Linux terminal window (defaulting to Ubuntu) will open automatically. Complete the initial setup by creating a **username** and **password**.
5. Update your package manager and install `tmux` by running:
   ```bash
   sudo apt update && sudo apt install tmux -y
   ```

### 1.2 Enable and Configure Windows OpenSSH Server
1. Navigate to **Settings > System > Optional Features** (or *Apps > Optional Features* depending on your Windows version).
2. Look for **OpenSSH Server**. If it is not installed, click *Add a feature* / *View features*, search for "OpenSSH Server", and install it.
3. Open **PowerShell (Admin)** and configure the OpenSSH service to start automatically:
   ```powershell
   # Start the SSH daemon service
   Start-Service sshd

   # Set startup type to Automatic so it runs when the PC boots
   Set-Service -Name sshd -StartupType 'Automatic'
   ```
4. Verify your current Windows username by running:
   ```powershell
   whoami
   ```
   *(Note down this username; you will need it for the client configuration).*

---

## Step 2: Establish the Tailscale Connection

1. Download and install **Tailscale** on both `home-pc` and `office-pc`.
2. Sign in using the same identity provider on both devices to add them to your private Tailnet.
3. Open the Tailscale app interface or admin console and note down the **Tailscale IP address** (e.g., `100.x.y.z`) or the **MagicDNS hostname** (e.g., `office-pc.tailnet-name.ts.net`) belonging to `office-pc`.

---

## Step 3: Configure VS Code on the Home PC (`home-pc`)

### 3.1 Install Extensions
1. Open **VS Code** on your home machine.
2. Click on the **Extensions** view icon on the sidebar (`Ctrl + Shift + X`).
3. Search for and install the official **Remote - SSH** extension developed by Microsoft.

### 3.2 Configure the SSH Host File
1. Press `Ctrl + Shift + P` (or `F1`) to bring up the Command Palette.
2. Type and select **`Remote-SSH: Connect to Host...`** and then choose **`Configure SSH Hosts...`**.
3. Select your user-specific configuration file (typically found at `C:\Users\<YourHomeUser>\.ssh\config`).
4. Append the following structural blocks to the file. This forces the Windows OpenSSH connection to route straight into the Linux subsystem (`wsl`) and allocates a TTY layer for interactive terminals:

```text
Host office-pc
    HostName <YOUR_OFFICE_PC_TAILSCALE_IP_OR_MAGICDNS_HERE>
    User <YOUR_OFFICE_PC_WINDOWS_USERNAME_HERE>
    RemoteCommand wsl
    RequestTTY yes
```
*Replace `<YOUR_OFFICE_PC_TAILSCALE_IP_OR_MAGICDNS_HERE>` and `<YOUR_OFFICE_PC_WINDOWS_USERNAME_HERE>` with the real credentials gathered in prior steps.*

---

## Step 4: Connecting and Automating tmux in VS Code

### 4.1 Make the Initial Connection
1. In VS Code on `home-pc`, press `Ctrl + Shift + P` and trigger **`Remote-SSH: Connect to Host...`**.
2. Select **`office-pc`**.
3. If prompted to choose the target platform platform type, choose **`Linux`** (since the `RemoteCommand wsl` handles the environment handoff).
4. Enter your Windows account password when prompted.

### 4.2 Automate Persistent tmux Profiles
To make sure that closing your VS Code window or dropping your Tailscale connection never terminates your running workloads, map tmux to your default terminal behavior.

1. Once the VS Code window successfully links to the remote session, open the settings interface via `Ctrl + ,`.
2. Ensure you click on the **Remote [SSH: office-pc]** tab near the top window layout so changes write exclusively to the host environment profile.
3. Click the **Open Settings (JSON)** icon in the top right window quadrant to edit raw rules directly.
4. Merge or insert the following layout directives into your settings dictionary:

```json
{
    "terminal.integrated.profiles.linux": {
        "tmux-ssh-persistent": {
            "path": "tmux",
            "args": ["new-session", "-A", "-s", "vscode-remote"]
        }
    },
    "terminal.integrated.defaultProfile.linux": "tmux-ssh-persistent"
}
```

### How This Session Persistence Works
The critical components inside this argument parameter block are `-A` and `-s vscode-remote`:
* The `-s vscode-remote` sets up a dedicated, predictable tracking name for your target terminal workspace.
* The `-A` flag acts as an "Attach or Create" directive. If a session named `vscode-remote` already exists in background WSL runtimes, VS Code will transparently hook back into it. If it doesn't exist (like right after a system reboot), it spins up a completely fresh context. 

Now, when you hit `Ctrl + \`` to open your terminal pane inside your SSH workspace, your code environments, execution logs, and background processes are completely isolated from network blips or unexpected laptop disconnects!
