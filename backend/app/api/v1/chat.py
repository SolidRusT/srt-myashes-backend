from fastapi import APIRouter, Depends, HTTPException, status, Body
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
import uuid
from datetime import datetime
from app.services.llm_service import LLMService
from app.services.cache_service import set_cache, get_cache_value
from loguru import logger

router = APIRouter()

# Service instance
llm_service = LLMService()

# Models for request and response
class Message(BaseModel):
    role: str = Field(..., description="The role of the message sender (user or assistant)")
    content: str = Field(..., description="The content of the message")
    timestamp: Optional[datetime] = Field(None, description="Message timestamp")

class ChatRequest(BaseModel):
    messages: List[Message] = Field(..., description="The conversation history")
    server: Optional[str] = Field(None, description="The game server context (if applicable)")
    temperature: Optional[float] = Field(0.7, description="Temperature for response generation")
    
class ContextDocument(BaseModel):
    id: str = Field(..., description="Document ID")
    text: str = Field(..., description="Document text content")
    source: str = Field(..., description="Source of the document")
    type: str = Field(..., description="Type of the document")
    server: Optional[str] = Field(None, description="Server-specific information (if applicable)")
    score: float = Field(..., description="Relevance score")

class ChatResponse(BaseModel):
    id: str = Field(..., description="Response ID")
    response: str = Field(..., description="AI assistant response")
    context_documents: List[ContextDocument] = Field([], description="Relevant documents used for context")
    timestamp: datetime = Field(..., description="Response timestamp")

@router.post("/completions", response_model=ChatResponse, status_code=status.HTTP_200_OK)
async def chat_completion(request: ChatRequest = Body(...)):
    """
    Get a chat completion response from the AI assistant.
    
    This endpoint processes a chat conversation and returns a response from the AI,
    along with the relevant context documents used to generate the response.
    """
    try:
        # Format messages for the LLM service
        formatted_messages = [
            {"role": msg.role, "content": msg.content}
            for msg in request.messages
        ]
        
        # Extract the latest user message as the query
        latest_user_message = next(
            (msg.content for msg in reversed(request.messages) if msg.role == "user"),
            ""
        )
        
        # Get completion from LLM service
        response_text, context_docs = await llm_service.get_chat_completion(
            messages=formatted_messages,
            query=latest_user_message,
            server=request.server,
            temperature=request.temperature
        )
        
        # Format context documents
        formatted_context = [
            ContextDocument(
                id=str(doc.get("id", "")),
                text=doc.get("text", ""),
                source=doc.get("source", ""),
                type=doc.get("type", ""),
                server=doc.get("server"),
                score=float(doc.get("score", 0))
            )
            for doc in context_docs
        ]
        
        # Create response
        response_id = str(uuid.uuid4())
        response = ChatResponse(
            id=response_id,
            response=response_text,
            context_documents=formatted_context,
            timestamp=datetime.now()
        )
        
        return response
        
    except Exception as e:
        logger.error(f"Error in chat completion: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while processing your request."
        )

@router.get("/history/{session_id}", response_model=List[Message])
async def get_chat_history(session_id: str):
    """
    Get the chat history for a specific session.
    """
    try:
        # Get chat history from cache
        cache_key = f"chat:history:{session_id}"
        chat_history = await get_cache_value(cache_key, [])
        
        # Format and return as Message objects
        return [
            Message(
                role=msg.get("role", "unknown"),
                content=msg.get("content", ""),
                timestamp=datetime.fromisoformat(msg.get("timestamp")) if msg.get("timestamp") else None
            )
            for msg in chat_history
        ]
        
    except Exception as e:
        logger.error(f"Error getting chat history: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while retrieving chat history."
        )

@router.post("/history/{session_id}", status_code=status.HTTP_201_CREATED)
async def save_chat_history(session_id: str, messages: List[Message] = Body(...)):
    """
    Save the chat history for a specific session.
    """
    try:
        # Format messages for storage
        formatted_messages = [
            {
                "role": msg.role,
                "content": msg.content,
                "timestamp": msg.timestamp.isoformat() if msg.timestamp else datetime.now().isoformat()
            }
            for msg in messages
        ]
        
        # Save to cache
        cache_key = f"chat:history:{session_id}"
        await set_cache(cache_key, formatted_messages, expire=86400 * 30)  # 30 days
        
        return {"status": "success", "message": "Chat history saved successfully"}
        
    except Exception as e:
        logger.error(f"Error saving chat history: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while saving chat history."
        )
