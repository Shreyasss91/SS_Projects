# Wiki: Syncing Uncommitted Work Between Multiple Machines in Git

This guide details how to seamlessly transfer unstaged, staged, and uncommitted changes from one computer (**PC1**) to another (**PC2**) without polluting your production `main` branch timeline.

---

## 🛠️ Method 1: The Remote Feature Branch Approach (Recommended)
This is the safest and cleanest method for distributed teams. It utilizes the remote repository (e.g., GitHub, GitLab) as a secure cloud buffer by storing your work-in-progress (WIP) on an isolated tracking branch. 

*Note: This approach handles a mix of both staged and unstaged files perfectly.*

### Step 1: Securely Uploading from PC1
Run these commands on **PC1** to bundle all local modifications and send them to the remote server:

```bash
# 1. Create and switch to an isolated, temporary tracking branch
git checkout -b wip-transfer-branch

# 2. Stage all remaining untracked and unstaged modifications
# (This safely bundles previously staged AND unstaged files together)
git add .

# 3. Create a temporary work-in-progress commit
git commit -m "WIP: Transferring ongoing work to PC2"

# 4. Push the temporary branch up to your remote repository
git push origin wip-transfer-branch
```

### Step 2: Retrieving and Updating Baseline on PC2
Switch to **PC2**. Before grabbing your temporary branch, we will download all remote changes and bring your local `main` branch up to speed so your workspace baseline is perfectly up to date:

```bash
# 1. Download all latest metadata from your remote repository
git fetch origin

# 2. Update your local main branch with any new cloud commits while keeping it clean
git checkout main
git reset --hard origin/main

# 3. Switch to the temporary transfer branch
git checkout wip-transfer-branch
```


### Step 3: Un-committing Changes & Resuming Work
To bring the files back into your active workspace, strip away the temporary commit wrapper. You have two options depending on how you want your staging area to look:

#### Option A: Keep everything, but make it all UNSTAGED (Standard)
```bash
# Erases the commit; all files (previously staged & unstaged) become unstaged
git reset HEAD^
```

#### Option B: Keep everything and restore the STAGED files back to the staged index
```bash
# Erases the commit but keeps your previously staged files in the staged area
git reset --soft HEAD^
```

#### 💡 Deep Dive: What happens under the hood after `git reset`?
* **Your Files:** They remain 100% intact. No code is lost [A].
* **Local History:** The temporary "WIP" commit is erased from your local timeline on PC2 [A].
* **Active Branch:** You remain checked out on `wip-transfer-branch` [A].
* **Remote History:** The commit still exists untouched on GitHub/GitLab, meaning PC2 is now safely "behind" the remote server.

### Step 4: Moving Changes back to Main
Now that your changes are sitting safely back in your workspace as active, uncommitted files, switch back to your primary working branch:

```bash
# Switch back to your main branch (your active changes will safely travel with you)
git checkout main
```

### Step 5: Remote Cleanup
Since your local `main` branch was already updated in Step 2, you are ready to code immediately. All that is left to do is wipe away the temporary transfer footprint:

```bash
# 1. Safely delete the temporary branch locally from PC2
git branch -d wip-transfer-branch

# 2. Wipe the temporary branch off the remote server (GitHub/GitLab)
git push origin --delete wip-transfer-branch
```

---

## 💾 Method 2: The Git Patch Approach (Offline/No-Remote)
Use this fallback method if you do not have permission to push new branches to the remote repository, or if you are working completely offline. 

### Step 1: Exporting the Patch from PC1
Because you have a mix of staged and unstaged changes, you must generate a patch file that explicitly captures both states:

```bash
# 1. Export all unstaged AND staged changes into a unified patch file
git diff HEAD > my_workspace_changes.patch
```

### Step 2: Transfer the Patch
Move the generated `my_workspace_changes.patch` file from **PC1** to **PC2** using any external transfer mechanism:
* USB Flash Drive
* Local Network Share
* Cloud Storage (Google Drive, Dropbox)
* Email / Slack Direct Message

### Step 3: Importing the Patch on PC2
Ensure your repository on **PC2** is synchronized to the baseline `main` branch before applying the structural delta:

```bash
# 1. Ensure you are on the main branch
git checkout main

# 2. Synchronize with the upstream remote to match PC1's baseline
git pull origin main

# 3. Inject the file changes directly into your active working directory
git apply my_workspace_changes.patch
```
*Note: The patch tool applies all changes to your workspace as unstaged files. You will need to manually re-stage (`git add`) any specific files you want back in the index.*

---

## 🔍 Alternative Method: Git Stash (Advanced)
If you prefer a stash-based workflow, you can explicitly tell Git to stash both your staging area and your working tree independently, though you will still need a dummy branch to transport it over the network.

```bash
# On PC1: Stash your mixed state workspace
git stash --keep-index
git stash

# Create a temporary branch to carry both stashes
git checkout -b temp-stash-branch
git stash pop stash@{1} # Pops the unstaged changes
git add .
git stash pop stash@{0} # Pops the staged changes
git commit -m "WIP: Staged and Unstaged tracking"
git push origin temp-stash-branch
```
