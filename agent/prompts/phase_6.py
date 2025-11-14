"""
Phase 6 prompt - Road to Rustboro City
"""

from typing import List, Any
from .common import build_base_prompt


def _get_full_path_to_direction(state_data, target_direction: str, location_name: str = '') -> List[str]:
    """
    Get full A* path to the most extreme REACHABLE point in a given direction.
    Tries multiple candidate points until it finds one that's actually pathable.
    """
    print(f"[PHASE 6 DEBUG] _get_full_path_to_direction called: direction={target_direction}, location={location_name}")
    
    if not state_data:
        print("[PHASE 6 DEBUG] No state_data provided!")
        return []
    
    try:
        from utils.map_formatter import format_map_grid
        from utils.state_formatter import astar_pathfind
        
        # Get player info
        player_data = state_data.get('player', {})
        player_position = player_data.get('position', {})
        player_coords = (int(player_position.get('x', 0)), int(player_position.get('y', 0)))
        
        # Get map data
        map_info = state_data.get('map', {})
        raw_tiles = map_info.get('tiles', [])
        npcs = map_info.get('npcs', [])
        
        if not raw_tiles:
            return []
        
        # Generate grid
        grid = format_map_grid(raw_tiles, "South", npcs, player_coords, location_name=location_name)
        
        if not grid:
            return []
        
        grid_height = len(grid)
        grid_width = len(grid[0]) if grid else 0
        
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
            return []
        
        # Convert to grid array index
        player_y_idx = grid_height - 1 - player_grid_y
        
        # Find ALL walkable tiles and filter by direction
        walkable_tiles = ['.', '~', 'S']
        candidates = []
        center_x = grid_width // 2
        center_y = grid_height // 2
        
        for y_idx, row in enumerate(grid):
            for x_idx, symbol in enumerate(row):
                if symbol in walkable_tiles:
                    # Calculate grid Y coordinate
                    grid_y = grid_height - 1 - y_idx
                    
                    # Filter by direction
                    if target_direction == 'UP' and grid_y > player_grid_y:
                        # Higher Y = more north, prefer centered
                        score = (grid_y * 1000) - abs(x_idx - center_x)
                        candidates.append((score, (x_idx, y_idx)))
                    elif target_direction == 'DOWN' and grid_y < player_grid_y:
                        score = (grid_y * -1000) - abs(x_idx - center_x)
                        candidates.append((score, (x_idx, y_idx)))
                    elif target_direction == 'LEFT' and x_idx < player_grid_x:
                        score = (x_idx * -1000) - abs(y_idx - center_y)
                        candidates.append((score, (x_idx, y_idx)))
                    elif target_direction == 'RIGHT' and x_idx > player_grid_x:
                        score = (x_idx * 1000) - abs(y_idx - center_y)
                        candidates.append((score, (x_idx, y_idx)))
        
        # Sort by score (best first)
        candidates.sort(reverse=True, key=lambda x: x[0])
        
        print(f"[PHASE 6 DEBUG] Found {len(candidates)} candidate tiles in direction {target_direction}")
        
        # Try to path to each candidate until we find one that works
        for i, (score, goal_pos) in enumerate(candidates[:20]):  # Try up to 20 best candidates
            path = astar_pathfind(grid, (player_grid_x, player_y_idx), goal_pos, location_name)
            if path and len(path) > 0:
                print(f"[PHASE 6 DEBUG] Found path to candidate #{i+1}: {path}")
                return path
        
        print(f"[PHASE 6 DEBUG] No path found to any candidate")
        return []
        
    except Exception as e:
        import traceback
        print(f"[PHASE 6 PATHFINDING ERROR] {e}")
        traceback.print_exc()
        return []


def _get_route_104_north_path(state_data, location_name: str = '') -> List[str]:
    """Get full A* path to the most northern point in Route 104."""
    return _get_full_path_to_direction(state_data, 'UP', location_name)


def _get_petalburg_west_path(state_data, location_name: str = '') -> List[str]:
    """Get full A* path to the most western point in Petalburg."""
    return _get_full_path_to_direction(state_data, 'LEFT', location_name)


