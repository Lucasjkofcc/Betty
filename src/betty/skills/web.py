from ddgs import DDGS


def search_web(query: str, max_results: int = 5):
    results = DDGS().text(
        query,
        max_results=max_results,
    )

    return [
        {
            "title": result["title"],
            "url": result["href"],
            "snippet": result["body"],
        }
        for result in results
    ]
