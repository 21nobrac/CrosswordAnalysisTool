import csv
from collections import Counter
import os

FREQ_FILE = "nyt_answer_freqs_1976_2012.csv"

def update_freq_db(all_words, freq_file=FREQ_FILE):
    """
    Update the frequency CSV with new crossword answers.

    all_words: list[str]
        A list of all across + down answers (e.g. from get_across_words + get_down_words)
    freq_file: str
        Path to the frequency database CSV
    """

    # Normalize and count incoming words
    new_counts = Counter(w.strip().upper() for w in all_words if w.strip())

    # Load existing counts
    existing = Counter()
    if os.path.exists(freq_file):
        with open(freq_file, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                existing[row["answer"]] = int(row["count"])

    # Merge
    for word, c in new_counts.items():
        existing[word] += c

    # Write back to CSV
    with open(freq_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["answer", "count"])
        for answer, count in existing.most_common():
            writer.writerow([answer, count])

    print(f"✅ Updated frequency DB with {len(new_counts)} new answers ({len(existing)} total).")
