"""
Travel and world exploration commands.

Handles: /travel, /map, /locations, /explore
"""

import logging
from typing import List

from .base import GameCommand, CommandResult, CommandContext
from dnd_rag_system.constants import Commands
from dnd_rag_system.systems.world_builder import generate_llm_enhanced_location

logger = logging.getLogger(__name__)


class ExploreCommand(GameCommand):
    """Handle /explore command - discover new locations using LLM."""

    def get_patterns(self) -> List[str]:
        return [Commands.EXPLORE]  # '/explore'

    def execute(self, user_input: str, context: CommandContext) -> CommandResult:
        """
        Explore and discover a new location.
        
        Uses the roleplay LLM to generate rich, contextual descriptions
        based on current location, NPCs, defeated enemies, and game state.
        """
        current_loc = context.session.get_current_location_obj()
        
        if not current_loc:
            return CommandResult.failure("You need to be in a location before you can explore!")
        
        # Limit: Maximum 12 locations can be discovered from any single location
        # This prevents infinite exploration and keeps the world manageable
        MAX_CONNECTIONS = 12
        if len(current_loc.connections) >= MAX_CONNECTIONS:
            return CommandResult.failure(
                f"You've thoroughly explored {current_loc.name}. "
                f"There are no new areas to discover from here. "
                f"Try exploring from one of the {len(current_loc.connections)} connected locations instead."
            )
        
        # Prepare game context for LLM
        game_context = {
            'npcs_present': context.session.npcs_present,
            'defeated_enemies': getattr(context.session, 'defeated_enemies', {}),
        }
        
        # Define LLM function wrapper
        def llm_generate_func(prompt: str) -> str:
            """Call the roleplay LLM to generate location description."""
            # Access the LLM client from GameMaster
            if context.gm:
                try:
                    # Use the GameMaster's roleplay LLM client
                    if context.use_hf_api:
                        # Use HF API
                        return context.gm._query_hf(prompt)
                    else:
                        # Use Ollama with roleplay model
                        return context.gm._query_ollama(prompt)
                except Exception as e:
                    logger.error(f"LLM location generation failed: {e}")
                    raise
            else:
                raise ValueError("No LLM client available for location generation")
        
        # Generate new location using LLM
        try:
            new_location = generate_llm_enhanced_location(
                current_loc,
                llm_generate_func,
                game_context
            )
            
            # Add to world map
            context.session.add_location(new_location)
            
            # Move to the new location
            context.session.current_location = new_location.name
            
            # Build rich feedback
            feedback = f"🔍 **Exploring from {current_loc.name}...**\n\n"
            feedback += f"🗺️ **You discover: {new_location.name}**\n\n"
            feedback += f"_{new_location.description}_\n\n"
            feedback += f"**Type:** {new_location.location_type.value}\n"
            
            if not new_location.is_safe:
                feedback += "⚠️ **This area feels dangerous!**\n"
            
            feedback += f"\n💡 Added to your map. Use `/map` to see all discovered locations."
            
            logger.info(f"🔍 Explored from {current_loc.name} → discovered {new_location.name}")
            
            return CommandResult.success(feedback)
            
        except Exception as e:
            logger.error(f"Exploration failed: {e}")
            return CommandResult.failure(
                f"⚠️ Exploration failed: {str(e)}\n\n"
                f"Try using `/travel` to move to known locations instead."
            )


class TravelCommand(GameCommand):
    """Handle /travel <location> command."""

    def get_patterns(self) -> List[str]:
        return ['/travel ']  # Trailing space for prefix match

    def execute(self, user_input: str, context: CommandContext) -> CommandResult:
        """Travel to a location."""
        # Extract destination
        destination = user_input.split(' ', 1)[1].strip() if ' ' in user_input else ""
        if not destination:
            return CommandResult.failure("Specify a destination! Example: /travel Tavern")

        # Move to location
        success, message = context.session.travel_to(destination)

        if not success:
            # Location not found
            available_locs = ", ".join(list(context.session.world_map.keys())[:5])
            feedback = f"⚠️ {message}\n\n"
            feedback += f"**Known Locations:** {available_locs}\n\n"
            feedback += f"💡 Use `/map` to see all locations"
            return CommandResult.failure(feedback)

        # Successful travel
        new_location = context.session.get_current_location_obj()
        feedback = f"🗺️ **Arrived at {new_location.name}**\n\n"
        feedback += f"_{new_location.description}_\n\n"

        # Show available items if any
        if new_location.available_items:
            items_preview = ", ".join(new_location.available_items[:5])
            feedback += f"**Items here:** {items_preview}\n\n"

        # Show NPCs if any
        if new_location.resident_npcs:
            npcs_preview = ", ".join(new_location.resident_npcs[:5])
            feedback += f"**NPCs present:** {npcs_preview}\n\n"

        return CommandResult.success(feedback)


class MapCommand(GameCommand):
    """Handle /map command."""

    def get_patterns(self) -> List[str]:
        return [Commands.MAP]  # '/map'

    def execute(self, user_input: str, context: CommandContext) -> CommandResult:
        """Show world map with discovered locations."""
        locations = context.session.get_discovered_locations()

        if not locations:
            return CommandResult.failure("No locations discovered yet!")

        current_loc = context.session.current_location or "Unknown"

        feedback = "🗺️ **World Map**\n\n"
        feedback += f"**Current Location:** {current_loc}\n\n"
        feedback += "**Discovered Locations:**\n"

        for loc_name in locations:
            loc = context.session.get_location(loc_name)
            marker = "📍" if loc_name == current_loc else "  "
            feedback += f"{marker} **{loc_name}**"

            if loc:
                feedback += f" - {loc.description[:50]}..."
                if loc.resident_npcs:
                    feedback += f" (NPCs: {', '.join(loc.resident_npcs[:2])})"

            feedback += "\n"

        feedback += f"\n💡 Use `/travel <location>` to move"

        return CommandResult.success(feedback)


class LocationsCommand(GameCommand):
    """Handle /locations command."""

    def get_patterns(self) -> List[str]:
        return [Commands.LOCATIONS]  # '/locations'

    def execute(self, user_input: str, context: CommandContext) -> CommandResult:
        """Show detailed information about all discovered locations."""
        locations = context.session.get_discovered_locations()

        if not locations:
            return CommandResult.failure("No locations discovered yet!")

        feedback = "📍 **Known Locations**\n\n"

        for loc_name in locations:
            loc = context.session.get_location(loc_name)
            if not loc:
                continue

            current = "📍 " if loc_name == context.session.current_location else "   "
            feedback += f"{current}**{loc.name}**\n"
            feedback += f"_{loc.description}_\n"

            if loc.resident_npcs:
                feedback += f"NPCs: {', '.join(loc.resident_npcs)}\n"

            if loc.available_items:
                items_preview = ', '.join(loc.available_items[:5])
                if len(loc.available_items) > 5:
                    items_preview += f" (+{len(loc.available_items) - 5} more)"
                feedback += f"Items: {items_preview}\n"

            feedback += "\n"

        return CommandResult.success(feedback)
