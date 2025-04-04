from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class Coordinate(BaseModel):
    """Represents a location coordinate in the game world."""
    x: float
    y: float
    z: Optional[float] = None


class ItemSource(BaseModel):
    """Represents a source of where an item can be obtained."""
    type: str = Field(..., description="Source type (drop, craft, vendor, etc.)")
    details: str = Field(..., description="Source details")


class ItemLocation(BaseModel):
    """Represents a location where an item can be found."""
    zone: str = Field(..., description="Zone/region name")
    coordinates: Optional[Coordinate] = None
    notes: Optional[str] = None


class ItemStat(BaseModel):
    """Represents a statistic of an item."""
    name: str = Field(..., description="Stat name")
    value: Any = Field(..., description="Stat value")


class CraftingMaterial(BaseModel):
    """Represents a material required for crafting."""
    item_id: str = Field(..., description="Material item ID")
    name: str = Field(..., description="Material name")
    amount: int = Field(..., description="Amount required")
    quality: Optional[str] = None


class CraftingRecipe(BaseModel):
    """Represents a crafting recipe."""
    recipe_id: str = Field(..., description="Recipe ID")
    materials: List[CraftingMaterial] = Field(default_factory=list)
    skill: str = Field(..., description="Crafting skill required")
    skill_level: str = Field(..., description="Skill level required")


class Item(BaseModel):
    """Represents an item in the game."""
    id: str = Field(..., description="Item ID")
    name: str = Field(..., description="Item name")
    quality: str = Field(..., description="Item quality (Common, Uncommon, etc.)")
    type: str = Field(..., description="Item type (Weapon, Armor, Resource, etc.)")
    subtype: Optional[str] = None
    description: Optional[str] = None
    stats: Optional[List[ItemStat]] = None
    level: Optional[int] = None
    sources: Optional[List[ItemSource]] = None
    locations: Optional[List[ItemLocation]] = None
    recipe: Optional[CraftingRecipe] = None
    used_in: Optional[List[str]] = None
    icon_url: Optional[str] = None


class RacialTrait(BaseModel):
    """Represents a racial trait."""
    name: str = Field(..., description="Trait name")
    description: str = Field(..., description="Trait description")


class Race(BaseModel):
    """Represents a playable race in the game."""
    id: str = Field(..., description="Race ID")
    name: str = Field(..., description="Race name")
    description: str = Field(..., description="Race description")
    racial_traits: List[RacialTrait] = Field(default_factory=list)


class Archetype(BaseModel):
    """Represents a character archetype (base class)."""
    id: str = Field(..., description="Archetype ID")
    name: str = Field(..., description="Archetype name")
    description: str = Field(..., description="Archetype description")


class Class(BaseModel):
    """Represents a character class (combination of two archetypes)."""
    id: str = Field(..., description="Class ID")
    name: str = Field(..., description="Class name")
    primary: str = Field(..., description="Primary archetype")
    secondary: str = Field(..., description="Secondary archetype")
    description: str = Field(..., description="Class description")


class Skill(BaseModel):
    """Represents a character skill."""
    id: str = Field(..., description="Skill ID")
    name: str = Field(..., description="Skill name")
    description: str = Field(..., description="Skill description")
    level: int = Field(..., description="Skill level")
    category: str = Field(..., description="Skill category")
    class_name: Optional[str] = None


class BuildClass(BaseModel):
    """Represents the class selection in a character build."""
    primary: str = Field(..., description="Primary archetype")
    secondary: str = Field(..., description="Secondary archetype")
    classType: str = Field(..., description="Resulting class name")


class Equipment(BaseModel):
    """Represents an equipment item in a character build."""
    id: str = Field(..., description="Equipment ID")
    name: str = Field(..., description="Equipment name")
    slot: str = Field(..., description="Equipment slot")
    quality: str = Field(..., description="Item quality")
    stats: Dict[str, Any] = Field(..., description="Item stats")


class CharacterBuild(BaseModel):
    """Represents a complete character build."""
    id: str = Field(..., description="Build ID")
    name: str = Field(..., description="Build name")
    description: Optional[str] = None
    race: str = Field(..., description="Character race")
    classes: BuildClass = Field(..., description="Character class combination")
    level: int = Field(..., description="Character level")
    skills: List[Skill] = Field(default_factory=list)
    equipment: List[Equipment] = Field(default_factory=list)
    created_at: str = Field(..., description="Creation timestamp")
    updated_at: str = Field(..., description="Last update timestamp")
    user_id: Optional[str] = None
    is_public: bool = Field(True, description="Whether the build is public")
    tags: List[str] = Field(default_factory=list)


class Zone(BaseModel):
    """Represents a zone/region in the game world."""
    id: str = Field(..., description="Zone ID")
    name: str = Field(..., description="Zone name")
    type: str = Field(..., description="Zone type (Forest, Desert, Mountain, etc.)")
    region: str = Field(..., description="Region the zone belongs to")
    level_range: Optional[str] = None
    description: Optional[str] = None
    points_of_interest: Optional[List[str]] = None
    resources: Optional[List[str]] = None
    nodes: Optional[List[Dict[str, Any]]] = None


class ResourceNode(BaseModel):
    """Represents a gatherable resource node."""
    id: str = Field(..., description="Node ID")
    resource: str = Field(..., description="Resource name")
    type: str = Field(..., description="Resource type")
    locations: List[Dict[str, Any]] = Field(..., description="Where to find this resource")
    level: Optional[str] = None
    respawn_time: Optional[str] = None
    notes: Optional[str] = None


class LocationPoint(BaseModel):
    """Represents a point of interest on the map."""
    id: str = Field(..., description="Point ID")
    name: str = Field(..., description="Point name")
    type: str = Field(..., description="Point type (Resource, NPC, POI, etc.)")
    coordinates: Coordinate = Field(..., description="Location coordinates")
    zone: str = Field(..., description="Zone/region name")
    description: Optional[str] = None
    resources: Optional[List[str]] = None
    npcs: Optional[List[str]] = None
    quests: Optional[List[str]] = None
    difficulty: Optional[str] = None
    notes: Optional[str] = None


class Profession(BaseModel):
    """Represents a crafting or gathering profession."""
    id: str = Field(..., description="Profession ID")
    name: str = Field(..., description="Profession name")
    type: str = Field(..., description="Profession type (Gathering, Processing, Crafting)")
    description: str = Field(..., description="Profession description")
    tiers: List[Dict[str, str]] = Field(..., description="Skill tiers and requirements")
    recipes: Optional[List[str]] = None


class DocumentMetadata(BaseModel):
    """Metadata for a document to be stored in the vector database."""
    id: str = Field(..., description="Document ID")
    type: str = Field(..., description="Document type (item, zone, skill, etc.)")
    source: str = Field(..., description="Source URL or identifier")
    server: Optional[str] = None
    timestamp: str = Field(..., description="Timestamp when the document was created")


class Document(BaseModel):
    """A document to be stored in the vector database."""
    id: str = Field(..., description="Document ID")
    text: str = Field(..., description="Document text content")
    metadata: DocumentMetadata = Field(..., description="Document metadata")
    embedding: Optional[List[float]] = None
