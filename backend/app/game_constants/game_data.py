"""
Static game data for Ashes of Creation.

This data is used for validation and class name computation.
Source: https://ashesofcreation.wiki/
"""
from typing import Dict, Tuple, Set

# 8 base archetypes
ARCHETYPES: Set[str] = {
    "fighter",
    "tank",
    "rogue",
    "ranger",
    "mage",
    "summoner",
    "cleric",
    "bard",
}

# 64 class combinations (primary, secondary) -> class_name
CLASS_MATRIX: Dict[Tuple[str, str], str] = {
    # Fighter primary
    ("fighter", "fighter"): "Weapon Master",
    ("fighter", "tank"): "Dreadnought",
    ("fighter", "rogue"): "Shadowblade",
    ("fighter", "ranger"): "Hunter",
    ("fighter", "mage"): "Spellsword",
    ("fighter", "summoner"): "Bladecaller",
    ("fighter", "cleric"): "Highsword",
    ("fighter", "bard"): "Bladedancer",

    # Tank primary
    ("tank", "fighter"): "Knight",
    ("tank", "tank"): "Guardian",
    ("tank", "rogue"): "Nightshield",
    ("tank", "ranger"): "Warden",
    ("tank", "mage"): "Spellshield",
    ("tank", "summoner"): "Keeper",
    ("tank", "cleric"): "Paladin",
    ("tank", "bard"): "Argent",

    # Rogue primary
    ("rogue", "fighter"): "Duelist",
    ("rogue", "tank"): "Shadow Guardian",
    ("rogue", "rogue"): "Assassin",
    ("rogue", "ranger"): "Predator",
    ("rogue", "mage"): "Nightspell",
    ("rogue", "summoner"): "Shadow Lord",
    ("rogue", "cleric"): "Cultist",
    ("rogue", "bard"): "Charlatan",

    # Ranger primary
    ("ranger", "fighter"): "Strider",
    ("ranger", "tank"): "Sentinel",
    ("ranger", "rogue"): "Scout",
    ("ranger", "ranger"): "Hawkeye",
    ("ranger", "mage"): "Scion",
    ("ranger", "summoner"): "Falconer",
    ("ranger", "cleric"): "Soulbow",
    ("ranger", "bard"): "Bowsinger",

    # Mage primary
    ("mage", "fighter"): "Battle Mage",
    ("mage", "tank"): "Spellstone",
    ("mage", "rogue"): "Shadow Caster",
    ("mage", "ranger"): "Spell Hunter",
    ("mage", "mage"): "Archwizard",
    ("mage", "summoner"): "Warlock",
    ("mage", "cleric"): "Acolyte",
    ("mage", "bard"): "Sorcerer",

    # Summoner primary
    ("summoner", "fighter"): "Wild Blade",
    ("summoner", "tank"): "Brood Warden",
    ("summoner", "rogue"): "Shadowmancer",
    ("summoner", "ranger"): "Beast Master",
    ("summoner", "mage"): "Spellmancer",
    ("summoner", "summoner"): "Conjurer",
    ("summoner", "cleric"): "Necromancer",
    ("summoner", "bard"): "Enchanter",

    # Cleric primary
    ("cleric", "fighter"): "Templar",
    ("cleric", "tank"): "Apostle",
    ("cleric", "rogue"): "Shadow Disciple",
    ("cleric", "ranger"): "Protector",
    ("cleric", "mage"): "Oracle",
    ("cleric", "summoner"): "Shaman",
    ("cleric", "cleric"): "High Priest",
    ("cleric", "bard"): "Scryer",

    # Bard primary
    ("bard", "fighter"): "Tellsword",
    ("bard", "tank"): "Siren",
    ("bard", "rogue"): "Trickster",
    ("bard", "ranger"): "Song Warden",
    ("bard", "mage"): "Magician",
    ("bard", "summoner"): "Song Caller",
    ("bard", "cleric"): "Soul Weaver",
    ("bard", "bard"): "Minstrel",
}

# 9 playable races with parent race info
RACES: Dict[str, Dict[str, str]] = {
    "kaelar": {"parent": "Aela Humans", "name": "Kaelar"},
    "vaelune": {"parent": "Aela Humans", "name": "Vaelune"},
    "dunir": {"parent": "Dünzenkell Dwarves", "name": "Dunir"},
    "nikua": {"parent": "Dünzenkell Dwarves", "name": "Nikua"},
    "empyrean": {"parent": "Pyrian Elves", "name": "Empyrean"},
    "pyrai": {"parent": "Pyrian Elves", "name": "Py'rai"},
    "renkai": {"parent": "Kaivek Orcs", "name": "Ren'kai"},
    "vek": {"parent": "Kaivek Orcs", "name": "Vek"},
    "tulnar": {"parent": "Tulnar", "name": "Tulnar"},
}

# Valid race keys for validation
VALID_RACES: Set[str] = set(RACES.keys())


def get_class_name(primary: str, secondary: str) -> str | None:
    """
    Get the class name for an archetype combination.

    Args:
        primary: Primary archetype (lowercase)
        secondary: Secondary archetype (lowercase)

    Returns:
        Class name string, or None if invalid combination
    """
    return CLASS_MATRIX.get((primary.lower(), secondary.lower()))


def validate_archetype(archetype: str) -> bool:
    """Check if an archetype is valid."""
    return archetype.lower() in ARCHETYPES


def validate_race(race: str) -> bool:
    """Check if a race is valid."""
    return race.lower() in VALID_RACES


def get_race_display_name(race: str) -> str | None:
    """Get the display name for a race."""
    race_data = RACES.get(race.lower())
    return race_data["name"] if race_data else None
