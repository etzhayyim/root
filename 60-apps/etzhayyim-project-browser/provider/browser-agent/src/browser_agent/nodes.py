"""LangGraph node implementations."""

from __future__ import annotations

import asyncio
import json
import os

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

from .state import BrowserSearchState, SearchResult, SparkSection
from .tools import fetch_page, web_search

LLM_BASE_URL = os.environ.get('LLM_BASE_URL', 'https://openrouter.ai/api/v1')
LLM_API_KEY = os.environ.get('LLM_API_KEY', os.environ.get('OPENROUTER_API_KEY', ''))
LLM_MODEL = os.environ.get('LLM_MODEL', 'google/gemma-3-27b-it')
MAX_SEARCH_RESULTS = 8
MAX_SCRAPE_URLS = 6
MAX_ITERATIONS = 2
QUALITY_THRESHOLD = 0.75


def _llm() -> ChatOpenAI:
    return ChatOpenAI(
        base_url=LLM_BASE_URL,
        api_key=LLM_API_KEY,
        model=LLM_MODEL,
        temperature=0.2,
    )


async def plan_queries(state: BrowserSearchState) -> dict:
    """Decompose the user query into 2-4 targeted sub-queries."""
    system = (
        "You decompose a user query into 2-4 distinct web search sub-queries that together "
        "cover the topic comprehensively. Return a JSON array of strings only."
    )
    context = f'\nCurrent page: {state.page_url}' if state.page_url else ''
    prompt = f'Query: {state.query}{context}\n\nReturn JSON array of 2-4 sub-queries:'

    llm = _llm()
    msg = await llm.ainvoke([SystemMessage(content=system), HumanMessage(content=prompt)])
    text = msg.content.strip()

    try:
        # extract JSON array from response
        start = text.index('[')
        end = text.rindex(']') + 1
        sub_queries: list[str] = json.loads(text[start:end])
    except (ValueError, json.JSONDecodeError):
        sub_queries = [state.query]

    return {'sub_queries': sub_queries[:4], 'iteration': state.iteration + 1}


async def search_web(state: BrowserSearchState) -> dict:
    """Run parallel web searches for all sub-queries."""
    tasks = [web_search(q, max_results=3) for q in state.sub_queries]
    results_nested = await asyncio.gather(*tasks, return_exceptions=True)

    seen_urls: set[str] = {r.url for r in state.search_results}
    new_results: list[SearchResult] = []

    for batch in results_nested:
        if isinstance(batch, Exception):
            continue
        for item in batch:
            url = item.get('url', '')
            if url and url not in seen_urls:
                seen_urls.add(url)
                new_results.append(SearchResult(
                    url=url,
                    title=item.get('title', ''),
                    snippet=item.get('snippet', '')
                ))

    return {'search_results': new_results[:MAX_SEARCH_RESULTS]}


async def scrape_pages(state: BrowserSearchState) -> dict:
    """Fetch full content for top search results."""
    already_scraped = {r.url for r in state.scraped_contents}
    to_scrape = [
        r for r in state.search_results
        if r.url not in already_scraped
    ][:MAX_SCRAPE_URLS]

    tasks = [fetch_page(r.url) for r in to_scrape]
    raw_contents: list[str | BaseException] = await asyncio.gather(*tasks, return_exceptions=True)  # type: ignore[assignment]

    enriched: list[SearchResult] = []
    for result, content in zip(to_scrape, raw_contents):  # type: ignore[union-attr]
        text = result.snippet if isinstance(content, BaseException) else str(content)
        enriched.append(SearchResult(
            url=result.url,
            title=result.title,
            snippet=result.snippet,
            content=text[:4000]
        ))

    return {'scraped_contents': enriched}


async def synthesize(state: BrowserSearchState) -> dict:
    """Synthesize scraped content into a structured Sparkpage."""
    sources_text = '\n\n'.join(
        f'[{i+1}] {r.title}\nURL: {r.url}\n{r.content or r.snippet}'
        for i, r in enumerate(state.scraped_contents[:MAX_SCRAPE_URLS])
    )

    system = (
        "You synthesize web research into a well-structured, informative page (Sparkpage). "
        "Return a JSON array of {\"title\": string, \"content\": string} sections. "
        "Include 3-5 sections. Be comprehensive but concise. Cite sources inline as [1], [2], etc."
    )

    prompt = (
        f'User query: {state.query}\n\n'
        f'Source materials:\n{sources_text}\n\n'
        'Return JSON array of sections:'
    )

    llm = _llm()
    msg = await llm.ainvoke([SystemMessage(content=system), HumanMessage(content=prompt)])
    text = msg.content.strip()

    sections: list[SparkSection] = []
    try:
        start = text.index('[')
        end = text.rindex(']') + 1
        raw: list[dict] = json.loads(text[start:end])
        sections = [SparkSection(title=s.get('title', ''), content=s.get('content', '')) for s in raw]
    except (ValueError, json.JSONDecodeError):
        sections = [SparkSection(title='Summary', content=text)]

    return {'sections': sections}


async def quality_check(state: BrowserSearchState) -> dict:
    """Score synthesis quality; decide if re-search is needed."""
    if state.iteration >= MAX_ITERATIONS:
        return {'quality_score': 1.0, 'needs_more': False}

    total_content = sum(len(r.content) for r in state.scraped_contents)
    section_count = len(state.sections)

    # heuristic: enough content + enough sections = good quality
    score = min(1.0, (total_content / 8000) * 0.6 + (section_count / 4) * 0.4)
    needs_more = score < QUALITY_THRESHOLD and state.iteration < MAX_ITERATIONS

    return {'quality_score': score, 'needs_more': needs_more}
