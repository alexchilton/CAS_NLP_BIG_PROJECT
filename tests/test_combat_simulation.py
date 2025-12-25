"""
Combat Simulation Test

Simulates a full D&D combat encounter between:
- Half-Elf Fighter/Magic-User/Cleric (multiclass)
- Dark Elf (Drow) Rogue

Features:
- Random stat generation
- Random level generation
- Spell casting with slot tracking
- Weapon attacks with damage rolls
- Initiative and turn order
- Combat until death
"""

import random
import sys
from pathlib import Path

# Add project to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from dnd_rag_system.systems.game_state import (
    CharacterState, SpellSlots, CombatState, Condition
)


def roll_dice(num_dice: int, die_size: int, modifier: int = 0) -> int:
    """Roll dice (e.g., 2d6+3)."""
    total = sum(random.randint(1, die_size) for _ in range(num_dice))
    return total + modifier


def roll_stat() -> int:
    """Roll a D&D ability score (3d6, keep best 3 of 4d6)."""
    rolls = [random.randint(1, 6) for _ in range(4)]
    rolls.sort(reverse=True)
    return sum(rolls[:3])


def ability_modifier(score: int) -> int:
    """Calculate ability modifier from score."""
    return (score - 10) // 2


def create_half_elf_multiclass() -> CharacterState:
    """Create a random half-elf Fighter/Magic-User/Cleric."""
    # Random stats
    str_score = roll_stat()
    dex_score = roll_stat()
    con_score = roll_stat()
    int_score = roll_stat()
    wis_score = roll_stat()
    cha_score = roll_stat()

    # Half-elf racial bonuses (+2 CHA, +1 to two others)
    cha_score += 2
    str_score += 1
    wis_score += 1

    # Random level (3-8)
    level = random.randint(3, 8)

    # Multiclass: Fighter 2/Cleric 2/Wizard remaining
    fighter_levels = 2
    cleric_levels = 2
    wizard_levels = max(1, level - 4)

    # Calculate HP (d10 for fighter, d8 for cleric, d6 for wizard)
    con_mod = ability_modifier(con_score)
    hp = 10 + con_mod  # Fighter 1st level (max)
    hp += roll_dice(1, 10, con_mod)  # Fighter 2nd
    hp += roll_dice(1, 8, con_mod)   # Cleric 1st
    hp += roll_dice(1, 8, con_mod)   # Cleric 2nd
    for _ in range(wizard_levels):
        hp += roll_dice(1, 6, con_mod)

    # AC (chainmail + DEX or leather + DEX)
    ac = 16 + min(2, ability_modifier(dex_score))  # Chainmail

    # Spell slots (Cleric 2 + Wizard levels)
    caster_level_cleric = cleric_levels
    caster_level_wizard = wizard_levels

    # Simplified spell slots (level 2 cleric + wizard levels)
    spell_slots = SpellSlots(
        level_1=3,  # Combined from both
        level_2=2 if (caster_level_cleric + caster_level_wizard) >= 3 else 0,
        level_3=2 if (caster_level_cleric + caster_level_wizard) >= 5 else 0,
    )

    char = CharacterState(
        character_name="Aelindra Silverstaff",
        max_hp=hp,
        level=level
    )

    # Store stats in inventory as metadata (for combat calculations)
    char.inventory["_stats"] = {
        "STR": str_score,
        "DEX": dex_score,
        "CON": con_score,
        "INT": int_score,
        "WIS": wis_score,
        "CHA": cha_score
    }
    char.inventory["_ac"] = ac
    char.inventory["_weapon"] = "Longsword"
    char.inventory["_weapon_damage"] = "1d8"

    char.spell_slots = spell_slots
    char.hit_dice_max = level
    char.hit_dice_current = level

    # Spells known
    char.inventory["_spells"] = [
        "Cure Wounds",      # Cleric 1st
        "Sacred Flame",     # Cleric cantrip
        "Bless",           # Cleric 1st (concentration)
        "Magic Missile",   # Wizard 1st
        "Shield",          # Wizard 1st (reaction)
        "Burning Hands",   # Wizard 1st
    ]

    return char


