import requests

def get_json(title: str):
    url = "https://en.wikipedia.org/w/api.php"
    params = {
        "action": "query",
        "titles": title,
        "format": "json"
    }
    headers = {
        "User-Agent": "CrosswordAnalysisTool/1.0 (https://github.com/21nobrac/CrosswordAnalysisTool; carbonamarshall@gmail.com)"
    }
    response = requests.get(url, params=params, headers=headers)
    response.raise_for_status()
    return response.json()

def contains_article(title: str):
    data = get_json(title)
    pages = data["query"]["pages"]
    # If the key is "-1", the page doesn’t exist
    return "-1" not in pages
