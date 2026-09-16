"""
News/web search tool backed by the Serper API (https://serper.dev, has a
free tier). Used by data_gatherer (recent news for CompanyData) and
risk_analyst (searching for red flags, litigation, downgrades, etc.).

Kept as a thin, explicit wrapper rather than importing crewai_tools'
SerperDevTool directly so the description can be tailored per use case and
so there's one obvious place to swap in a different search provider later.
"""

import json
import os

import requests
from crewai.tools import tool

SERPER_URL = "https://google.serper.dev/search"


def _serper_search(query: str, num_results: int = 6) -> str:
    api_key = os.getenv("SERPER_API_KEY")
    if not api_key:
        return json.dumps(
            {"error": "SERPER_API_KEY not set. Add it to your .env file to enable search."}
        )

    try:
        resp = requests.post(
            SERPER_URL,
            headers={"X-API-KEY": api_key, "Content-Type": "application/json"},
            data=json.dumps({"q": query, "num": num_results}),
            timeout=15,
        )
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:  # noqa: BLE001
        return json.dumps({"error": f"Search failed for query '{query}': {e}"})

    results = []
    for item in data.get("organic", [])[:num_results]:
        results.append(
            {
                "headline": item.get("title"),
                "source": item.get("link"),
                "date": item.get("date", "unknown"),
                "summary": item.get("snippet"),
            }
        )
    return json.dumps({"query": query, "results": results}, default=str)


@tool("News Search")
def news_search_tool(query: str) -> str:
    """
    Search recent news and web results for a query — e.g. a company name
    plus 'earnings', 'lawsuit', 'downgrade', or 'risk' to surface relevant
    recent coverage.

    Args:
        query: The search query, e.g. 'Apple Inc recent news' or
            'Apple Inc antitrust lawsuit 2026'.

    Returns:
        A JSON string with a list of {headline, source, date, summary} items.
    """
    return _serper_search(query)
