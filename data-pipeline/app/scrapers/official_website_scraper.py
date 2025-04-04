import os
import json
import asyncio
import aiohttp
from bs4 import BeautifulSoup
from datetime import datetime
from loguru import logger
from typing import List, Dict, Any, Optional, Set
import re
import time
from pathlib import Path
from playwright.async_api import async_playwright
from tqdm.asyncio import tqdm
import uuid

from config import settings
from schemas import (
    Race, RacialTrait, Archetype, Class, 
    Document, DocumentMetadata, Zone
)

# Constants
OFFICIAL_BASE_URL = settings.OFFICIAL_URL
DATA_DIR = os.path.join(settings.RAW_DATA_DIR, "official")
USER_AGENT = settings.USER_AGENT

# URLs to scrape by category
SCRAPE_URLS = {
    "races": ["/races"],
    "archetypes": ["/archetypes"],
    "world": ["/world", "/world/environments", "/world/nodes"],
    "wiki": ["/wiki"],
    "media": ["/media/latest-news"]
}

async def save_json(data: Any, filename: str, category: str):
    """Save data to a JSON file."""
    # Create directory if it doesn't exist
    os.makedirs(os.path.join(DATA_DIR, category), exist_ok=True)
    
    # Save the file
    file_path = os.path.join(DATA_DIR, category, f"{filename}.json")
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    logger.debug(f"Saved {file_path}")

async def get_last_scrape_time(category: str) -> float:
    """Get the timestamp of the last scrape for a category."""
    timestamp_file = os.path.join(DATA_DIR, category, "_last_scrape.txt")
    
    try:
        if os.path.exists(timestamp_file):
            with open(timestamp_file, 'r') as f:
                return float(f.read().strip())
    except Exception as e:
        logger.error(f"Error reading last scrape time: {e}")
    
    return 0  # Default to epoch start if no timestamp exists

async def update_last_scrape_time(category: str):
    """Update the timestamp of the last scrape for a category."""
    timestamp_file = os.path.join(DATA_DIR, category, "_last_scrape.txt")
    
    # Create directory if it doesn't exist
    os.makedirs(os.path.join(DATA_DIR, category), exist_ok=True)
    
    # Update timestamp
    with open(timestamp_file, 'w') as f:
        f.write(str(time.time()))

async def scrape_races_page(browser):
    """Scrape information about playable races."""
    try:
        logger.info("Scraping races data")
        
        # Navigate to the races page
        page = await browser.new_page()
        await page.goto(f"{OFFICIAL_BASE_URL}/races", wait_until="networkidle")
        
        # Extract the page content
        content = await page.content()
        soup = BeautifulSoup(content, 'html.parser')
        
        # Find the main content section
        main_content = soup.select_one('.main-content')
        if not main_content:
            logger.error("Could not find main content section on races page")
            return []
        
        # Find race sections
        race_sections = main_content.select('.race-section')
        races = []
        
        for section in race_sections:
            try:
                # Extract race name
                race_name_elem = section.select_one('.race-name')
                race_name = race_name_elem.text.strip() if race_name_elem else "Unknown Race"
                
                # Extract race description
                race_desc_elem = section.select_one('.race-description')
                race_description = race_desc_elem.text.strip() if race_desc_elem else ""
                
                # Extract racial traits
                traits_section = section.select('.racial-trait')
                racial_traits = []
                
                for trait in traits_section:
                    trait_name_elem = trait.select_one('.trait-name')
                    trait_desc_elem = trait.select_one('.trait-description')
                    
                    if trait_name_elem and trait_desc_elem:
                        racial_traits.append(
                            RacialTrait(
                                name=trait_name_elem.text.strip(),
                                description=trait_desc_elem.text.strip()
                            )
                        )
                
                # Create race object
                race = Race(
                    id=str(uuid.uuid4()),
                    name=race_name,
                    description=race_description,
                    racial_traits=racial_traits
                )
                
                races.append(race)
                
            except Exception as e:
                logger.error(f"Error parsing race section: {e}")
        
        # Create documents for vector storage
        documents = []
        for race in races:
            # Create document for the race
            trait_text = "\n".join([f"{trait.name}: {trait.description}" for trait in race.racial_traits])
            
            doc_text = f"""
            Race: {race.name}
            
            Description:
            {race.description}
            
            Racial Traits:
            {trait_text}
            """
            
            document = Document(
                id=f"race-{race.id}",
                text=doc_text.strip(),
                metadata=DocumentMetadata(
                    id=race.id,
                    type="race",
                    source=f"{OFFICIAL_BASE_URL}/races",
                    server=None,
                    timestamp=datetime.now().isoformat()
                )
            )
            
            documents.append(document)
        
        # Save the race data
        race_data = [race.dict() for race in races]
        await save_json(race_data, "races", "races")
        
        # Also save each document for indexing
        await save_json([doc.dict() for doc in documents], "race_documents", "races")
        
        logger.info(f"Scraped {len(races)} races from official website")
        
        # Close the page
        await page.close()
        
        return documents
    
    except Exception as e:
        logger.error(f"Error scraping races page: {e}")
        return []