def create_drow_rogue() -> CharacterState:
    """Create a random Drow (Dark Elf) Rogue."""
    # Random stats (Drow get +2 DEX, +1 CHA)
    str_score = roll_stat()
    dex_score = roll_stat() + 2  # Drow racial
    con_score = roll_stat()
    int_score = roll_stat()
    wis_score = roll_stat()
    cha_score = roll_stat() + 1  # Drow racial

    # Random level (3-8)
    level = random.randint(3, 8)

    # Calculate HP (d8 for rogue)
    con_mod = ability_modifier(con_score)
    hp = 8 + con_mod  # 1st level max
    for _ in range(level - 1):
        hp += roll_dice(1, 8, con_mod)

    # AC (leather armor + DEX)
    ac = 11 + ability_modifier(dex_score)

    # Drow innate spellcasting
    spell_slots = SpellSlots(
        level_1=2,  # Drow magic
        level_2=1 if level >= 5 else 0
    )

    char = CharacterState(
        character_name="Vhaeraun Nightstalker",
        max_hp=hp,
        level=level
    )

    # Store stats
    char.inventory["_stats"] = {
        "STR": str_score,
        "DEX": dex_score,
        "CON": con_score,
        "INT": int_score,
        "WIS": wis_score,
        "CHA": cha_score
    }
    char.inventory["_ac"] = ac
    char.inventory["_weapon"] = "Rapier"
    char.inventory["_weapon_damage"] = "1d8"

    char.spell_slots = spell_slots
    char.hit_dice_max = level
    char.hit_dice_current = level

    # Drow spells
    char.inventory["_spells"] = [
        "Dancing Lights",  # Drow cantrip
        "Faerie Fire",    # Drow 1st level
        "Darkness",       # Drow 2nd level
    ]

    # Sneak attack damage
    sneak_attack_dice = (level + 1) // 2
    char.inventory["_sneak_attack"] = f"{sneak_attack_dice}d6"

    return char


def print_character_sheet(char: CharacterState):
    """Print character information."""
    stats = char.inventory.get("_stats", {})
    ac = char.inventory.get("_ac", 10)
    weapon = char.inventory.get("_weapon", "Unarmed")
    spells = char.inventory.get("_spells", [])

    print(f"\n{'='*60}")
    print(f"  {char.character_name} - Level {char.level}")
    print(f"{'='*60}")
    print(f"HP: {char.current_hp}/{char.max_hp} | AC: {ac}")
    print(f"Weapon: {weapon}")

    if stats:
        print(f"STR: {stats['STR']} ({ability_modifier(stats['STR']):+d}) | "
              f"DEX: {stats['DEX']} ({ability_modifier(stats['DEX']):+d}) | "
              f"CON: {stats['CON']} ({ability_modifier(stats['CON']):+d})")
        print(f"INT: {stats['INT']} ({ability_modifier(stats['INT']):+d}) | "
              f"WIS: {stats['WIS']} ({ability_modifier(stats['WIS']):+d}) | "
              f"CHA: {stats['CHA']} ({ability_modifier(stats['CHA']):+d})")

    if spells:
        print(f"Spells: {', '.join(spells)}")

    slots = char.spell_slots.get_available()
    if slots:
        slot_str = ", ".join([f"L{lvl}: {curr}/{max_}" for lvl, (curr, max_) in slots.items()])
        print(f"Spell Slots: {slot_str}")

    print(f"{'='*60}\n")


def make_attack(attacker: CharacterState, defender: CharacterState) -> dict:
    """Make a weapon attack."""
    attacker_stats = attacker.inventory.get("_stats", {})
    defender_ac = defender.inventory.get("_ac", 10)
    weapon = attacker.inventory.get("_weapon", "Unarmed")
    weapon_damage = attacker.inventory.get("_weapon_damage", "1d4")

    # Attack roll (d20 + STR or DEX modifier + proficiency)
    str_mod = ability_modifier(attacker_stats.get("STR", 10))
    dex_mod = ability_modifier(attacker_stats.get("DEX", 10))
    prof_bonus = (attacker.level - 1) // 4 + 2  # Proficiency bonus

    # Use DEX for finesse weapons (rapier), STR for others
    attack_mod = dex_mod if "Rapier" in weapon else str_mod

    attack_roll = roll_dice(1, 20, attack_mod + prof_bonus)
    natural_roll = attack_roll - attack_mod - prof_bonus

    # Critical hit on natural 20, critical miss on natural 1
    critical = natural_roll == 20
    miss = natural_roll == 1

    if miss or (attack_roll < defender_ac and not critical):
        return {
            "hit": False,
            "critical": False,
            "attack_roll": attack_roll,
            "damage": 0,
            "message": f"⚔️  {attacker.character_name} attacks with {weapon} (rolled {attack_roll} vs AC {defender_ac}) - MISS!"
        }

    # Hit! Roll damage
    dice_parts = weapon_damage.split('d')
    num_dice = int(dice_parts[0])
    die_size = int(dice_parts[1])

    damage_mod = attack_mod

    if critical:
        # Critical hit: double damage dice
        damage = roll_dice(num_dice * 2, die_size, damage_mod)
        message = f"⚔️  {attacker.character_name} attacks with {weapon} (rolled {attack_roll} vs AC {defender_ac}) - CRITICAL HIT! {damage} damage!"
    else:
        damage = roll_dice(num_dice, die_size, damage_mod)
        message = f"⚔️  {attacker.character_name} attacks with {weapon} (rolled {attack_roll} vs AC {defender_ac}) - HIT for {damage} damage!"

    # Check for sneak attack (Rogue)
    if "_sneak_attack" in attacker.inventory and random.random() > 0.5:
        sneak_dice = attacker.inventory["_sneak_attack"]
        dice_parts = sneak_dice.split('d')
        sneak_damage = roll_dice(int(dice_parts[0]), int(dice_parts[1]))
        damage += sneak_damage
        message += f" (+ {sneak_damage} sneak attack!)"

    return {
        "hit": True,
        "critical": critical,
        "attack_roll": attack_roll,
        "damage": damage,
        "message": message
    }


