from pymilvus import connections, Collection, CollectionSchema, FieldSchema, DataType, utility
import asyncio
from concurrent.futures import ThreadPoolExecutor
from tqdm import tqdm
import torch
import numpy as np
import time
import os
from datetime import datetime
from loguru import logger
from typing import List, Dict, Any, Optional
from sentence_transformers import SentenceTransformer

from config import settings
from schemas import Document

# Global variables
_embedding_model = None

def get_embedding_model():
    """Get or load the embedding model."""
    global _embedding_model
    
    if _embedding_model is None:
        # Check if CUDA is available
        device = "cuda" if torch.cuda.is_available() else "cpu"
        logger.info(f"Loading embedding model {settings.EMBEDDING_MODEL} on {device}")
        
        try:
            # Load the model
            _embedding_model = SentenceTransformer(settings.EMBEDDING_MODEL, device=device)
            logger.info(f"Embedding model loaded successfully on {device}")
        except Exception as e:
            logger.error(f"Error loading embedding model: {e}")
            raise
    
    return _embedding_model

def generate_embeddings(texts: List[str], batch_size: int = 32) -> List[List[float]]:
    """
    Generate embeddings for a list of texts.
    
    Args:
        texts: List of text strings to embed
        batch_size: Batch size for processing
        
    Returns:
        List of embedding vectors
    """
    model = get_embedding_model()
    
    try:
        # Process in batches to avoid OOM issues
        all_embeddings = []
        
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            
            # Generate embeddings
            with torch.no_grad():
                embeddings = model.encode(batch, convert_to_tensor=True)
                
                # Convert to numpy and then to list
                embeddings_np = embeddings.cpu().numpy()
                all_embeddings.append(embeddings_np)
        
        # Concatenate all batches
        if len(all_embeddings) > 1:
            return np.vstack(all_embeddings).tolist()
        elif len(all_embeddings) == 1:
            return all_embeddings[0].tolist()
        else:
            return []
            
    except Exception as e:
        logger.error(f"Error generating embeddings: {e}")
        raise

async def setup_vector_collection():
    """Set up the Milvus collection if it doesn't exist."""
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
            logger.info(f"Collection {settings.MILVUS_COLLECTION} already exists")
            return
        
        # Define fields for the collection
        fields = [
            FieldSchema(name="id", dtype=DataType.VARCHAR, max_length=100, is_primary=True),
            FieldSchema(name="text", dtype=DataType.VARCHAR, max_length=65535),
            FieldSchema(name="metadata", dtype=DataType.JSON),
            FieldSchema(name="source", dtype=DataType.VARCHAR, max_length=1000),
            FieldSchema(name="type", dtype=DataType.VARCHAR, max_length=100),
            FieldSchema(name="server", dtype=DataType.VARCHAR, max_length=100),
            FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=settings.EMBEDDING_DIMENSION)
        ]
        
        # Create schema and collection
        schema = CollectionSchema(fields, "Ashes of Creation knowledge base")
        collection = Collection(settings.MILVUS_COLLECTION, schema)
        
        # Create index for vector search
        index_params = {
            "metric_type": "COSINE",
            "index_type": "HNSW",
            "params": {"M": 8, "efConstruction": 64}
        }
        collection.create_index("embedding", index_params)
        
        logger.info(f"Created collection {settings.MILVUS_COLLECTION} with index")
        
    except Exception as e:
        logger.error(f"Error setting up vector collection: {e}")
        raise

