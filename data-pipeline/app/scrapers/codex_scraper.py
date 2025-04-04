import os
import json
import asyncio
import aiohttp
from bs4 import BeautifulSoup
from loguru import logger
from typing import List, Dict, Any, Set
import re
from pathlib import Path
from playwright.async_api import async_playwright
from tqdm.asyncio import tqdm_asyncio
import time

# Constants
CODEX_BASE_URL = "https://ashescodex.com"
DATA_DIR = "/data/raw/codex"
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"

# URLs to scrape by category
SCRAPE_URLS = {
    "items": [
        "/items",
        "/items/weapons",
        "/items/armor",
        "/items/accessories",
        "/items/resources",
        "/items/tools",
        "/items/consumables",
    ],
    "locations": [
        "/world/nodes",
        "/world/points-of-interest",
        "/world/resources",
    ],
    "crafting": [
        "/crafting/recipes",
        "/crafting/professions",
    ],
    "character": [
        "/character/archetypes",
        "/character/classes",
        "/character/races",
        "/character/builds",
    ],
}

async def save_json(data: Dict[str, Any], filename: str, category: str):
    """Save data to a JSON file."""
    # Create directory if it doesn't exist
    os.makedirs(f"{DATA_DIR}/{category}", exist_ok=True)
    
    # Save the file
    file_path = f"{DATA_DIR}/{category}/{filename}.json"
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    logger.debug(f"Saved {file_path}")

async def get_last_scrape_time(category: str) -> float:
    """Get the timestamp of the last scrape for a category."""
    timestamp_file = f"{DATA_DIR}/{category}/_last_scrape.txt"
    
    try:
        if os.path.exists(timestamp_file):
            with open(timestamp_file, 'r') as f:
                return float(f.read().strip())
    except Exception as e:
        logger.error(f"Error reading last scrape time: {e}")
    
    return 0  # Default to epoch start if no timestamp exists

async def update_last_scrape_time(category: str):
    """Update the timestamp of the last scrape for a category."""
    timestamp_file = f"{DATA_DIR}/{category}/_last_scrape.txt"
    
    # Create directory if it doesn't exist
    os.makedirs(f"{DATA_DIR}/{category}", exist_ok=True)
    
    # Update timestamp
    with open(timestamp_file, 'w') as f:
        f.write(str(time.time()))

async def scrape_items_page(url: str, category: str, page: int = 1, browser=None) -> List[Dict[str, Any]]:
    """Scrape items from a paginated list."""
    items = []
    
    try:
        # Navigate to the page
        full_url = f"{CODEX_BASE_URL}{url}?page={page}"
        page_obj = await browser.new_page()
        await page_obj.goto(full_url)
        await page_obj.wait_for_load_state("networkidle")
        
        # Get page content
        content = await page_obj.content()
        soup = BeautifulSoup(content, 'html.parser')
        
        # Extract items
        item_cards = soup.select(".item-card")
        
        for card in item_cards:
            try:
                item_id = card.get("data-item-id", "")
                item_name = card.select_one(".item-name").text.strip()
                item_quality = card.select_one(".item-quality").text.strip() if card.select_one(".item-quality") else ""
                item_type = card.select_one(".item-type").text.strip() if card.select_one(".item-type") else ""
                item_url = card.select_one("a")["href"] if card.select_one("a") else ""
                
                item_data = {
                    "id": item_id,
                    "name": item_name,
                    "quality": item_quality,
                    "type": item_type,
                    "url": item_url,
                    "source": f"{CODEX_BASE_URL}{item_url}" if item_url else "",
                }
                
                items.append(item_data)
            except Exception as e:
                logger.error(f"Error parsing item card: {e}")
        
        # Check if there's a next page
        next_page = soup.select_one(".pagination .next:not(.disabled)")
        has_next_page = bool(next_page)
        
        # Close the page
        await page_obj.close()
        
        return items, has_next_page
        
    except Exception as e:
        logger.error(f"Error scraping items page {url}?page={page}: {e}")
        return [], False

