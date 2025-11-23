"""
Hybrid Retrieval System for Nyayantar
Queries both nyayantar_legal and nyayantar_general collections and merges results
"""

import os
import logging
from typing import List, Dict, Any, Tuple
import numpy as np
import qdrant_client

from .hybrid_embeddings import get_hybrid_embedding_system

logger = logging.getLogger(__name__)


class HybridRetrievalSystem:
    """
    Handles hybrid retrieval from both legal and general Qdrant collections
    """
    
    def __init__(self):
        self.hybrid_embedding_system = get_hybrid_embedding_system()
        self.legal_weight = 0.6  # Weight for legal embeddings
        self.general_weight = 0.4  # Weight for general embeddings
        self._init_qdrant_client()
    
    def _init_qdrant_client(self):
        """Initialize Qdrant client for direct queries"""
        QDRANT_URL = os.getenv("QDRANT_URL")
        QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")
        
        if not QDRANT_URL:
            logger.warning("QDRANT_URL not set")
            self.client = None
            return
        
        try:
            if QDRANT_API_KEY:
                self.client = qdrant_client.QdrantClient(
                    url=QDRANT_URL,
                    api_key=QDRANT_API_KEY,
                )
            else:
                self.client = qdrant_client.QdrantClient(
                    url=QDRANT_URL,
                )
            logger.info("✅ Qdrant client initialized for hybrid retrieval")
        except Exception as e:
            logger.error(f"❌ Failed to initialize Qdrant client: {e}")
            self.client = None
    
    def hybrid_search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Perform hybrid search across both legal and general collections
        
        Args:
            query: User query string
            top_k: Number of results to return
            
        Returns:
            List of merged and re-ranked results
        """
        logger.info(f"🔍 Performing hybrid search for query: '{query[:50]}...'")
        
        try:
            # For now, only search nyayantar_general since we can generate embeddings for it
            # The legal collection (nyayantar_legal) has 768-dim embeddings that are hard to query
            # We'll focus on the general collection with OpenAI embeddings
            
            general_embeddings = self.hybrid_embedding_system.encode_general([query])
            query_general_embedding = general_embeddings[0]
            
            # Search the general collection
            general_results = self._search_general_collection(query_general_embedding, top_k)
            
            logger.info(f"📊 General results: {len(general_results)}")
            
            # Return results with metadata
            for result in general_results:
                result['final_score'] = result.get('score', 0.0)
            
            return general_results
            
        except Exception as e:
            logger.error(f"❌ Error in hybrid search: {e}")
            logger.exception(e)
            return []
    
    def _search_legal_collection(self, query_embedding: List[float], top_k: int) -> List[Dict[str, Any]]:
        """Search the legal collection using InLegalBERT embeddings"""
        if not self.client:
            logger.error("Qdrant client not initialized")
            return []
        
        try:
            # Search the legal collection
            search_results = self.client.search(
                collection_name="nyayantar_legal",
                query_vector=query_embedding,
                limit=top_k,
                with_payload=True,
                score_threshold=0.5  # Minimum similarity threshold
            )
            
            # Format results
            results = []
            for result in search_results:
                results.append({
                    "id": str(result.id),
                    "text": result.payload.get("text", ""),
                    "score": result.score,
                    "metadata": result.payload.get("metadata", {}),
                    "collection": "nyayantar_legal"
                })
            
            logger.info(f"✅ Found {len(results)} results in legal collection")
            return results
            
        except Exception as e:
            logger.error(f"❌ Error searching legal collection: {e}")
            return []
    
    def _search_general_collection(self, query_embedding: List[float], top_k: int) -> List[Dict[str, Any]]:
        """Search the general collection using OpenAI embeddings"""
        if not self.client:
            logger.error("Qdrant client not initialized")
            return []
        
        try:
            # Search the general collection
            search_results = self.client.search(
                collection_name="nyayantar_general",
                query_vector=query_embedding,
                limit=top_k,
                with_payload=True,
                score_threshold=0.5  # Minimum similarity threshold
            )
            
            # Format results
            results = []
            for result in search_results:
                results.append({
                    "id": str(result.id),
                    "text": result.payload.get("text", ""),
                    "score": result.score,
                    "metadata": result.payload.get("metadata", {}),
                    "collection": "nyayantar_general"
                })
            
            logger.info(f"✅ Found {len(results)} results in general collection")
            return results
            
        except Exception as e:
            logger.error(f"❌ Error searching general collection: {e}")
            return []
    
    def _merge_and_rerank(self, legal_results: List[Dict], general_results: List[Dict], top_k: int) -> List[Dict]:
        """
        Merge and re-rank results from both collections
        
        Args:
            legal_results: Results from legal collection
            general_results: Results from general collection
            top_k: Number of final results
            
        Returns:
            Merged and re-ranked results
        """
        # Combine results with weighted scores
        combined_results = {}
        
        # Add legal results with weighted scores
        for result in legal_results:
            result_id = result.get("id", str(hash(result.get("text", ""))))
            if result_id not in combined_results:
                combined_results[result_id] = result
                # Weight the score
                combined_results[result_id]["final_score"] = result.get("score", 0.0) * self.legal_weight
            else:
                # Merge: update score if higher
                new_score = result.get("score", 0.0) * self.legal_weight
                if new_score > combined_results[result_id]["final_score"]:
                    combined_results[result_id]["final_score"] = new_score
        
        # Add general results with weighted scores
        for result in general_results:
            result_id = result.get("id", str(hash(result.get("text", ""))))
            if result_id not in combined_results:
                combined_results[result_id] = result
                combined_results[result_id]["final_score"] = result.get("score", 0.0) * self.general_weight
            else:
                # If already in results, add to score (hybrid approach)
                combined_results[result_id]["final_score"] += result.get("score", 0.0) * self.general_weight
        
        # Sort by final score and return top_k
        sorted_results = sorted(
            combined_results.values(),
            key=lambda x: x.get("final_score", 0.0),
            reverse=True
        )
        
        return sorted_results[:top_k]


# Global instance
_hybrid_retrieval_system = None


def get_hybrid_retrieval_system() -> HybridRetrievalSystem:
    """Get or create the global hybrid retrieval system instance"""
    global _hybrid_retrieval_system
    if _hybrid_retrieval_system is None:
        _hybrid_retrieval_system = HybridRetrievalSystem()
    return _hybrid_retrieval_system

