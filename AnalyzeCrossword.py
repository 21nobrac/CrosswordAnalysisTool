from wordfreq import zipf_frequency
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

# Example grid from Feb 11, 2024 NYT mini
# '.' means black square
grid = [
    list("..CBS"),
    list("USHER"),
    list("BAITS"),
    list("EVES."),
    list("REF..")
]

def get_across_words(grid):
    words = []
    for r, row in enumerate(grid):
        current = ""
        for c, ch in enumerate(row + ['.']):  # sentinel
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
        for r in range(grid.shape[0] + 1):  # sentinel
            ch = grid[r, c] if r < grid.shape[0] else '.'
            if ch != '.':
                current += ch
            elif len(current) > 1:
                words.append(((r - len(current), c), 'down', current))
                current = ""
            else:
                current = ""
    return words

def get_word_rarity(word):
    """Returns a rarity score: higher = rarer"""
    freq = zipf_frequency(word.lower(), "en")
    return round(7 - freq, 3)

def analyze_crossword(grid):
    across = get_across_words(grid)
    down = get_down_words(grid)
    all_words = across + down

    # Map each cell -> across/down word rarity
    h, w = len(grid), len(grid[0])
    across_map = np.zeros((h, w))
    down_map = np.zeros((h, w))
    mask = np.array([[ch == '.' for ch in row] for row in grid])

    for (r, c), direction, word in all_words:
        rarity = get_word_rarity(word)
        if direction == 'across':
            for i in range(len(word)):
                across_map[r, c + i] = rarity
        else:
            for i in range(len(word)):
                down_map[r + i, c] = rarity

    # Average across/down where both exist
    combined = np.zeros((h, w))
    for r in range(h):
        for c in range(w):
            vals = [v for v in [across_map[r, c], down_map[r, c]] if v > 0]
            combined[r, c] = np.mean(vals) if vals else np.nan

    # Apply mask (make black squares NaN)
    combined[mask] = np.nan

    return combined

def plot_crossword_heatmap(grid, difficulty_map):
    plt.figure(figsize=(6, 6))
    ax = sns.heatmap(
        difficulty_map,
        cmap="magma_r",
        annot=False,
        fmt=".1f",
        square=True,
        linewidths=0.5,
        cbar_kws={"label": "Stretch / Difficulty"},
    )
    plt.title("Crossword Difficulty Heatmap")

    # Overlay the letters
    h, w = len(grid), len(grid[0])
    for r in range(h):
        for c in range(w):
            letter = grid[r][c]
            if letter != '.':
                # Adjust x,y because we transposed in the heatmap
                ax.text(
                    c + 0.5,  # x position
                    r + 0.5,  # y position
                    letter,
                    color="grey",
                    ha="center",
                    va="center",
                    fontsize=14,
                    fontweight="bold",
                )

    plt.show()

# Run analysis and visualize
difficulty_map = analyze_crossword(grid)
plot_crossword_heatmap(grid, difficulty_map)