async def scrape_item_details(item: Dict[str, Any], browser=None) -> Dict[str, Any]:
    """Scrape detailed information about an item."""
    if not item.get("url"):
        return item
    
    try:
        # Navigate to the item page
        full_url = f"{CODEX_BASE_URL}{item['url']}"
        page_obj = await browser.new_page()
        await page_obj.goto(full_url)
        await page_obj.wait_for_load_state("networkidle")
        
        # Get page content
        content = await page_obj.content()
        soup = BeautifulSoup(content, 'html.parser')
        
        # Extract item details
        item_details = {}
        
        # Basic info
        item_details["name"] = soup.select_one("h1.item-name").text.strip() if soup.select_one("h1.item-name") else item.get("name", "")
        item_details["quality"] = soup.select_one(".item-quality").text.strip() if soup.select_one(".item-quality") else item.get("quality", "")
        item_details["type"] = soup.select_one(".item-type").text.strip() if soup.select_one(".item-type") else item.get("type", "")
        
        # Description
        description = soup.select_one(".item-description")
        item_details["description"] = description.text.strip() if description else ""
        
        # Stats
        stats = []
        stats_section = soup.select_one(".item-stats")
        if stats_section:
            stat_items = stats_section.select("li")
            for stat in stat_items:
                stats.append(stat.text.strip())
        item_details["stats"] = stats
        
        # Sources (how to obtain)
        sources = []
        sources_section = soup.select_one(".item-sources")
        if sources_section:
            source_items = sources_section.select("li")
            for source in source_items:
                sources.append(source.text.strip())
        item_details["sources"] = sources
        
        # Crafting recipe
        recipe = {}
        recipe_section = soup.select_one(".item-recipe")
        if recipe_section:
            materials = []
            material_items = recipe_section.select(".recipe-material")
            for material in material_items:
                material_name = material.select_one(".material-name").text.strip() if material.select_one(".material-name") else ""
                material_amount = material.select_one(".material-amount").text.strip() if material.select_one(".material-amount") else ""
                materials.append({
                    "name": material_name,
                    "amount": material_amount
                })
            recipe["materials"] = materials
            
            recipe["skill"] = recipe_section.select_one(".recipe-skill").text.strip() if recipe_section.select_one(".recipe-skill") else ""
            recipe["level"] = recipe_section.select_one(".recipe-level").text.strip() if recipe_section.select_one(".recipe-level") else ""
            
        item_details["recipe"] = recipe if recipe else None
        
        # Used in (what crafting recipes use this item)
        used_in = []
        used_in_section = soup.select_one(".item-used-in")
        if used_in_section:
            used_in_items = used_in_section.select("li")
            for used in used_in_items:
                used_in.append(used.text.strip())
        item_details["used_in"] = used_in
        
        # Locations
        locations = []
        locations_section = soup.select_one(".item-locations")
        if locations_section:
            location_items = locations_section.select("li")
            for location in location_items:
                locations.append(location.text.strip())
        item_details["locations"] = locations
        
        # Close the page
        await page_obj.close()
        
        # Merge with original item data
        item.update(item_details)
        
        # Create a document structure for indexing
        document = {
            "id": item.get("id", ""),
            "text": f"""
                Name: {item.get('name', '')}
                Quality: {item.get('quality', '')}
                Type: {item.get('type', '')}
                Description: {item.get('description', '')}
                Stats: {', '.join(item.get('stats', []))}
                How to obtain: {', '.join(item.get('sources', []))}
                Locations: {', '.join(item.get('locations', []))}
                Used in: {', '.join(item.get('used_in', []))}
            """,
            "metadata": item,
            "source": full_url,
            "type": "item"
        }
        
        return document
        
    except Exception as e:
        logger.error(f"Error scraping item details for {item.get('name', 'unknown')}: {e}")
        return item