def _path_to_leftmost_stairs(state_data, location_name: str = '') -> List[str]:
    """
    Find the leftmost stairs/warp (S) on the map and path to it.
    Used for entering Petalburg Woods from Route 104.
    """
    if not state_data:
        return []
    
    try:
        from utils.map_formatter import format_map_grid
        from utils.state_formatter import astar_pathfind
        
        # Get player info
        player_data = state_data.get('player', {})
        player_position = player_data.get('position', {})
        player_coords = (int(player_position.get('x', 0)), int(player_position.get('y', 0)))
        
        # Get map data
        map_info = state_data.get('map', {})
        raw_tiles = map_info.get('tiles', [])
        npcs = map_info.get('npcs', [])
        
        if not raw_tiles:
            return []
        
        # Generate grid
        grid = format_map_grid(raw_tiles, "South", npcs, player_coords, location_name=location_name)
        
        if not grid:
            return []
        
        grid_height = len(grid)
        
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
            return []
        
        # Find all stairs/warp tiles (S) - NOT doors (D)!
        # Only 'S' represents the Petalburg Woods entrance
        stairs_positions = []
        for y_idx, row in enumerate(grid):
            for x_idx, symbol in enumerate(row):
                if symbol == 'S':  # ONLY stairs, NOT 'D' (doors)
                    stairs_positions.append((x_idx, y_idx))
        
        if not stairs_positions:
            print("[PHASE 6 DEBUG] No stairs found on map")
            return []
        
        # Filter out stairs near water (within 5 tiles of 'W') AND near map edges
        # Petalburg Woods entrance is on land, not near water or edges
        grid_height = len(grid)
        valid_stairs = []
        for stairs_pos in stairs_positions:
            sx, sy = stairs_pos
            
            # Reject stairs in top 3 rows (near edge, usually water areas)
            if sy <= 2:
                print(f"[PHASE 6 DEBUG] Stairs at {stairs_pos} rejected (too close to top edge)")
                continue
            
            # Check if near water (within 5 tiles)
            near_water = False
            for dy in range(-5, 6):
                for dx in range(-5, 6):
                    check_x = sx + dx
                    check_y = sy + dy
                    
                    # Check bounds
                    if 0 <= check_y < len(grid) and 0 <= check_x < len(grid[check_y]):
                        if grid[check_y][check_x] == 'W':
                            near_water = True
                            break
                if near_water:
                    break
            
            if not near_water:
                valid_stairs.append(stairs_pos)
                print(f"[PHASE 6 DEBUG] Stairs at {stairs_pos} is valid (not near water/edge)")
            else:
                print(f"[PHASE 6 DEBUG] Stairs at {stairs_pos} rejected (near water)")
        
        if not valid_stairs:
            print("[PHASE 6 DEBUG] No valid stairs found (all near water)")
            return []
        
        # Pick the leftmost valid stairs (smallest X coordinate)
        leftmost_stairs = min(valid_stairs, key=lambda pos: pos[0])
        print(f"[PHASE 6 DEBUG] Found {len(valid_stairs)} valid stairs, leftmost at {leftmost_stairs}")
        
        # Convert player to grid array index
        player_y_idx = grid_height - 1 - player_grid_y
        
        # Use A* to find path to stairs
        path = astar_pathfind(grid, (player_grid_x, player_y_idx), leftmost_stairs, location_name)
        
        return path if path else []
        
    except Exception as e:
        import traceback
        print(f"[PHASE 6 STAIRS PATHFINDING ERROR] {e}")
        traceback.print_exc()
        return []


