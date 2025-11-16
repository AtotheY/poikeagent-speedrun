"""
Phase 4 prompt - Rival Battle & Pokedex
"""

from typing import List, Any
from .common import build_base_prompt
# from utils.state_formatter import find_path_around_obstacle  # Not in original repo


def _is_objective_completed(objectives: List[Any], objective_id: str) -> bool:
    """
    Check if a specific objective is completed.
    
    Args:
        objectives: List of objective objects
        objective_id: ID of the objective to check
        
    Returns:
        True if objective is completed, False otherwise
    """
    if not objectives:
        return False
    
    for obj in objectives:
        if hasattr(obj, 'id') and obj.id == objective_id and hasattr(obj, 'completed'):
            return obj.completed
    
    return False


def _get_phase_4_suggested_action(state_data, current_location: str = None, objectives: List[Any] = None) -> str:
    """
    Calculate the suggested action for Phase 4 based on location.
    
    Location-specific logic for ROUTE_103 objective:
    - Brendan's House 2F: Path to stairs (S), then go UP
    - Brendan's House 1F: Path to door (D), then go DOWN  
    - Littleroot Town: Go south to bottom, path to Birch's lab door (D), then go UP
    - Route 101/103: Go north, then RIGHT at top to find rival
    
    Args:
        state_data: Game state data
        current_location: Current location name
        objectives: Current objectives list
        
    Returns:
        Suggested action string to append at end of prompt
    """
    if not state_data:
        return ""
    
    route_103_done = objectives and _is_objective_completed(objectives, "ROUTE_103")
    
    # Location-specific handling for ROUTE_103 objective
    if not route_103_done and current_location:
        loc_upper = current_location.upper()
        
        # BRENDAN'S HOUSE 2F - go to stairs and exit
        if "BRENDAN" in loc_upper and "2F" in loc_upper:
            from utils.map_formatter import format_tile_to_symbol, format_map_grid
            from utils.state_formatter import astar_pathfind
            map_info = state_data.get('map', {})
            raw_tiles = map_info.get('tiles', [])
            if raw_tiles and len(raw_tiles) > 0:
                # Convert raw_tiles to symbol grid
                player_data = state_data.get('player', {})
                player_position = player_data.get('position', {})
                player_coords = (int(player_position.get('x', 0)), int(player_position.get('y', 0)))
                location_name = player_data.get('location', '')
                npcs = map_info.get('npcs', [])
                
                grid = format_map_grid(raw_tiles, "South", npcs, player_coords, location_name=location_name)
                
                if not grid:
                    return "\nSuggested action: DOWN"
                
                # Find player on grid
                player_grid_x = None
                player_grid_y = None
                for y_idx, row in enumerate(grid):
                    for x_idx, symbol in enumerate(row):
                        if symbol == 'P':
                            player_grid_x = x_idx
                            player_grid_y = y_idx
                            break
                    if player_grid_x is not None:
                        break
                
                if player_grid_x is None:
                    return "\nSuggested action: DOWN"
                
                # Check if already on stairs
                if grid[player_grid_y][player_grid_x] == 'S':
                    return "\nSuggested action: UP"
                
                # Find stairs on the symbol grid
                stairs_pos = None
                for y in range(len(grid)):
                    for x in range(len(grid[y])):
                        if grid[y][x] == 'S':
                            stairs_pos = (x, y)
                            break
                    if stairs_pos:
                        break
                
                # Use A* to pathfind to stairs
                if stairs_pos:
                    path = astar_pathfind(grid, (player_grid_x, player_grid_y), stairs_pos, location_name)
                    if path and len(path) > 0:
                        # Add one more UP to go through the stairs
                        path.append('UP')
                        return f"\nSuggested action: {', '.join(path)}"
            return "\nSuggested action: DOWN"
        
        # BRENDAN'S HOUSE 1F - go to door and exit
        elif "BRENDAN" in loc_upper and "1F" in loc_upper:
            from utils.map_formatter import format_map_grid
            from utils.state_formatter import astar_pathfind
            map_info = state_data.get('map', {})
            raw_tiles = map_info.get('tiles', [])
            if raw_tiles and len(raw_tiles) > 0:
                # Convert raw_tiles to symbol grid
                player_data = state_data.get('player', {})
                player_position = player_data.get('position', {})
                player_coords = (int(player_position.get('x', 0)), int(player_position.get('y', 0)))
                location_name = player_data.get('location', '')
                npcs = map_info.get('npcs', [])
                
                grid = format_map_grid(raw_tiles, "South", npcs, player_coords, location_name=location_name)
                
                if not grid:
                    return "\nSuggested action: DOWN"
                
                # Find player on grid
                player_grid_x = None
                player_grid_y = None
                for y_idx, row in enumerate(grid):
                    for x_idx, symbol in enumerate(row):
                        if symbol == 'P':
                            player_grid_x = x_idx
                            player_grid_y = y_idx
                            break
                    if player_grid_x is not None:
                        break
                
                if player_grid_x is None:
                    return "\nSuggested action: DOWN"
                
                # Check if already on door
                if grid[player_grid_y][player_grid_x] == 'D':
                    return "\nSuggested action: DOWN"
                
                # Find door on the symbol grid
                door_pos = None
                for y in range(len(grid)):
                    for x in range(len(grid[y])):
                        if grid[y][x] == 'D':
                            door_pos = (x, y)
                            break
                    if door_pos:
                        break
                
                # Use A* to pathfind to door
                if door_pos:
                    path = astar_pathfind(grid, (player_grid_x, player_grid_y), door_pos, location_name)
                    if path and len(path) > 0:
                        # Add one more DOWN to exit through the door
                        path.append('DOWN')
                        return f"\nSuggested action: {', '.join(path)}"
            return "\nSuggested action: DOWN"
        
        # LITTLEROOT TOWN - go south, then find Birch's lab
        elif "LITTLEROOT" in loc_upper:
            from utils.map_formatter import format_map_grid, format_tile_to_symbol
            from utils.state_formatter import astar_pathfind
            map_info = state_data.get('map', {})
            raw_tiles = map_info.get('tiles', [])
            
            if raw_tiles:
                # Convert raw_tiles to symbol grid
                player_data = state_data.get('player', {})
                player_position = player_data.get('position', {})
                player_coords = (int(player_position.get('x', 0)), int(player_position.get('y', 0)))
                location_name = player_data.get('location', '')
                npcs = map_info.get('npcs', [])
                
                grid = format_map_grid(raw_tiles, "South", npcs, player_coords, location_name=location_name)
                
                if not grid:
                    return "\nSuggested action: DOWN"
                
                # Find player on grid
                player_grid_x = None
                player_grid_y = None
                for y_idx, row in enumerate(grid):
                    for x_idx, symbol in enumerate(row):
                        if symbol == 'P':
                            player_grid_x = x_idx
                            player_grid_y = y_idx
                            break
                    if player_grid_x is not None:
                        break
                
                if player_grid_x is None:
                    return "\nSuggested action: DOWN"
                
                # Check if at bottom of map
                tiles_below = 0
                walkable_below = 0
                for y in range(player_grid_y + 1, len(grid)):
                    for symbol in grid[y]:
                        tiles_below += 1
                        if symbol in ['.', '~', 'D', 'S']:
                            walkable_below += 1
                
                # At bottom - find door to Birch's lab using A*
                if tiles_below > 0 and (walkable_below / tiles_below) < 0.1:
                    # Find nearest door
                    door_pos = None
                    for y in range(len(grid)):
                        for x in range(len(grid[y])):
                            if grid[y][x] == 'D':
                                door_pos = (x, y)
                                break
                        if door_pos:
                            break
                    
                    # Use A* to pathfind to door
                    if door_pos:
                        path = astar_pathfind(grid, (player_grid_x, player_grid_y), door_pos, location_name)
                        if path and len(path) > 0:
                            # Add one more UP to enter Birch's lab
                            path.append('UP')
                            return f"\nSuggested action: {', '.join(path)}"
                    return "\nSuggested action: LEFT"
                else:
                    # Continue south
                    # path_info = find_path_around_obstacle(state_data, 'DOWN')  # Not in original repo
                    # if path_info and path_info.get('is_blocked') and path_info.get('detour_needed'):
                    #     action_seq = path_info.get('action_sequence', [])
                    #     if action_seq:
                    #         return f"\nSuggested action: {', '.join(action_seq)}"
                    return "\nSuggested action: DOWN"
        
        # ROUTE 101/103 - go north to rival
        elif "ROUTE" in loc_upper:
            map_info = state_data.get('map', {})
            raw_tiles = map_info.get('tiles', [])
            
            if raw_tiles:
                center_y = len(raw_tiles) // 2
                tiles_above = 0
                walkable_above = 0
                
                for y in range(center_y):
                    if y < len(raw_tiles):
                        for tile in raw_tiles[y]:
                            if tile:
                                tiles_above += 1
                                from utils.map_formatter import format_tile_to_symbol
                                symbol = format_tile_to_symbol(tile)
                                if symbol in ['.', '~', 'D', 'S']:
                                    walkable_above += 1
                
                # At top - go RIGHT to find rival
                if tiles_above > 0 and (walkable_above / tiles_above) < 0.1:
                    return "\nSuggested action: RIGHT"
            
            # Continue north
            # path_info = find_path_around_obstacle(state_data, 'UP')  # Not in original repo
            # if path_info and path_info.get('is_blocked') and path_info.get('detour_needed'):
            #     action_seq = path_info.get('action_sequence', [])
            #     if action_seq:
            #         return f"\nSuggested action: {', '.join(action_seq)}"
            return "\nSuggested action: UP"
    
    return "\nSuggested action: UP"


