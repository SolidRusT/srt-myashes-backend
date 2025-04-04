import os
from typing import List, Dict, Any, Optional, Tuple
import json
import httpx
from loguru import logger
from config import settings
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from services.vector_store import query_vector_store

class LLMService:
    """Service for interacting with the Language Model API."""
    
    def __init__(self):
        self.api_key = settings.OPENAI_API_KEY
        self.api_base = settings.OPENAI_API_BASE
        self.model = settings.OPENAI_MODEL
        
        if not self.api_key:
            logger.warning("OPENAI_API_KEY not set. API calls will fail!")
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=30),
        retry=retry_if_exception_type((httpx.ConnectError, httpx.ReadTimeout, httpx.HTTPStatusError))
    )
    async def _make_api_request(self, endpoint: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Make a request to the OpenAI-compatible API."""
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        
        url = f"{self.api_base}/{endpoint}"
        
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            return response.json()
    
    async def get_chat_completion(self, 
                                 messages: List[Dict[str, str]], 
                                 query: str,
                                 server: Optional[str] = None,
                                 temperature: float = 0.7,
                                 max_tokens: int = 2000) -> Tuple[str, List[Dict[str, Any]]]:
        """
        Get a completion from the chat model with enhanced context from the vector store.
        
        Args:
            messages: The conversation history
            query: The current user query
            server: Optional game server to filter results by
            temperature: Randomness of the output (0-1)
            max_tokens: Maximum tokens to generate
            
        Returns:
            Tuple of (response text, relevant context documents)
        """
        # Query the vector store for relevant information
        filters = {"server": server} if server else None
        relevant_docs = query_vector_store(query, limit=settings.VECTOR_SEARCH_TOP_K, filters=filters)
        
        # Format the context
        context_text = "Relevant information from the Ashes of Creation knowledge base:\n\n"
        
        for i, doc in enumerate(relevant_docs, 1):
            context_text += f"[Document {i}]\n"
            context_text += f"Type: {doc.get('type', 'Unknown')}\n"
            if doc.get('server'):
                context_text += f"Server: {doc.get('server')}\n"
            context_text += f"Source: {doc.get('source', 'Unknown')}\n"
            context_text += f"Content: {doc.get('text', '')}\n\n"
        
        # Add system message with game information and context
        system_message = {
            "role": "system",
            "content": f"""You are an expert assistant for the MMORPG game Ashes of Creation. 
Your goal is to provide accurate, helpful information to players based on your knowledge of the game.

{context_text}

When answering questions:
1. Focus on accuracy and cite your sources when possible
2. If information might be server-specific, indicate which server it applies to
3. If you don't know something, admit it rather than making up information
4. For economic questions, specify if prices are estimates and provide ranges
5. When discussing locations, be specific about zone names and nearby landmarks
6. For crafting questions, break down material requirements and provide step-by-step instructions
7. Include appropriate links to official resources or wiki pages when relevant

Current date: 2025-04-03"""
        }
        
        # Prepare the full message list
        full_messages = [system_message] + messages
        
        try:
            # Make the API request
            payload = {
                "model": self.model,
                "messages": full_messages,
                "temperature": temperature,
                "max_tokens": max_tokens,
                "top_p": 1,
                "frequency_penalty": 0,
                "presence_penalty": 0
            }
            
            response = await self._make_api_request("chat/completions", payload)
            
            # Extract the response text
            response_text = response["choices"][0]["message"]["content"]
            
            return response_text, relevant_docs
            
        except Exception as e:
            logger.error(f"Error getting chat completion: {e}")
            return "I'm sorry, I encountered an error processing your request. Please try again.", []
