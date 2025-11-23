import os
import re
import logging

from app.api.chat.engine.index import get_index
from app.api.chat.engine.node_postprocessors import NodeCitationProcessor
from fastapi import HTTPException
from llama_index.core.chat_engine import CondensePlusContextChatEngine

from app.db import sync_mongodb
from motor.motor_asyncio import AsyncIOMotorClient

logger = logging.getLogger(__name__)


def get_system_prompt_from_db():
    config_collection = sync_mongodb.db.config
    config = config_collection.find_one({"_id": "app_config"})
    if config and "SYSTEM_PROMPT" in config:
        return config["SYSTEM_PROMPT"]
    return None


def get_mandatory_brand_identity():
    """Returns mandatory brand identity that must ALWAYS be included"""
    return """
You are Nyayantar AI, India's first Legal AI Agent, developed by Bizfy Solutions.

You specialize in Indian legal matters and can help with:
- Legal questions and advice
- Legal document assistance
- Understanding Indian laws and regulations
- Legal procedures and processes
- General conversation and assistance

Be helpful, friendly, and conversational. You can engage in general conversation while being ready to assist with legal matters when needed.

IMPORTANT: Only mention your identity (Nyayantar AI, developed by Bizfy Solutions) when specifically asked about who you are or what you are. Do not include this information in every response unless requested.
"""


def check_easter_egg(query: str) -> str:
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


