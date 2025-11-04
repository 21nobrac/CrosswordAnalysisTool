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
import math

FREQ_FILE = "nyt_answer_freqs.csv"

# Select algorithm by name
algo_name = "split_wiki"  # e.g., "split_avg", "single"
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
    """Compute a novelty score (0-1): 1.0 = totally new, 0.0 = most common."""
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

def compute_novelty_log(word, freq_db, base=5, unseen_score=1.0, round_digits=3):
    """
    Novelty in [0,1] using a log scale. 1.0 = totally new, 0.0 = most common.
    - base: log base (default 5)
    - unseen_score: returned for words not in freq_db (default 1.0)
    """
    word = word.upper()

    if not freq_db:
        return float(round(unseen_score, round_digits))
    if word not in freq_db:
        return float(round(unseen_score, round_digits))

    # counts with +1 smoothing to allow log(0) avoidance
    counts = list(freq_db.values())
    min_c = min(counts)
    max_c = max(counts)

    # add 1 to everything to avoid log(0)
    def log_x(x):
        if base == math.e:
            return math.log(x + 1)
        return math.log(x + 1, base)

    l_min = log_x(min_c)
    l_max = log_x(max_c)
    if l_max == l_min:
        # all counts equal -> choose fallback (here we treat all known words as non-novel)
        return float(round(0.0, round_digits))

    l_word = log_x(freq_db[word])
    normalized = (l_word - l_min) / (l_max - l_min)
    novelty = 1.0 - normalized
    return float(round(novelty, round_digits))

def compute_crosswordese(stretch, novelty, round_digits=3):
    normalized_stretch = min(stretch / 7, 1)
    return round((normalized_stretch * (1 - novelty)), round_digits)


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
        novelty = compute_novelty_log(word, freq_db)
        crosswordese = compute_crosswordese(stretch, novelty)

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
    print("\nTop 5 most novel answers:")
    for w in sorted(word_data, key=lambda x: -x["novelty"])[:5]:
        print(f"  {w['word']}: {w['novelty']}")

    print("\nTop 5 hardest answers:")
    for w in sorted(word_data, key=lambda x: -x["stretch"])[:5]:
        print(f"  {w['word']}: {w['stretch']}")

    print("\nTop 5 most crosswordese answers:")
    for w in sorted(word_data, key=lambda x: -x["crosswordese"])[:5]:
        print(f"  {w['word']}: {w['crosswordese']}")

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
