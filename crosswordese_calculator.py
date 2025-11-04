import pandas as pd
import numpy as np
from wordfreq_algorithms import ALGORITHMS

# -------------------------------
# CONFIG
# -------------------------------

DATA_FILE = "nyt_answer_freqs.csv"
ALGO_NAME = "split_avg"  # choose: split_avg, unsplit, split_penalty

# -------------------------------
# LOAD DATABASE
# -------------------------------

df = pd.read_csv(DATA_FILE)

# Make sure expected columns exist
if "answer" not in df.columns or "count" not in df.columns:
    raise ValueError("CSV must contain 'answer' and 'count' columns.")

# Normalize crossword frequencies
df["crossword_freq"] = df["count"] / df["count"].sum()

# Clean and normalize answers
df["answer"] = df["answer"].astype(str).str.strip()

# -------------------------------
# LANGUAGE RARITY / FREQUENCY
# -------------------------------

rarity_func = ALGORITHMS.get(ALGO_NAME, ALGORITHMS["split_avg"])

def rarity_to_freq(word):
    """
    Convert a rarity score (approx. 0-7 scale) back to an estimated
    language frequency for log-ratio comparison.
    """
    rarity = rarity_func(word)
    est_zipf = 7 - rarity
    # Convert from Zipf (log10 per million) to linear probability
    return 10 ** (est_zipf - 6)

df["lang_freq"] = df["answer"].apply(rarity_to_freq)
df["lang_freq"] = df["lang_freq"].clip(lower=1e-12)

# -------------------------------
# CROSSWORDESE SCORE
# -------------------------------

df["crosswordese"] = np.log10(df["crossword_freq"] / df["lang_freq"])
df["rank"] = df["crosswordese"].rank(ascending=False)

# -------------------------------
# OUTPUT
# -------------------------------

print(f"Using rarity algorithm: {ALGO_NAME}\n")
print(df.sort_values("crosswordese", ascending=False).head(20)[["answer", "crosswordese"]])

# Optional: save for later
df.to_csv(f"crosswordese_{ALGO_NAME}.csv", index=False)
