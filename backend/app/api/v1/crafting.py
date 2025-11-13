from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
import uuid
from app.services.vector_store import query_vector_store
from app.services.cache_service import set_cache, get_cache_value
from loguru import logger

router = APIRouter()

# Models
class CraftingMaterial(BaseModel):
    id: str = Field(..., description="Material item ID")
    name: str = Field(..., description="Material name")
    amount: int = Field(..., description="Amount required")
    quality: Optional[str] = Field(None, description="Required material quality")

class Recipe(BaseModel):
    id: str = Field(..., description="Recipe ID")
    name: str = Field(..., description="Recipe name")
    result_item_id: str = Field(..., description="ID of the resulting item")
    result_item_name: str = Field(..., description="Name of the resulting item")
    result_amount: int = Field(1, description="Amount produced")
    result_quality: Optional[str] = Field(None, description="Quality of the resulting item")
    profession: str = Field(..., description="Crafting profession")
    level: str = Field(..., description="Required skill level")
    materials: List[CraftingMaterial] = Field(..., description="Required materials")
    stations: Optional[List[str]] = Field(None, description="Required crafting stations")
    duration: Optional[str] = Field(None, description="Crafting duration")
    notes: Optional[str] = Field(None, description="Additional notes")

class Profession(BaseModel):
    id: str = Field(..., description="Profession ID")
    name: str = Field(..., description="Profession name")
    type: str = Field(..., description="Profession type (Gathering, Processing, Crafting)")
    description: str = Field(..., description="Profession description")
    tiers: List[Dict[str, str]] = Field(..., description="Skill tiers and requirements")
    recipes: Optional[List[str]] = Field(None, description="Recipe IDs for this profession")

class CraftingCalculation(BaseModel):
    item_name: str = Field(..., description="Name of the item to craft")
    amount: int = Field(..., description="Amount to craft")
    recipe: Recipe = Field(..., description="Recipe information")
    required_materials: List[Dict[str, Any]] = Field(..., description="Required materials with nested dependencies")
    total_base_materials: List[Dict[str, Any]] = Field(..., description="Flattened list of base materials needed")
    estimated_cost: Optional[Dict[str, Any]] = Field(None, description="Estimated cost information")

# Routes
@router.get("/professions", response_model=List[Profession])
async def get_professions():
    """
    Get a list of all crafting professions.
    """
    try:
        # Check cache first
        cache_key = "crafting:professions"
        cached_data = await get_cache_value(cache_key)
        
        if cached_data:
            return [Profession(**prof) for prof in cached_data]
        
        # Query vector store
        results = query_vector_store("list all crafting professions", limit=20, filters={"type": "crafting_profession"})
        
        # Convert to Profession objects
        professions = []
        for doc in results:
            metadata = doc.get("metadata", {})
            
            # Create profession object
            profession = Profession(
                id=metadata.get("id", str(uuid.uuid4())),
                name=metadata.get("name", "Unknown Profession"),
                type=metadata.get("type", "Unknown"),
                description=metadata.get("description", ""),
                tiers=metadata.get("tiers", []),
                recipes=None  # We'll fill this later if needed
            )
            
            professions.append(profession)
        
        # Cache the result
        await set_cache(cache_key, [prof.dict() for prof in professions], expire=86400)  # 1 day
        
        return professions
        
    except Exception as e:
        logger.error(f"Error getting professions: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve professions"
        )

@router.get("/professions/{profession_id}", response_model=Profession)
async def get_profession(profession_id: str):
    """
    Get detailed information about a specific profession.
    """
    try:
        # Check cache first
        cache_key = f"crafting:profession:{profession_id}"
        cached_data = await get_cache_value(cache_key)
        
        if cached_data:
            return Profession(**cached_data)
        
        # Query vector store
        results = query_vector_store(f"profession id:{profession_id}", limit=1, filters={"type": "crafting_profession"})
        
        if not results:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Profession not found"
            )
        
        doc = results[0]
        metadata = doc.get("metadata", {})
        
        # Create profession object
        profession = Profession(
            id=metadata.get("id", profession_id),
            name=metadata.get("name", "Unknown Profession"),
            type=metadata.get("type", "Unknown"),
            description=metadata.get("description", ""),
            tiers=metadata.get("tiers", []),
            recipes=None  # Will be populated if we implement related recipes
        )
        
        # Cache the result
        await set_cache(cache_key, profession.dict(), expire=86400)  # 1 day
        
        return profession
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting profession: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve profession"
        )

