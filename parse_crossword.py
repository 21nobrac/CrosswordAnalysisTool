import json

def load_grid_from_json(path):
    """Load crossword grid as a 2D list of characters from NYT-style JSON."""
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    rows, cols = data["size"]["rows"], data["size"]["cols"]
    flat = data["grid"]
    grid_2d = [flat[r * cols:(r + 1) * cols] for r in range(rows)]
    return grid_2d