async def scrape_archetypes_page(browser):
    """Scrape information about character archetypes and classes."""
    try:
        logger.info("Scraping archetypes data")
        
        # Navigate to the archetypes page
        page = await browser.new_page()
        await page.goto(f"{OFFICIAL_BASE_URL}/archetypes", wait_until="networkidle")
        
        # Extract the page content
        content = await page.content()
        soup = BeautifulSoup(content, 'html.parser')
        
        # Find the main content section
        main_content = soup.select_one('.main-content')
        if not main_content:
            logger.error("Could not find main content section on archetypes page")
            return []
        
        # Find archetype sections
        archetype_sections = main_content.select('.archetype-section')
        archetypes = []
        
        for section in archetype_sections:
            try:
                # Extract archetype name
                archetype_name_elem = section.select_one('.archetype-name')
                archetype_name = archetype_name_elem.text.strip() if archetype_name_elem else "Unknown Archetype"
                
                # Extract archetype description
                archetype_desc_elem = section.select_one('.archetype-description')
                archetype_description = archetype_desc_elem.text.strip() if archetype_desc_elem else ""
                
                # Create archetype object
                archetype = Archetype(
                    id=str(uuid.uuid4()),
                    name=archetype_name,
                    description=archetype_description
                )
                
                archetypes.append(archetype)
                
            except Exception as e:
                logger.error(f"Error parsing archetype section: {e}")
        
        # Find class information
        class_sections = main_content.select('.class-combination')
        classes = []
        
        for section in class_sections:
            try:
                # Extract class name
                class_name_elem = section.select_one('.class-name')
                class_name = class_name_elem.text.strip() if class_name_elem else "Unknown Class"
                
                # Extract primary and secondary archetypes
                archetypes_elem = section.select_one('.class-archetypes')
                if archetypes_elem:
                    archetype_text = archetypes_elem.text.strip()
                    # Try to parse "Primary + Secondary" format
                    match = re.search(r'(\w+)\s*\+\s*(\w+)', archetype_text)
                    if match:
                        primary = match.group(1).strip()
                        secondary = match.group(2).strip()
                    else:
                        # Fallback
                        primary = "Unknown"
                        secondary = "Unknown"
                else:
                    primary = "Unknown"
                    secondary = "Unknown"
                
                # Extract class description
                class_desc_elem = section.select_one('.class-description')
                class_description = class_desc_elem.text.strip() if class_desc_elem else ""
                
                # Create class object
                class_obj = Class(
                    id=str(uuid.uuid4()),
                    name=class_name,
                    primary=primary,
                    secondary=secondary,
                    description=class_description
                )
                
                classes.append(class_obj)
                
            except Exception as e:
                logger.error(f"Error parsing class section: {e}")
        
        # Create documents for vector storage
        documents = []
        
        # Add archetype documents
        for archetype in archetypes:
            doc_text = f"""
            Archetype: {archetype.name}
            
            Description:
            {archetype.description}
            """
            
            document = Document(
                id=f"archetype-{archetype.id}",
                text=doc_text.strip(),
                metadata=DocumentMetadata(
                    id=archetype.id,
                    type="archetype",
                    source=f"{OFFICIAL_BASE_URL}/archetypes",
                    server=None,
                    timestamp=datetime.now().isoformat()
                )
            )
            
            documents.append(document)
        
        # Add class documents
        for class_obj in classes:
            doc_text = f"""
            Class: {class_obj.name}
            Primary Archetype: {class_obj.primary}
            Secondary Archetype: {class_obj.secondary}
            
            Description:
            {class_obj.description}
            """
            
            document = Document(
                id=f"class-{class_obj.id}",
                text=doc_text.strip(),
                metadata=DocumentMetadata(
                    id=class_obj.id,
                    type="class",
                    source=f"{OFFICIAL_BASE_URL}/archetypes",
                    server=None,
                    timestamp=datetime.now().isoformat()
                )
            )
            
            documents.append(document)
        
        # Save the archetype and class data
        archetype_data = [archetype.dict() for archetype in archetypes]
        class_data = [class_obj.dict() for class_obj in classes]
        
        await save_json(archetype_data, "archetypes", "archetypes")
        await save_json(class_data, "classes", "archetypes")
        
        # Also save each document for indexing
        await save_json([doc.dict() for doc in documents], "archetype_documents", "archetypes")
        
        logger.info(f"Scraped {len(archetypes)} archetypes and {len(classes)} classes from official website")
        
        # Close the page
        await page.close()
        
        return documents
    
    except Exception as e:
        logger.error(f"Error scraping archetypes page: {e}")
        return []

