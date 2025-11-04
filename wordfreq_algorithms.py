# wordfreq_algorithms.py
from wordfreq import zipf_frequency
import numpy as np
import wordninja as wnj

# -------------------------------
# Base / reference algorithm
# -------------------------------

def rarity_split_average(word: str, verbose=False) -> float:
    """
    Returns a rarity score (higher = rarer) using a hybrid single/split model.
    - Uses wordfreq.zipf_frequency for the base word.
    - If splitting (via wordninja) yields multiple tokens, uses average freq.
    """
    word = word.lower().strip()

    unsplit_freq = zipf_frequency(word, "en")
    split_tokens = wnj.split(word)
    split_freq = np.mean([zipf_frequency(w, "en") for w in split_tokens]) if len(split_tokens) > 1 else 0

    best_freq = max(unsplit_freq, split_freq)
    used_split = (best_freq == split_freq) and (len(split_tokens) > 1)
    rarity = round(7 - best_freq, 3)

    if verbose:
        if used_split:
            print(f"'{word.upper()}' → split as {split_tokens}, using split average ({rarity})")
        else:
            print(f"'{word.upper()}' → treated as single word ({rarity})")

    return rarity

# -------------------------------
# Alternate algorithms (examples)
# -------------------------------

def rarity_unsplit_only(word: str, verbose=False) -> float:
    """Simpler version: just 7 - zipf_frequency(word)."""
    rarity = round(7 - zipf_frequency(word.lower(), "en"), 3)
    if verbose:
        print(f"'{word.upper()}' → unsplit rarity {rarity}")
    return rarity

def rarity_split_penalty(word: str, verbose=False) -> float:
    """
    Penalizes phrases slightly (split avg - 0.2) so single words dominate.
    """
    word = word.lower().strip()
    unsplit_freq = zipf_frequency(word, "en")
    split_tokens = wnj.split(word)
    split_freq = np.mean([zipf_frequency(w, "en") for w in split_tokens]) if len(split_tokens) > 1 else 0

    best_freq = max(unsplit_freq, split_freq - 0.2)
    rarity = round(7 - best_freq, 3)

    if verbose:
        print(f"'{word.upper()}' → split as {split_tokens} (penalized), rarity {rarity}")

    return rarity

# -------------------------------
# Algorithm registry
# -------------------------------

ALGORITHMS = {
    "split_avg": rarity_split_average,
    "unsplit": rarity_unsplit_only,
    "split_penalty": rarity_split_penalty,
}