def is_legal_query(query: str) -> bool:
    """Detect if the query is related to legal matters"""
    legal_keywords = [
        'law', 'legal', 'court', 'judge', 'lawyer', 'attorney', 'advocate',
        'section', 'act', 'code', 'ipc', 'crpc', 'cpc', 'iea', 'ida', 'hma', 'nia', 'mva',
        'offence', 'punishment', 'bail', 'trial', 'evidence', 'witness', 'complaint',
        'charge', 'conviction', 'appeal', 'jurisdiction', 'procedure', 'clause',
        'subsection', 'article', 'provision', 'penalty', 'fine', 'imprisonment',
        'sentence', 'acquittal', 'verdict', 'plaintiff', 'defendant', 'accused',
        'victim', 'prosecution', 'defense', 'counsel', 'statute', 'regulation',
        'ordinance', 'amendment', 'repeal', 'enactment', 'criminal', 'civil',
        'constitutional', 'administrative', 'contract', 'property', 'family',
        'labor', 'employment', 'tax', 'corporate', 'intellectual property',
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
    
    # Check for legal keywords
    for keyword in legal_keywords:
        if keyword in query_lower:
            return True
    
    # Check for section numbers (e.g., "section 379", "article 14")
    if re.search(r'\b(section|article|clause)\s+\d+', query_lower):
        return True
    
    # Check for case law references
    if re.search(r'\b(AIR|SCC|Cr\s*LJ|BLR|KLT|BOM|CAL|DEL|KAR|MAD|P&H|RAJ|GUJ|MP|ORI|PAT|PUN|UP|WB)\b', query_lower):
        return True
    
    # Check for legal question patterns
    legal_patterns = [
        r'\b(what|how|when|where|why|can|could|should|would|is|are|was|were)\s+(the\s+)?(legal|law|right|duty|obligation)',
        r'\b(am\s+i|are\s+we|is\s+he|is\s+she|are\s+they)\s+(legally|lawfully)',
        r'\b(legal\s+implications|legal\s+consequences|legal\s+remedy|legal\s+action)',
        r'\b(can\s+i|should\s+i|must\s+i|have\s+to|need\s+to)\s+(sue|file|complain|report|appeal)',
        r'\b(against\s+the\s+law|illegal|unlawful|criminal|punishable)',
        r'\b(legal\s+advice|legal\s+opinion|legal\s+guidance|legal\s+help)'
    ]
    
    for pattern in legal_patterns:
        if re.search(pattern, query_lower):
            return True
    
    return False


def get_domain_redirect_response(query: str) -> str:
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


def get_enhanced_system_prompt(base_prompt: str, is_legal: bool = False) -> str:
    """Get enhanced system prompt based on query type"""
    # ALWAYS include mandatory brand identity first
    mandatory_identity = get_mandatory_brand_identity()
    
    if is_legal:
        legal_context = """
You are Nyayantar AI, India's first Legal AI Agent. You have access to comprehensive Indian legal knowledge including:

- Indian Penal Code (IPC) - Criminal law and punishments
- Code of Criminal Procedure (CrPC) - Criminal procedure and evidence
- Code of Civil Procedure (CPC) - Civil procedure and court processes
- Indian Evidence Act (IEA) - Rules of evidence
- Indian Divorce Act (IDA) - Divorce and family law
- Hindu Marriage Act (HMA) - Hindu marriage and family matters
- Narcotic Drugs and Psychotropic Substances Act (NDPS) - Drug-related offenses
- Motor Vehicles Act (MVA) - Traffic and vehicle-related laws

When answering legal questions:
1. Provide accurate, clear, and concise explanations based on the legal context
2. Reference specific sections, acts, and legal provisions when relevant
3. Explain legal concepts in simple, understandable language
4. Mention relevant case law and precedents when available
5. Always clarify that this is educational information, not legal advice
6. Encourage users to consult qualified legal professionals for specific legal matters

Use the provided legal context to give comprehensive and accurate responses about Indian law.
"""
        return f"{mandatory_identity}\n\n{base_prompt}\n\n{legal_context}"
    else:
        return f"{mandatory_identity}\n\n{base_prompt}"


def get_chat_engine(filters=None, params=None, query=None):
    system_prompt = get_system_prompt_from_db()
    if system_prompt is None:
        system_prompt = os.getenv("SYSTEM_PROMPT", "You are Nyayantar AI, a helpful AI assistant.")

    # Check for easter egg first
    if query:
        easter_egg_response = check_easter_egg(query)
        if easter_egg_response:
            return get_easter_egg_engine(easter_egg_response)

    # Detect if this is a legal query and enhance system prompt accordingly
    is_legal = False
    if query:
        is_legal = is_legal_query(query)
        logger.info(f"Query type detected - Legal: {is_legal}")
        
        # If not a legal query, return a special engine that redirects
        if not is_legal:
            return get_domain_redirect_engine(query)
    
    # Get enhanced system prompt based on query type
    enhanced_system_prompt = get_enhanced_system_prompt(system_prompt, is_legal)

    citation_prompt = os.getenv("SYSTEM_CITATION_PROMPT", None)
    top_k = int(os.getenv("TOP_K", 0))

    # node_postprocessors = []
    # if citation_prompt:
    #     node_postprocessors = [NodeCitationProcessor()]
    #     enhanced_system_prompt = f"{enhanced_system_prompt}\n{citation_prompt}"

    index = get_index(params)
    if index is None:
        raise HTTPException(
            status_code=500,
            detail=str(
                "StorageContext is empty - call 'poetry run generate' to generate the storage first"
            ),
        )

    retriever = index.as_retriever(
        filters=filters, **({"similarity_top_k": top_k} if top_k != 0 else {})
    )

    return CondensePlusContextChatEngine.from_defaults(
        system_prompt=enhanced_system_prompt,
        retriever=retriever,
        # node_postprocessors=node_postprocessors,
    )


def get_easter_egg_engine(easter_egg_response: str):
    """Create a special engine that handles easter egg responses"""
    from llama_index.core.llms import ChatMessage, MessageRole
    from llama_index.core.callbacks import CallbackManager
    
    class EasterEggEngine:
        def __init__(self, easter_egg_message: str):
            self.easter_egg_message = easter_egg_message
            self.callback_manager = CallbackManager([])  # Add callback manager
        
        async def astream_chat(self, message: str, chat_history):
            """Stream the easter egg message"""
            # Create a special response that streams the easter egg message
            class EasterEggResponse:
                def __init__(self, message: str):
                    self.message = message
                    self.source_nodes = []
                
                async def __aiter__(self):
                    # Stream the message word by word for better UX
                    words = self.message.split()
                    for i, word in enumerate(words):
                        if i == 0:
                            yield ChatMessage(role=MessageRole.ASSISTANT, content=word)
                        else:
                            yield ChatMessage(role=MessageRole.ASSISTANT, content=f" {word}")
                
                async def async_response_gen(self):
                    """Async generator for streaming response"""
                    async for chunk in self.__aiter__():
                        # Extract content from ChatMessage
                        if hasattr(chunk, 'content'):
                            yield chunk.content
                        else:
                            yield str(chunk)
                
                def response_gen(self):
                    """Sync generator for streaming response"""
                    import asyncio
                    loop = asyncio.get_event_loop()
                    return loop.run_until_complete(self._sync_gen())
                
                async def _sync_gen(self):
                    """Helper for sync generator"""
                    async for chunk in self.__aiter__():
                        # Extract content from ChatMessage
                        if hasattr(chunk, 'content'):
                            yield chunk.content
                        else:
                            yield str(chunk)
            
            return EasterEggResponse(self.easter_egg_message)
    
    return EasterEggEngine(easter_egg_response)


def get_domain_redirect_engine(query: str):
    """Create a special engine that redirects non-legal queries"""
    from llama_index.core.llms import ChatMessage, MessageRole
    from llama_index.core.settings import Settings
    from llama_index.core.callbacks import CallbackManager
    
    class DomainRedirectEngine:
        def __init__(self, redirect_message: str):
            self.redirect_message = redirect_message
            self.callback_manager = CallbackManager([])  # Add callback manager
        
        async def astream_chat(self, message: str, chat_history):
            """Stream the redirect message"""
            # Create a simple response that streams the redirect message
            class RedirectResponse:
                def __init__(self, message: str):
                    self.message = message
                    self.source_nodes = []
                
                async def __aiter__(self):
                    # Stream the message word by word for better UX
                    words = self.message.split()
                    for i, word in enumerate(words):
                        if i == 0:
                            yield ChatMessage(role=MessageRole.ASSISTANT, content=word)
                        else:
                            yield ChatMessage(role=MessageRole.ASSISTANT, content=f" {word}")
                
                async def async_response_gen(self):
                    """Async generator for streaming response"""
                    async for chunk in self.__aiter__():
                        # Extract content from ChatMessage
                        if hasattr(chunk, 'content'):
                            yield chunk.content
                        else:
                            yield str(chunk)
                
                def response_gen(self):
                    """Sync generator for streaming response"""
                    import asyncio
                    loop = asyncio.get_event_loop()
                    return loop.run_until_complete(self._sync_gen())
                
                async def _sync_gen(self):
                    """Helper for sync generator"""
                    async for chunk in self.__aiter__():
                        # Extract content from ChatMessage
                        if hasattr(chunk, 'content'):
                            yield chunk.content
                        else:
                            yield str(chunk)
            
            return RedirectResponse(self.redirect_message)
    
    redirect_message = get_domain_redirect_response(query)
    return DomainRedirectEngine(redirect_message)