def cast_offensive_spell(caster: CharacterState, target: CharacterState) -> dict:
    """Cast an offensive spell."""
    spells = caster.inventory.get("_spells", [])
    caster_stats = caster.inventory.get("_stats", {})
    target_ac = target.inventory.get("_ac", 10)

    # Choose a spell to cast
    offensive_spells = []

    if "Magic Missile" in spells and caster.spell_slots.has_slot(1):
        offensive_spells.append(("Magic Missile", 1, "auto-hit"))
    if "Burning Hands" in spells and caster.spell_slots.has_slot(1):
        offensive_spells.append(("Burning Hands", 1, "save"))
    if "Sacred Flame" in spells:  # Cantrip
        offensive_spells.append(("Sacred Flame", 0, "save"))
    if "Faerie Fire" in spells and caster.spell_slots.has_slot(1):
        offensive_spells.append(("Faerie Fire", 1, "support"))

    if not offensive_spells:
        return {"cast": False, "message": "No offensive spells available"}

    spell_name, spell_level, spell_type = random.choice(offensive_spells)

    # Cast the spell
    result = caster.cast_spell(spell_level, spell_name)
    if not result["success"]:
        return {"cast": False, "message": f"Failed to cast {spell_name} - no spell slots"}

    # Calculate damage
    damage = 0
    message = f"✨ {caster.character_name} casts {spell_name}!"

    if spell_name == "Magic Missile":
        # 3 missiles, 1d4+1 each
        missiles = 3
        damage = sum(roll_dice(1, 4, 1) for _ in range(missiles))
        message += f" {missiles} missiles strike for {damage} force damage (auto-hit)!"

    elif spell_name == "Burning Hands":
        # 3d6 fire damage, DEX save for half
        damage = roll_dice(3, 6)
        # Simplified: 50% chance to save
        if random.random() > 0.5:
            damage //= 2
            message += f" Flames erupt! {target.character_name} saves for {damage} fire damage (halved)!"
        else:
            message += f" Flames erupt! {damage} fire damage!"

    elif spell_name == "Sacred Flame":
        # Cantrip: 1d8 radiant, DEX save
        if random.random() > 0.5:
            damage = 0
            message += f" Radiant light descends, but {target.character_name} dodges!"
        else:
            damage = roll_dice(1, 8)
            message += f" Radiant light strikes for {damage} radiant damage!"

    elif spell_name == "Faerie Fire":
        # Support spell - grants advantage
        message += f" {target.character_name} is outlined in magical light!"
        # Don't apply damage, just a visual effect for this simulation
        damage = 0

    return {
        "cast": True,
        "spell": spell_name,
        "damage": damage,
        "message": message
    }


def take_turn(attacker: CharacterState, defender: CharacterState, round_num: int):
    """Take a combat turn."""
    print(f"\n--- {attacker.character_name}'s Turn ---")

    # 40% chance to cast spell if available, 60% to attack
    if random.random() < 0.4:
        spell_result = cast_offensive_spell(attacker, defender)
        if spell_result.get("cast"):
            print(spell_result["message"])
            if spell_result.get("damage", 0) > 0:
                damage_result = defender.take_damage(spell_result["damage"])
                print(f"💥 {defender.character_name} takes {damage_result['damage_taken']} damage! ({defender.current_hp}/{defender.max_hp} HP remaining)")
                if damage_result.get("unconscious"):
                    print(f"💀 {defender.character_name} falls unconscious!")
            return
        # Spell failed, fall through to attack

    # Make weapon attack
    attack_result = make_attack(attacker, defender)
    print(attack_result["message"])

    if attack_result["hit"]:
        damage_result = defender.take_damage(attack_result["damage"])
        print(f"💥 {defender.character_name} takes {damage_result['damage_taken']} damage! ({defender.current_hp}/{defender.max_hp} HP remaining)")

        if damage_result.get("unconscious"):
            print(f"💀 {defender.character_name} falls unconscious!")


