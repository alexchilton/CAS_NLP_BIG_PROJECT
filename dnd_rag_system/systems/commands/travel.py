"""
Travel and world exploration commands.

Handles: /travel, /map, /locations
"""

import logging
from typing import List

from .base import GameCommand, CommandResult, CommandContext
from dnd_rag_system.constants import Commands

logger = logging.getLogger(__name__)


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
