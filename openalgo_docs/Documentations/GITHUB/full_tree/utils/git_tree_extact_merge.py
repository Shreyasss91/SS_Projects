import requests
import zipfile
import shutil

from pathlib import Path
from collections import defaultdict

# ==========================================================
# CONFIG
# ==========================================================

OWNER = "marketcalls"
REPO = "openalgo"
BRANCH = "main"

OUTPUT_DIR = Path(
    r"C:\Users\admin\Desktop\openalgo_docs\GITHUB\full_tree"
)

ZIP_FILE = OUTPUT_DIR / "repo.zip"

EXTRACT_DIR = OUTPUT_DIR / "repository"

MASTER_MERGED_FILE = (
    OUTPUT_DIR /
    "OPENALGO_FULL_REPOSITORY.md"
)

# ==========================================================
# TEXT FILE TYPES
# ==========================================================

TEXT_EXTENSIONS = {
    ".md",
    ".txt",
    ".py",
    ".json",
    ".yaml",
    ".yml",
    ".csv",
    ".html",
    ".htm",
    ".js",
    ".ts",
    ".css",
    ".ini",
    ".cfg",
    ".conf",
    ".toml",
    ".xml",
    ".sh",
    ".bat",
    ".ps1",
    ".sql",
    ".env",
    ".rst",
}

# ==========================================================
# CLEAN OUTPUT
# ==========================================================

OUTPUT_DIR.mkdir(
    parents=True,
    exist_ok=True
)

if EXTRACT_DIR.exists():
    shutil.rmtree(EXTRACT_DIR)

# ==========================================================
# DOWNLOAD ZIP
# ==========================================================

zip_url = (
    f"https://github.com/"
    f"{OWNER}/{REPO}"
    f"/archive/refs/heads/{BRANCH}.zip"
)

print(f"Downloading repository ZIP...")
print(zip_url)

r = requests.get(zip_url, stream=True)
r.raise_for_status()

with open(ZIP_FILE, "wb") as f:
    for chunk in r.iter_content(8192):
        f.write(chunk)

print("ZIP downloaded.")

# ==========================================================
# EXTRACT ZIP
# ==========================================================

print("Extracting ZIP...")

with zipfile.ZipFile(ZIP_FILE, "r") as z:
    z.extractall(EXTRACT_DIR)

print("ZIP extracted.")

# ==========================================================
# FIND REPO ROOT
# ==========================================================

repo_roots = [
    p for p in EXTRACT_DIR.iterdir()
    if p.is_dir()
]

if not repo_roots:
    raise Exception(
        "Repository root not found."
    )

REPO_ROOT = repo_roots[0]

print(f"Repository root: {REPO_ROOT}")

# ==========================================================
# COLLECT FILES BY FOLDER
# ==========================================================

folder_files = defaultdict(list)

all_files = []

for file in REPO_ROOT.rglob("*"):

    if not file.is_file():
        continue

    # skip generated merge files
    if file.name.startswith("_MERGED_"):
        continue

    folder_files[str(file.parent)].append(file)

    all_files.append(file)

print()
print(f"Total files found: {len(all_files)}")

# ==========================================================
# FUNCTION TO WRITE FILE CONTENT
# ==========================================================

def write_file_to_markdown(
    merged,
    file,
    base_dir
):
    rel_path = file.relative_to(base_dir)

    merged.write("\n\n---\n\n")
    merged.write(
        f"# FILE: {rel_path}\n\n"
    )

    suffix = file.suffix.lower()

    # ------------------------------------------------------
    # TEXT FILE
    # ------------------------------------------------------

    if suffix in TEXT_EXTENSIONS:

        try:

            content = file.read_text(
                encoding="utf-8",
                errors="ignore"
            )

            merged.write(
                f"```{suffix.lstrip('.')}\n"
            )

            merged.write(content)

            merged.write(
                "\n```\n"
            )

        except Exception as e:

            merged.write(
                "[ERROR READING FILE]\n\n"
            )

            merged.write(
                str(e)
            )

            merged.write("\n")

    # ------------------------------------------------------
    # BINARY FILE
    # ------------------------------------------------------

    else:

        size = file.stat().st_size

        merged.write(
            "[BINARY FILE]\n\n"
        )

        merged.write(
            f"Type: {suffix}\n\n"
        )

        merged.write(
            f"Size: {size} bytes\n\n"
        )

        merged.write(
            f"Path: {rel_path}\n"
        )

# ==========================================================
# CREATE MERGED FILE PER FOLDER
# ==========================================================

print()
print("Creating folder merges...")

for folder, files in folder_files.items():

    folder_path = Path(folder)

    merged_file = (
        folder_path /
        "_MERGED_FOLDER_CONTENT.md"
    )

    with open(
        merged_file,
        "w",
        encoding="utf-8"
    ) as merged:

        merged.write(
            f"# Folder Merge\n\n"
        )

        merged.write(
            f"Folder: {folder_path}\n\n"
        )

        for file in sorted(files):

            write_file_to_markdown(
                merged,
                file,
                REPO_ROOT
            )

    print(
        f"Created: {merged_file}"
    )

# ==========================================================
# CREATE MASTER MERGED FILE
# ==========================================================

print()
print("Creating master merged file...")

with open(
    MASTER_MERGED_FILE,
    "w",
    encoding="utf-8"
) as merged:

    merged.write(
        "# OpenAlgo Full Repository\n\n"
    )

    merged.write(
        f"Repository: {OWNER}/{REPO}\n\n"
    )

    merged.write(
        f"Branch: {BRANCH}\n\n"
    )

    merged.write(
        f"Total Files: {len(all_files)}\n\n"
    )

    for file in sorted(all_files):

        write_file_to_markdown(
            merged,
            file,
            REPO_ROOT
        )

print()
print("====================================")
print("DONE")
print("====================================")
print(f"Repository Root:")
print(REPO_ROOT)
print()
print(f"Master Merge:")
print(MASTER_MERGED_FILE)