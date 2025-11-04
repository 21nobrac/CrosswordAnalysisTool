import requests
import json
from datetime import datetime, timedelta

HEADERS = {
    "User-Agent": "CrosswordAnalysisTool/1.0 (https://github.com/21nobrac/CrosswordAnalysisTool; carbonamarshall@gmail.com)"
}
    

def get_json(title: str):
    url = "https://en.wikipedia.org/w/api.php"
    params = {
        "action": "query",
        "titles": title,
        "format": "json"
    }
    response = requests.get(url, params=params, headers=HEADERS)
    response.raise_for_status()
    return response.json()

def get_canonical_title(title: str, lang: str = "en") -> str:
    """
    Check if a Wikipedia article exists and return its canonical title.
    Returns (exists, canonical_title).
    """
    url = f"https://{lang}.wikipedia.org/w/api.php"
    params = {
        "action": "query",
        "titles": title,
        "format": "json"
    }
    r = requests.get(url, params=params, headers=HEADERS)
    r.raise_for_status()
    data = r.json()
    pages = data["query"]["pages"]

    # The API returns a dict of pages keyed by ID.
    page = next(iter(pages.values()))
    if "missing" in page:
        return "None"
    return page["title"]  # Canonical title from Wikipedia

def get_views(title: str, days: int = 30, lang: str = "en") -> int:
    """
    Return total Wikipedia pageviews for the given title (canonical form recommended).
    """
    end_date = datetime.today()
    start_date = end_date - timedelta(days=days)
    safe_title = get_canonical_title(title).replace(" ", "_")

    url = (
        f"https://wikimedia.org/api/rest_v1/metrics/pageviews/per-article/"
        f"{lang}.wikipedia/all-access/all-agents/{safe_title}/daily/"
        f"{start_date.strftime('%Y%m%d')}/{end_date.strftime('%Y%m%d')}"
    )

    r = requests.get(url, headers=HEADERS)
    if r.status_code != 200:
        print(f"Error fetching views for '{title}': HTTP {r.status_code}")
        return 0

    data = r.json()
    items = data.get("items", [])
    return sum(item["views"] for item in items)

def contains_article(title: str):
    data = get_json(title)
    pages = data["query"]["pages"]
    # If the key is "-1", the page doesn’t exist
    return "-1" not in pages
