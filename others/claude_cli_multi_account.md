# Running Claude Code CLI with Multiple Accounts Simultaneously

Yes, you can run **Claude Code (the Claude CLI)** from two different terminals using different accounts at the same time. 

By default, Claude Code stores its authentication, settings, and session data in a single directory (`~/.claude`). If you login to a different account normally, it will overwrite the session of the other terminal. To prevent this, you can use the **`CLAUDE_CONFIG_DIR` environment variable** to isolate each terminal session into its own configuration folder.

---

## 🛠️ Step-by-Step Setup

Follow the instructions below depending on your Operating System to set up isolated configurations.

### 🌐 For macOS and Linux

#### 1. Create Isolated Directories
Open your terminal and create distinct folders for each account's configuration data:
```bash
mkdir -p ~/.claude-personal
mkdir -p ~/.claude-work
```

#### 2. Configure Aliases
Add shortcuts to your shell configuration file (usually `~/.zshrc` for macOS or `~/.bashrc` for Linux) so you don't have to type the full environment variable every time.

Open your profile file in an editor (e.g., `nano ~/.zshrc`), and add the following lines at the bottom:
```bash
# Claude CLI Multi-Account Aliases
alias claude-personal="CLAUDE_CONFIG_DIR=~/.claude-personal claude"
alias claude-work="CLAUDE_CONFIG_DIR=~/.claude-work claude"
```
if it doesn't work, use this format
function claude-personal { $env:CLAUDE_CONFIG_DIR="$HOME\.claude-personal"; claude @args }

#### 3. Apply Changes
Save the file and refresh your current terminal session:
```bash
source ~/.zshrc
```
*(If you are using Bash, replace `.zshrc` with `.bashrc`)*

---

### 🪟 For Windows (PowerShell)

#### 1. Create Isolated Directories
Open PowerShell and create the directories to hold your separate user data:
```powershell
mkdir $env:USERPROFILE\.claude-personal
mkdir $env:USERPROFILE\.claude-work
```

#### 2. Configure Profile Functions
Open your PowerShell profile file to add custom command functions. Run:
```powershell
notepad $PROFILE
```
If the file doesn't exist, confirm to create it. Paste the following functions into the script:
```powershell
function claude-personal {
    $env:CLAUDE_CONFIG_DIR="$env:USERPROFILE\.claude-personal"
    claude
}

function claude-work {
    $env:CLAUDE_CONFIG_DIR="$env:USERPROFILE\.claude-work"
    claude
}
```

#### 3. Apply Changes
Save and close Notepad, then reload your PowerShell profile:
```powershell
. $PROFILE
```

---

## 🚀 How to Launch and Authenticate

Once your shortcuts are created, you can log into both accounts concurrently in different terminal windows.

1. **Open Terminal 1 (Personal Account):**
   * Run the command: `claude-personal`
   * Once the Claude prompt opens, type `/login` and complete the authentication process for your personal account.
2. **Open Terminal 2 (Work Account):**
   * Open a completely new terminal tab or window.
   * Run the command: `claude-work`
   * Once the prompt opens, type `/login` and authenticate with your work or secondary account credentials.

---

## 💡 Pro-Tips for Multi-Account Usage

* **Verify Your Identity:** Inside any active Claude CLI session, you can run the `/config` or check your current account status to verify which profile is active.
* **Persistent Sessions:** As long as you launch Claude using your designated aliases/functions (`claude-personal` or `claude-work`), your history, projects, and credentials will remain fully isolated and logged in across reboots.