async def scrape_location_details(url: str, category: str, browser=None) -> List[Dict[str, Any]]:
    """Scrape detailed information about locations."""
    locations = []
    
    try:
        # Navigate to the page
        full_url = f"{CODEX_BASE_URL}{url}"
        page_obj = await browser.new_page()
        await page_obj.goto(full_url)
        await page_obj.wait_for_load_state("networkidle")
        
        # Get page content
        content = await page_obj.content()
        soup = BeautifulSoup(content, 'html.parser')
        
        # Extract locations
        location_cards = soup.select(".location-card")
        
        for card in location_cards:
            try:
                location_id = card.get("data-location-id", "")
                location_name = card.select_one(".location-name").text.strip() if card.select_one(".location-name") else ""
                location_type = card.select_one(".location-type").text.strip() if card.select_one(".location-type") else ""
                location_zone = card.select_one(".location-zone").text.strip() if card.select_one(".location-zone") else ""
                location_url = card.select_one("a")["href"] if card.select_one("a") else ""
                
                # Extract location details if there's a URL
                location_details = {
                    "id": location_id,
                    "name": location_name,
                    "type": location_type,
                    "zone": location_zone,
                    "url": location_url,
                    "source": f"{CODEX_BASE_URL}{location_url}" if location_url else "",
                }
                
                # Create a document structure for indexing
                document = {
                    "id": location_id,
                    "text": f"""
                        Name: {location_name}
                        Type: {location_type}
                        Zone: {location_zone}
                    """,
                    "metadata": location_details,
                    "source": f"{CODEX_BASE_URL}{location_url}" if location_url else "",
                    "type": "location"
                }
                
                locations.append(document)
            except Exception as e:
                logger.error(f"Error parsing location card: {e}")
        
        # Close the page
        await page_obj.close()
        
        return locations
        
    except Exception as e:
        logger.error(f"Error scraping locations {url}: {e}")
        return []

