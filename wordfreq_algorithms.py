# wordfreq_algorithms.py
from wordfreq import zipf_frequency
from wikipedia_query import contains_article
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
    split_freq = (
        float(np.mean([zipf_frequency(w, "en") for w in split_tokens]))
        if len(split_tokens) > 1
        else 0.0
    )

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
# Alternate algorithms
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
    split_freq = (
        float(np.mean([zipf_frequency(w, "en") for w in split_tokens]))
        if len(split_tokens) > 1
        else 0.0
    )

    best_freq = max(unsplit_freq, split_freq - 0.2)
    rarity = round(7 - best_freq, 3)

    if verbose:
        print(f"'{word.upper()}' → split as {split_tokens} (penalized), rarity {rarity}")

    return rarity

def rarity_split_wikipedia(word: str, verbose=False) -> float:
    """
    Returns a rarity score (higher = rarer) using a hybrid single/split model,
    with weighting based on Wikipedia presence.

    - Uses wordfreq.zipf_frequency for the base word.
    - If splitting (via wordninja) yields multiple tokens, uses average freq.
    - Checks Wikipedia presence for both the unsplit and the split form.
      * If an article exists, the term is treated as more common (freq + wiki_weight).
      * If not, treated as slightly rarer (freq - wiki_weight).
    - Chooses whichever (unsplit vs split) gives the higher adjusted frequency.
    """
    wiki_weight = 0.2
    word = word.lower().strip()

    # --- Base frequencies ---
    unsplit_freq = zipf_frequency(word, "en")
    split_tokens = wnj.split(word)
    split_freq = (
        float(np.mean([zipf_frequency(w, "en") for w in split_tokens]))
        if len(split_tokens) > 1
        else 0.0
    )

    # --- Wikipedia lookups ---
    split_phrase = " ".join(split_tokens) if len(split_tokens) > 1 else ""
    has_unsplit_article = contains_article(word)
    has_split_article = contains_article(split_phrase) if split_phrase else False

    # --- Apply Wikipedia weighting ---
    if has_unsplit_article:
        unsplit_freq *= 1 + wiki_weight
    else:
        unsplit_freq *= 1 - wiki_weight

    if len(split_tokens) > 1:
        if has_split_article:
            split_freq *= 1 + wiki_weight
        else:
            split_freq *= 1 - wiki_weight

    # --- Determine which path to use ---
    best_freq = max(unsplit_freq, split_freq)
    used_split = (best_freq == split_freq) and (len(split_tokens) > 1)

    rarity = round(7 - best_freq, 3)

    # --- Verbose output ---
    if verbose:
        if used_split:
            print(
                f"'{word.upper()}' → split as {split_tokens}, "
                f"Wikipedia={'found' if has_split_article else 'not found'}, "
                f"rarity={rarity}"
            )
        else:
            print(
                f"'{word.upper()}' → treated as single word, "
                f"Wikipedia={'found' if has_unsplit_article else 'not found'}, "
                f"rarity={rarity}"
            )

    return rarity

# -------------------------------
# Algorithm registry
# -------------------------------

ALGORITHMS = {
    "split_avg": rarity_split_average,
    "unsplit": rarity_unsplit_only,
    "split_penalty": rarity_split_penalty,
    "split_wiki": rarity_split_wikipedia,
}
