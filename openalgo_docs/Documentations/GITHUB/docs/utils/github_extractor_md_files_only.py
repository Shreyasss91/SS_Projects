import requests
from pathlib import Path

OWNER = "marketcalls"
REPO = "openalgo"
BRANCH = "main"

GITHUB_API = "https://api.github.com"

OUTPUT_DIR = Path(r"C:\Users\admin\Desktop\openalgo_docs\GITHUB\docs")
START_PATH = "docs/userguide"
MERGED_FILE = OUTPUT_DIR / "OpenAlgo_userguide_Merged.md"

session = requests.Session()
session.headers.update({
    "Accept": "application/vnd.github+json"
})

downloaded_files = []


def download_folder(repo_path: str):
    url = f"{GITHUB_API}/repos/{OWNER}/{REPO}/contents/{repo_path}?ref={BRANCH}"

    response = session.get(url)
    response.raise_for_status()

    items = response.json()

    for item in items:

        if item["type"] == "dir":
            download_folder(item["path"])

        elif item["type"] == "file":

            if item["name"].lower().endswith(".md"):

                relative_path = Path(item["path"])
                local_file = OUTPUT_DIR / relative_path

                local_file.parent.mkdir(
                    parents=True,
                    exist_ok=True
                )

                print(f"Downloading: {item['path']}")

                content = session.get(
                    item["download_url"]
                ).text

                local_file.write_text(
                    content,
                    encoding="utf-8"
                )

                downloaded_files.append(local_file)


print("Downloading markdown files...")
download_folder(START_PATH)

print(f"Downloaded {len(downloaded_files)} files")

# --------------------------------------------------
# Merge markdown files
# --------------------------------------------------

with open(MERGED_FILE, "w", encoding="utf-8") as merged:

    merged.write("# OpenAlgo API Documentation\n\n")

    for file in sorted(downloaded_files):

        relative = file.relative_to(OUTPUT_DIR)

        merged.write("\n\n")
        merged.write("---\n\n")
        merged.write(f"# FILE: {relative}\n\n")

        content = file.read_text(
            encoding="utf-8",
            errors="ignore"
        )

        merged.write(content)
        merged.write("\n")

print(f"Merged file created:\n{MERGED_FILE}")