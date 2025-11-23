#!/usr/bin/env python3
"""
Legal Chat Routes for Nyayantar
Enhanced chat functionality with legal knowledge integration
"""

import json
import logging
from typing import List, Dict, Any, Optional
from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Request,
    status,
    Query,
)
from llama_index.core.llms import MessageRole

from app.api.chat.events import EventCallbackHandler
from app.api.chat.models import (
    ChatData,
    Message,
    Result,
    SourceNodes,
)
from app.api.chat.vercel_response import VercelStreamResponse
from app.api.chat.engine.legal_chat_engine import get_legal_chat_engine
from app.api.chat.engine.query_filter import generate_filters
from app.models.user_model import User
from app.core.user import get_current_user
from app.api.chat.summary import summary_generator
from app.services import conversation_service

legal_chat_router = r = APIRouter()

logger = logging.getLogger("uvicorn")

@r.post("")
async def legal_chat(
    request: Request,
    data: ChatData,
    conversation_id: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
):
    """
    Enhanced chat endpoint with legal knowledge integration
    """
    if not conversation_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Conversation ID is required for authenticated requests.",
        )
    
    try:
        USER_ID = current_user.email
        conversation = await conversation_service.get_or_create_conversation(
            conversation_id
        )
        
        if conversation:
            stored_messages = conversation.get("messages", [])
            incoming_messages = data.messages
            if len(incoming_messages) < len(stored_messages):
                await conversation_service.truncate_conversation(
                    conversation_id, len(incoming_messages), USER_ID
                )

        if conversation.get("summary") == "New Chat":
            if len(data.messages) <= 2:
                summary = await summary_generator(data.messages)
        else:
            try:
                summary = conversation.get("summary")
            except Exception as e:
                summary = "New Chat"
        
        last_message_content = data.get_last_message_content()
        messages = data.get_history_messages()

        await conversation_service.update_conversation(
            conversation_id,
            {"role": MessageRole.USER, "content": last_message_content},
        )

        # Get legal chat engine
        legal_chat_engine = get_legal_chat_engine()
        
        # Convert messages to chat history format
        chat_history = []
        for i in range(0, len(messages) - 1, 2):
            if i + 1 < len(messages):
                user_msg = messages[i].content if messages[i].role == MessageRole.USER else ""
                ai_msg = messages[i + 1].content if messages[i + 1].role == MessageRole.ASSISTANT else ""
                if user_msg and ai_msg:
                    chat_history.append((user_msg, ai_msg))

        # Process with legal chat engine
        response_data = legal_chat_engine.chat(last_message_content, chat_history)
        
        # Extract response and metadata
        final_response = response_data["response"]
        source = response_data["source"]
        metadata = response_data["metadata"]
        
        # Create source nodes for legal responses
        source_nodes = []
        if source in ["FAISS", "QDRANT", "HYBRID", "JSON"]:
            source_nodes = [{
                "node_id": f"legal_{i}",
                "text": metadata.get("results_metadata", [])[i].get("text", "")[:200] + "..." if i < len(metadata.get("results_metadata", [])) else "",
                "metadata": metadata.get("results_metadata", [])[i] if i < len(metadata.get("results_metadata", [])) else {},
                "score": metadata.get("results_metadata", [])[i].get("score", 0.0) if i < len(metadata.get("results_metadata", [])) else 0.0
            } for i in range(min(3, len(metadata.get("results_metadata", []))))]

        # Create suggested questions for legal queries
        suggested_questions = []
        if metadata.get("query_type") == "legal":
            suggested_questions = [
                "What is the punishment for this offense?",
                "What are the essential elements required?",
                "Are there any exceptions to this law?",
                "What is the procedure for filing a case?",
                "What are the recent amendments to this law?"
            ]

        # Update conversation with response
        await conversation_service.update_conversation(
            conversation_id,
            {
                "role": MessageRole.ASSISTANT,
                "content": final_response,
                "annotations": [
                    {"type": "sources", "data": source_nodes},
                    {"type": "suggested_questions", "data": suggested_questions},
                    {"type": "legal_metadata", "data": metadata},
                    {"type": "source_type", "data": source}
                ],
            },
            summary=summary,
            user_id=USER_ID,
        )

        # Return response in the same format as regular chat
        return {
            "response": final_response,
            "source": source,
            "metadata": metadata,
            "source_nodes": source_nodes,
            "suggested_questions": suggested_questions
        }
        
    except Exception as e:
        logger.exception("Error in legal chat engine", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error in legal chat engine: {e}",
        ) from e

@r.get("/legal/stats")
async def get_legal_stats(
    current_user: User = Depends(get_current_user),
):
    """Get legal knowledge base statistics"""
    try:
        legal_chat_engine = get_legal_chat_engine()
        stats = legal_chat_engine.get_legal_knowledge_stats()
        return stats
    except Exception as e:
        logger.error(f"Error getting legal stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting legal stats: {e}",
        ) from e

@r.post("/legal/search")
async def search_legal_sections(
    act_type: str,
    query: str = "",
    limit: int = 5,
    current_user: User = Depends(get_current_user),
):
    """Search legal sections by act type"""
    try:
        legal_chat_engine = get_legal_chat_engine()
        results = legal_chat_engine.search_legal_sections(act_type, query, limit)
        return {
            "act_type": act_type,
            "query": query,
            "results": results,
            "count": len(results)
        }
    except Exception as e:
        logger.error(f"Error searching legal sections: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error searching legal sections: {e}",
        ) from e

@r.post("/legal/enable")
async def enable_legal_system(
    current_user: User = Depends(get_current_user),
):
    """Enable the legal knowledge system"""
    try:
        legal_chat_engine = get_legal_chat_engine()
        legal_chat_engine.enable_legal_system()
        return {"message": "Legal knowledge system enabled", "status": "success"}
    except Exception as e:
        logger.error(f"Error enabling legal system: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error enabling legal system: {e}",
        ) from e

@r.post("/legal/disable")
async def disable_legal_system(
    current_user: User = Depends(get_current_user),
):
    """Disable the legal knowledge system"""
    try:
        legal_chat_engine = get_legal_chat_engine()
        legal_chat_engine.disable_legal_system()
        return {"message": "Legal knowledge system disabled", "status": "success"}
    except Exception as e:
        logger.error(f"Error disabling legal system: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error disabling legal system: {e}",
        ) from e