def get_phase_6_prompt(
    objectives=None,  # Accept objectives parameter for consistency
    debug: bool = False,
    include_base_intro: bool = False,  # No generic intro
    include_pathfinding_rules: bool = False,  # No long pathfinding rules
    include_pathfinding_helper: bool = False,  # NO - we provide custom suggested actions!
    include_response_structure: bool = True,  # Keep action input format
    include_action_history: bool = False,  # Remove action history
    include_location_history: bool = False,  # Remove location history
    include_objectives: bool = False,  # Remove objectives (we have milestone instructions)
    include_movement_memory: bool = False,  # Remove movement memory
    include_stuck_warning: bool = False,  # Remove stuck warnings
    state_data=None,  # For pathfinding
    formatted_state='',  # For getting current location
    **kwargs
) -> str:
    """
    Get the Phase 6 prompt template.
    
    Phase 6 covers: Road to Rustboro City
    """
    # Get current location from formatted_state
    current_location = ''
    if formatted_state and "Current Location:" in formatted_state:
        for line in formatted_state.split('\n'):
            if line.strip().startswith("Current Location:"):
                current_location = line.split(":", 1)[1].strip()
                break
    
    # Calculate suggested action based on location
    suggested_action = _get_phase_6_suggested_action(state_data, current_location)
    print(f"[PHASE 6 DEBUG] Suggested action calculated: '{suggested_action}'")
    
    # Handle special locations in Phase 6  
    loc_upper = current_location.upper() if current_location else ""
    
    if "ROUTE_102" in loc_upper or "ROUTE 102" in loc_upper:
        # Wally is showing you how to catch Pokemon - spam A
        phase_intro = """🎮 PHASE 6: Road to Rustboro City

📍 ROUTE 102 - WALLY'S TUTORIAL
- Wally is showing you how to catch Pokemon
- Just spam A to skip the dialogue/tutorial: A, A, A, A, A, A, A, A, A, A, A, A, A, A, A, A, A, A, A, A"""
    
    elif "GYM" in loc_upper:
        phase_intro = """🎮 PHASE 6: Road to Rustboro City

📍 IN PETALBURG GYM  
- Spam A to finish all dialogue/Wally tutorial
- Then exit the gym via the door"""
    
    elif "PETALBURG" in loc_upper:
        phase_intro = """🎮 PHASE 6: Road to Rustboro City

📍 PETALBURG CITY
- Exit Petalburg and head WEST toward Route 104
- Follow the suggested action to path west"""
    
    elif "ROUTE_104" in loc_upper or "ROUTE 104" in loc_upper:
        phase_intro = """🎮 PHASE 6: Road to Rustboro City

📍 ROUTE 104
- CHAIN THE ENTIRE THING IN ONE ACTION. 
- FOLLOW THE SUGGESTED ACTIONS EXACTLY! """
    
    else:
        phase_intro = """🎮 - CHAIN THE ENTIRE THING IN ONE ACTION. 
- FOLLOW THE SUGGESTED ACTIONS EXACTLY!."""
    
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
        suggested_action_suffix=suggested_action,  # Add custom suggested action
        formatted_state=formatted_state,
        state_data=state_data,
        **kwargs
    )


