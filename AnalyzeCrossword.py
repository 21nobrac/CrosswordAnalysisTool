from wordfreq import zipf_frequency
import numpy as np
from pprint import pprint

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
    """Returns a rarity score: lower = rarer"""
    freq = zipf_frequency(word.lower(), "en")
    # zipf_frequency: 1 = rare, 7 = very common
    return round(7 - freq, 3)  # invert so higher = rarer

def analyze_crossword(grid):
    across = get_across_words(grid)
    down = get_down_words(grid)
    all_words = across + down

    report = []
    for (r, c), direction, word in all_words:
        rarity = get_word_rarity(word)
        report.append({
            "word": word,
            "direction": direction,
            "pos": (r, c),
            "rarity": rarity
        })
    return report

report = analyze_crossword(grid)
pprint(report)
