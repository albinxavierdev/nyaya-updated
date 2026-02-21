import os
import logging

from app.api.chat.engine.index import get_index
from app.api.chat.engine.retriever_fallback import RetrieverWithEmptyFallback
from app.api.chat.engine.retriever_hybrid import HybridRetriever
from app.db import sync_mongodb
from fastapi import HTTPException
from llama_index.core.chat_engine import CondensePlusContextChatEngine

logger = logging.getLogger(__name__)


def get_system_prompt_from_db():
    config = sync_mongodb.db.config.find_one({"_id": "app_config"})
    if config and "SYSTEM_PROMPT" in config:
        return config["SYSTEM_PROMPT"]
    return None


def get_enhanced_system_prompt(base_prompt: str) -> str:
    identity = (
        "You are Nyayantar AI, India's first Legal AI Agent, developed by Bizfy Solutions. "
        "Always refer to yourself as Nyayantar (or 'I am Nyayantar'). When asked who built or developed you, say Bizfy Solutions. "
        "You specialize in Indian legal matters."
    )
    language_rule = (
        "Users may ask in Hindi, Hinglish, or English. "
        "Understand the language of the user's query and answer in the same language (Hindi, Hinglish, or English) accordingly."
    )
    legal_context = (
        "You have access to Indian legal knowledge (IPC, CrPC, CPC, IEA, family laws, etc.) and, when provided, "
        "web search results for up-to-date or factual information. "
        "For legal questions: use the provided context (documents and any web sources), reference sections/acts when relevant, "
        "explain simply, and state this is educational not legal advice. "
        "When context includes web sources (marked with 'Source: ...'), prefer citing them for factual or recent information to reduce hallucination."
    )
    disclaimer_and_contact = (
        "Disclaimer: If the user requires legal assistance (e.g. representation, case-specific advice, or expert help), "
        "we can assist by connecting them to legal experts. "
        "When the user asks for contact details, legal assistance, or how to get in touch with Nyayantar for expert help, "
        "provide these contact details: Email: hello@nyayantar.com, Phone: +918103682787."
    )
    redirect_rule = (
        "If the question is not about law or legal matters (e.g. medical, technical, financial, tax, cooking, sports, identification of people/things), "
        "do not use the retrieved context. Reply briefly as Nyayantar and suggest the user consult the right expert "
        "(e.g. medical→doctor, technical→IT professional, financial→advisor, tax→CA, recipes→culinary expert). "
        "Keep it to one short sentence."
    )
    return f"{identity}\n\n{language_rule}\n\n{base_prompt}\n\n{legal_context}\n\n{disclaimer_and_contact}\n\n{redirect_rule}"


def get_chat_engine(filters=None, params=None, query=None, event_handler=None):
    system_prompt = get_system_prompt_from_db()
    if system_prompt is None:
        system_prompt = os.getenv("SYSTEM_PROMPT", "You are Nyayantar AI, a helpful AI assistant.")
    system_prompt = get_enhanced_system_prompt(system_prompt)

    index = get_index(params)
    if index is None:
        raise HTTPException(
            status_code=500,
            detail="StorageContext is empty - call 'poetry run generate' to generate the storage first",
        )

    top_k = int(os.getenv("TOP_K", 0))
    base_retriever = index.as_retriever(
        filters=filters, **({"similarity_top_k": top_k} if top_k != 0 else {})
    )
    kb_retriever = RetrieverWithEmptyFallback(base_retriever)
    retriever = HybridRetriever(kb_retriever, event_handler=event_handler)

    return CondensePlusContextChatEngine.from_defaults(
        system_prompt=system_prompt,
        retriever=retriever,
    )