def run_combat():
    """Run a full combat simulation."""
    print("\n" + "="*60)
    print("  🎲 D&D COMBAT SIMULATOR 🎲")
    print("="*60)
    print("\n⚡ Generating Characters...\n")

    # Create characters
    hero = create_half_elf_multiclass()
    villain = create_drow_rogue()

    # Show character sheets
    print_character_sheet(hero)
    print_character_sheet(villain)

    # Roll initiative
    hero_stats = hero.inventory.get("_stats", {})
    villain_stats = villain.inventory.get("_stats", {})

    hero_init = roll_dice(1, 20, ability_modifier(hero_stats.get("DEX", 10)))
    villain_init = roll_dice(1, 20, ability_modifier(villain_stats.get("DEX", 10)))

    print(f"\n🎲 Initiative Rolls:")
    print(f"  {hero.character_name}: {hero_init}")
    print(f"  {villain.character_name}: {villain_init}")

    # Create combat state
    combat = CombatState()
    combat.start_combat({
        hero.character_name: hero_init,
        villain.character_name: villain_init
    })

    print(f"\n⚔️  COMBAT BEGINS! ⚔️")
    print(f"Turn Order: ", end="")
    for name, init in combat.initiative_order:
        print(f"{name} ({init})", end="  ")
    print("\n")

    # Combat loop
    while hero.is_conscious() and villain.is_conscious():
        current_name = combat.get_current_turn()

        print(f"\n{'='*60}")
        print(f"  ROUND {combat.round_number} - {current_name}'s Turn")
        print(f"{'='*60}")

        if current_name == hero.character_name:
            take_turn(hero, villain, combat.round_number)
        else:
            take_turn(villain, hero, combat.round_number)

        combat.next_turn()

        # Safety: max 20 rounds
        if combat.round_number > 20:
            print("\n⏰ Combat timeout after 20 rounds!")
            break

    # Combat ended
    print("\n" + "="*60)
    print("  ⚔️  COMBAT ENDED  ⚔️")
    print("="*60)

    if hero.is_conscious() and not villain.is_conscious():
        print(f"\n🏆 VICTORY! {hero.character_name} defeats {villain.character_name}!")
        print(f"   {hero.character_name} has {hero.current_hp}/{hero.max_hp} HP remaining")
    elif villain.is_conscious() and not hero.is_conscious():
        print(f"\n💀 DEFEAT! {villain.character_name} defeats {hero.character_name}!")
        print(f"   {villain.character_name} has {villain.current_hp}/{villain.max_hp} HP remaining")
    else:
        print(f"\n⚖️  DRAW! Both combatants still standing after {combat.round_number} rounds!")

    # Final stats
    print(f"\n📊 Combat Statistics:")
    print(f"   Rounds: {combat.round_number}")
    print(f"   {hero.character_name}: {hero.current_hp}/{hero.max_hp} HP")
    print(f"   {villain.character_name}: {villain.current_hp}/{villain.max_hp} HP")

    # Spell slots used
    hero_slots = hero.spell_slots.get_available()
    villain_slots = villain.spell_slots.get_available()

    if hero_slots:
        print(f"\n   {hero.character_name} Spell Slots:")
        for lvl, (curr, max_) in hero_slots.items():
            used = max_ - curr
            if max_ > 0:
                print(f"      Level {lvl}: {used}/{max_} used")

    if villain_slots:
        print(f"\n   {villain.character_name} Spell Slots:")
        for lvl, (curr, max_) in villain_slots.items():
            used = max_ - curr
            if max_ > 0:
                print(f"      Level {lvl}: {used}/{max_} used")

    print("\n" + "="*60 + "\n")


if __name__ == "__main__":
    # Seed for reproducibility (remove for true randomness)
    # random.seed(42)

    print("\n🎮 Starting Combat Simulation...\n")
    run_combat()

    print("\n✅ Combat simulation complete!")
    print("\n💡 Run again for a new random battle!\n")
