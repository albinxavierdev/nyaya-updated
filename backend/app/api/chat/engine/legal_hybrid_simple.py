#!/usr/bin/env python3
"""
Simple Hybrid Legal Knowledge System for Nyayantar
Uses existing Qdrant + simple text matching for legal knowledge
"""

import json
import os
import re
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
import logging

# Use existing Qdrant setup
from llama_index.vector_stores.qdrant import QdrantVectorStore
from llama_index.core.schema import Document as LlamaDocument
from llama_index.core.settings import Settings

logger = logging.getLogger(__name__)

class SimpleHybridLegalSystem:
    """
    Simple hybrid legal knowledge system using:
    - Qdrant: Multi-act coverage (1,958 sections)
    - JSON Lookup: Direct section access
    - Text Matching: Simple legal query detection
    """
    
    def __init__(self, 
                 legal_data_path: str = "legal_data",
                 qdrant_collection: str = "legal_knowledge"):
        
        self.legal_data_path = Path(legal_data_path)
        self.qdrant_collection = qdrant_collection
        
        # Legal knowledge base
        self.laws_raw_data = None
        self.legal_sections_data = None
        
        # Qdrant components
        self.qdrant_vectorstore = None
        
        # Initialize the system
        self._initialize_system()
    
    def _initialize_system(self):
        """Initialize the simple hybrid system"""
        logger.info("🚀 Initializing Simple Hybrid Legal System...")
        
        # Load legal data
        self._load_legal_data()
        
        # Initialize Qdrant
        self._initialize_qdrant()
        
        logger.info("✅ Simple Hybrid Legal System initialized")
    
    def _load_legal_data(self):
        """Load legal knowledge base data"""
        logger.info("📖 Loading legal knowledge base...")
        
        # Load laws_raw.json for IPC data
        laws_raw_file = self.legal_data_path / "raw" / "laws_raw.json"
        if laws_raw_file.exists():
            with open(laws_raw_file, "r", encoding="utf-8") as f:
                self.laws_raw_data = json.load(f)
            logger.info(f"✅ Loaded IPC data: {len(self.laws_raw_data.get('IPC', {}))} sections")
        
        # Load processed legal sections
        processed_file = self.legal_data_path / "converted" / "all_legal_documents.json"
        if processed_file.exists():
            with open(processed_file, "r", encoding="utf-8") as f:
                self.legal_sections_data = json.load(f)
            logger.info(f"✅ Loaded legal sections: {len(self.legal_sections_data)} documents")
    
    def _initialize_qdrant(self):
        """Initialize Qdrant for multi-act coverage"""
        logger.info("🗄️ Initializing Qdrant for multi-act coverage...")
        
        try:
            # Get Qdrant vector store from existing system
            from app.api.chat.engine.vectordb import get_vector_store
            self.qdrant_vectorstore = get_vector_store()
            logger.info("✅ Qdrant vector store connected")
        except Exception as e:
            logger.error(f"❌ Failed to initialize Qdrant: {e}")
    
    def hybrid_retrieve(self, query: str, k: int = 5) -> Tuple[str, str, List[Dict]]:
        """
        Simple hybrid retrieval combining JSON lookup and Qdrant search
        
        Args:
            query: User query
            k: Number of results to retrieve
            
        Returns:
            Tuple of (context_text, source_type, results_metadata)
        """
        logger.info(f"🔍 Simple hybrid retrieval for query: '{query}'")
        
        context_parts = []
        source = "GEN"
        results_metadata = []
        
        # 1️⃣ Direct JSON lookup for specific sections
        section_match = re.search(r'\bsection\s*(\d+)\b', query.lower())
        if section_match:
            section_number = section_match.group(1)
            section_result = self._direct_section_lookup(section_number)
            if section_result:
                context_parts.append(section_result["text"])
                results_metadata.append(section_result["metadata"])
                source = "JSON"
                logger.info(f"✅ Direct section lookup: Section {section_number}")
        
        # 2️⃣ Simple text search in legal sections
        if self.legal_sections_data:
            text_results = self._simple_text_search(query, k=k)
            if text_results:
                for result in text_results:
                    context_parts.append(result["text"])
                    results_metadata.append(result["metadata"])
                source = "TEXT" if source == "GEN" else "HYBRID"
                logger.info(f"✅ Text search: {len(text_results)} results")
        
        # 3️⃣ Qdrant search (if available)
        if self.qdrant_vectorstore:
            qdrant_results = self._qdrant_search(query, k=k)
            if qdrant_results:
                for result in qdrant_results:
                    context_parts.append(result["text"])
                    results_metadata.append(result["metadata"])
                source = "QDRANT" if source == "GEN" else "HYBRID"
                logger.info(f"✅ Qdrant search: {len(qdrant_results)} results")
        
        # Combine context
        context = "\n\n".join(context_parts)
        
        logger.info(f"📊 Final result: {source} with {len(context_parts)} context parts")
        return context.strip(), source, results_metadata
    
    def _direct_section_lookup(self, section_number: str) -> Optional[Dict]:
        """Direct lookup of specific section number"""
        if not self.laws_raw_data:
            return None
        
        section_key = f"section{section_number}"
        if section_key in self.laws_raw_data["IPC"]:
            details = self.laws_raw_data["IPC"][section_key]
            text = f"Section {section_number}: {details.get('title', '')}\n{details.get('content', '')}"
            return {
                "text": text,
                "metadata": {
                    "section": section_key,
                    "title": details.get("title", ""),
                    "act_type": "IPC",
                    "source": "Direct lookup"
                }
            }
        return None
    
    def _simple_text_search(self, query: str, k: int = 5) -> List[Dict]:
        """Simple text search in legal sections"""
        if not self.legal_sections_data:
            return []
        
        query_lower = query.lower()
        results = []
        
        for doc in self.legal_sections_data:
            text = doc.get("text", "")
            metadata = doc.get("metadata", {})
            
            # Simple scoring based on keyword matches
            score = 0
            query_words = query_lower.split()
            
            for word in query_words:
                if word in text.lower():
                    score += 1
                if word in metadata.get("title", "").lower():
                    score += 2
                if word in metadata.get("act_type", "").lower():
                    score += 1
            
            if score > 0:
                results.append({
                    "text": f"{metadata.get('title', '')}\n{text[:500]}{'...' if len(text) > 500 else ''}",
                    "metadata": metadata,
                    "score": score
                })
        
        # Sort by score and return top k
        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:k]
    
    def _qdrant_search(self, query: str, k: int = 5) -> List[Dict]:
        """Qdrant search for multi-act coverage"""
        if not self.qdrant_vectorstore:
            return []
        
        try:
            # This would need to be implemented based on your Qdrant setup
            # For now, return empty list as placeholder
            logger.info("Qdrant search not yet implemented")
            return []
        except Exception as e:
            logger.error(f"❌ Qdrant search error: {e}")
            return []
    
    def search_by_act_type(self, act_type: str, query: str = "", k: int = 5) -> List[Dict]:
        """Search documents by specific act type"""
        logger.info(f"🔍 Searching {act_type} documents...")
        
        results = []
        
        # Search in legal sections data
        if self.legal_sections_data:
            for doc in self.legal_sections_data:
                metadata = doc.get("metadata", {})
                if metadata.get("act_type", "").upper() == act_type.upper():
                    results.append({
                        "text": doc.get("text", ""),
                        "metadata": metadata,
                        "score": 1.0
                    })
        
        logger.info(f"✅ Found {len(results)} {act_type} results")
        return results[:k]
    
    def get_legal_knowledge_stats(self) -> Dict[str, Any]:
        """Get statistics about the legal knowledge base"""
        stats = {
            "faiss_available": False,
            "qdrant_available": self.qdrant_vectorstore is not None,
            "laws_raw_sections": len(self.laws_raw_data.get("IPC", {})) if self.laws_raw_data else 0,
            "legal_documents": len(self.legal_sections_data) if self.legal_sections_data else 0,
            "system_type": "simple_hybrid"
        }
        
        return stats

# Global instance
_simple_hybrid_legal_system = None

def get_simple_hybrid_legal_system() -> SimpleHybridLegalSystem:
    """Get or create the global simple hybrid legal system instance"""
    global _simple_hybrid_legal_system
    if _simple_hybrid_legal_system is None:
        _simple_hybrid_legal_system = SimpleHybridLegalSystem()
    return _simple_hybrid_legal_system
