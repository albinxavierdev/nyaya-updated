"""Retriever wrapper that returns a placeholder node when retrieval is empty.

CondensePlusContextChatEngine uses CompactAndRefine, which never calls the LLM
when context_nodes is empty. This wrapper ensures we always have at least one
node so the user still gets an LLM response when the vector store has no docs.
"""
from typing import List

from llama_index.core.base.base_retriever import BaseRetriever
from llama_index.core.schema import NodeWithScore, TextNode
from llama_index.core.indices.query.schema import QueryBundle

_EMPTY_PLACEHOLDER_TEXT = (
    "No relevant documents found. Answer the user based on general knowledge."
)


class RetrieverWithEmptyFallback(BaseRetriever):
    """Wraps a retriever and returns one placeholder node when it would return none."""

    def __init__(self, retriever: BaseRetriever, **kwargs):
        super().__init__(**kwargs)
        self._retriever = retriever

    def _retrieve(self, query_bundle: QueryBundle) -> List[NodeWithScore]:
        nodes = self._retriever._retrieve(query_bundle)
        if not nodes:
            return [
                NodeWithScore(
                    node=TextNode(text=_EMPTY_PLACEHOLDER_TEXT),
                    score=0.0,
                )
            ]
        return nodes

    async def _aretrieve(self, query_bundle: QueryBundle) -> List[NodeWithScore]:
        nodes = await self._retriever._aretrieve(query_bundle)
        if not nodes:
            return [
                NodeWithScore(
                    node=TextNode(text=_EMPTY_PLACEHOLDER_TEXT),
                    score=0.0,
                )
            ]
        return nodes
