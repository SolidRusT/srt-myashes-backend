from pymilvus import connections, Collection, utility
from app.config import settings
from loguru import logger
import numpy as np
from typing import List, Dict, Any, Optional
from sentence_transformers import SentenceTransformer
import torch
import os

# Global variables
_vector_store = None
_embedding_model = None

def get_embedding_model():
    """Get the sentence transformer model for embeddings."""
    global _embedding_model
    
    if _embedding_model is None:
        # Check if CUDA is available
        device = "cuda" if torch.cuda.is_available() else "cpu"
        logger.info(f"Loading embedding model on {device}")
        
        # Load the model
        _embedding_model = SentenceTransformer(settings.EMBEDDING_MODEL, device=device)
    
    return _embedding_model

def generate_embeddings(texts: List[str]) -> List[List[float]]:
    """Generate embeddings for a list of texts."""
    model = get_embedding_model()
    embeddings = model.encode(texts, convert_to_tensor=True)
    return embeddings.cpu().numpy().tolist()

def get_vector_store():
    """Get the Milvus vector store client."""
    global _vector_store
    
    if _vector_store is None:
        try:
            # Connect to Milvus
            connections.connect(
                alias="default",
                host=settings.MILVUS_HOST,
                port=settings.MILVUS_PORT,
                user=settings.MILVUS_USER,
                password=settings.MILVUS_PASSWORD
            )
            
            # Check if collection exists
            if utility.has_collection(settings.MILVUS_COLLECTION):
                _vector_store = Collection(settings.MILVUS_COLLECTION)
                _vector_store.load()
            else:
                logger.warning(f"Collection {settings.MILVUS_COLLECTION} does not exist. It will be created during the data pipeline process.")
            
            logger.info(f"Connected to Milvus at {settings.MILVUS_HOST}:{settings.MILVUS_PORT}")
        except Exception as e:
            logger.error(f"Failed to connect to Milvus: {e}")
            raise
    
    return _vector_store

def query_vector_store(query: str, limit: int = 5, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
    """
    Query the vector store with semantic search.
    
    Args:
        query: The search query text
        limit: Maximum number of results to return
        filters: Optional filters to apply to the search
    
    Returns:
        A list of documents with their metadata and relevance scores
    """
    try:
        vector_store = get_vector_store()
        
        if vector_store is None:
            logger.error("Vector store not initialized")
            return []
    except Exception as e:
        logger.error(f"Error accessing vector store: {e}")
        # Return empty results rather than crashing
        return []
    
    try:
        # Generate embedding for the query
        query_embedding = generate_embeddings([query])[0]
        
        # Prepare search parameters
        search_params = {
            "metric_type": "COSINE",
            "params": {"nprobe": 10},
        }
    except Exception as e:
        logger.error(f"Error generating embeddings: {e}")
        return []
    
    # Prepare output fields
    output_fields = ["id", "text", "metadata", "source", "type", "server"]
    
    # Prepare filter expression if filters are provided
    expr = None
    if filters:
        filter_expressions = []
        
        if "type" in filters and filters["type"]:
            filter_expressions.append(f'type == "{filters["type"]}"')
            
        if "server" in filters and filters["server"]:
            filter_expressions.append(f'server == "{filters["server"]}"')
            
        if filter_expressions:
            expr = " && ".join(filter_expressions)
    
    # Execute search
    try:
        results = vector_store.search(
            data=[query_embedding],
            anns_field="embedding",
            param=search_params,
            limit=limit,
            expr=expr,
            output_fields=output_fields,
        )
    except Exception as e:
        logger.error(f"Error searching vector store: {e}")
        return []
    
    # Format results
    formatted_results = []
    for hits in results:
        for hit in hits:
            formatted_results.append({
                "id": hit.entity.get("id"),
                "text": hit.entity.get("text"),
                "metadata": hit.entity.get("metadata"),
                "source": hit.entity.get("source"),
                "type": hit.entity.get("type"),
                "server": hit.entity.get("server"),
                "score": hit.score,
            })
    
    return formatted_results