async def index_documents(documents: List[Document]):
    """
    Index documents in the Milvus vector store.
    
    Args:
        documents: List of documents to index
    """
    if not documents:
        logger.warning("No documents provided for indexing")
        return
    
    try:
        # Connect to Milvus
        connections.connect(
            alias="default",
            host=settings.MILVUS_HOST,
            port=settings.MILVUS_PORT,
            user=settings.MILVUS_USER,
            password=settings.MILVUS_PASSWORD
        )
        
        # Get the collection
        collection = Collection(settings.MILVUS_COLLECTION)
        
        # Prepare the data for insertion
        total_docs = len(documents)
        batch_size = 50  # Process in batches of 50 documents
        
        logger.info(f"Indexing {total_docs} documents in batches of {batch_size}")
        
        for i in tqdm(range(0, total_docs, batch_size), desc="Indexing documents"):
            batch = documents[i:i + batch_size]
            
            # Extract document texts
            texts = [doc.text for doc in batch]
            
            # Generate embeddings (CPU-intensive operation)
            with ThreadPoolExecutor() as executor:
                loop = asyncio.get_event_loop()
                embeddings = await loop.run_in_executor(executor, generate_embeddings, texts)
            
            # Prepare batch data for insertion
            ids = [doc.id for doc in batch]
            metadata_json = [doc.metadata.json() for doc in batch]
            sources = [doc.metadata.source for doc in batch]
            types = [doc.metadata.type for doc in batch]
            servers = [doc.metadata.server if doc.metadata.server else "" for doc in batch]
            
            # Insert data into Milvus
            collection.insert([
                ids,           # id field
                texts,         # text field
                metadata_json, # metadata field
                sources,       # source field
                types,         # type field
                servers,       # server field
                embeddings     # embedding field
            ])
            
            # Small delay to avoid overwhelming the server
            await asyncio.sleep(0.1)
        
        # Flush to make sure data is committed
        collection.flush()
        
        # Create an index if it doesn't exist
        if not collection.has_index():
            logger.info("Creating index for vector search")
            index_params = {
                "metric_type": "COSINE",
                "index_type": "HNSW",
                "params": {"M": 8, "efConstruction": 64}
            }
            collection.create_index("embedding", index_params)
        
        logger.info(f"Successfully indexed {total_docs} documents")
        
    except Exception as e:
        logger.error(f"Error indexing documents: {e}")
        raise

async def delete_documents_by_source(source: str):
    """
    Delete documents from the vector store by source.
    
    Args:
        source: Source to match for deletion
    """
    try:
        # Connect to Milvus
        connections.connect(
            alias="default",
            host=settings.MILVUS_HOST,
            port=settings.MILVUS_PORT,
            user=settings.MILVUS_USER,
            password=settings.MILVUS_PASSWORD
        )
        
        # Get the collection
        collection = Collection(settings.MILVUS_COLLECTION)
        
        # Delete by expression
        expr = f"source like '{source}%'"
        collection.delete(expr)
        
        # Flush to make sure data is committed
        collection.flush()
        
        logger.info(f"Deleted documents with source: {source}")
        
    except Exception as e:
        logger.error(f"Error deleting documents: {e}")
        raise

async def query_similar_documents(query_text: str, limit: int = 5, filters: Optional[Dict[str, Any]] = None):
    """
    Query for documents similar to the query text.
    
    Args:
        query_text: The text to find similar documents for
        limit: Maximum number of results to return
        filters: Optional filters to apply (type, server, etc.)
        
    Returns:
        List of documents with similarity scores
    """
    try:
        # Connect to Milvus
        connections.connect(
            alias="default",
            host=settings.MILVUS_HOST,
            port=settings.MILVUS_PORT,
            user=settings.MILVUS_USER,
            password=settings.MILVUS_PASSWORD
        )
        
        # Get the collection
        collection = Collection(settings.MILVUS_COLLECTION)
        
        # Load the collection if not already loaded
        collection.load()
        
        # Generate query embedding
        query_embedding = generate_embeddings([query_text])[0]
        
        # Prepare search parameters
        search_params = {
            "metric_type": "COSINE",
            "params": {"ef": 100}
        }
        
        # Prepare filter expression if filters are provided
        expr = None
        if filters:
            filter_parts = []
            
            if "type" in filters and filters["type"]:
                filter_parts.append(f"type == '{filters['type']}'")
                
            if "server" in filters and filters["server"]:
                filter_parts.append(f"server == '{filters['server']}'")
                
            if filter_parts:
                expr = " && ".join(filter_parts)
        
        # Execute search
        results = collection.search(
            data=[query_embedding],
            anns_field="embedding",
            param=search_params,
            limit=limit,
            expr=expr,
            output_fields=["id", "text", "metadata", "source", "type", "server"]
        )
        
        # Process results
        documents = []
        if results and len(results) > 0:
            for hits in results:
                for hit in hits:
                    documents.append({
                        "id": hit.entity.get("id"),
                        "text": hit.entity.get("text"),
                        "metadata": hit.entity.get("metadata"),
                        "source": hit.entity.get("source"),
                        "type": hit.entity.get("type"),
                        "server": hit.entity.get("server"),
                        "score": hit.score
                    })
        
        return documents
        
    except Exception as e:
        logger.error(f"Error querying similar documents: {e}")
        raise