def _get_phase_6_suggested_action(state_data, current_location: str = None) -> str:
    """
    Calculate the suggested action for Phase 6 based on location.
    """
    print(f"[PHASE 6 DEBUG] _get_phase_6_suggested_action called with location={current_location}")
    
    if not state_data:
        print("[PHASE 6 DEBUG] No state_data!")
        return ""
    
    # Check if in battle FIRST (location info is hidden during battle)
    game_data = state_data.get('game', {})
    is_in_battle = game_data.get('is_in_battle', False) or game_data.get('in_battle', False)
    
    print(f"[PHASE 6 DEBUG] game_data={game_data}, is_in_battle={is_in_battle}")
    
    # If in battle, return randomized battle sequence (33/33/33) - 3 different sequences
    if is_in_battle:
        import random
        rand = random.random()
        if rand < 0.33:
            return "\nSuggested action: UP, LEFT, A, B, LEFT, LEFT, LEFT, LEFT, LEFT, LEFT A, RIGHT, UP, RIGHT, A, B, B"
        elif rand < 0.66:
            return "\nSuggested action: UP, LEFT, A, B, LEFT, LEFT, LEFT, LEFT, LEFT, LEFT, A, LEFT, DOWN, DOWN, A, B, B"
        else:
            return "\nSuggested action: UP, LEFT, A, B, LEFT, LEFT, LEFT, LEFT, LEFT, LEFT, A, LEFT, DOWN, DOWN, RIGHT, RIGHT, A, B, B"
    
    # Not in battle - check location for navigation
    if not current_location:
        return ""
    
    loc_upper = current_location.upper()
    
    # Route 102 - Wally tutorial, spam A
    if "ROUTE_102" in loc_upper or "ROUTE 102" in loc_upper:
        return "\nSuggested action: A, A, A, A, A, A, A, A, A, A, A, A, A, A, A, A, A, A, A, A"
    
    # Gym - spam A then exit
    elif "GYM" in loc_upper:
        return "\nSuggested action: A, A, A, A, A, A, A, A, A, A, A, A, A, A, A, A, RIGHT, DOWN, A"
    
    # Petalburg City - path west
    elif "PETALBURG" in loc_upper:
        action_seq = _get_petalburg_west_path(state_data, current_location)
        if action_seq and len(action_seq) > 0:
            action_seq.append('A')
            return f"\nSuggested action: {', '.join(action_seq)}"
        return "\nSuggested action: LEFT, A"
    
    # Petalburg Woods - navigate through the maze
    # Priority: NORTH > EAST > WEST > SOUTH (woods go northeast first)
    elif "MAP" in loc_upper or "WOOD" in loc_upper or "PETALBURG" in current_location:
        print(f"[PHASE 6 DEBUG] In Petalburg Woods, trying all directions")
        
        # Try north first - this is the main direction through the woods
        north_seq = _get_full_path_to_direction(state_data, 'UP', current_location)
        if north_seq and len(north_seq) > 0:
            print(f"[PHASE 6 DEBUG] Using NORTH path: {north_seq}")
            north_seq.append('A')
            return f"\nSuggested action: {', '.join(north_seq)}"
        
        # North blocked, try EAST (woods go northeast)
        print(f"[PHASE 6 DEBUG] North blocked, trying EAST")
        east_seq = _get_full_path_to_direction(state_data, 'RIGHT', current_location)
        if east_seq and len(east_seq) > 0:
            # Count how many RIGHT moves in the path
            right_count = east_seq.count('RIGHT')
            if right_count > 0:
                # Multiply horizontal movement by 3x to escape local minimums
                east_seq = ['RIGHT'] * (right_count * 3)
                print(f"[PHASE 6 DEBUG] Using EAST path (3x multiplied): {east_seq}")
                east_seq.append('A')
                return f"\nSuggested action: {', '.join(east_seq)}"
        
        # East blocked, try west
        print(f"[PHASE 6 DEBUG] East blocked, trying WEST")
        west_seq = _get_full_path_to_direction(state_data, 'LEFT', current_location)
        if west_seq and len(west_seq) > 0:
            # Count how many LEFT moves in the path
            left_count = west_seq.count('LEFT')
            if left_count > 0:
                # Multiply horizontal movement by 3x to escape local minimums
                west_seq = ['LEFT'] * (left_count * 3)
                print(f"[PHASE 6 DEBUG] Using WEST path (3x multiplied): {west_seq}")
                west_seq.append('A')
                return f"\nSuggested action: {', '.join(west_seq)}"
        
        # Last resort - go south (backwards)
        print(f"[PHASE 6 DEBUG] All forward directions blocked, trying SOUTH")
        south_seq = _get_full_path_to_direction(state_data, 'DOWN', current_location)
        if south_seq and len(south_seq) > 0:
            print(f"[PHASE 6 DEBUG] Using SOUTH path: {south_seq}")
            south_seq.append('A')
            return f"\nSuggested action: {', '.join(south_seq)}"
        
        # Absolute fallback
        print(f"[PHASE 6 DEBUG] No paths found, using fallback")
        return "\nSuggested action: RIGHT, A"
    
    # Route 104 - check for stairs/warp first, then try both north and west
    elif "ROUTE_104" in loc_upper or "ROUTE 104" in loc_upper:
        # Check if there's a stairs/warp (S) on the map - entrance to Petalburg Woods
        stairs_path = _path_to_leftmost_stairs(state_data, current_location)
        if stairs_path and len(stairs_path) > 0:
            # Found stairs - path to it and add 8 UPs to enter the woods
            print(f"[PHASE 6 DEBUG] Found stairs, pathing to it: {stairs_path}")
            stairs_path.extend(['UP'] * 8)
            stairs_path.append('A')
            return f"\nSuggested action: {', '.join(stairs_path)}"
        
        print(f"[PHASE 6 DEBUG] No stairs found, trying both NORTH and WEST paths")
        
        # Get both paths
        north_seq = _get_route_104_north_path(state_data, current_location)
        west_seq = _get_petalburg_west_path(state_data, current_location)
        
        north_len = len(north_seq) if north_seq else 0
        west_len = len(west_seq) if west_seq else 0
        
        print(f"[PHASE 6 DEBUG] North path length: {north_len}, West path length: {west_len}")
        
        # Pick whichever path is LONGER (makes more progress)
        if west_len > north_len:
            # West makes more progress - use it
            print(f"[PHASE 6 DEBUG] West path is longer, using WEST")
            west_seq.append('A')
            return f"\nSuggested action: {', '.join(west_seq)}"
        elif north_len > 0:
            # North path exists and is longer/equal - use it
            print(f"[PHASE 6 DEBUG] North path is longer/equal, using NORTH")
            north_seq.append('A')
            return f"\nSuggested action: {', '.join(north_seq)}"
        elif west_len > 0:
            # Only west path exists
            print(f"[PHASE 6 DEBUG] Only west path exists, using WEST")
            west_seq.append('A')
            return f"\nSuggested action: {', '.join(west_seq)}"
        else:
            # No paths found - fallback
            print(f"[PHASE 6 DEBUG] No paths found, using fallback")
            return "\nSuggested action: DOWN, A"
    
    return ""

