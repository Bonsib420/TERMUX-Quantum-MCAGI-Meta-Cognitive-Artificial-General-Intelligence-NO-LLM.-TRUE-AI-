"""
Web search wrapper - works with or without duckduckgo_search.
Falls back to simple requests-based search if DDGS not available.
"""

import logging
from typing import List, Dict, Optional

logger = logging.getLogger("quantum_ai")

# Try to import DDGS
DDGS_AVAILABLE = False
try:
    from duckduckgo_search import DDGS
    DDGS_AVAILABLE = True
except ImportError:
    try:
        from ddgs import DDGS
        DDGS_AVAILABLE = True
    except ImportError:
        pass


async def web_search(query: str, max_results: int = 5) -> List[Dict]:
    """
    Search the web for information.
    Uses DDGS if available, falls back to DuckDuckGo Instant Answer API.
    """
    
    if DDGS_AVAILABLE:
        try:
            with DDGS() as ddgs:
                results = list(ddgs.text(query, max_results=max_results))
                return [
                    {
                        "title": r.get("title", ""),
                        "body": r.get("body", ""),
                        "href": r.get("href", "")
                    }
                    for r in results
                ]
        except Exception as e:
            logger.warning(f"DDGS search failed: {e}")
    
    # Fallback to instant answer API
    try:
        import requests
        url = "https://api.duckduckgo.com/"
        params = {
            "q": query,
            "format": "json",
            "no_html": 1,
            "skip_disambig": 1
        }
        response = requests.get(url, params=params, timeout=10)
        data = response.json()
        
        results = []
        
        # Abstract
        if data.get("Abstract"):
            results.append({
                "title": data.get("Heading", query),
                "body": data["Abstract"],
                "href": data.get("AbstractURL", "")
            })
        
        # Related topics
        for topic in data.get("RelatedTopics", [])[:max_results]:
            if isinstance(topic, dict) and topic.get("Text"):
                results.append({
                    "title": topic.get("Text", "")[:50],
                    "body": topic.get("Text", ""),
                    "href": topic.get("FirstURL", "")
                })
        
        return results[:max_results]
        
    except Exception as e:
        logger.warning(f"Fallback search failed: {e}")
        return []


def search_sync(query: str, max_results: int = 5) -> List[Dict]:
    """Synchronous version of web search."""
    import asyncio
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    return loop.run_until_complete(web_search(query, max_results))


def is_ddgs_available() -> bool:
    """Check if DDGS is available."""
    return DDGS_AVAILABLE
