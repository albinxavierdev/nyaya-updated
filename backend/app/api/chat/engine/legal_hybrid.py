#!/usr/bin/env python3
"""
Hybrid Legal Knowledge System for Nyayantar
Combines FAISS (deep IPC knowledge) with Qdrant (broad multi-act coverage)
"""

import json
import os
import re
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
import logging

# FAISS for deep IPC knowledge
try:
    import faiss
    from langchain_community.vectorstores import FAISS
    from langchain_huggingface import HuggingFaceEmbeddings
    from langchain.schema import Document
    FAISS_AVAILABLE = True
except ImportError:
    FAISS_AVAILABLE = False
    print("⚠️ FAISS not available. Install with: pip install faiss-cpu langchain-community langchain-huggingface")

# Qdrant for broad multi-act coverage
from llama_index.vector_stores.qdrant import QdrantVectorStore
from llama_index.core.schema import Document as LlamaDocument
from llama_index.core.settings import Settings

logger = logging.getLogger(__name__)

class HybridLegalKnowledgeSystem:
    """
    Hybrid legal knowledge system combining:
    - FAISS: Deep IPC knowledge (1,430+ sections with case law)
    - Qdrant: Broad multi-act coverage (7 legal acts, 1,958 sections)
    """
    
    def __init__(self, 
                 legal_data_path: str = "legal_data",
                 faiss_index_path: str = "legal_data/faiss_index",
                 qdrant_collection: str = "legal_knowledge"):
        
        self.legal_data_path = Path(legal_data_path)
        self.faiss_index_path = Path(faiss_index_path)
        self.faiss_index_path.mkdir(exist_ok=True)
        
        # Initialize FAISS components
        self.faiss_available = FAISS_AVAILABLE
        self.faiss_vectorstore = None
        self.faiss_embedding_model = None
        
        # Initialize Qdrant components
        self.qdrant_vectorstore = None
        self.qdrant_collection = qdrant_collection
        
        # Legal knowledge base
        self.laws_raw_data = None
        self.legal_sections_data = None
        
        # Initialize the system
        self._initialize_system()
    
    def _initialize_system(self):
        """Initialize both FAISS and Qdrant systems"""
        logger.info("🚀 Initializing Hybrid Legal Knowledge System...")
        
        # Load legal data
        self._load_legal_data()
        
        # Initialize FAISS for deep IPC knowledge
        if self.faiss_available:
            self._initialize_faiss()
        
        # Initialize Qdrant for broad multi-act coverage
        self._initialize_qdrant()
        
        logger.info("✅ Hybrid Legal Knowledge System initialized successfully")
    
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
    
    def _initialize_faiss(self):
        """Initialize FAISS for deep IPC knowledge"""
        logger.info("🤖 Initializing FAISS for deep IPC knowledge...")
        
        try:
            # Initialize InLegalBERT embedding model
            self.faiss_embedding_model = HuggingFaceEmbeddings(
                model_name="law-ai/InLegalBERT",
                model_kwargs={'device': 'cpu'}
            )
            logger.info("✅ InLegalBERT embedding model loaded")
            
            # Try to load existing FAISS index
            faiss_index_file = self.faiss_index_path / "ipc_embed_db_inlegalbert"
            if faiss_index_file.exists():
                try:
                    self.faiss_vectorstore = FAISS.load_local(
                        str(faiss_index_file),
                        self.faiss_embedding_model,
                        allow_dangerous_deserialization=True
                    )
                    logger.info("✅ FAISS index loaded successfully")
                except Exception as e:
                    logger.warning(f"⚠️ Failed to load FAISS index: {e}")
                    self._build_faiss_index()
            else:
                self._build_faiss_index()
                
        except Exception as e:
            logger.error(f"❌ Failed to initialize FAISS: {e}")
            self.faiss_available = False
    
    def _build_faiss_index(self):
        """Build FAISS index from IPC data"""
        logger.info("🔨 Building FAISS index from IPC data...")
        
        if not self.laws_raw_data or not self.faiss_embedding_model:
            logger.error("❌ Cannot build FAISS index: Missing data or embedding model")
            return
        
        # Create documents from IPC data
        docs = []
        for section, details in self.laws_raw_data["IPC"].items():
            title = details.get("title", "")
            content = details.get("content", "")
            text = f"{section}: {title}\n{content}"
            
            doc = Document(
                page_content=text,
                metadata={
                    "section": section,
                    "title": title,
                    "act_type": "IPC",
                    "source": "Ratanlal & Dhirajlal (36th Edition)"
                }
            )
            docs.append(doc)
        
        # Build FAISS index
        self.faiss_vectorstore = FAISS.from_documents(docs, self.faiss_embedding_model)
        
        # Save index
        faiss_index_file = self.faiss_index_path / "ipc_embed_db_inlegalbert"
        self.faiss_vectorstore.save_local(str(faiss_index_file))
        
        logger.info(f"✅ FAISS index built with {len(docs)} IPC sections")
    
    def _initialize_qdrant(self):
        """Initialize Qdrant for broad multi-act coverage"""
        logger.info("🗄️ Initializing Qdrant for broad multi-act coverage...")
        
        try:
            # Get Qdrant vector store from existing system
            from app.api.chat.engine.vectordb import get_vector_store
            self.qdrant_vectorstore = get_vector_store()
            logger.info("✅ Qdrant vector store connected")
        except Exception as e:
            logger.error(f"❌ Failed to initialize Qdrant: {e}")
    
    def hybrid_retrieve(self, query: str, k: int = 5, score_threshold: float = 0.65) -> Tuple[str, str, List[Dict]]:
        """
        Hybrid retrieval combining FAISS and Qdrant
        
        Args:
            query: User query
            k: Number of results to retrieve
            score_threshold: Minimum score threshold for FAISS results
            
        Returns:
            Tuple of (context_text, source_type, results_metadata)
        """
        logger.info(f"🔍 Hybrid retrieval for query: '{query}'")
        
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
        
        # 2️⃣ FAISS semantic search for deep IPC knowledge
        if self.faiss_available and self.faiss_vectorstore:
            faiss_results = self._faiss_search(query, k=k, score_threshold=score_threshold)
            if faiss_results:
                for result in faiss_results:
                    context_parts.append(result["text"])
                    results_metadata.append(result["metadata"])
                source = "FAISS" if source == "GEN" else "HYBRID"
                logger.info(f"✅ FAISS search: {len(faiss_results)} results")
        
        # 3️⃣ Qdrant search for broad multi-act coverage
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
    
    def _faiss_search(self, query: str, k: int = 5, score_threshold: float = 0.65) -> List[Dict]:
        """FAISS semantic search for deep IPC knowledge"""
        if not self.faiss_vectorstore:
            return []
        
        try:
            results = self.faiss_vectorstore.similarity_search_with_score(query, k=k)
            filtered_results = []
            
            for doc, score in results:
                if score < score_threshold:  # Lower score = higher similarity in FAISS
                    filtered_results.append({
                        "text": f"{doc.metadata.get('section', '')} - {doc.metadata.get('title', '')}\n{doc.page_content}",
                        "metadata": doc.metadata,
                        "score": float(score)
                    })
            
            return filtered_results
        except Exception as e:
            logger.error(f"❌ FAISS search error: {e}")
            return []
    
    def _qdrant_search(self, query: str, k: int = 5) -> List[Dict]:
        """Qdrant search for broad multi-act coverage"""
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
        
        # Search in FAISS if IPC
        if act_type.upper() == "IPC" and self.faiss_available and self.faiss_vectorstore:
            faiss_results = self._faiss_search(query, k=k)
            results.extend(faiss_results)
        
        # Search in Qdrant for all act types
        if self.qdrant_vectorstore:
            qdrant_results = self._qdrant_search(query, k=k)
            # Filter by act type
            filtered_results = [r for r in qdrant_results if r["metadata"].get("act_type", "").upper() == act_type.upper()]
            results.extend(filtered_results)
        
        logger.info(f"✅ Found {len(results)} {act_type} results")
        return results
    
    def get_legal_knowledge_stats(self) -> Dict[str, Any]:
        """Get statistics about the legal knowledge base"""
        stats = {
            "faiss_available": self.faiss_available,
            "qdrant_available": self.qdrant_vectorstore is not None,
            "laws_raw_sections": len(self.laws_raw_data.get("IPC", {})) if self.laws_raw_data else 0,
            "legal_documents": len(self.legal_sections_data) if self.legal_sections_data else 0,
            "system_type": "hybrid"
        }
        
        if self.faiss_available and self.faiss_vectorstore:
            stats["faiss_index_size"] = self.faiss_vectorstore.index.ntotal if hasattr(self.faiss_vectorstore, 'index') else 0
        
        return stats

# Global instance
_hybrid_legal_system = None

def get_hybrid_legal_system() -> HybridLegalKnowledgeSystem:
    """Get or create the global hybrid legal system instance"""
    global _hybrid_legal_system
    if _hybrid_legal_system is None:
        _hybrid_legal_system = HybridLegalKnowledgeSystem()
    return _hybrid_legal_system
