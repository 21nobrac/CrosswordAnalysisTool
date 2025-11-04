import json
import glob
from collections import Counter
import csv
import os
from tqdm import tqdm

# Root folder containing all NYT JSONs
JSON_ROOT = "nyt_crosswords-master"
OUTPUT_FILE = "nyt_answer_freqs.csv"

counts = Counter()

# Recursively find all JSONs
json_files = glob.glob(os.path.join(JSON_ROOT, "**", "*.json"), recursive=True)
print(f"Found {len(json_files):,} JSON files to process.\n")

# Process with progress bar
for path in tqdm(json_files, desc="Processing puzzles"):
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        a = data.get("answers", {})
        if not a:
            continue

        answers = []
        answers.extend(a.get("across", []) or [])
        answers.extend(a.get("down", []) or [])

        for ans in answers:
            if ans and isinstance(ans, str):
                counts[ans.strip().upper()] += 1

    except Exception as e:
        print(f"\nError reading {path}: {e}")

# Write to CSV
with open(OUTPUT_FILE, "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerow(["answer", "count"])
    for answer, count in counts.most_common():
        writer.writerow([answer, count])

print(f"\n Done! Wrote {len(counts):,} unique answers to {OUTPUT_FILE}")
