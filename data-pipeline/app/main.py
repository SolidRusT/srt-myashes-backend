import os
import time
import asyncio
import schedule
from loguru import logger
import sys
from datetime import datetime
from pathlib import Path

# Set up logging
logger.remove()
logger.add(sys.stdout, level=os.getenv("LOG_LEVEL", "INFO"))
logger.add("logs/data_pipeline_{time}.log", rotation="100 MB", level="INFO")

# Import data processors
from scrapers.wiki_scraper import scrape_ashes_wiki
from scrapers.codex_scraper import scrape_ashes_codex
from scrapers.official_website_scraper import scrape_official_website
from processors.game_files_processor import process_game_files
from indexers.vector_indexer import setup_vector_collection, index_documents
from processors.chunk_processor import chunk_documents

async def run_data_pipeline(force_full_scrape=False):
    """
    Run the complete data pipeline process.
    
    Args:
        force_full_scrape: Whether to force a full scrape instead of incremental
    """
    start_time = time.time()
    logger.info(f"Starting data pipeline run at {datetime.now().isoformat()}")
    
    try:
        # Create data directories if they don't exist
        Path("/data/raw").mkdir(parents=True, exist_ok=True)
        Path("/data/processed").mkdir(parents=True, exist_ok=True)
        Path("/data/images").mkdir(parents=True, exist_ok=True)
        
        # Step 1: Setup Milvus Collection
        logger.info("Setting up Milvus collection...")
        await setup_vector_collection()
        
        # Step 2: Scrape data from sources
        logger.info("Scraping data from sources...")
        
        # Run scrapers in parallel
        scraping_tasks = [
            scrape_ashes_wiki(force_full=force_full_scrape),
            scrape_ashes_codex(force_full=force_full_scrape),
            scrape_official_website(force_full=force_full_scrape)
        ]
        
        # Add game files processing if available
        game_files_path = os.getenv("GAME_FILES_PATH")
        if game_files_path and os.path.exists(game_files_path):
            scraping_tasks.append(process_game_files(game_files_path))
        
        # Wait for all scraping tasks to complete
        await asyncio.gather(*scraping_tasks)
        
        # Step 3: Process and chunk the documents
        logger.info("Processing and chunking documents...")
        documents = await chunk_documents("/data/raw", "/data/processed")
        
        # Step 4: Index documents in vector store
        logger.info(f"Indexing {len(documents)} documents in vector store...")
        await index_documents(documents)
        
        # Log completion
        duration = time.time() - start_time
        logger.info(f"Data pipeline completed in {duration:.2f} seconds")
        
    except Exception as e:
        logger.error(f"Error in data pipeline: {e}")
        raise

def schedule_pipeline():
    """Schedule the data pipeline to run at regular intervals."""
    # Get interval from environment (default to 24 hours)
    interval_seconds = int(os.getenv("SCRAPE_INTERVAL", "86400"))
    
    # Convert to hours for more readable logging
    interval_hours = interval_seconds / 3600
    
    logger.info(f"Scheduling data pipeline to run every {interval_hours:.1f} hours")
    
    # Schedule the pipeline
    schedule.every(interval_seconds).seconds.do(lambda: asyncio.run(run_data_pipeline()))
    
    # Run immediately on startup
    asyncio.run(run_data_pipeline(force_full_scrape=True))
    
    # Keep the scheduler running
    while True:
        schedule.run_pending()
        time.sleep(1)

if __name__ == "__main__":
    logger.info("Starting Ashes of Creation data pipeline service")
    
    # If running in development mode with the --dev flag, run once and exit
    if len(sys.argv) > 1 and sys.argv[1] == "--dev":
        logger.info("Running in development mode (one-time execution)")
        asyncio.run(run_data_pipeline(force_full_scrape=True))
    else:
        # Otherwise, run on a schedule
        schedule_pipeline()
