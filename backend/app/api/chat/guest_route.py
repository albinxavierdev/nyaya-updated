import json
import logging
from typing import Optional
from fastapi import (
    APIRouter,
    HTTPException,
    Request,
    status,
)
from fastapi.responses import StreamingResponse
from llama_index.core.llms import MessageRole

from app.api.chat.events import EventCallbackHandler
from app.api.chat.models import ChatData
from app.api.chat.vercel_response import VercelStreamResponse
from app.api.chat.engine import get_chat_engine
from app.api.chat.engine.query_filter import generate_filters

guest_router = r = APIRouter()

logger = logging.getLogger("uvicorn")


@r.post("")
async def guest_chat(
    request: Request,
    data: ChatData,
):
    """
    Guest chat endpoint for unauthenticated users.
    Does not require authentication or conversation persistence.
    """
    try:
        last_message_content = data.get_last_message_content()
        messages = data.get_history_messages()

        doc_ids = data.get_chat_document_ids()
        filters = generate_filters(doc_ids)
        params = data.data or {}
        
        logger.info(
            f"Guest chat request with filters: {str(filters)}",
        )
        
        # Pass the query to enable legal context detection
        chat_engine = get_chat_engine(filters=filters, params=params, query=last_message_content)

        event_handler = EventCallbackHandler()
        chat_engine.callback_manager.handlers.append(event_handler)  # type: ignore

        response = await chat_engine.astream_chat(last_message_content, messages)

        final_response = ""
        suggested_questions = []
        source_nodes = []
        event = []
        tools = []

        async def enhanced_content_generator():
            nonlocal final_response, suggested_questions, source_nodes, event, tools
            async for chunk in VercelStreamResponse.content_generator(
                request, event_handler, response, data
            ):
                yield chunk

                if chunk.startswith(VercelStreamResponse.TEXT_PREFIX):
                    final_response += json.loads(chunk[2:].strip())
                elif chunk.startswith(VercelStreamResponse.DATA_PREFIX):
                    data_chunk = json.loads(chunk[2:].strip())[0]
                    if data_chunk["type"] == "suggested_questions":
                        suggested_questions = data_chunk["data"]
                    elif data_chunk["type"] == "sources":
                        try:
                            source_nodes = data_chunk["data"]
                        except Exception:
                            source_nodes = []
                    elif data_chunk["type"] == "events":
                        try:
                            event = data_chunk["data"]
                        except Exception:
                            event = []
                    elif data_chunk["type"] == "tools":
                        try:
                            tools = data_chunk["data"]
                        except Exception:
                            tools = []

            # Note: Guest conversations are not saved to database
            logger.info(f"Guest chat completed. Response length: {len(final_response)}")

        return VercelStreamResponse(
            request,
            event_handler,
            response,
            chat_data=data,
            content=enhanced_content_generator(),
        )
    except Exception as e:
        logger.exception("Error in guest chat engine", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error in guest chat engine: {e}",
        ) from e