def _get_phase_4_conditional_prompts(objectives: List[Any], current_location: str = None) -> str:
    """
    Generate conditional prompt sections based on completed objectives.
    
    Phase 4 Objectives (in order):
    - OLDALE_TOWN: Reach Oldale Town (first town north of Route 101)
    - ROUTE_103: Navigate to Route 103 to battle your rival
    - RECEIVED_POKEDEX: Receive the Pokedex from Professor Birch
    
    Args:
        objectives: List of objective objects
        current_location: Current location name
        
    Returns:
        Conditional prompt text based on current progress
    """
    conditional_sections = []
    
    
#     if not _is_objective_completed(objectives, "OLDALE_TOWN"):
#         # Still need to reach Oldale Town
#         conditional_sections.append("""
# 🗺️  FIND YOUR RIVAL:

# YOUR GOAL IS TO GO NORTH (UP) NEVER GO DOWN UNLESS YOU HAVE A REASON TO.

# IMPORTANT - THIS IS THE MOST IMPORTANT INSTRUCTION:
# - WHEN IN BATTLE, ALWAYS DO: "A, B, LEFT, A, RIGHT, A" TO ATTACK. CHAIN THE ENTIRE THING IN ONE ACTION.
# - YOUR GOAL IS TO GO COMPLETELY NORTH AND AVOID DOORS AT ALL COSTS. IF YOU CANNOT ANYMORE, YOUR GOAL IS TO GO NEXT TO THE 'N' ON THE MAP AND PRESS A.
# - IF YOU ARE IN PROFESSOR BIRCHS LAB, GO DOWN!!! PLEASE JUST GO DOWN IF U SEE PROFESSIOR BIRCH'S LAB ANYWHERE IN THE LOCATION INFORMATION. JUST DOWN!
# - YOUR RIVAL IS MARKED AS N ON THE MAP in the most NORTHERN part of the map on route 103. YOU NEED TO GO RIGHT BESIDE HER AND CLICK A. THIS WILL INVOLVE GOING DOWN ONE AND RIGHT A BUNCH.
# - YOUR RIVAL IS AT (7,13) FACE IT AND PRESS A. MOVE RIGHT IF YOU DO NOT SEE THEM.
# - FOLLOW THE SUGGESTED ACTION UNLESS U ARE GOING TO YOUR RIVAL. IT IS ALWAYS SMARTER THAN YOU.
# """)


    if not _is_objective_completed(objectives, "OLDALE_TOWN"):
        # Still need to reach Oldale Town - provide location-specific guidance
        loc_upper = current_location.upper() if current_location else ""
        
        # Add general instruction about pressing A
        conditional_sections.append("""
⚠️ CRITICAL: ALWAYS END YOUR ACTION CHAINS WITH 'A' TO INTERACT!
- When navigating: Add 'A' at the end (e.g., "LEFT, UP, UP, A")
- When at doors/stairs: Add 'A' at the end (e.g., "DOWN, A")
- When near NPCs: Add 'A' at the end (e.g., "RIGHT, A")
- This ensures you interact with doors, stairs, NPCs, and objects automatically!
""")
        
        if "BRENDAN" in loc_upper and "2F" in loc_upper:
            conditional_sections.append("""
🏠 BRENDAN'S HOUSE 2F:
- Look for the STAIRS symbol (S) on the map
- Path to the stairs (usually DOWN)
- When standing on stairs (S), press UP to go downstairs
- Follow the suggested action and ADD 'A' at the end
""")
        elif "BRENDAN" in loc_upper and "1F" in loc_upper:
            conditional_sections.append("""
🏠 BRENDAN'S HOUSE 1F:
- Look for the DOOR symbol (D) on the map
- Path to the door (usually DOWN)
- When standing on door (D), press DOWN to exit
- Follow the suggested action and ADD 'A' at the end
""")
        elif "LITTLEROOT" in loc_upper:
            conditional_sections.append("""
🏘️ LITTLEROOT TOWN:
- Go SOUTH to the bottom of the map
- Look for Birch's lab door (D) - it's at the southern area
- Path to the door (may need to go LEFT/RIGHT)
- When near the door (D), press UP to enter Birch's lab
- Follow the suggested action and ADD 'A' at the end
""")
        elif "ROUTE" in loc_upper:
            conditional_sections.append("""
🗺️ ROUTE 101/103 - FIND YOUR RIVAL:
- Go NORTH (UP) towards Route 103
- When you reach the top (can't go further north), go RIGHT
- Your rival is at the top-right of Route 103
- ALWAYS ADD 'A' at the end of movement to interact with rival
- IN BATTLE: Use "A, B, LEFT, A, RIGHT, A" as one chain
- Follow the suggested action and ADD 'A' at the end
""")
        else:
            conditional_sections.append("""
🗺️ FIND YOUR RIVAL:
- Exit Brendan's house and head to Birch's lab
- Navigate through Littleroot Town
- Head north through Route 101 to Route 103
- Find rival at top-right of Route 103
- ALWAYS ADD 'A' at the end of every action chain
- Follow the suggested action and ADD 'A' at the end
""")
    
    elif not _is_objective_completed(objectives, "ROUTE_103"):
        conditional_sections.append("""
⚔️ FIND YOUR RIVAL:
- From Oldale Town, head north to Route 103
- Your rival is waiting on Route 103 which is straight NORTH for a Pokemon battle
- Safe walkable spots on the map are denoted as "." while blocked spots are denoted as "#".
- Keep going north as far as you can. Note this may mean you have to go around blocked spots by going left then right.
- ALWAYS ADD 'A' at the end of movement chains to interact with rival/objects
- You may encounter pokemon battles - if you do press over and over until the battle is over.
""")
    
    elif not _is_objective_completed(objectives, "RECEIVED_POKEDEX"):
        conditional_sections.append("""
📱 GET THE POKEDEX:
- After defeating your rival, return to Littleroot Town
- Visit Professor Birch's lab
- You'll receive the Pokedex - a device to record Pokemon data
- Press A to advance dialogue and receive the Pokedex
- The Pokedex is essential for tracking your Pokemon journey!""")
    
    
    return "\n".join(conditional_sections)


