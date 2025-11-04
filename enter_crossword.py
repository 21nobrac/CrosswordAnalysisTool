import json

def main():
    # Get publisher and date info
    publisher = input("Enter publisher name (e.g., NYT): ").strip()
    date = input("Enter date (e.g., 2024-02-11): ").strip()

    print("\nNow enter your crossword grid line by line.")
    print("Use '.' for black squares. Leave a blank line when done.\n")

    # Read grid lines until user enters a blank line
    grid_lines = []
    while True:
        line = input()
        if not line.strip():
            break
        grid_lines.append(line.strip())

    # Validate grid
    if not grid_lines:
        print("Error: No grid entered.")
        return

    # Calculate grid dimensions
    rows = len(grid_lines)
    cols = len(grid_lines[0])
    if any(len(line) != cols for line in grid_lines):
        print("Error: All lines must be the same length.")
        return

    # Flatten grid
    grid_flat = [c for line in grid_lines for c in line]

    # Build JSON structure
    crossword_data = {
        "publisher": publisher,
        "date": date,
        "size": {
            "rows": rows,
            "cols": cols
        },
        "grid": grid_flat
    }

    # Construct filename
    filename = f"{publisher}_{date}.json".replace(" ", "_")

    # Write to file
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(crossword_data, f, indent=2)

    print(f"\nCrossword saved to {filename}")

if __name__ == "__main__":
    main()
