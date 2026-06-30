from pathlib import Path
import csv

DOCS_DIR = Path(r"C:\Users\admin\Desktop\openalgo_docs\Design_Documentation\original_md")
MAPPING_FILE = Path(r"C:\Users\admin\Desktop\openalgo_docs\Design_Documentation\utils\Design_docs_order_mapping.csv")
OUTPUT_FILE = DOCS_DIR / "OpenAlgo_Design_Documentation.md"

entries = []

with open(MAPPING_FILE, newline="", encoding="utf-8") as f:
    reader = csv.DictReader(f)

    for row in reader:
        rank = int(row["rank_number"])
        filename = row["filename"]

        title = filename.replace(".md", "").replace("-", " ").title()

        entries.append((rank, filename, title))

entries.sort(key=lambda x: x[0])

with open(OUTPUT_FILE, "w", encoding="utf-8") as out:

    out.write("# OpenAlgo V1 API Documentation\n\n")

    out.write("## Table of Contents\n\n")

    for rank, _, title in entries:
        out.write(f"{rank}. {title}\n")

    out.write("\n---\n")

    for rank, filename, title in entries:

        file_path = DOCS_DIR / filename

        if not file_path.exists():
            print(f"Missing file: {file_path}")
            continue

        print(f"Merging {rank}: {filename}")

        out.write(f"\n\n# {title}\n\n")

        with open(file_path, "r", encoding="utf-8") as f:
            out.write(f.read())

        out.write("\n\n---\n")

print(f"\nGenerated: {OUTPUT_FILE}")