from pymilvus import connections, Collection, CollectionSchema, FieldSchema, DataType, utility
import os
import json
import numpy as np
import uuid
from loguru import logger
from typing import List, Dict, Any
import torch
from sentence_transformers import SentenceTransformer
from tqdm import tqdm
import asyncio
from concurrent.futures import ThreadPoolExecutor

# Constants
COLLECTION_NAME = os.getenv("MILVUS_COLLECTION", "ashes_knowledge")
EMBEDDING_DIM = 1024  # Dimension for BGE Large model
MILVUS_HOST = os.getenv("MILVUS_HOST", "localhost")
MILVUS_PORT = int(os.getenv("MILVUS_PORT", "19530"))
MILVUS_USER = os.getenv("MILVUS_USER", "")
MILVUS_PASSWORD = os.getenv("MILVUS_PASSWORD", "")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "BAAI/bge-large-en-v1.5")
BATCH_SIZE = 100  # Number of documents to process at once

# Global variables
_embedding_model = None

def get_embedding_model():
    """Get the sentence transformer model for embeddings."""
    global _embedding_model
    
    if _embedding_model is None:
        # Check if CUDA is available
        device = "cuda" if torch.cuda.is_available() else "cpu"
        logger.info(f"Loading embedding model {EMBEDDING_MODEL} on {device}")
        
        # Load the model
        _embedding_model = SentenceTransformer(EMBEDDING_MODEL, device=device)
    
    return _embedding_model

def generate_embeddings(texts: List[str]) -> List[List[float]]:
    """Generate embeddings for a list of texts."""
    model = get_embedding_model()
    
    # Generate embeddings in batches to avoid OOM issues
    all_embeddings = []
    for i in range(0, len(texts), BATCH_SIZE):
        batch_texts = texts[i:i+BATCH_SIZE]
        batch_embeddings = model.encode(batch_texts, convert_to_tensor=True)
        all_embeddings.append(batch_embeddings.cpu().numpy())
    
    # Concatenate all batches
    if len(all_embeddings) > 1:
        return np.vstack(all_embeddings).tolist()
    elif len(all_embeddings) == 1:
        return all_embeddings[0].tolist()
    else:
        return []

async def setup_vector_collection():
    """Set up the Milvus collection if it doesn't exist."""
    try:
        # Connect to Milvus
        connections.connect(
            alias="default",
            host=MILVUS_HOST,
            port=MILVUS_PORT,
            user=MILVUS_USER,
            password=MILVUS_PASSWORD
        )
        
        # Check if collection exists
        if utility.has_collection(COLLECTION_NAME):
            logger.info(f"Collection {COLLECTION_NAME} already exists")
            return
        
        # Define fields for the collection
        fields = [
            FieldSchema(name="id", dtype=DataType.VARCHAR, max_length=100, is_primary=True),
            FieldSchema(name="text", dtype=DataType.VARCHAR, max_length=65535),
            FieldSchema(name="metadata", dtype=DataType.JSON),  # Store JSON metadata
            FieldSchema(name="source", dtype=DataType.VARCHAR, max_length=1000),
            FieldSchema(name="type", dtype=DataType.VARCHAR, max_length=100),
            FieldSchema(name="server", dtype=DataType.VARCHAR, max_length=100),
            FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=EMBEDDING_DIM)
        ]
        
        # Create schema and collection
        schema = CollectionSchema(fields, "Ashes of Creation knowledge base")
        collection = Collection(COLLECTION_NAME, schema)
        
        # Create index for vector search
        index_params = {
            "metric_type": "COSINE",
            "index_type": "HNSW",
            "params": {"M": 8, "efConstruction": 64}
        }
        collection.create_index("embedding", index_params)
        
        logger.info(f"Created collection {COLLECTION_NAME} with index")
        
    except Exception as e:
        logger.error(f"Error setting up vector collection: {e}")
        raise

async def index_documents(documents: List[Dict[str, Any]]):
    """
    Index documents in the Milvus vector store.
    
    Args:
        documents: List of document dictionaries with text and metadata
    """
    try:
        # Connect to Milvus
        connections.connect(
            alias="default",
            host=MILVUS_HOST,
            port=MILVUS_PORT,
            user=MILVUS_USER,
            password=MILVUS_PASSWORD
        )
        
        # Get the collection
        collection = Collection(COLLECTION_NAME)
        
        # Process in batches
        for i in range(0, len(documents), BATCH_SIZE):
            batch = documents[i:i+BATCH_SIZE]
            
            # Prepare batch data
            ids = [doc.get("id", str(uuid.uuid4())) for doc in batch]
            texts = [doc.get("text", "") for doc in batch]
            metadatas = [json.dumps(doc.get("metadata", {})) for doc in batch]
            sources = [doc.get("source", "") for doc in batch]
            types = [doc.get("type", "general") for doc in batch]
            servers = [doc.get("server", "") for doc in batch]
            
            # Generate embeddings (CPU-intensive)
            with ThreadPoolExecutor() as executor:
                loop = asyncio.get_event_loop()
                embeddings = await loop.run_in_executor(executor, generate_embeddings, texts)
            
            # Insert data
            entities = [
                ids,
                texts,
                metadatas,
                sources,
                types,
                servers,
                embeddings
            ]
            
            collection.insert(entities)
            logger.info(f"Indexed batch of {len(batch)} documents")
        
        # Flush to make sure data is committed
        collection.flush()
        
        # Log completion
        logger.info(f"Successfully indexed {len(documents)} documents")
        
    except Exception as e:
        logger.error(f"Error indexing documents: {e}")
        raise