async def scrape_crafting_details(url: str, category: str, browser=None) -> List[Dict[str, Any]]:
    """Scrape detailed information about crafting."""
    crafting_items = []
    
    try:
        # Navigate to the page
        full_url = f"{CODEX_BASE_URL}{url}"
        page_obj = await browser.new_page()
        await page_obj.goto(full_url)
        await page_obj.wait_for_load_state("networkidle")
        
        # Get page content
        content = await page_obj.content()
        soup = BeautifulSoup(content, 'html.parser')
        
        if "recipes" in url:
            # Extract recipes
            recipe_cards = soup.select(".recipe-card")
            
            for card in recipe_cards:
                try:
                    recipe_id = card.get("data-recipe-id", "")
                    recipe_name = card.select_one(".recipe-name").text.strip() if card.select_one(".recipe-name") else ""
                    recipe_profession = card.select_one(".recipe-profession").text.strip() if card.select_one(".recipe-profession") else ""
                    recipe_level = card.select_one(".recipe-level").text.strip() if card.select_one(".recipe-level") else ""
                    recipe_url = card.select_one("a")["href"] if card.select_one("a") else ""
                    
                    # Extract recipe materials
                    materials = []
                    material_items = card.select(".recipe-material")
                    for material in material_items:
                        material_name = material.select_one(".material-name").text.strip() if material.select_one(".material-name") else ""
                        material_amount = material.select_one(".material-amount").text.strip() if material.select_one(".material-amount") else ""
                        materials.append({
                            "name": material_name,
                            "amount": material_amount
                        })
                    
                    # Recipe details
                    recipe_details = {
                        "id": recipe_id,
                        "name": recipe_name,
                        "profession": recipe_profession,
                        "level": recipe_level,
                        "materials": materials,
                        "url": recipe_url,
                        "source": f"{CODEX_BASE_URL}{recipe_url}" if recipe_url else "",
                    }
                    
                    # Create a document structure for indexing
                    materials_text = ", ".join([f"{m.get('amount', '')} {m.get('name', '')}" for m in materials])
                    document = {
                        "id": recipe_id,
                        "text": f"""
                            Recipe: {recipe_name}
                            Profession: {recipe_profession}
                            Level: {recipe_level}
                            Materials: {materials_text}
                        """,
                        "metadata": recipe_details,
                        "source": f"{CODEX_BASE_URL}{recipe_url}" if recipe_url else "",
                        "type": "crafting_recipe"
                    }
                    
                    crafting_items.append(document)
                except Exception as e:
                    logger.error(f"Error parsing recipe card: {e}")
        
        elif "professions" in url:
            # Extract professions
            profession_cards = soup.select(".profession-card")
            
            for card in profession_cards:
                try:
                    profession_id = card.get("data-profession-id", "")
                    profession_name = card.select_one(".profession-name").text.strip() if card.select_one(".profession-name") else ""
                    profession_type = card.select_one(".profession-type").text.strip() if card.select_one(".profession-type") else ""
                    profession_url = card.select_one("a")["href"] if card.select_one("a") else ""
                    
                    # Extract profession details
                    description = card.select_one(".profession-description").text.strip() if card.select_one(".profession-description") else ""
                    tiers = []
                    tier_items = card.select(".profession-tier")
                    for tier in tier_items:
                        tier_name = tier.select_one(".tier-name").text.strip() if tier.select_one(".tier-name") else ""
                        tier_description = tier.select_one(".tier-description").text.strip() if tier.select_one(".tier-description") else ""
                        tiers.append({
                            "name": tier_name,
                            "description": tier_description
                        })
                    
                    # Profession details
                    profession_details = {
                        "id": profession_id,
                        "name": profession_name,
                        "type": profession_type,
                        "description": description,
                        "tiers": tiers,
                        "url": profession_url,
                        "source": f"{CODEX_BASE_URL}{profession_url}" if profession_url else "",
                    }
                    
                    # Create a document structure for indexing
                    tiers_text = " ".join([f"{t.get('name', '')}: {t.get('description', '')}" for t in tiers])
                    document = {
                        "id": profession_id,
                        "text": f"""
                            Profession: {profession_name}
                            Type: {profession_type}
                            Description: {description}
                            Tiers: {tiers_text}
                        """,
                        "metadata": profession_details,
                        "source": f"{CODEX_BASE_URL}{profession_url}" if profession_url else "",
                        "type": "crafting_profession"
                    }
                    
                    crafting_items.append(document)
                except Exception as e:
                    logger.error(f"Error parsing profession card: {e}")
        
        # Close the page
        await page_obj.close()
        
        return crafting_items
        
    except Exception as e:
        logger.error(f"Error scraping crafting {url}: {e}")
        return []