async def scrape_world_page(browser):
    """Scrape information about the game world."""
    try:
        logger.info("Scraping world data")
        
        # Navigate to the world page
        page = await browser.new_page()
        await page.goto(f"{OFFICIAL_BASE_URL}/world", wait_until="networkidle")
        
        # Extract the page content
        content = await page.content()
        soup = BeautifulSoup(content, 'html.parser')
        
        # Find the main content section
        main_content = soup.select_one('.main-content')
        if not main_content:
            logger.error("Could not find main content section on world page")
            return []
        
        # Find zone/region sections
        zone_sections = main_content.select('.zone-section')
        zones = []
        
        for section in zone_sections:
            try:
                # Extract zone name
                zone_name_elem = section.select_one('.zone-name')
                zone_name = zone_name_elem.text.strip() if zone_name_elem else "Unknown Zone"
                
                # Extract zone type
                zone_type_elem = section.select_one('.zone-type')
                zone_type = zone_type_elem.text.strip() if zone_type_elem else "Unknown"
                
                # Extract zone region
                zone_region_elem = section.select_one('.zone-region')
                zone_region = zone_region_elem.text.strip() if zone_region_elem else "Unknown Region"
                
                # Extract zone description
                zone_desc_elem = section.select_one('.zone-description')
                zone_description = zone_desc_elem.text.strip() if zone_desc_elem else ""
                
                # Extract zone level range
                zone_level_elem = section.select_one('.zone-level')
                zone_level = zone_level_elem.text.strip() if zone_level_elem else None
                
                # Extract points of interest
                poi_elems = section.select('.zone-poi')
                points_of_interest = [poi.text.strip() for poi in poi_elems if poi.text.strip()]
                
                # Extract resources
                resource_elems = section.select('.zone-resource')
                resources = [res.text.strip() for res in resource_elems if res.text.strip()]
                
                # Create zone object
                zone = Zone(
                    id=str(uuid.uuid4()),
                    name=zone_name,
                    type=zone_type,
                    region=zone_region,
                    level_range=zone_level,
                    description=zone_description,
                    points_of_interest=points_of_interest,
                    resources=resources,
                    nodes=[]  # Would need more detailed scraping for nodes
                )
                
                zones.append(zone)
                
            except Exception as e:
                logger.error(f"Error parsing zone section: {e}")
        
        # Create documents for vector storage
        documents = []
        for zone in zones:
            # Format points of interest and resources for text
            poi_text = "\n".join(zone.points_of_interest) if zone.points_of_interest else ""
            resources_text = "\n".join(zone.resources) if zone.resources else ""
            
            doc_text = f"""
            Zone: {zone.name}
            Type: {zone.type}
            Region: {zone.region}
            Level Range: {zone.level_range or 'Unknown'}
            
            Description:
            {zone.description}
            
            Points of Interest:
            {poi_text}
            
            Resources:
            {resources_text}
            """
            
            document = Document(
                id=f"zone-{zone.id}",
                text=doc_text.strip(),
                metadata=DocumentMetadata(
                    id=zone.id,
                    type="zone",
                    source=f"{OFFICIAL_BASE_URL}/world",
                    server=None,
                    timestamp=datetime.now().isoformat()
                )
            )
            
            documents.append(document)
        
        # Save the zone data
        zone_data = [zone.dict() for zone in zones]
        await save_json(zone_data, "zones", "world")
        
        # Also save each document for indexing
        await save_json([doc.dict() for doc in documents], "world_documents", "world")
        
        logger.info(f"Scraped {len(zones)} zones from official website")
        
        # Close the page
        await page.close()
        
        return documents
    
    except Exception as e:
        logger.error(f"Error scraping world page: {e}")
        return []