def get_phase_4_prompt(
    objectives: List[Any] = None,
    debug: bool = False,
    include_base_intro: bool = False,  # No generic intro
    include_pathfinding_rules: bool = False,  # No long pathfinding rules
    include_pathfinding_helper: bool = True,  # YES - show A* pathfinding actions!
    include_response_structure: bool = True,  # Keep action input format
    include_action_history: bool = False,  # Remove action history
    include_location_history: bool = False,  # Remove location history
    include_objectives: bool = False,  # Remove objectives (we have milestone instructions)
    include_movement_memory: bool = False,  # Remove movement memory
    include_stuck_warning: bool = False,  # Remove stuck warnings
    include_phase_tips: bool = False,  # No tips
    formatted_state: str = None,  # To extract location
    state_data = None,  # For pathfinding helper
    **kwargs
) -> str:
    """
    Get the Phase 4 prompt template with conditional sections based on objectives.
    
    Phase 4 covers: Rival battle on Route 103 and receiving the Pokedex
    
    CLEAN PROMPT - Only includes:
    - Milestone-based instructions
    - Map / Legend / Map Tiles (from formatted_state)
    - Game State
    - Action input instructions
    - Pathfinding recommended actions (A* paths)
    
    Args:
        objectives: List of current objective objects (for conditional prompts)
        debug: If True, log the prompt to console
        formatted_state: Formatted state string (includes map)
        state_data: Game state data for pathfinding helper
        **kwargs: All other prompt building arguments (passed to build_base_prompt)
        
    Returns:
        Complete formatted prompt string
    """
    # Extract current location from formatted_state if available
    current_location = None
    if formatted_state and "Current Location:" in formatted_state:
        # Extract location from "Current Location: OLDALE_TOWN" line
        for line in formatted_state.split('\n'):
            if line.strip().startswith("Current Location:"):
                current_location = line.split(":", 1)[1].strip()
                break
    
    # If no location from formatted_state, try state_data
    if not current_location and state_data:
        current_location = state_data.get('player', {}).get('location', '')
    
    # Build base intro
    base_intro = "🎮 PHASE 4: Rival Battle & Pokedex"
    
    # Add conditional prompts based on objectives and location
    conditional_prompts = _get_phase_4_conditional_prompts(objectives or [], current_location)
    
    # Build phase intro - only add tips if requested
    if include_phase_tips:
        phase_intro = f"""{base_intro}

{conditional_prompts}
"""
    else:
        phase_intro = f"""{base_intro}

{conditional_prompts}"""
    
    # Calculate suggested action for Phase 4
    suggested_action = _get_phase_4_suggested_action(state_data, current_location, objectives)
    
    return build_base_prompt(
        phase_intro=phase_intro,
        debug=debug,
        include_base_intro=include_base_intro,
        include_pathfinding_rules=include_pathfinding_rules,
        include_pathfinding_helper=include_pathfinding_helper,
        include_response_structure=include_response_structure,
        include_action_history=include_action_history,
        include_location_history=include_location_history,
        include_objectives=include_objectives,
        include_movement_memory=include_movement_memory,
        include_stuck_warning=include_stuck_warning,
        phase_intro_at_end=True,  # Put milestone instructions AFTER map/state
        suggested_action_suffix=suggested_action,  # Add suggested action at the end
        formatted_state=formatted_state,
        state_data=state_data,
        **kwargs
    )