@router.get("/recipes", response_model=List[Recipe])
async def get_recipes(
    profession: Optional[str] = None,
    level: Optional[str] = None,
    contains_material: Optional[str] = None,
    result_item: Optional[str] = None,
    limit: int = Query(20, ge=1, le=100)
):
    """
    Get a list of crafting recipes with optional filters.
    """
    try:
        # Build cache key
        cache_params = f"prof={profession or ''}&level={level or ''}&material={contains_material or ''}&item={result_item or ''}&limit={limit}"
        cache_key = f"crafting:recipes:{cache_params}"
        
        # Check cache first
        cached_data = await get_cache_value(cache_key)
        
        if cached_data:
            return [Recipe(**recipe) for recipe in cached_data]
        
        # Build search query
        if result_item:
            search_text = f"recipe for {result_item}"
        elif contains_material:
            search_text = f"recipes using {contains_material}"
        else:
            search_text = "crafting recipes"
            
        if profession:
            search_text += f" profession:{profession}"
            
        if level:
            search_text += f" level:{level}"
        
        # Query vector store
        filters = {"type": "crafting_recipe"}
        results = query_vector_store(search_text, limit=limit, filters=filters)
        
        # Convert to Recipe objects
        recipes = []
        for doc in results:
            metadata = doc.get("metadata", {})
            
            # Apply additional filters that might not be handled by the vector search
            if profession and metadata.get("profession", "").lower() != profession.lower():
                continue
                
            if level and metadata.get("level", "").lower() != level.lower():
                continue
                
            if contains_material:
                materials = metadata.get("materials", [])
                material_match = False
                for mat in materials:
                    if contains_material.lower() in mat.get("name", "").lower():
                        material_match = True
                        break
                        
                if not material_match:
                    continue
                    
            if result_item and result_item.lower() not in metadata.get("name", "").lower():
                continue
            
            # Extract materials
            materials = []
            if "materials" in metadata:
                for mat_data in metadata["materials"]:
                    materials.append(CraftingMaterial(
                        id=mat_data.get("id", str(uuid.uuid4())),
                        name=mat_data.get("name", "Unknown Material"),
                        amount=int(mat_data.get("amount", "1").split()[0]),
                        quality=None  # We don't have quality info in the metadata
                    ))
            
            # Create recipe object
            recipe = Recipe(
                id=metadata.get("id", str(uuid.uuid4())),
                name=metadata.get("name", "Unknown Recipe"),
                result_item_id=metadata.get("result_item_id", str(uuid.uuid4())),
                result_item_name=metadata.get("name", "Unknown Item"),
                result_amount=1,  # Default to 1
                result_quality=None,  # We don't have quality info in the metadata
                profession=metadata.get("profession", "Unknown"),
                level=metadata.get("level", "Unknown"),
                materials=materials,
                stations=None,  # We don't have stations info in the metadata
                duration=None,  # We don't have duration info in the metadata
                notes=None
            )
            
            recipes.append(recipe)
        
        # Cache the result
        await set_cache(cache_key, [recipe.dict() for recipe in recipes], expire=3600)  # 1 hour
        
        return recipes
        
    except Exception as e:
        logger.error(f"Error getting recipes: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve recipes"
        )

@router.get("/recipes/{recipe_id}", response_model=Recipe)
async def get_recipe(recipe_id: str):
    """
    Get detailed information about a specific recipe.
    """
    try:
        # Check cache first
        cache_key = f"crafting:recipe:{recipe_id}"
        cached_data = await get_cache_value(cache_key)
        
        if cached_data:
            return Recipe(**cached_data)
        
        # Query vector store
        results = query_vector_store(f"recipe id:{recipe_id}", limit=1, filters={"type": "crafting_recipe"})
        
        if not results:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Recipe not found"
            )
        
        doc = results[0]
        metadata = doc.get("metadata", {})
        
        # Extract materials
        materials = []
        if "materials" in metadata:
            for mat_data in metadata["materials"]:
                materials.append(CraftingMaterial(
                    id=mat_data.get("id", str(uuid.uuid4())),
                    name=mat_data.get("name", "Unknown Material"),
                    amount=int(mat_data.get("amount", "1").split()[0]),
                    quality=None  # We don't have quality info in the metadata
                ))
        
        # Create recipe object
        recipe = Recipe(
            id=metadata.get("id", recipe_id),
            name=metadata.get("name", "Unknown Recipe"),
            result_item_id=metadata.get("result_item_id", str(uuid.uuid4())),
            result_item_name=metadata.get("name", "Unknown Item"),
            result_amount=1,  # Default to 1
            result_quality=None,  # We don't have quality info in the metadata
            profession=metadata.get("profession", "Unknown"),
            level=metadata.get("level", "Unknown"),
            materials=materials,
            stations=None,  # We don't have stations info in the metadata
            duration=None,  # We don't have duration info in the metadata
            notes=None
        )
        
        # Cache the result
        await set_cache(cache_key, recipe.dict(), expire=3600)  # 1 hour
        
        return recipe
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting recipe: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve recipe"
        )

