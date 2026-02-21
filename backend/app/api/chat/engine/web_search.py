"""
Web search for grounding answers in up-to-date, factual content.

Used alongside the knowledge-base retriever so the LLM gets:
1. Context from your indexed documents (Qdrant).
2. Context from the web (DuckDuckGo), reducing hallucination and filling gaps.

Results are returned as LlamaIndex nodes so they can be merged with vector
retrieval and passed to the chat engine as additional context.

Env (optional):
  WEB_SEARCH_MAX_RESULTS   Max number of web results to add (default: 5).
  WEB_SEARCH_SNIPPET_MAX_CHARS  Max chars per snippet (default: 500).
"""
import logging
import os
from typing import List

from llama_index.core.schema import NodeWithScore, TextNode

logger = logging.getLogger(__name__)

# Max web results to add to context (avoids token explosion)
WEB_SEARCH_MAX_RESULTS = int(os.getenv("WEB_SEARCH_MAX_RESULTS", "5"))
# Max chars per snippet to include
WEB_SEARCH_SNIPPET_MAX_CHARS = int(os.getenv("WEB_SEARCH_SNIPPET_MAX_CHARS", "500"))


def _run_duckduckgo(query: str) -> List[dict]:
    """Run DuckDuckGo text search. Returns list of {title, body, href}."""
    try:
        from duckduckgo_search import DDGS

        with DDGS() as ddgs:
            results = list(
                ddgs.text(
                    query,
                    region="wt-wt",
                    safesearch="moderate",
                    max_results=WEB_SEARCH_MAX_RESULTS,
                )
            )
        return [
            {
                "title": r.get("title", ""),
                "body": (r.get("body") or "")[:WEB_SEARCH_SNIPPET_MAX_CHARS],
                "href": r.get("href", ""),
            }
            for r in results
        ]
    except Exception as e:
        logger.warning("Web search failed: %s", e, exc_info=False)
        return []


def web_search_to_nodes(query: str) -> List[NodeWithScore]:
    """
    Run web search for `query` and return results as LlamaIndex NodeWithScore list.

    Used by the hybrid retriever to inject web context into the chat engine.
    Score is fixed (e.g. 0.7) so they are used as supplementary context;
    knowledge-base results typically have higher similarity scores.
    """
    raw = _run_duckduckgo(query)
    nodes: List[NodeWithScore] = []
    for i, r in enumerate(raw):
        title = (r.get("title") or "").strip()
        body = (r.get("body") or "").strip()
        href = (r.get("href") or "").strip()
        if not body and not title:
            continue
        text = f"{title}\n{body}".strip()
        if href:
            text += f"\nSource: {href}"
        node = TextNode(
            text=text,
            metadata={
                "source": "web",
                "url": href,
                "URL": href,  # for SourceNodes.get_url_from_metadata
                "title": title,
            },
        )
        # Use a fixed score so web results don't override strong KB hits
        nodes.append(NodeWithScore(node=node, score=0.7 - (i * 0.05)))
    return nodes
