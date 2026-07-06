# Guide: Keep VS Code Remote-SSH Terminals Alive on Windows

This guide configures native VS Code persistent sessions. This ensures that if your home internet drops, your Home PC sleeps, or your connection blinks, your background terminal processes (Python, scripts, etc.) stay safely running on your remote Windows Office PC.

---

## 🛠️ Step-by-Step Configuration

### Step 1: Open VS Code Settings
1. Open VS Code on your **Home PC**.
2. Connect to your **Office PC** via Remote-SSH.
3. Open Settings by pressing **`Ctrl + ,`** (or **`Cmd + ,`** on macOS).

### Step 2: Open the JSON Settings Editor
1. Look at the top-right corner of the Settings tab.
2. Click the **Open Settings (JSON)** icon (looks like a document file with a curved arrow).

### Step 3: Apply the Settings Changes
1. Paste the following configuration lines inside the main curly brackets `{ ... }`.
2. *Note: If you paste this at the bottom of the file, ensure you add a comma (`,`) to the end of the line directly above it.*
or you can manually enter these settings in GUI(File -> Preferences -> Settings)
```json
"terminal.integrated.enablePersistentSessions": true,
"terminal.integrated.persistentSessionReviveProcess": "onexitAndWindowClose",
"terminal.integrated.persistentSessionScrollback": 2000 <--- A large Number
```

### Step 4: Save and Close
1. Save the file by pressing **`Ctrl + S`** (or **`Cmd + S`**).
2. Close the `settings.json` tab.

---

## ⚙️ How It Works

* **`enablePersistentSessions: true`**  
  Tells the VS Code server agent running on your Office PC to track and protect open shell sessions.
* **`persistentSessionReviveProcess: "onexitAndWindowClose"`**  
  Forces the Office PC to freeze and preserve running processes if the home network disconnects, the window closes, or your home machine powers down.
* **`persistentSessionScrollback: 2000`**  
  Saves up to 2000 lines of console logs. This ensures your output data remains visible upon reconnection.

---

## 🧪 How to Verify Your Setup

1. Start a long-running execution or script in your terminal window.
2. Disconnect your Home PC from the internet (turn off Wi-Fi or pull the ethernet cable) for 1 minute.
3. Turn the internet back on and allow the VS Code window to automatically reconnect.
4. **Expected Result:** Your terminal pane will automatically stitch back together with your logs intact and the process still executing.