@router.get("/calculate", response_model=CraftingCalculation)
async def calculate_crafting(
    item_name: str,
    amount: int = Query(1, ge=1, le=1000)
):
    """
    Calculate materials needed to craft a specified amount of an item.
    """
    try:
        # Build cache key
        cache_key = f"crafting:calculate:{item_name}:{amount}"
        
        # Check cache first
        cached_data = await get_cache_value(cache_key)
        
        if cached_data:
            return CraftingCalculation(**cached_data)
        
        # Find the recipe for the item
        recipe_results = query_vector_store(f"recipe for {item_name}", limit=1, filters={"type": "crafting_recipe"})
        
        if not recipe_results:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Recipe for {item_name} not found"
            )
        
        recipe_doc = recipe_results[0]
        recipe_metadata = recipe_doc.get("metadata", {})
        
        # Extract materials
        materials = []
        if "materials" in recipe_metadata:
            for mat_data in recipe_metadata["materials"]:
                materials.append(CraftingMaterial(
                    id=mat_data.get("id", str(uuid.uuid4())),
                    name=mat_data.get("name", "Unknown Material"),
                    amount=int(mat_data.get("amount", "1").split()[0]),
                    quality=None
                ))
        
        # Create recipe object
        recipe = Recipe(
            id=recipe_metadata.get("id", str(uuid.uuid4())),
            name=recipe_metadata.get("name", "Unknown Recipe"),
            result_item_id=recipe_metadata.get("result_item_id", str(uuid.uuid4())),
            result_item_name=recipe_metadata.get("name", "Unknown Item"),
            result_amount=1,  # Default to 1
            result_quality=None,
            profession=recipe_metadata.get("profession", "Unknown"),
            level=recipe_metadata.get("level", "Unknown"),
            materials=materials,
            stations=None,
            duration=None,
            notes=None
        )
        
        # Calculate required materials
        required_materials = []
        for material in materials:
            # Check if this material is craftable
            is_craftable = False
            sub_materials = []
            
            # For now, we'll assume no sub-crafting (this would require recursion)
            required_materials.append({
                "id": material.id,
                "name": material.name,
                "amount": material.amount * amount,
                "is_craftable": is_craftable,
                "sub_materials": sub_materials
            })
        
        # Calculate total base materials (same as required for now since we don't handle sub-crafting)
        total_base_materials = []
        for mat in required_materials:
            total_base_materials.append({
                "id": mat["id"],
                "name": mat["name"],
                "amount": mat["amount"]
            })
        
        # Create calculation object
        calculation = CraftingCalculation(
            item_name=item_name,
            amount=amount,
            recipe=recipe,
            required_materials=required_materials,
            total_base_materials=total_base_materials,
            estimated_cost=None  # We don't have price data
        )
        
        # Cache the result
        await set_cache(cache_key, calculation.dict(), expire=3600)  # 1 hour
        
        return calculation
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error calculating crafting: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to calculate crafting requirements"
        )

@router.get("/progression/{profession}", response_model=List[Dict[str, Any]])
async def get_progression_guide(profession: str):
    """
    Get a progression guide for a specific profession.
    """
    try:
        # Check cache first
        cache_key = f"crafting:progression:{profession}"
        cached_data = await get_cache_value(cache_key)
        
        if cached_data:
            return cached_data
        
        # Query vector store for the profession info
        profession_results = query_vector_store(f"{profession} profession", limit=1, filters={"type": "crafting_profession"})
        
        if not profession_results:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Profession {profession} not found"
            )
        
        # Query for recipes by this profession
        recipe_results = query_vector_store(f"{profession} recipes by level", limit=50, filters={"type": "crafting_recipe"})
        
        # Group recipes by level
        recipes_by_level = {}
        for doc in recipe_results:
            metadata = doc.get("metadata", {})
            level = metadata.get("level", "Unknown")
            
            if level not in recipes_by_level:
                recipes_by_level[level] = []
                
            recipes_by_level[level].append({
                "id": metadata.get("id", str(uuid.uuid4())),
                "name": metadata.get("name", "Unknown Recipe"),
                "materials": metadata.get("materials", []),
                "difficulty": "Easy"  # Default since we don't have difficulty data
            })
        
        # Create progression guide
        progression_guide = []
        
        # Sort levels (assuming they're in format like "Novice", "Journeyman", etc.)
        levels = list(recipes_by_level.keys())
        
        # Known tiers in order
        known_tiers = ["Novice", "Journeyman", "Adept", "Expert", "Master", "Grandmaster"]
        
        # Sort by known tiers
        levels.sort(key=lambda x: known_tiers.index(x) if x in known_tiers else 999)
        
        for level in levels:
            level_recipes = recipes_by_level[level]
            
            # Skip empty levels
            if not level_recipes:
                continue
                
            progression_guide.append({
                "level": level,
                "recommended_recipes": level_recipes[:5],  # Take top 5 recipes for each level
                "tips": f"Focus on creating {level_recipes[0]['name']} to efficiently level up.",
                "materials_to_gather": [mat["name"] for recipe in level_recipes[:3] for mat in recipe["materials"][:2]]
            })
        
        # Cache the result
        await set_cache(cache_key, progression_guide, expire=86400)  # 1 day
        
        return progression_guide
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting progression guide: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve progression guide"
        )