async def scrape_character_details(url: str, category: str, browser=None) -> List[Dict[str, Any]]:
    """Scrape detailed information about character options."""
    character_items = []
    
    try:
        # Navigate to the page
        full_url = f"{CODEX_BASE_URL}{url}"
        page_obj = await browser.new_page()
        await page_obj.goto(full_url)
        await page_obj.wait_for_load_state("networkidle")
        
        # Get page content
        content = await page_obj.content()
        soup = BeautifulSoup(content, 'html.parser')
        
        if "archetypes" in url or "classes" in url:
            # Extract classes/archetypes
            class_cards = soup.select(".class-card")
            
            for card in class_cards:
                try:
                    class_id = card.get("data-class-id", "")
                    class_name = card.select_one(".class-name").text.strip() if card.select_one(".class-name") else ""
                    class_category = "archetype" if "archetypes" in url else "class"
                    class_url = card.select_one("a")["href"] if card.select_one("a") else ""
                    
                    # Extract class details
                    description = card.select_one(".class-description").text.strip() if card.select_one(".class-description") else ""
                    abilities = []
                    ability_items = card.select(".class-ability")
                    for ability in ability_items:
                        ability_name = ability.select_one(".ability-name").text.strip() if ability.select_one(".ability-name") else ""
                        ability_description = ability.select_one(".ability-description").text.strip() if ability.select_one(".ability-description") else ""
                        abilities.append({
                            "name": ability_name,
                            "description": ability_description
                        })
                    
                    # Class details
                    class_details = {
                        "id": class_id,
                        "name": class_name,
                        "type": class_category,
                        "description": description,
                        "abilities": abilities,
                        "url": class_url,
                        "source": f"{CODEX_BASE_URL}{class_url}" if class_url else "",
                    }
                    
                    # Create a document structure for indexing
                    abilities_text = " ".join([f"{a.get('name', '')}: {a.get('description', '')}" for a in abilities])
                    document = {
                        "id": class_id,
                        "text": f"""
                            {class_category.title()}: {class_name}
                            Description: {description}
                            Abilities: {abilities_text}
                        """,
                        "metadata": class_details,
                        "source": f"{CODEX_BASE_URL}{class_url}" if class_url else "",
                        "type": class_category
                    }
                    
                    character_items.append(document)
                except Exception as e:
                    logger.error(f"Error parsing class card: {e}")
        
        elif "races" in url:
            # Extract races
            race_cards = soup.select(".race-card")
            
            for card in race_cards:
                try:
                    race_id = card.get("data-race-id", "")
                    race_name = card.select_one(".race-name").text.strip() if card.select_one(".race-name") else ""
                    race_url = card.select_one("a")["href"] if card.select_one("a") else ""
                    
                    # Extract race details
                    description = card.select_one(".race-description").text.strip() if card.select_one(".race-description") else ""
                    racial_traits = []
                    trait_items = card.select(".racial-trait")
                    for trait in trait_items:
                        trait_name = trait.select_one(".trait-name").text.strip() if trait.select_one(".trait-name") else ""
                        trait_description = trait.select_one(".trait-description").text.strip() if trait.select_one(".trait-description") else ""
                        racial_traits.append({
                            "name": trait_name,
                            "description": trait_description
                        })
                    
                    # Race details
                    race_details = {
                        "id": race_id,
                        "name": race_name,
                        "description": description,
                        "racial_traits": racial_traits,
                        "url": race_url,
                        "source": f"{CODEX_BASE_URL}{race_url}" if race_url else "",
                    }
                    
                    # Create a document structure for indexing
                    traits_text = " ".join([f"{t.get('name', '')}: {t.get('description', '')}" for t in racial_traits])
                    document = {
                        "id": race_id,
                        "text": f"""
                            Race: {race_name}
                            Description: {description}
                            Racial Traits: {traits_text}
                        """,
                        "metadata": race_details,
                        "source": f"{CODEX_BASE_URL}{race_url}" if race_url else "",
                        "type": "race"
                    }
                    
                    character_items.append(document)
                except Exception as e:
                    logger.error(f"Error parsing race card: {e}")
        
        elif "builds" in url:
            # Extract build guides
            build_cards = soup.select(".build-card")
            
            for card in build_cards:
                try:
                    build_id = card.get("data-build-id", "")
                    build_name = card.select_one(".build-name").text.strip() if card.select_one(".build-name") else ""
                    build_class = card.select_one(".build-class").text.strip() if card.select_one(".build-class") else ""
                    build_url = card.select_one("a")["href"] if card.select_one("a") else ""
                    
                    # Extract build details
                    description = card.select_one(".build-description").text.strip() if card.select_one(".build-description") else ""
                    build_type = card.select_one(".build-type").text.strip() if card.select_one(".build-type") else ""
                    author = card.select_one(".build-author").text.strip() if card.select_one(".build-author") else ""
                    
                    # Build details
                    build_details = {
                        "id": build_id,
                        "name": build_name,
                        "class": build_class,
                        "type": build_type,
                        "description": description,
                        "author": author,
                        "url": build_url,
                        "source": f"{CODEX_BASE_URL}{build_url}" if build_url else "",
                    }
                    
                    # Create a document structure for indexing
                    document = {
                        "id": build_id,
                        "text": f"""
                            Build: {build_name}
                            Class: {build_class}
                            Type: {build_type}
                            Author: {author}
                            Description: {description}
                        """,
                        "metadata": build_details,
                        "source": f"{CODEX_BASE_URL}{build_url}" if build_url else "",
                        "type": "build"
                    }
                    
                    character_items.append(document)
                except Exception as e:
                    logger.error(f"Error parsing build card: {e}")
        
        # Close the page
        await page_obj.close()
        
        return character_items
        
    except Exception as e:
        logger.error(f"Error scraping character {url}: {e}")
        return []

