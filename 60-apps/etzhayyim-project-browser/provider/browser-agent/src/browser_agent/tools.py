"""Web search and page fetch tools."""

from __future__ import annotations

import os
import re

import httpx
from bs4 import BeautifulSoup

# SearXNG meta search (internal, no API key required)
SEARXNG_URL = os.environ.get('SEARXNG_URL', 'https://searxng.etzhayyim.com')
CRAWL_ENGINE_URL = os.environ.get('CRAWL_ENGINE_URL', 'https://crawl-engine.etzhayyim.com')
BROWSERLESS_URL = os.environ.get('BROWSERLESS_URL', 'https://browserless.etzhayyim.com')

MAX_CONTENT_CHARS = 4000


async def web_search(query: str, max_results: int = 5) -> list[dict]:
    """Search via internal SearXNG meta search aggregator."""
    return await _searxng_search(query, max_results)


async def _searxng_search(query: str, max_results: int) -> list[dict]:
    """GET /search?format=json from internal SearXNG instance."""
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            r = await client.get(
                f'{SEARXNG_URL}/search',
                params={
                    'q': query,
                    'format': 'json',
                    'categories': 'general',
                    'engines': 'bing,duckduckgo,brave',
                },
                headers={'User-Agent': 'etzhayyim-browser-agent/1.0'},
            )
            if r.status_code != 200:
                return []
            data = r.json()
            results = []
            for item in data.get('results', [])[:max_results]:
                url = item.get('url', '')
                if url:
                    results.append({
                        'url': url,
                        'title': item.get('title', ''),
                        'snippet': item.get('content', ''),
                    })
            return results
    except Exception:
        return []


async def fetch_page(url: str) -> str:
    """Fetch page text via crawl-engine or direct HTTP."""
    # prefer crawl-engine for JS-heavy pages
    try:
        async with httpx.AsyncClient(timeout=20) as client:
            r = await client.post(
                f'{CRAWL_ENGINE_URL}/fetch',
                json={'url': url, 'fetchMode': 'static'}
            )
            if r.status_code == 200:
                data = r.json()
                return _truncate(data.get('content', '') or data.get('text', ''))
    except Exception:
        pass

    # direct fallback
    try:
        async with httpx.AsyncClient(timeout=15, follow_redirects=True) as client:
            r = await client.get(url, headers={'User-Agent': 'etzhayyim-browser-agent/1.0'})
            soup = BeautifulSoup(r.text, 'html.parser')
            for tag in soup(['script', 'style', 'nav', 'footer', 'aside']):
                tag.decompose()
            return _truncate(soup.get_text(separator='\n', strip=True))
    except Exception:
        return ''


def _truncate(text: str) -> str:
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text[:MAX_CONTENT_CHARS]