async def scrape_news_page(browser, limit: int = 10):
    """Scrape recent news articles."""
    try:
        logger.info("Scraping news data")
        
        # Navigate to the news page
        page = await browser.new_page()
        await page.goto(f"{OFFICIAL_BASE_URL}/media/latest-news", wait_until="networkidle")
        
        # Extract the page content
        content = await page.content()
        soup = BeautifulSoup(content, 'html.parser')
        
        # Find the news article sections
        article_sections = soup.select('.news-article')[:limit]  # Limit to the most recent articles
        articles = []
        
        for section in article_sections:
            try:
                # Extract article title
                title_elem = section.select_one('.article-title')
                title = title_elem.text.strip() if title_elem else "Unknown Article"
                
                # Extract article date
                date_elem = section.select_one('.article-date')
                date = date_elem.text.strip() if date_elem else "Unknown Date"
                
                # Extract article URL
                url_elem = section.select_one('a')
                url = url_elem['href'] if url_elem and 'href' in url_elem.attrs else ""
                
                # If URL is relative, make it absolute
                if url and not url.startswith('http'):
                    url = f"{OFFICIAL_BASE_URL}{url if url.startswith('/') else '/' + url}"
                
                # Extract article summary
                summary_elem = section.select_one('.article-summary')
                summary = summary_elem.text.strip() if summary_elem else ""
                
                # Create article object
                article = {
                    "id": str(uuid.uuid4()),
                    "title": title,
                    "date": date,
                    "url": url,
                    "summary": summary,
                    "content": None  # Full content would require visiting each article page
                }
                
                articles.append(article)
                
            except Exception as e:
                logger.error(f"Error parsing news article: {e}")
        
        # Create documents for vector storage
        documents = []
        for article in articles:
            doc_text = f"""
            News Article: {article['title']}
            Date: {article['date']}
            
            Summary:
            {article['summary']}
            
            Read more: {article['url']}
            """
            
            document = Document(
                id=f"news-{article['id']}",
                text=doc_text.strip(),
                metadata=DocumentMetadata(
                    id=article['id'],
                    type="news",
                    source=article['url'] or f"{OFFICIAL_BASE_URL}/media/latest-news",
                    server=None,
                    timestamp=datetime.now().isoformat()
                )
            )
            
            documents.append(document)
        
        # Save the news data
        await save_json(articles, "news", "media")
        
        # Also save each document for indexing
        await save_json([doc.dict() for doc in documents], "news_documents", "media")
        
        logger.info(f"Scraped {len(articles)} news articles from official website")
        
        # Close the page
        await page.close()
        
        return documents
    
    except Exception as e:
        logger.error(f"Error scraping news page: {e}")
        return []

async def scrape_official_website(force_full: bool = False):
    """Main function to scrape the official Ashes of Creation website."""
    logger.info("Starting official website scraper")
    
    try:
        # Create base directory if it doesn't exist
        os.makedirs(DATA_DIR, exist_ok=True)
        
        # Initialize browser
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            
            # Track all documents for combined storage
            all_documents = []
            
            # Scrape races
            race_docs = await scrape_races_page(browser)
            all_documents.extend(race_docs)
            
            # Scrape archetypes and classes
            archetype_docs = await scrape_archetypes_page(browser)
            all_documents.extend(archetype_docs)
            
            # Scrape world information
            world_docs = await scrape_world_page(browser)
            all_documents.extend(world_docs)
            
            # Scrape news
            news_docs = await scrape_news_page(browser)
            all_documents.extend(news_docs)
            
            # Save all documents in a single file for easier processing
            await save_json([doc.dict() for doc in all_documents], "all_documents", "")
            
            # Update last scrape time for each category
            for category in SCRAPE_URLS.keys():
                await update_last_scrape_time(category)
            
            # Close the browser
            await browser.close()
            
            logger.info(f"Completed official website scraping with {len(all_documents)} documents")
            
    except Exception as e:
        logger.error(f"Error in official website scraper: {e}")

if __name__ == "__main__":
    # For testing the module directly
    asyncio.run(scrape_official_website(force_full=True))
