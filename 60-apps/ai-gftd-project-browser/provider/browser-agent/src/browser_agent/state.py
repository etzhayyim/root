"""LangGraph state for browser search graph."""

from __future__ import annotations

import operator
from typing import Annotated

from pydantic import BaseModel, Field


class SearchResult(BaseModel):
    url: str
    title: str
    snippet: str
    content: str = ''


class SparkSection(BaseModel):
    title: str
    content: str


class BrowserSearchState(BaseModel):
    query: str
    page_url: str = ''

    sub_queries: list[str] = Field(default_factory=list)
    search_results: Annotated[list[SearchResult], operator.add] = Field(default_factory=list)
    scraped_contents: Annotated[list[SearchResult], operator.add] = Field(default_factory=list)

    sections: list[SparkSection] = Field(default_factory=list)
    quality_score: float = 0.0
    iteration: int = 0

    # internal routing
    needs_more: bool = False
