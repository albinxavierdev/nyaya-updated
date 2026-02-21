"""
Hybrid retriever: knowledge base (vector store) + web search.

Retrieves from both sources and merges results so the chat engine gets:
- Your indexed legal/docs content (high relevance when it matches).
- Fresh web results (factual, up-to-date) to reduce hallucination.

Order: KB nodes first (by score), then web nodes. The LLM sees a single
context block with clear source labels (metadata.source = "web" vs doc).

When an event_handler is provided, pushes a "Searched web for '...' (N results)"
event so it shows in the UI events list.
Env: ENABLE_WEB_SEARCH  Set to "false"/"0" to disable web search (default: "true").
"""
import logging
import os
from typing import List, Optional

from llama_index.core.base.base_retriever import BaseRetriever
from llama_index.core.schema import NodeWithScore
from llama_index.core.indices.query.schema import QueryBundle

from app.api.chat.engine.web_search import web_search_to_nodes

logger = logging.getLogger(__name__)

ENABLE_WEB_SEARCH = os.getenv("ENABLE_WEB_SEARCH", "true").lower() in ("true", "1", "yes")


class HybridRetriever(BaseRetriever):
    """
    Wraps an existing retriever and adds web search results to the context.

    When ENABLE_WEB_SEARCH is true, runs DuckDuckGo search for the query and
    appends results as additional nodes (with source=web in metadata).
    Optionally pushes a custom event (what was searched) when event_handler is set.
    """

    def __init__(
        self,
        retriever: BaseRetriever,
        enable_web_search: bool = None,
        event_handler=None,
        **kwargs,
    ):
        super().__init__(**kwargs)
        self._retriever = retriever
        self._enable_web = enable_web_search if enable_web_search is not None else ENABLE_WEB_SEARCH
        self._event_handler = event_handler

    def _retrieve(self, query_bundle: QueryBundle) -> List[NodeWithScore]:
        nodes = self._retriever._retrieve(query_bundle)
        if self._enable_web and query_bundle.query_str.strip():
            try:
                web_nodes = web_search_to_nodes(query_bundle.query_str)
                nodes = list(nodes) + web_nodes
                if self._event_handler and web_nodes:
                    q = query_bundle.query_str[:60] + ("..." if len(query_bundle.query_str) > 60 else "")
                    self._event_handler.push_custom_event(
                        f"Searched web for: \"{q}\" ({len(web_nodes)} results)"
                    )
            except Exception as e:
                logger.warning("Web search in hybrid retriever failed: %s", e)
        return nodes

    async def _aretrieve(self, query_bundle: QueryBundle) -> List[NodeWithScore]:
        nodes = await self._retriever._aretrieve(query_bundle)
        if self._enable_web and query_bundle.query_str.strip():
            try:
                web_nodes = web_search_to_nodes(query_bundle.query_str)
                nodes = list(nodes) + web_nodes
                if self._event_handler and web_nodes:
                    q = query_bundle.query_str[:60] + ("..." if len(query_bundle.query_str) > 60 else "")
                    self._event_handler.push_custom_event(
                        f"Searched web for: \"{q}\" ({len(web_nodes)} results)"
                    )
            except Exception as e:
                logger.warning("Web search in hybrid retriever failed: %s", e)
        return nodes
