#!/usr/bin/env python3
"""
web_search.py — keyless internet search for the response pipeline.

Sources (no API keys required):
  1. Wikipedia REST API   — primary, structured, high-quality summaries
  2. Wikipedia opensearch — title suggestions when summary fails
  3. DuckDuckGo HTML      — fallback for non-encyclopedic queries

Public surface:
  search(query, max_results=3)         -> List[SearchHit]
  is_question(text)                    -> bool       (auto-trigger heuristic)
  has_explicit_search_token(text)      -> bool       (looks for "!search ")
  strip_search_token(text)             -> str        (removes "!search " prefix)

Each SearchHit: {
  "title":   str,
  "snippet": str,        # plain-text, ready to feed into the stylizer
  "source":  "wikipedia" | "duckduckgo",
  "url":     str,
  "score":   float,      # rough relevance, higher is better
}
"""

from __future__ import annotations

import json
import re
import urllib.parse
import urllib.request
from html import unescape
from typing import Dict, List, Optional

USER_AGENT = "QuantumMCAGI/1.0 (+research; pipeline=v2)"
TIMEOUT = 6.0

# ---------------------------------------------------------------------------
# Trigger detection
# ---------------------------------------------------------------------------

_QUESTION_WORDS = {
    "who", "what", "when", "where", "why", "how", "which", "whose",
    "can", "could", "would", "should", "is", "are", "was", "were",
    "do", "does", "did", "will", "tell", "explain", "define",
}


def has_explicit_search_token(text: str) -> bool:
    return text.strip().lower().startswith("!search ") or text.strip().lower() == "!search"


def strip_search_token(text: str) -> str:
    s = text.strip()
    if s.lower().startswith("!search "):
        return s[8:].strip()
    return s


def is_question(text: str) -> bool:
    s = text.strip()
    if not s:
        return False
    if s.endswith("?"):
        return True
    first = s.split(maxsplit=1)[0].lower().rstrip(",.;:")
    return first in _QUESTION_WORDS


# ---------------------------------------------------------------------------
# HTTP helpers
# ---------------------------------------------------------------------------

def _http_get(url: str, *, headers: Optional[Dict[str, str]] = None) -> Optional[bytes]:
    req_headers = {"User-Agent": USER_AGENT, "Accept": "*/*"}
    if headers:
        req_headers.update(headers)
    req = urllib.request.Request(url, headers=req_headers)
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            return resp.read()
    except Exception:
        return None


def _strip_html(html: str) -> str:
    text = re.sub(r"<script[^>]*>.*?</script>", " ", html, flags=re.S | re.I)
    text = re.sub(r"<style[^>]*>.*?</style>", " ", text, flags=re.S | re.I)
    text = re.sub(r"<[^>]+>", " ", text)
    text = unescape(text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


# ---------------------------------------------------------------------------
# Wikipedia
# ---------------------------------------------------------------------------

def _wiki_summary(title: str) -> Optional[Dict]:
    safe = urllib.parse.quote(title.replace(" ", "_"), safe="")
    url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{safe}"
    raw = _http_get(url)
    if not raw:
        return None
    try:
        data = json.loads(raw.decode("utf-8", errors="replace"))
    except json.JSONDecodeError:
        return None
    extract = (data.get("extract") or "").strip()
    if not extract:
        return None
    return {
        "title": data.get("title") or title,
        "snippet": extract,
        "source": "wikipedia",
        "url": (data.get("content_urls") or {}).get("desktop", {}).get("page", f"https://en.wikipedia.org/wiki/{safe}"),
        "score": 0.9,
    }


def _wiki_opensearch(query: str, limit: int = 5) -> List[str]:
    params = urllib.parse.urlencode({
        "action": "opensearch",
        "search": query,
        "limit": str(limit),
        "namespace": "0",
        "format": "json",
    })
    url = f"https://en.wikipedia.org/w/api.php?{params}"
    raw = _http_get(url)
    if not raw:
        return []
    try:
        data = json.loads(raw.decode("utf-8", errors="replace"))
    except json.JSONDecodeError:
        return []
    if isinstance(data, list) and len(data) >= 2 and isinstance(data[1], list):
        return [t for t in data[1] if isinstance(t, str)]
    return []


def _search_wikipedia(query: str, max_results: int) -> List[Dict]:
    hits: List[Dict] = []
    direct = _wiki_summary(query)
    if direct:
        hits.append(direct)
    if len(hits) >= max_results:
        return hits[:max_results]
    for title in _wiki_opensearch(query, limit=max_results + 2):
        if any(h["title"].lower() == title.lower() for h in hits):
            continue
        s = _wiki_summary(title)
        if s:
            s["score"] = max(0.4, s["score"] - 0.1 * len(hits))
            hits.append(s)
        if len(hits) >= max_results:
            break
    return hits[:max_results]


# ---------------------------------------------------------------------------
# DuckDuckGo (HTML fallback, no key)
# ---------------------------------------------------------------------------

_DDG_RESULT_RE = re.compile(
    r'<a[^>]+class="[^"]*result__a[^"]*"[^>]+href="([^"]+)"[^>]*>(.*?)</a>'
    r'.*?<a[^>]+class="[^"]*result__snippet[^"]*"[^>]*>(.*?)</a>',
    re.S | re.I,
)


def _search_duckduckgo(query: str, max_results: int) -> List[Dict]:
    url = "https://html.duckduckgo.com/html/?" + urllib.parse.urlencode({"q": query})
    raw = _http_get(url, headers={"Accept": "text/html"})
    if not raw:
        return []
    html = raw.decode("utf-8", errors="replace")
    out: List[Dict] = []
    for m in _DDG_RESULT_RE.finditer(html):
        href, title_html, snippet_html = m.groups()
        title = _strip_html(title_html)
        snippet = _strip_html(snippet_html)
        if not title or not snippet:
            continue
        real_url = href
        if href.startswith("//duckduckgo.com/l/"):
            qs = urllib.parse.urlparse(href).query
            params = urllib.parse.parse_qs(qs)
            if "uddg" in params:
                real_url = urllib.parse.unquote(params["uddg"][0])
        out.append({
            "title": title,
            "snippet": snippet,
            "source": "duckduckgo",
            "url": real_url,
            "score": max(0.3, 0.7 - 0.05 * len(out)),
        })
        if len(out) >= max_results:
            break
    return out


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

def search(query: str, max_results: int = 3) -> List[Dict]:
    query = (query or "").strip()
    if not query:
        return []
    hits = _search_wikipedia(query, max_results)
    if len(hits) < max_results:
        ddg = _search_duckduckgo(query, max_results - len(hits))
        seen_titles = {h["title"].lower() for h in hits}
        for h in ddg:
            if h["title"].lower() not in seen_titles:
                hits.append(h)
                if len(hits) >= max_results:
                    break
    return hits


if __name__ == "__main__":
    import sys
    q = " ".join(sys.argv[1:]) or "photosynthesis"
    for h in search(q):
        print(f"[{h['source']:10}] {h['title']}")
        print(f"   {h['snippet'][:160]}")
        print(f"   {h['url']}")
        print()
