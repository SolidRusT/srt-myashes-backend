import os
import json
import uuid
from typing import List, Dict, Any, Optional
from loguru import logger
import re
from pathlib import Path
import asyncio
from glob import glob

# Constants
MAX_CHUNK_SIZE = 1024  # Maximum chunk size in characters
MIN_CHUNK_SIZE = 50    # Minimum chunk size in characters
OVERLAP_SIZE = 100     # Overlap between chunks in characters

async def load_raw_documents(raw_data_dir: str) -> List[Dict[str, Any]]:
    """
    Load raw documents from the data directory.
    
    Args:
        raw_data_dir: Directory containing raw JSON documents
        
    Returns:
        List of document dictionaries
    """
    documents = []
    
    # Get all JSON files
    json_files = glob(f"{raw_data_dir}/**/*.json", recursive=True)
    
    for file_path in json_files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                file_data = json.load(f)
                
                # Handle both single documents and arrays of documents
                if isinstance(file_data, list):
                    documents.extend(file_data)
                else:
                    documents.append(file_data)
                    
        except Exception as e:
            logger.error(f"Error loading document {file_path}: {e}")
    
    logger.info(f"Loaded {len(documents)} raw documents")
    return documents

def chunk_text(text: str, metadata: Dict[str, Any], source: str, doc_type: str, server: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Split text into chunks with possible overlap.
    
    Args:
        text: Text to chunk
        metadata: Metadata for the document
        source: Source of the document
        doc_type: Type of the document
        server: Server-specific information (if applicable)
        
    Returns:
        List of chunk dictionaries
    """
    chunks = []
    
    # If text is too short for chunking, return as a single chunk
    if len(text) <= MAX_CHUNK_SIZE:
        chunk_id = str(uuid.uuid4())
        chunks.append({
            "id": chunk_id,
            "text": text,
            "metadata": {**metadata, "chunk_index": 0},
            "source": source,
            "type": doc_type,
            "server": server
        })
        return chunks
    
    # Split by paragraphs first to try to preserve context
    paragraphs = re.split(r'\n\s*\n', text)
    
    current_chunk = []
    current_size = 0
    chunk_index = 0
    
    for para in paragraphs:
        para_size = len(para)
        
        # If a single paragraph is too large, split it by sentences
        if para_size > MAX_CHUNK_SIZE:
            sentences = re.split(r'(?<=[.!?])\s+', para)
            for sentence in sentences:
                sentence_size = len(sentence)
                
                # If adding this sentence would exceed max size, create a chunk and start a new one
                if current_size + sentence_size > MAX_CHUNK_SIZE and current_size > MIN_CHUNK_SIZE:
                    chunk_text = "\n\n".join(current_chunk)
                    chunk_id = str(uuid.uuid4())
                    chunks.append({
                        "id": chunk_id,
                        "text": chunk_text,
                        "metadata": {**metadata, "chunk_index": chunk_index},
                        "source": source,
                        "type": doc_type,
                        "server": server
                    })
                    
                    # Start a new chunk with overlap
                    overlap_text = current_chunk[-1] if current_chunk else ""
                    current_chunk = [overlap_text] if overlap_text else []
                    current_size = len(overlap_text) if overlap_text else 0
                    chunk_index += 1
                
                current_chunk.append(sentence)
                current_size += sentence_size
        else:
            # If adding this paragraph would exceed max size, create a chunk and start a new one
            if current_size + para_size > MAX_CHUNK_SIZE and current_size > MIN_CHUNK_SIZE:
                chunk_text = "\n\n".join(current_chunk)
                chunk_id = str(uuid.uuid4())
                chunks.append({
                    "id": chunk_id,
                    "text": chunk_text,
                    "metadata": {**metadata, "chunk_index": chunk_index},
                    "source": source,
                    "type": doc_type,
                    "server": server
                })
                
                # Start a new chunk with overlap
                overlap_text = current_chunk[-1] if current_chunk else ""
                current_chunk = [overlap_text] if overlap_text else []
                current_size = len(overlap_text) if overlap_text else 0
                chunk_index += 1
            
            current_chunk.append(para)
            current_size += para_size
    
    # Add the final chunk if there's content left
    if current_chunk:
        chunk_text = "\n\n".join(current_chunk)
        chunk_id = str(uuid.uuid4())
        chunks.append({
            "id": chunk_id,
            "text": chunk_text,
            "metadata": {**metadata, "chunk_index": chunk_index},
            "source": source,
            "type": doc_type,
            "server": server
        })
    
    return chunks

async def chunk_documents(raw_data_dir: str, processed_data_dir: str) -> List[Dict[str, Any]]:
    """
    Process and chunk raw documents into smaller pieces for efficient indexing.
    
    Args:
        raw_data_dir: Directory containing raw documents
        processed_data_dir: Directory to store processed chunks
        
    Returns:
        List of processed document chunks
    """
    # Load raw documents
    raw_documents = await load_raw_documents(raw_data_dir)
    all_chunks = []
    
    # Process each document
    for doc in raw_documents:
        text = doc.get("text", doc.get("content", ""))
        metadata = doc.get("metadata", {})
        source = doc.get("source", "unknown")
        doc_type = doc.get("type", "general")
        server = doc.get("server", None)
        
        # Skip if no text content
        if not text:
            continue
        
        # Chunk the document
        chunks = chunk_text(text, metadata, source, doc_type, server)
        all_chunks.extend(chunks)
    
    # Save processed chunks
    os.makedirs(processed_data_dir, exist_ok=True)
    
    # Group chunks by type for organization
    chunks_by_type = {}
    for chunk in all_chunks:
        chunk_type = chunk.get("type", "general")
        if chunk_type not in chunks_by_type:
            chunks_by_type[chunk_type] = []
        chunks_by_type[chunk_type].append(chunk)
    
    # Save each type to a separate file
    for chunk_type, chunks in chunks_by_type.items():
        output_path = os.path.join(processed_data_dir, f"{chunk_type}_chunks.json")
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(chunks, f, ensure_ascii=False, indent=2)
    
    logger.info(f"Processed {len(raw_documents)} documents into {len(all_chunks)} chunks")
    return all_chunks
