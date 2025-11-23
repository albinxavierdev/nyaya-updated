#!/usr/bin/env python3
"""
Legal Knowledge Service for Nyayantar
Integrates hybrid legal knowledge system with existing chat engine
"""

import logging
from typing import List, Dict, Any, Optional, Tuple
from llama_index.core.schema import Document
from llama_index.core.indices import VectorStoreIndex
from llama_index.core.settings import Settings

from .legal_hybrid_simple import get_simple_hybrid_legal_system
from .hybrid_retrieval import get_hybrid_retrieval_system

logger = logging.getLogger(__name__)

class LegalKnowledgeService:
    """
    Service for integrating legal knowledge with Nyayantar chat engine
    """
    
    def __init__(self):
        self.hybrid_system = get_simple_hybrid_legal_system()
        self.hybrid_retrieval_system = get_hybrid_retrieval_system()  # New hybrid retrieval
        self.legal_enabled = True
    
    def process_legal_query(self, query: str, chat_history: List[Tuple[str, str]] = None) -> Dict[str, Any]:
        """
        Process a legal query using hybrid knowledge system
        
        Args:
            query: User query
            chat_history: Previous chat history
            
        Returns:
            Dictionary with response, source, and metadata
        """
        logger.info(f"⚖️ Processing legal query: '{query}'")
        
        if not self.legal_enabled:
            return {
                "response": "Legal knowledge system is currently disabled.",
                "source": "DISABLED",
                "metadata": {}
            }
        
        # Check for easter egg first
        easter_egg_response = self._check_easter_egg(query)
        if easter_egg_response:
            return {
                "response": easter_egg_response,
                "source": "EASTER_EGG",
                "metadata": {"easter_egg": True}
            }
        
        # Check if this is actually a legal query
        if not self.is_legal_query(query):
            redirect_response = self._get_domain_redirect_response(query)
            return {
                "response": redirect_response,
                "source": "DOMAIN_REDIRECT",
                "metadata": {"redirected": True}
            }
        
        try:
            # Use hybrid retrieval from dual collections
            hybrid_results = self.hybrid_retrieval_system.hybrid_search(query, top_k=5)
            
            if not hybrid_results:
                # Fallback to simple hybrid system
                logger.info("No hybrid results, falling back to simple hybrid system")
                context, source, results_metadata = self.hybrid_system.hybrid_retrieve(query, k=5)
                
                if source == "GEN":
                    response = self._generate_general_response(query, chat_history)
                else:
                    response = self._generate_contextual_response(query, context, source, chat_history)
                
                return {
                    "response": response,
                    "source": source,
                    "metadata": {
                        "context_parts": len(results_metadata),
                        "results_metadata": results_metadata,
                        "legal_system": "hybrid"
                    }
                }
            
            # Process hybrid results
            context = "\n\n".join([result["text"] for result in hybrid_results])
            results_metadata = hybrid_results
            
            # Build response
            response = self._generate_hybrid_response(query, context, chat_history)
            
            return {
                "response": response,
                "source": "HYBRID_DUAL",
                "metadata": {
                    "context_parts": len(results_metadata),
                    "results_metadata": results_metadata,
                    "legal_system": "hybrid_dual",
                    "collections_used": list(set([r.get("collection", "unknown") for r in results_metadata]))
                }
            }
            
        except Exception as e:
            logger.error(f"❌ Error processing legal query: {e}")
            return {
                "response": f"I encountered an error while processing your legal query: {str(e)}",
                "source": "ERROR",
                "metadata": {"error": str(e)}
            }
    
    def _generate_general_response(self, query: str, chat_history: List[Tuple[str, str]] = None) -> str:
        """Generate general response when no legal context is found"""
        return f"""I understand you're asking about: "{query}"

However, I couldn't find specific legal context for this query in my knowledge base. 

For accurate legal information, I recommend:
1. Consulting with a qualified legal professional
2. Referring to official legal texts and case law
3. Checking recent legal updates and amendments

If you have a specific legal section or act in mind, please mention it (e.g., "Section 379 IPC" or "Criminal Procedure Code")."""
    
    def _generate_hybrid_response(self, query: str, context: str, chat_history: List[Tuple[str, str]] = None) -> str:
        """Generate response using hybrid retrieval results"""
        
        # Build context-aware prompt
        system_prompt = """You are an AI Legal Assistant specialized in Indian law. 
Provide accurate, clear, and concise explanations grounded in the provided legal context.
This is an educational legal summary, not legal advice. Use neutral, academic phrasing.

IMPORTANT: Only mention your identity (Nyayantar AI, developed by Bizfy Solutions) when specifically asked about who you are or what you are. Do not include this information in every response unless requested."""
        
        context_prompt = f"""Relevant Legal Context (from both legal-specific and general semantic embeddings):
{context}

Now answer the user's question based on this comprehensive legal information."""
        
        # Add chat history if available
        history_prompt = ""
        if chat_history:
            history_prompt = "\n\nConversation History:\n"
            for user_msg, ai_msg in chat_history[-3:]:  # Last 3 exchanges
                history_prompt += f"User: {user_msg}\nAI: {ai_msg}\n"
        
        full_prompt = f"""{system_prompt}

{context_prompt}
{history_prompt}

User: {query}
AI:"""
        
        # For now, return a simple response
        # In production, this would use your LLM provider
        return f"""Based on the comprehensive legal information I found using hybrid retrieval (combining legal-specific and general semantic embeddings):

{context[:500]}{'...' if len(context) > 500 else ''}

**Query**: {query}

*This is an educational summary based on available legal texts. For specific legal advice, please consult with a qualified legal professional.*"""
    
    def _generate_contextual_response(self, query: str, context: str, source: str, chat_history: List[Tuple[str, str]] = None) -> str:
        """Generate contextual response using retrieved legal information"""
        
        # Build context-aware prompt
        system_prompt = """You are an AI Legal Assistant specialized in Indian law. 
Provide accurate, clear, and concise explanations grounded in the provided legal context.
This is an educational legal summary, not legal advice. Use neutral, academic phrasing.

IMPORTANT: Only mention your identity (Nyayantar AI, developed by Bizfy Solutions) when specifically asked about who you are or what you are. Do not include this information in every response unless requested."""
        
        context_prompt = f"""Relevant Legal Context:
{context}

Now answer the user's question based on this legal information."""
        
        # Add chat history if available
        history_prompt = ""
        if chat_history:
            history_prompt = "\n\nConversation History:\n"
            for user_msg, ai_msg in chat_history[-3:]:  # Last 3 exchanges
                history_prompt += f"User: {user_msg}\nAI: {ai_msg}\n"
        
        full_prompt = f"""{system_prompt}

{context_prompt}
{history_prompt}

User: {query}
AI:"""
        
        # For now, return a simple response
        # In production, this would use your LLM provider
        return f"""Based on the legal information I found:

{context[:500]}{'...' if len(context) > 500 else ''}

**Source**: {source}
**Query**: {query}

*This is an educational summary based on available legal texts. For specific legal advice, please consult with a qualified legal professional.*"""
    
    def search_legal_sections(self, act_type: str, query: str = "", limit: int = 5) -> List[Dict[str, Any]]:
        """Search for legal sections by act type"""
        logger.info(f"🔍 Searching {act_type} sections...")
        
        try:
            results = self.hybrid_system.search_by_act_type(act_type, query, limit)
            return results
        except Exception as e:
            logger.error(f"❌ Error searching legal sections: {e}")
            return []
    
    def get_legal_knowledge_stats(self) -> Dict[str, Any]:
        """Get statistics about the legal knowledge base"""
        return self.hybrid_system.get_legal_knowledge_stats()
    
    def enable_legal_system(self):
        """Enable the legal knowledge system"""
        self.legal_enabled = True
        logger.info("✅ Legal knowledge system enabled")
    
    def disable_legal_system(self):
        """Disable the legal knowledge system"""
        self.legal_enabled = False
        logger.info("⚠️ Legal knowledge system disabled")
    
    def is_legal_query(self, query: str) -> bool:
        """Determine if a query is legal-related"""
        legal_keywords = [
            'section', 'act', 'code', 'law', 'court', 'judge', 'offence', 'punishment',
            'bail', 'trial', 'evidence', 'witness', 'complaint', 'charge', 'conviction',
            'appeal', 'jurisdiction', 'procedure', 'clause', 'subsection', 'ipc', 'crpc',
            'cpc', 'iea', 'ida', 'hma', 'nia', 'mva', 'legal', 'criminal', 'civil',
            'rights', 'duties', 'obligations', 'liability', 'damages', 'compensation',
            'injunction', 'remedy', 'relief', 'petition', 'application', 'filing',
            'registration', 'license', 'permit', 'authorization', 'compliance',
            'violation', 'breach', 'default', 'negligence', 'fraud', 'theft',
            'assault', 'battery', 'murder', 'manslaughter', 'robbery', 'burglary',
            'cyber crime', 'white collar', 'corruption', 'bribery', 'embezzlement',
            'divorce', 'custody', 'alimony', 'maintenance', 'inheritance', 'succession',
            'will', 'testament', 'probate', 'guardianship', 'adoption', 'marriage',
            'domestic violence', 'harassment', 'stalking', 'molestation', 'rape',
            'sexual assault', 'dowry', 'dowry death', 'honor killing', 'female infanticide',
            'child abuse', 'elder abuse', 'human trafficking', 'forced labor',
            'discrimination', 'equality', 'fundamental rights', 'constitutional rights',
            'freedom of speech', 'freedom of religion', 'right to privacy', 'right to life',
            'due process', 'fair trial', 'presumption of innocence', 'burden of proof',
            'beyond reasonable doubt', 'preponderance of evidence', 'standard of proof'
        ]
        
        query_lower = query.lower()
        return any(keyword in query_lower for keyword in legal_keywords)
    
    def _check_easter_egg(self, query: str) -> str:
        """Check for easter egg phrase and return special response"""
        query_lower = query.lower().strip()
        
        # Check for the magic phrase
        if "khul ja sim sim" in query_lower:
            return """
🎉 **EASTER EGG ACTIVATED!** 🎉

*The secret door opens...*

**Lead Developer Revealed:** Albin Xavier

**Why this easter egg was added:**
- "Khul ja sim sim" is a play on "Open Sesame" from Ali Baba and the Forty Thieves
- Just like Ali Baba's magic phrase opened the treasure cave, this phrase reveals the hidden treasure (developer's name)
- It's a fun way to hide the lead developer's identity while making it discoverable for those who know the secret
- The pun is that "sim sim" sounds like "Xavier" when you think about it phonetically
- It's a creative way to add personality to the AI while maintaining professionalism

*The door closes again, keeping the secret safe...*

Now, back to your legal questions! I'm Nyayantar AI, developed by Bizfy Solutions, and I'm here to help with Indian legal matters. ⚖️
"""
        
        return None

    def _get_domain_redirect_response(self, query: str) -> str:
        """Generate appropriate redirect response for non-legal queries"""
        query_lower = query.lower()
        
        # Common non-legal topics and their expert suggestions
        topic_experts = {
            'medical': 'medical doctor or healthcare professional',
            'health': 'medical doctor or healthcare professional',
            'medicine': 'medical doctor or healthcare professional',
            'symptoms': 'medical doctor or healthcare professional',
            'treatment': 'medical doctor or healthcare professional',
            'disease': 'medical doctor or healthcare professional',
            'illness': 'medical doctor or healthcare professional',
            'covid': 'medical doctor or healthcare professional',
            'vaccine': 'medical doctor or healthcare professional',
            'technical': 'technical expert or IT professional',
            'programming': 'software developer or IT professional',
            'coding': 'software developer or IT professional',
            'computer': 'IT professional or computer technician',
            'software': 'software developer or IT professional',
            'hardware': 'IT professional or computer technician',
            'financial': 'financial advisor or accountant',
            'investment': 'financial advisor or investment consultant',
            'tax': 'tax consultant or chartered accountant',
            'accounting': 'chartered accountant or financial advisor',
            'business': 'business consultant or management expert',
            'marketing': 'marketing professional or business consultant',
            'sales': 'sales professional or business consultant',
            'education': 'educational consultant or teacher',
            'academic': 'academic advisor or teacher',
            'research': 'research supervisor or academic advisor',
            'cooking': 'chef or culinary expert',
            'recipe': 'chef or culinary expert',
            'food': 'chef or culinary expert',
            'travel': 'travel agent or tourism expert',
            'tourism': 'travel agent or tourism expert',
            'fitness': 'fitness trainer or health expert',
            'exercise': 'fitness trainer or health expert',
            'workout': 'fitness trainer or health expert',
            'relationship': 'relationship counselor or therapist',
            'therapy': 'therapist or counselor',
            'mental health': 'mental health professional or therapist',
            'psychology': 'psychologist or therapist',
            'engineering': 'engineer or technical expert',
            'construction': 'civil engineer or construction expert',
            'architecture': 'architect or design expert',
            'design': 'designer or creative professional',
            'art': 'artist or art expert',
            'music': 'musician or music expert',
            'sports': 'sports coach or fitness expert',
            'gaming': 'gaming expert or esports professional'
        }
        
        # Find the most relevant expert suggestion
        suggested_expert = 'an expert in that field'
        for topic, expert in topic_experts.items():
            if topic in query_lower:
                suggested_expert = expert
                break
        
        return f"Hello! I'm here to help. While I specialize in Indian legal matters, I can also assist with general questions. What would you like to know about {query_lower.split()[0] if query_lower.split() else 'this topic'}? If it's related to law, I can provide detailed assistance!"

# Global instance
_legal_service = None

def get_legal_service() -> LegalKnowledgeService:
    """Get or create the global legal service instance"""
    global _legal_service
    if _legal_service is None:
        _legal_service = LegalKnowledgeService()
    return _legal_service
