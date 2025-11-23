import logging
import os
from llama_index.core.indices import VectorStoreIndex
from llama_index.core.settings import Settings
from app.api.chat.engine.vectordb import get_vector_store

# Conditionally import multi-provider functions
ENABLE_MULTI_PROVIDER = os.getenv("ENABLE_MULTI_PROVIDER", "false").lower() == "true"
if ENABLE_MULTI_PROVIDER:
    from app.multi_provider_settings import get_current_provider, get_available_providers
else:
    # Dummy functions for single-provider mode
    def get_current_provider():
        return os.getenv("MODEL_PROVIDER", "openai")
    
    def get_available_providers():
        return []


logger = logging.getLogger("uvicorn")

# Cache for provider-specific indices
_provider_indices = {}


def get_index(params=None):
    """Get or create index for the current provider."""
    current_provider = get_current_provider()
    logger.info(f"Getting index for provider: {current_provider}")
    
    # Check if we have a cached index for this provider
    if current_provider in _provider_indices:
        logger.info(f"Using cached index for provider: {current_provider}")
        return _provider_indices[current_provider]
    
    # Create new index for the current provider
    logger.info("Creating new index for current provider...")
    store = get_vector_store()
    
    # Create index with current provider's embedding model
    index = VectorStoreIndex.from_vector_store(
        store,
        embed_model=Settings.embed_model  # Use current provider's embedding model
    )
    
    # Cache the index for this provider
    _provider_indices[current_provider] = index
    logger.info(f"Created and cached index for provider: {current_provider}")
    
    return index


def clear_provider_cache(provider_id=None):
    """Clear cached indices for a specific provider or all providers."""
    if provider_id:
        if provider_id in _provider_indices:
            del _provider_indices[provider_id]
            logger.info(f"Cleared cache for provider: {provider_id}")
    else:
        _provider_indices.clear()
        logger.info("Cleared all provider caches")


def get_provider_index(provider_id):
    """Get index for a specific provider."""
    if provider_id in _provider_indices:
        return _provider_indices[provider_id]
    return None
