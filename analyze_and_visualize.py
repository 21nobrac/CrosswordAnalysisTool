from parse_crossword import load_grid_from_json
from wordfreq import zipf_frequency
from update_freq_db import update_freq_db
from wordfreq_algorithms import ALGORITHMS
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import wordninja as wnj
import csv
import os

FREQ_FILE = "nyt_answer_freqs.csv"

# Select algorithm by name
algo_name = "split_avg"  # e.g., "split_avg", "single"
rarity_func = ALGORITHMS[algo_name]


# -------------------------------
# Frequency + novelty helpers
# -------------------------------

def load_freq_db(path=FREQ_FILE):
    """Load frequency database into a dict."""
    if not os.path.exists(path):
        print("No frequency file found. Novelty scores will be 1.0 for all answers.")
        return {}
    with open(path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        return {row["answer"]: int(row["count"]) for row in reader}


def compute_novelty(word, freq_db):
    """Compute a novelty score (0–1): 1.0 = totally new, 0.0 = most common."""
    word = word.upper()
    if not freq_db:
        return 1.0
    if word not in freq_db:
        return 1.0

    count = freq_db[word]
    max_count = max(freq_db.values())
    min_count = min(freq_db.values())
    novelty = 1 - (count - min_count) / (max_count - min_count + 1e-6)
    return round(novelty, 3)


def compute_crosswordese(word, freq_db):
    """
    Compute 'crosswordese' — how overrepresented a word is in crosswords vs English.
    Formula: (crossword_freq / lang_freq)
    Then log-scaled and normalized to roughly 0–7 range for display.
    """
    word = word.upper()
    crossword_count = freq_db.get(word, 0)
    total_crossword = sum(freq_db.values()) if freq_db else 1

    crossword_freq = crossword_count / total_crossword
    lang_freq = 10 ** (zipf_frequency(word.lower(), "en") - 6)  # convert Zipf to absolute freq

    if lang_freq == 0:
        return 7.0  # Extremely crosswordese (rare in language)
    ratio = crossword_freq / lang_freq

    # Log scale: positive = overrepresented
    score = np.log10(ratio + 1e-12) + 6  # shift upward to avoid negatives
    return round(score, 3)


# -------------------------------
# Grid parsing
# -------------------------------

def get_across_words(grid):
    words = []
    for r, row in enumerate(grid):
        current = ""
        for c, ch in enumerate(row + ['.']):
            if ch != '.':
                current += ch
            elif len(current) > 1:
                words.append(((r, c - len(current)), 'across', current))
                current = ""
            else:
                current = ""
    return words


def get_down_words(grid):
    grid = np.array(grid)
    words = []
    for c in range(grid.shape[1]):
        current = ""
        for r in range(grid.shape[0] + 1):
            ch = grid[r, c] if r < grid.shape[0] else '.'
            if ch != '.':
                current += ch
            elif len(current) > 1:
                words.append(((r - len(current), c), 'down', current))
                current = ""
            else:
                current = ""
    return words


# -------------------------------
# Crossword analysis
# -------------------------------

def analyze_crossword(grid):
    freq_db = load_freq_db()
    across = get_across_words(grid)
    down = get_down_words(grid)
    all_words = across + down

    h, w = len(grid), len(grid[0])
    mask = np.array([[ch == '.' for ch in row] for row in grid])

    stretch_map = np.zeros((h, w)) * np.nan
    novelty_map = np.zeros((h, w)) * np.nan
    crosswordese_map = np.zeros((h, w)) * np.nan

    word_data = []

    for (r, c), direction, word in all_words:
        stretch = rarity_func(word)
        novelty = compute_novelty(word, freq_db)
        crosswordese = compute_crosswordese(word, freq_db)

        word_data.append({
            "word": word.upper(),
            "stretch": stretch,
            "novelty": novelty,
            "crosswordese": crosswordese
        })

        print(f"→ '{word.upper()}': stretch={stretch:.3f}, novelty={novelty:.3f}, crosswordese={crosswordese:.3f}")

        target_map = {
            "stretch": stretch_map,
            "novelty": novelty_map,
            "crosswordese": crosswordese_map
        }

        for i in range(len(word)):
            rr, cc = (r, c + i) if direction == "across" else (r + i, c)
            for key, m in target_map.items():
                val = locals()[key]
                if not np.isnan(m[rr, cc]):
                    m[rr, cc] = np.mean([m[rr, cc], val])
                else:
                    m[rr, cc] = val

    # Mask out black squares
    stretch_map[mask] = np.nan
    novelty_map[mask] = np.nan
    crosswordese_map[mask] = np.nan

    # Print summary
    print("\nTop 3 most novel answers:")
    for w in sorted(word_data, key=lambda x: -x["novelty"])[:3]:
        print(f"  {w['word']}: {w['novelty']}")

    hardest = max(word_data, key=lambda x: x["stretch"])
    print(f"\nHardest (stretch): {hardest['word']} ({hardest['stretch']:.3f})")

    most_crosswordese = max(word_data, key=lambda x: x["crosswordese"])
    print(f"Most crosswordese: {most_crosswordese['word']} ({most_crosswordese['crosswordese']:.3f})")

    # Ask if user wants to update frequency DB
    update_choice = input("\nUpdate NYT frequency database with this puzzle? (y/n): ").strip().lower()
    if update_choice == "y":
        update_freq_db([w["word"] for w in word_data])

    return stretch_map, novelty_map, crosswordese_map


# -------------------------------
# Visualization
# -------------------------------

def plot_crossword_heatmap(grid, data_map, title):
    plt.figure(figsize=(6, 6))
    ax = sns.heatmap(
        data_map,
        cmap="coolwarm",
        annot=False,
        fmt=".1f",
        square=True,
        linewidths=0.5,
        cbar_kws={"label": title},
    )
    plt.title(title)
    h, w = len(grid), len(grid[0])
    for r in range(h):
        for c in range(w):
            letter = grid[r][c]
            if letter != '.':
                ax.text(
                    c + 0.5, r + 0.5, letter,
                    color="black", ha="center", va="center",
                    fontsize=14, fontweight="bold"
                )
    plt.show()


# -------------------------------
# Run the analyzer
# -------------------------------

if __name__ == "__main__":
    grid = load_grid_from_json("NYT_2025-11-03.json")
    stretch_map, novelty_map, crosswordese_map = analyze_crossword(grid)

    plot_crossword_heatmap(grid, stretch_map, "Stretch (Rarity / Difficulty)")
    plot_crossword_heatmap(grid, novelty_map, "Novelty (NYT Uniqueness)")
    plot_crossword_heatmap(grid, crosswordese_map, "Crosswordese (Overrepresentation)")
