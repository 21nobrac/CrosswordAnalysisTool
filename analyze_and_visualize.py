from parse_crossword import load_grid_from_json
from wordfreq import zipf_frequency
from update_freq_db import update_freq_db
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import wordninja as wnj
import csv
import os

FREQ_FILE = "nyt_answer_freqs_1976_2012.csv"

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
    """
    Compute a novelty score (0–1) for a crossword answer.
      1.0 = totally new
      0.0 = among the most common
    """
    word = word.upper()
    if not freq_db:
        return 1.0

    if word not in freq_db:
        return 1.0

    # normalize based on rank among top counts
    count = freq_db[word]
    max_count = max(freq_db.values())
    min_count = min(freq_db.values())
    novelty = 1 - (count - min_count) / (max_count - min_count + 1e-6)
    return round(novelty, 3)

# -------------------------------
# Word rarity helper
# -------------------------------

def get_word_rarity(word):
    """Returns a rarity score from English frequency (higher = rarer)."""
    word = word.lower()

    unsplitFreq = zipf_frequency(word, "en")
    splitTokens = wnj.split(word)
    if len(splitTokens) > 1:
        splitFreq = np.mean([zipf_frequency(w, "en") for w in splitTokens])
    else:
        splitFreq = 0

    bestFreq = max(unsplitFreq, splitFreq)
    used_split = bestFreq == splitFreq and len(splitTokens) > 1
    rarity = round(7 - bestFreq, 3)

    if used_split:
        print(f"'{word.upper()}' → split as {splitTokens}, using split average ({rarity})")
    else:
        print(f"'{word.upper()}' → treated as single word ({rarity})")

    return rarity

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
    across_map = np.zeros((h, w))
    down_map = np.zeros((h, w))
    mask = np.array([[ch == '.' for ch in row] for row in grid])

    for (r, c), direction, word in all_words:
        rarity = get_word_rarity(word)
        novelty = compute_novelty(word, freq_db)
        combined_score = np.mean([rarity, novelty * 7])  # normalize novelty to same scale

        print(f"→ '{word.upper()}': novelty {novelty}, combined {round(combined_score,3)}")

        if direction == 'across':
            for i in range(len(word)):
                across_map[r, c + i] = combined_score
        else:
            for i in range(len(word)):
                down_map[r + i, c] = combined_score

    combined = np.zeros((h, w))
    for r in range(h):
        for c in range(w):
            vals = [v for v in [across_map[r, c], down_map[r, c]] if v > 0]
            combined[r, c] = np.mean(vals) if vals else np.nan

    combined[mask] = np.nan

    # Ask if user wants to update frequency DB
    update_choice = input("\nUpdate NYT frequency database with this puzzle? (y/n): ").strip().lower()
    if update_choice == "y":
        update_freq_db([w for (_, _, w) in all_words])

    return combined

# -------------------------------
# Visualization
# -------------------------------

def plot_crossword_heatmap(grid, difficulty_map):
    plt.figure(figsize=(6, 6))
    ax = sns.heatmap(
        difficulty_map,
        cmap="magma_r",
        annot=False,
        fmt=".1f",
        square=True,
        linewidths=0.5,
        cbar_kws={"label": "Novelty / Difficulty"},
    )
    plt.title("Crossword Novelty & Difficulty Heatmap")

    h, w = len(grid), len(grid[0])
    for r in range(h):
        for c in range(w):
            letter = grid[r][c]
            if letter != '.':
                ax.text(
                    c + 0.5, r + 0.5, letter,
                    color="grey", ha="center", va="center",
                    fontsize=14, fontweight="bold"
                )
    plt.show()

# -------------------------------
# Run the analyzer
# -------------------------------

if __name__ == "__main__":
    grid = load_grid_from_json("02.json")
    difficulty_map = analyze_crossword(grid)
    plot_crossword_heatmap(grid, difficulty_map)