async def process_category(category: str, urls: List[str], force_full: bool = False):
    """Process a category of URLs."""
    try:
        # Create category directory
        os.makedirs(f"{DATA_DIR}/{category}", exist_ok=True)
        
        # Check last scrape time
        last_scrape = await get_last_scrape_time(category)
        current_time = time.time()
        
        # Skip if scraped recently and not forcing a full scrape
        if not force_full and current_time - last_scrape < 86400:  # 24 hours
            logger.info(f"Skipping {category} - scraped recently")
            return
        
        # Initialize playwright
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            
            all_documents = []
            
            for url in urls:
                if "items" in url:
                    # Handle paginated items
                    page = 1
                    has_next_page = True
                    
                    while has_next_page:
                        items, has_next_page = await scrape_items_page(url, category, page, browser)
                        
                        # Get details for each item
                        detailed_items = []
                        for item in items:
                            detailed_item = await scrape_item_details(item, browser)
                            detailed_items.append(detailed_item)
                        
                        # Save items
                        page_filename = f"{url.replace('/', '_')}_page_{page}"
                        await save_json(detailed_items, page_filename, category)
                        
                        all_documents.extend(detailed_items)
                        page += 1
                
                elif "locations" in url or "world" in url:
                    # Handle locations
                    locations = await scrape_location_details(url, category, browser)
                    
                    # Save locations
                    locations_filename = f"{url.replace('/', '_')}"
                    await save_json(locations, locations_filename, category)
                    
                    all_documents.extend(locations)
                
                elif "crafting" in url:
                    # Handle crafting
                    crafting_items = await scrape_crafting_details(url, category, browser)
                    
                    # Save crafting items
                    crafting_filename = f"{url.replace('/', '_')}"
                    await save_json(crafting_items, crafting_filename, category)
                    
                    all_documents.extend(crafting_items)
                
                elif "character" in url:
                    # Handle character options
                    character_items = await scrape_character_details(url, category, browser)
                    
                    # Save character items
                    character_filename = f"{url.replace('/', '_')}"
                    await save_json(character_items, character_filename, category)
                    
                    all_documents.extend(character_items)
            
            # Close browser
            await browser.close()
            
            # Save all documents for the category
            await save_json(all_documents, f"all_{category}", category)
            
            # Update last scrape time
            await update_last_scrape_time(category)
            
            logger.info(f"Scraped {len(all_documents)} documents from {category}")
    
    except Exception as e:
        logger.error(f"Error processing category {category}: {e}")

async def scrape_ashes_codex(force_full: bool = False):
    """Scrape data from Ashes Codex."""
    logger.info("Starting Ashes Codex scraper")
    
    try:
        # Create base directory
        os.makedirs(DATA_DIR, exist_ok=True)
        
        # Process each category
        tasks = []
        for category, urls in SCRAPE_URLS.items():
            task = process_category(category, urls, force_full)
            tasks.append(task)
        
        # Run tasks with progress reporting
        await tqdm_asyncio.gather(*tasks, desc="Scraping Ashes Codex")
        
        logger.info("Completed Ashes Codex scraping")
        
    except Exception as e:
        logger.error(f"Error in Ashes Codex scraper: {e}")
