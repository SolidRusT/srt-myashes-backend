#!/usr/bin/env python3
"""Seed script for build templates.

This script creates official build templates for common archetypes.
Templates are marked with is_template=True and cannot be modified by users.

Usage:
    python -m scripts.seed_templates

Or via Docker:
    kubectl exec -n myashes-backend deployment/myashes-backend -- \
        python -m scripts.seed_templates
"""
import sys
import os

# Add the backend directory to the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models.build import Build
from app.core.security import generate_build_id
from app.core.config import settings
from app.game_constants.game_data import get_class_name

# Template builds data
TEMPLATE_BUILDS = [
    # Tank Templates
    {
        "name": "Classic Tank - Paladin",
        "description": "A holy warrior combining the Tank's defensive capabilities with Cleric healing augments. Excels at sustaining damage while providing group support. Ideal for dungeon tanking and node sieges.",
        "primary_archetype": "tank",
        "secondary_archetype": "cleric",
        "race": "kaelar",
    },
    {
        "name": "Guardian Wall",
        "description": "Pure defensive powerhouse. Double Tank archetype means maximum protection abilities and unmatched resilience. Perfect for castle siege defense and protecting key allies.",
        "primary_archetype": "tank",
        "secondary_archetype": "tank",
        "race": "dunir",
    },
    # Healer Templates
    {
        "name": "Holy Healer - High Priest",
        "description": "The ultimate healing specialist. Double Cleric archetype provides unmatched healing output and support capabilities. Essential for raid progression and large-scale PvP.",
        "primary_archetype": "cleric",
        "secondary_archetype": "cleric",
        "race": "empyrean",
    },
    {
        "name": "Battle Cleric - Templar",
        "description": "A frontline healer who can hold their own in combat. Fighter secondary adds melee damage and survivability. Great for small group content and caravan runs.",
        "primary_archetype": "cleric",
        "secondary_archetype": "fighter",
        "race": "vaelune",
    },
    # DPS Templates (Melee)
    {
        "name": "Assassin - Silent Death",
        "description": "Master of stealth and burst damage. Double Rogue archetype maximizes critical strikes and evasion. Perfect for PvP ganking and taking down high-value targets.",
        "primary_archetype": "rogue",
        "secondary_archetype": "rogue",
        "race": "vek",
    },
    {
        "name": "Weapon Master - Berserker",
        "description": "Raw melee damage dealer. Double Fighter archetype provides versatile weapon skills and sustained DPS. Excellent for dungeon DPS and open-world farming.",
        "primary_archetype": "fighter",
        "secondary_archetype": "fighter",
        "race": "renkai",
    },
    # DPS Templates (Ranged)
    {
        "name": "Archwizard - Elemental Master",
        "description": "Pure magical destruction. Double Mage archetype delivers devastating AoE and single-target spells. Key role in sieges and dungeon boss encounters.",
        "primary_archetype": "mage",
        "secondary_archetype": "mage",
        "race": "pyrai",
    },
    {
        "name": "Hawkeye - Precision Archer",
        "description": "Long-range physical damage specialist. Double Ranger archetype maximizes accuracy and mobility. Ideal for kiting, scouting, and ranged PvP.",
        "primary_archetype": "ranger",
        "secondary_archetype": "ranger",
        "race": "nikua",
    },
    # Support Templates
    {
        "name": "Minstrel - Group Buff Master",
        "description": "Ultimate group support through music. Double Bard archetype provides powerful party-wide buffs and crowd control. Essential for organized group content.",
        "primary_archetype": "bard",
        "secondary_archetype": "bard",
        "race": "tulnar",
    },
    {
        "name": "Conjurer - Pet Army",
        "description": "Command an army of summoned creatures. Double Summoner archetype maximizes pet power and variety. Great for solo content and overwhelming enemies with numbers.",
        "primary_archetype": "summoner",
        "secondary_archetype": "summoner",
        "race": "empyrean",
    },
    # Hybrid Templates
    {
        "name": "Spellsword - Magic Warrior",
        "description": "Blend of steel and sorcery. Fighter primary with Mage secondary creates a versatile melee combatant with magical augments. Flexible role for all content types.",
        "primary_archetype": "fighter",
        "secondary_archetype": "mage",
        "race": "kaelar",
    },
    {
        "name": "Shaman - Spiritual Guide",
        "description": "Healer with summoning capabilities. Cleric primary with Summoner secondary provides healing plus spirit companions for extra utility. Unique support playstyle.",
        "primary_archetype": "cleric",
        "secondary_archetype": "summoner",
        "race": "tulnar",
    },
]


def seed_templates():
    """Seed template builds into the database."""
    # Create database engine
    engine = create_engine(settings.DATABASE_URL)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()
    
    try:
        created_count = 0
        skipped_count = 0
        
        for template_data in TEMPLATE_BUILDS:
            # Compute class name
            class_name = get_class_name(
                template_data["primary_archetype"],
                template_data["secondary_archetype"]
            )
            
            if not class_name:
                print(f"ERROR: Invalid archetype combination: {template_data['primary_archetype']} + {template_data['secondary_archetype']}")
                continue
            
            # Check if template with same name already exists
            existing = db.query(Build).filter(
                Build.name == template_data["name"],
                Build.is_template == True
            ).first()
            
            if existing:
                print(f"SKIP: Template already exists: {template_data['name']}")
                skipped_count += 1
                continue
            
            # Create the template build
            build = Build(
                build_id=generate_build_id(),
                name=template_data["name"],
                description=template_data["description"],
                primary_archetype=template_data["primary_archetype"],
                secondary_archetype=template_data["secondary_archetype"],
                class_name=class_name,
                race=template_data["race"],
                is_public=True,
                is_template=True,
                session_id="system_template",  # Special session for templates
            )
            
            db.add(build)
            print(f"CREATE: {template_data['name']} ({class_name})")
            created_count += 1
        
        db.commit()
        
        print(f"\n=== Summary ===")
        print(f"Created: {created_count}")
        print(f"Skipped: {skipped_count}")
        print(f"Total templates: {created_count + skipped_count}")
        
    except Exception as e:
        db.rollback()
        print(f"ERROR: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    print("Seeding build templates...")
    print(f"Database: {settings.DATABASE_URL[:50]}...")
    print()
    seed_templates()
