import os
import qdrant_client
from llama_index.vector_stores.qdrant import QdrantVectorStore


def get_vector_store(collection_name=None):
    """
    Get Qdrant vector store for a specific collection
    
    Args:
        collection_name: Name of the collection (defaults to env var or 'nyayantar')
    
    Returns:
        QdrantVectorStore instance
    """
    if collection_name is None:
        collection_name = os.getenv("QDRANT_COLLECTION", "nyayantar")
    
    QDRANT_URL = os.getenv("QDRANT_URL")
    QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")
    
    if not collection_name or not QDRANT_URL:
        raise ValueError(
            "Please set QDRANT_COLLECTION, QDRANT_URL"
            " to your environment variables or config them in the .env file"
        )
    
    if QDRANT_API_KEY:
        # creating a qdrant client instance
        client = qdrant_client.QdrantClient(
            url=QDRANT_URL,
            api_key=QDRANT_API_KEY,
        )

        aclient = qdrant_client.AsyncQdrantClient(
            url=QDRANT_URL,
            api_key=QDRANT_API_KEY,
        )

        store = QdrantVectorStore(
            client=client, aclient=aclient, collection_name=collection_name
        )
    else:
        client = qdrant_client.QdrantClient(
            url=QDRANT_URL,
        )

        aclient = qdrant_client.AsyncQdrantClient(
            url=QDRANT_URL,
        )

        store = QdrantVectorStore(
            client=client, aclient=aclient, collection_name=collection_name
        )
    return store


def get_dual_vector_stores():
    """
    Get both legal and general Qdrant vector stores for hybrid retrieval
    
    Returns:
        Tuple of (legal_store, general_store)
    """
    legal_store = get_vector_store("nyayantar_legal")
    general_store = get_vector_store("nyayantar_general")
    return legal_store, general_store
