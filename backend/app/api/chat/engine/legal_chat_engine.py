#!/usr/bin/env python3
"""
Legal Chat Engine for Nyayantar
Integrates legal knowledge with existing chat functionality
"""

import logging
from typing import List, Dict, Any, Optional, Tuple
from llama_index.core.chat_engine import CondensePlusContextChatEngine
from llama_index.core.indices import VectorStoreIndex
from llama_index.core.settings import Settings

from .legal_service import get_legal_service
from .index import get_index
from .node_postprocessors import NodeCitationProcessor

logger = logging.getLogger(__name__)

class LegalChatEngine:
    """
    Enhanced chat engine with legal knowledge integration
    """
    
    def __init__(self):
        self.legal_service = get_legal_service()
        self.base_chat_engine = None
        self.legal_enabled = True
    
    def get_chat_engine(self, filters=None, params=None):
        """Get the base chat engine"""
        if self.base_chat_engine is None:
            from .engine import get_chat_engine
            self.base_chat_engine = get_chat_engine(filters, params)
        return self.base_chat_engine
    
    def chat(self, message: str, chat_history: List[Tuple[str, str]] = None) -> Dict[str, Any]:
        """
        Process chat message with legal knowledge integration
        
        Args:
            message: User message
            chat_history: Previous chat history
            
        Returns:
            Dictionary with response and metadata
        """
        logger.info(f"💬 Processing chat message: '{message[:50]}...'")
        
        # Check if this is a legal query
        if self.legal_service.is_legal_query(message):
            logger.info("⚖️ Detected legal query, using legal knowledge system")
            return self._process_legal_query(message, chat_history)
        else:
            logger.info("📝 Regular query, using base chat engine")
            return self._process_regular_query(message, chat_history)
    
    def _process_legal_query(self, message: str, chat_history: List[Tuple[str, str]] = None) -> Dict[str, Any]:
        """Process legal queries using hybrid knowledge system"""
        try:
            # Use legal service for legal queries
            legal_response = self.legal_service.process_legal_query(message, chat_history)
            
            return {
                "response": legal_response["response"],
                "source": legal_response["source"],
                "metadata": {
                    **legal_response["metadata"],
                    "query_type": "legal",
                    "legal_system": "hybrid"
                }
            }
            
        except Exception as e:
            logger.error(f"❌ Error processing legal query: {e}")
            # Fallback to regular chat engine
            return self._process_regular_query(message, chat_history)
    
    def _process_regular_query(self, message: str, chat_history: List[Tuple[str, str]] = None) -> Dict[str, Any]:
        """Process regular queries using base chat engine"""
        try:
            # Use base chat engine for regular queries
            chat_engine = self.get_chat_engine()
            
            # Convert chat history to the format expected by the chat engine
            if chat_history:
                # The chat engine should handle history internally
                pass
            
            # Get response from base chat engine
            response = chat_engine.chat(message)
            
            return {
                "response": str(response),
                "source": "RAG",
                "metadata": {
                    "query_type": "regular",
                    "legal_system": "none"
                }
            }
            
        except Exception as e:
            logger.error(f"❌ Error processing regular query: {e}")
            return {
                "response": f"I encountered an error while processing your message: {str(e)}",
                "source": "ERROR",
                "metadata": {
                    "query_type": "error",
                    "error": str(e)
                }
            }
    
    def search_legal_sections(self, act_type: str, query: str = "", limit: int = 5) -> List[Dict[str, Any]]:
        """Search for legal sections by act type"""
        return self.legal_service.search_legal_sections(act_type, query, limit)
    
    def get_legal_knowledge_stats(self) -> Dict[str, Any]:
        """Get statistics about the legal knowledge base"""
        return self.legal_service.get_legal_knowledge_stats()
    
    def enable_legal_system(self):
        """Enable the legal knowledge system"""
        self.legal_enabled = True
        self.legal_service.enable_legal_system()
        logger.info("✅ Legal knowledge system enabled")
    
    def disable_legal_system(self):
        """Disable the legal knowledge system"""
        self.legal_enabled = False
        self.legal_service.disable_legal_system()
        logger.info("⚠️ Legal knowledge system disabled")
    
    def is_legal_query(self, query: str) -> bool:
        """Check if a query is legal-related"""
        return self.legal_service.is_legal_query(query)

# Global instance
_legal_chat_engine = None

def get_legal_chat_engine() -> LegalChatEngine:
    """Get or create the global legal chat engine instance"""
    global _legal_chat_engine
    if _legal_chat_engine is None:
        _legal_chat_engine = LegalChatEngine()
    return _legal_chat_engine
