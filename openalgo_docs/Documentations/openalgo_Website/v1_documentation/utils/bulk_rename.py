import csv
from pathlib import Path

# Folder containing markdown files
DOCS_DIR = Path(r"C:\Users\admin\Desktop\openalgo_docs\v1_documentation")   # change this

# CSV file
CSV_FILE = Path(r"C:\Users\admin\Desktop\openalgo_docs\v1_documentation\utils\v1_docs_order_mapping.csv")  # change this

with open(CSV_FILE, newline='', encoding='utf-8') as f:
    reader = csv.DictReader(f)

    for row in reader:
        rank = int(row["rank_number"])
        filename = row["filename"]

        old_file = DOCS_DIR / filename

        if not old_file.exists():
            print(f"Missing: {filename}")
            continue

        new_filename = f"{rank:02d}_{filename}"
        new_file = DOCS_DIR / new_filename

        old_file.rename(new_file)

        print(f"Renamed: {filename} -> {new_filename}")