import logging
import os

from llama_index.core.indices import VectorStoreIndex
from llama_index.core.settings import Settings

from app.api.chat.engine.vectordb import get_vector_store

logger = logging.getLogger(__name__)

_index = None


def get_index(params=None):
    global _index
    if _index is not None:
        return _index
    store = get_vector_store()
    _index = VectorStoreIndex.from_vector_store(
        store,
        embed_model=Settings.embed_model,
    )
    return _index
