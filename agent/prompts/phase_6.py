"""
Phase 6 prompt - Road to Rustboro City and beyond (FINAL PHASE)
Handles all gameplay from Route 104 through the end of the game.

Structure:
- Location-based nested conditions (location + objectives + Pokemon health)
- Simple pathfinding types:
  1. Combat (battle sequences)
  2. Directional priority (NORTH > EAST > WEST > SOUTH)
  3. Door pathing (path to door + append sequence)
  4. Hardcoded sequences
"""

from typing import List, Dict, Any, Optional, Tuple
from .common import build_base_prompt


# ============================================================================
# PHASE 6 CONFIGURATION
# ============================================================================

def _get_pokemon_hp_status(state_data) -> str:
    """
    Check if Pokemon have low HP (< 50%).
    Returns 'low' if any Pokemon is below 50% HP, 'full' otherwise.
    """
    try:
        party = state_data.get('party', [])
        for pokemon in party:
            if pokemon.get('hp', 0) > 0:  # Only check alive Pokemon
                max_hp = pokemon.get('max_hp', 1)
                current_hp = pokemon.get('hp', 0)
                hp_percent = (current_hp / max_hp) * 100
                if hp_percent < 50:
                    print(f"[PHASE 6 DEBUG] Low HP detected: {current_hp}/{max_hp} ({hp_percent:.1f}%)")
                    return 'low'
        return 'full'
    except Exception as e:
        print(f"[PHASE 6 DEBUG] Error checking HP: {e}")
        return 'full'


def _is_objective_completed(objectives, objective_id: str) -> bool:
    """Check if a specific objective is completed."""
    if not objectives:
        return False
    for obj in objectives:
        if hasattr(obj, 'id') and obj.id == objective_id and hasattr(obj, 'completed'):
            return obj.completed
    return False


# ============================================================================
# PATHFINDING UTILITIES
# ============================================================================

def _get_full_path_to_direction(state_data, target_direction: str, location_name: str = '') -> List[str]:
    """
    Get full A* path to a point in the target direction.
    Only considers targets that are at least 2+ tiles in that direction.
    Returns empty list if no valid path found (direction is blocked).
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
        grid_width = len(grid[0]) if grid else 0
        
        # Find player on grid
        player_grid_x = None
        player_y_idx = None  # Array index for A*
        player_visual_y = None  # Visual Y coordinate
        for y_idx, row in enumerate(grid):
            for x_idx, symbol in enumerate(row):
                if symbol == 'P':
                    player_grid_x = x_idx
                    player_y_idx = y_idx  # Array index (for A* pathfinding)
                    player_visual_y = grid_height - 1 - y_idx  # Visual Y coordinate
                    break
            if player_grid_x is not None:
                break
        
        if player_grid_x is None:
            return []
        
        # Find ALL walkable tiles and filter by direction
        # ONLY pick tiles that are at least 2+ tiles in the target direction
        # STRONGLY prefer staying on the same row/column (same Y for EAST/WEST, same X for NORTH/SOUTH)
        walkable_tiles = ['.', '~', 'S']
        candidates = []
        
        for y_idx, row in enumerate(grid):
            for x_idx, symbol in enumerate(row):
                if symbol in walkable_tiles:
                    # Calculate grid Y coordinate
                    grid_y = grid_height - 1 - y_idx
                    
                    # Filter by direction - MUST be at least 2 tiles in that direction
                    # Score: distance in target direction * 1000000 - deviation from same row/column * 1000
                    if target_direction == 'UP' and grid_y >= player_visual_y + 2:
                        # Prefer same X (same column)
                        distance = grid_y - player_visual_y
                        deviation = abs(x_idx - player_grid_x)
                        score = (distance * 1000000) - (deviation * 1000)
                        candidates.append((score, (x_idx, y_idx)))
                    elif target_direction == 'DOWN' and grid_y <= player_visual_y - 2:
                        # Prefer same X (same column)
                        distance = player_visual_y - grid_y
                        deviation = abs(x_idx - player_grid_x)
                        score = (distance * 1000000) - (deviation * 1000)
                        candidates.append((score, (x_idx, y_idx)))
                    elif target_direction == 'LEFT' and x_idx <= player_grid_x - 2:
                        # Prefer same Y (same row)
                        distance = player_grid_x - x_idx
                        deviation = abs(grid_y - player_visual_y)
                        score = (distance * 1000000) - (deviation * 1000)
                        candidates.append((score, (x_idx, y_idx)))
                    elif target_direction == 'RIGHT' and x_idx >= player_grid_x + 2:
                        # Prefer same Y (same row)
                        distance = x_idx - player_grid_x
                        deviation = abs(grid_y - player_visual_y)
                        score = (distance * 1000000) - (deviation * 1000)
                        candidates.append((score, (x_idx, y_idx)))
        
        # Sort by score (best first)
        candidates.sort(reverse=True, key=lambda x: x[0])
        
        print(f"[PHASE 6 PATHFINDING] Direction: {target_direction}, Player at visual ({player_grid_x}, {player_visual_y})")
        print(f"[PHASE 6 PATHFINDING] Found {len(candidates)} candidates")
        if len(candidates) > 0:
            print(f"[PHASE 6 PATHFINDING] Top 3 candidates (score, (x, y_idx)):")
            for i, (score, pos) in enumerate(candidates[:3]):
                # Convert to visual coordinates for clarity
                visual_y = grid_height - 1 - pos[1]
                print(f"  #{i+1}: score={score}, grid pos=({pos[0]}, {visual_y})")
        
        # Try to path to each candidate until we find one that works
        for i, (score, goal_pos) in enumerate(candidates[:20]):  # Try up to 20 best candidates
            path = astar_pathfind(grid, (player_grid_x, player_y_idx), goal_pos, location_name)
            if path and len(path) > 0:
                print(f"[PHASE 6 PATHFINDING] ✓ Found path to candidate #{i+1}: {path}")
                return path
        
        print(f"[PHASE 6 PATHFINDING] ✗ No path found for direction {target_direction}")
        return []
        
    except Exception as e:
        import traceback
        print(f"[PHASE 6 PATHFINDING ERROR] {e}")
        traceback.print_exc()
        return []


def _path_with_directional_priority(state_data, location_name: str, priority_order: List[str]) -> str:
    """
    Try to path in the given priority order.
    Priority order: list of directions like ['EAST', 'NORTH', 'WEST', 'SOUTH']
    Returns suggested action string.
    """
    print(f"[PHASE 6 DIRECTIONAL] Priority order: {priority_order}")
    
    direction_map = {
        'NORTH': 'UP',
        'SOUTH': 'DOWN',
        'EAST': 'RIGHT',
        'WEST': 'LEFT'
    }
    
    for direction in priority_order:
        target_dir = direction_map.get(direction, 'UP')
        print(f"[PHASE 6 DIRECTIONAL] Trying {direction} (target_dir={target_dir})")
        path_seq = _get_full_path_to_direction(state_data, target_dir, location_name)
        print(f"[PHASE 6 DIRECTIONAL] {direction} path result: {path_seq if path_seq else 'None/Empty'}")
        if path_seq and len(path_seq) > 0:
            print(f"[PHASE 6 DIRECTIONAL] ✓ Using {direction} path: {path_seq}")
            path_seq.append('A')
            return f"\nSuggested action: {', '.join(path_seq)}"
    
    # Fallback
    print("[PHASE 6 DIRECTIONAL] ⚠️ All directions failed, using fallback")
    return "\nSuggested action: RIGHT, A"


def _find_door_and_path(state_data, location_name: str, door_filter: str = 'any', 
                       append_sequence: Optional[List[str]] = None) -> str:
    """
    Find a door on the map and path to it, optionally appending a sequence.
    
    door_filter: 'any', 'northeast', 'north', 'south', etc.
    append_sequence: Additional actions to append after reaching door (e.g., ['UP', 'UP', 'A', 'A'])
    """
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
            return ""
        
        # Generate grid
        grid = format_map_grid(raw_tiles, "South", npcs, player_coords, location_name=location_name)
        
        if not grid:
            return ""
        
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
            return ""
        
        # Find all doors
        door_positions = []
        for y_idx, row in enumerate(grid):
            for x_idx, symbol in enumerate(row):
                if symbol == 'D':
                    door_positions.append((x_idx, y_idx))
        
        if not door_positions:
            print("[PHASE 6] No doors found")
            return ""
        
        # Filter doors based on criteria
        if door_filter == 'northeast':
            # Most north, then most east
            target_door = max(door_positions, key=lambda pos: (pos[1], pos[0]))
        elif door_filter == 'north':
            # Most north (highest Y)
            target_door = max(door_positions, key=lambda pos: pos[1])
        elif door_filter == 'south':
            # Most south (lowest Y)
            target_door = min(door_positions, key=lambda pos: pos[1])
        elif door_filter == 'east':
            # Most east (highest X)
            target_door = max(door_positions, key=lambda pos: pos[0])
        else:
            # Default: closest door
            target_door = min(door_positions, key=lambda pos: abs(pos[0] - player_grid_x) + abs(pos[1] - player_grid_y))
        
        print(f"[PHASE 6] Found door at {target_door} (filter: {door_filter})")
        
        # Path to door
        player_y_idx = grid_height - 1 - player_grid_y
        path = astar_pathfind(grid, (player_grid_x, player_y_idx), target_door, location_name)
        
        if not path:
            return ""
        
        # Append additional sequence if provided
        if append_sequence:
            path.extend(append_sequence)
        
        path.append('A')
        return f"\nSuggested action: {', '.join(path)}"
        
    except Exception as e:
        import traceback
        print(f"[PHASE 6 DOOR PATHFINDING ERROR] {e}")
        traceback.print_exc()
        return ""


def _get_battle_action() -> str:
    """Return randomized battle sequence (33/33/33 split)."""
    import random
    rand = random.random()
    if rand < 0.33:
        return "\nSuggested action: UP, LEFT, A, B, LEFT, LEFT, LEFT, LEFT, LEFT, LEFT, A, RIGHT, UP, RIGHT, A, B, B"
    elif rand < 0.66:
        return "\nSuggested action: UP, LEFT, A, B, LEFT, LEFT, LEFT, LEFT, LEFT, LEFT, A, LEFT, DOWN, DOWN, A, B, B"
    else:
        return "\nSuggested action: UP, LEFT, A, B, LEFT, LEFT, LEFT, LEFT, LEFT, LEFT, A, LEFT, DOWN, DOWN, RIGHT, RIGHT, A, B, B"


# ============================================================================
# LOCATION-BASED NAVIGATION LOGIC
# ============================================================================

def _handle_route_104_north(state_data, objectives, location_name: str) -> Tuple[str, str]:
    """
    Route 104 North navigation.
    Priority: EAST -> NORTH -> WEST (heading to Rustboro City)
    """
    print("[PHASE 6] _handle_route_104_north called")
    
    prompt = """🎮 PHASE 6: Road to Rustboro City

📍 ROUTE 104 NORTH
- Follow the suggested action
- CHAIN THE ENTIRE ACTION SEQUENCE"""
    
    action = _path_with_directional_priority(state_data, location_name, ['EAST', 'NORTH', 'WEST'])
    print(f"[PHASE 6] Route 104 North final action: {action}")
    return prompt, action


def _handle_rustboro_low_hp(state_data, objectives, location_name: str) -> Tuple[str, str]:
    """
    Rustboro City with low HP - need to heal at Pokemon Center.
    Path: NORTH 20 tiles -> Enter northeast door (Pokemon Center) -> Heal
    """
    prompt = """🎮 PHASE 6: Rustboro City

📍 RUSTBORO CITY - LOW HP
- Follow the suggested action
- CHAIN THE ENTIRE ACTION SEQUENCE"""
    
    # Path NORTH, then to northeast door, then healing sequence
    action = _find_door_and_path(
        state_data, 
        location_name, 
        door_filter='northeast',
        append_sequence=['UP', 'UP', 'UP', 'UP', 'A', 'A', 'A', 'A', 'A', 'A', 'A']
    )
    
    if not action:
        # Fallback: just go north
        action = _path_with_directional_priority(state_data, location_name, ['NORTH'])
    
    return prompt, action


def _handle_rustboro_pokemon_center(state_data, objectives, location_name: str) -> Tuple[str, str]:
    """
    Inside Pokemon Center after healing - exit.
    Press B 5 times to clear dialogue, then go DOWN 5 tiles.
    """
    prompt = """🎮 PHASE 6: Rustboro City

📍 POKEMON CENTER
- Follow the suggested action
- CHAIN THE ENTIRE ACTION SEQUENCE"""
    
    action = "\nSuggested action: B, B, B, B, B, DOWN, DOWN, DOWN, DOWN, DOWN, A"
    return prompt, action


def _handle_rustboro_full_hp(state_data, objectives, location_name: str) -> Tuple[str, str]:
    """
    Rustboro City with full HP - head to gym.
    Go EAST ~6 tiles, then enter the nearest door (gym).
    """
    prompt = """🎮 PHASE 6: Rustboro City

📍 RUSTBORO CITY - FULL HP
- Follow the suggested action
- CHAIN THE ENTIRE ACTION SEQUENCE"""
    
    # Find door after going east
    action = _find_door_and_path(
        state_data,
        location_name,
        door_filter='east',
        append_sequence=['UP', 'UP', 'UP', 'UP', 'A', 'A', 'A', 'A', 'A', 'A', 'A']
    )
    
    if not action:
        # Fallback: just go east
        action = _path_with_directional_priority(state_data, location_name, ['EAST'])
    
    return prompt, action


def _handle_rustboro_gym_before_badge(state_data, objectives, location_name: str) -> Tuple[str, str]:
    """
    Inside Rustboro Gym, before getting the badge.
    Path UP CENTER while spamming A (invisible NPCs).
    """
    prompt = """🎮 PHASE 6: Rustboro Gym

📍 RUSTBORO GYM
- Follow the suggested action
- CHAIN THE ENTIRE ACTION SEQUENCE"""
    
    # Path UP (centered) with A spam
    path_seq = _get_full_path_to_direction(state_data, 'UP', location_name)
    if path_seq and len(path_seq) > 0:
        # Add extra A's for interactions
        path_seq.extend(['A'] * 10)
        action = f"\nSuggested action: {', '.join(path_seq)}"
    else:
        action = "\nSuggested action: UP, A, A, A, A, A, A, A, A, A, A"
    
    return prompt, action


def _handle_rustboro_gym_after_badge(state_data, objectives, location_name: str) -> Tuple[str, str]:
    """
    Inside Rustboro Gym, after getting the badge.
    Path SOUTH to the door, add extra DOWN to exit.
    """
    prompt = """🎮 PHASE 6: Rustboro Gym

📍 RUSTBORO GYM - BADGE OBTAINED
- Follow the suggested action
- CHAIN THE ENTIRE ACTION SEQUENCE"""
    
    # Path to door (south), then add DOWN to exit
    action = _find_door_and_path(
        state_data,
        location_name,
        door_filter='south',
        append_sequence=['DOWN']
    )
    
    if not action:
        action = "\nSuggested action: DOWN, DOWN, DOWN, DOWN, DOWN, A"
    
    return prompt, action


# ============================================================================
# LEGACY LOCATIONS (from old Phase 6)
# ============================================================================

def _handle_route_102(state_data, objectives, location_name: str) -> Tuple[str, str]:
    """Route 102 - Wally's tutorial."""
    prompt = """🎮 PHASE 6: Road to Rustboro City

📍 ROUTE 102
- Follow the suggested action
- CHAIN THE ENTIRE ACTION SEQUENCE"""
    
    action = "\nSuggested action: A, A, A, A, A, A, A, A, A, A, A, A, A, A, A, A, A, A, A, A"
    return prompt, action


def _handle_gym(state_data, objectives, location_name: str) -> Tuple[str, str]:
    """Generic gym handler (Petalburg)."""
    prompt = """🎮 PHASE 6: Road to Rustboro City

📍 IN GYM
- Follow the suggested action
- CHAIN THE ENTIRE ACTION SEQUENCE"""
    
    action = "\nSuggested action: A, A, A, A, A, A, A, A, A, A, A, A, A, A, A, A, RIGHT, DOWN, A"
    return prompt, action


def _handle_petalburg(state_data, objectives, location_name: str) -> Tuple[str, str]:
    """Petalburg City - exit west."""
    prompt = """🎮 PHASE 6: Road to Rustboro City

📍 PETALBURG CITY
- Follow the suggested action
- CHAIN THE ENTIRE ACTION SEQUENCE"""
    
    action = _path_with_directional_priority(state_data, location_name, ['WEST'])
    return prompt, action


def _handle_petalburg_woods(state_data, objectives, location_name: str) -> Tuple[str, str]:
    """
    Petalburg Woods - navigate the maze.
    Priority: NORTH > EAST > WEST > SOUTH
    Horizontal movements are multiplied by 13x to escape local minimums.
    """
    prompt = """🎮 PHASE 6: Road to Rustboro City

📍 PETALBURG WOODS
- Follow the suggested action
- CHAIN THE ENTIRE ACTION SEQUENCE"""
    
    # Check for 'S' tile north (exit)
    map_info = state_data.get('map', {})
    raw_tiles = map_info.get('tiles', [])
    player_data = state_data.get('player', {})
    player_position = player_data.get('position', {})
    player_y = int(player_position.get('y', 0))
    
    s_tile_north = False
    try:
        for tile in raw_tiles:
            if isinstance(tile, (list, tuple)) and len(tile) >= 3:
                tile_x, tile_y, tile_type = tile[0], tile[1], tile[2]
                if tile_type == 'S' and tile_y > player_y:
                    s_tile_north = True
                    break
            elif isinstance(tile, dict):
                if tile.get('type') == 'S' and tile.get('y', 0) > player_y:
                    s_tile_north = True
                    break
    except:
        pass
    
    if s_tile_north:
        return prompt, "\nSuggested action: UP, UP, UP, UP, A"
    
    # Try NORTH
    north_seq = _get_full_path_to_direction(state_data, 'UP', location_name)
    if north_seq and len(north_seq) > 0:
        north_seq.append('A')
        return prompt, f"\nSuggested action: {', '.join(north_seq)}"
    
    # Try EAST with 13x multiplier
    east_seq = _get_full_path_to_direction(state_data, 'RIGHT', location_name)
    if east_seq and len(east_seq) > 0:
        right_count = east_seq.count('RIGHT')
        if right_count > 0:
            multiplied_seq = ['RIGHT'] * (right_count * 13)
            multiplied_seq.append('A')
            return prompt, f"\nSuggested action: {', '.join(multiplied_seq)}"
    
    # Try WEST with 13x multiplier
    west_seq = _get_full_path_to_direction(state_data, 'LEFT', location_name)
    if west_seq and len(west_seq) > 0:
        left_count = west_seq.count('LEFT')
        if left_count > 0:
            multiplied_seq = ['LEFT'] * (left_count * 13)
            multiplied_seq.append('A')
            return prompt, f"\nSuggested action: {', '.join(multiplied_seq)}"
    
    # Try SOUTH
    south_seq = _get_full_path_to_direction(state_data, 'DOWN', location_name)
    if south_seq and len(south_seq) > 0:
        south_seq.append('A')
        return prompt, f"\nSuggested action: {', '.join(south_seq)}"
    
    return prompt, "\nSuggested action: RIGHT, A"


def _handle_route_104_south(state_data, objectives, location_name: str) -> Tuple[str, str]:
    """
    Route 104 South (near Petalburg Woods entrance).
    If near stairs, go UP and RIGHT. Otherwise, look for stairs to enter woods.
    """
    from utils.map_formatter import format_map_grid
    from utils.state_formatter import astar_pathfind
    
    prompt = """🎮 PHASE 6: Road to Rustboro City

📍 ROUTE 104 SOUTH
- Follow the suggested action
- CHAIN THE ENTIRE ACTION SEQUENCE"""
    
    # Get player info
    player_data = state_data.get('player', {})
    player_position = player_data.get('position', {})
    player_coords = (int(player_position.get('x', 0)), int(player_position.get('y', 0)))
    
    # Get map data
    map_info = state_data.get('map', {})
    raw_tiles = map_info.get('tiles', [])
    npcs = map_info.get('npcs', [])
    
    # Generate grid
    grid = format_map_grid(raw_tiles, "South", npcs, player_coords, location_name=location_name)
    
    if not grid:
        return prompt, "\nSuggested action: UP, RIGHT, A"
    
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
        return prompt, "\nSuggested action: UP, RIGHT, A"
    
    # Find stairs tiles (S) - NOT doors (D)
    stairs_positions = []
    for y_idx, row in enumerate(grid):
        for x_idx, symbol in enumerate(row):
            if symbol == 'S':
                stairs_positions.append((x_idx, y_idx))
    
    if not stairs_positions:
        # No stairs, just go UP and RIGHT
        return prompt, "\nSuggested action: UP, UP, UP, RIGHT, RIGHT, RIGHT, A"
    
    # Filter out stairs near water or map edges
    valid_stairs = []
    for stairs_pos in stairs_positions:
        sx, sy = stairs_pos
        
        # Reject stairs in top 3 rows
        if sy <= 2:
            continue
        
        # Check if near water
        near_water = False
        for dy in range(-5, 6):
            for dx in range(-5, 6):
                check_x = sx + dx
                check_y = sy + dy
                if 0 <= check_y < len(grid) and 0 <= check_x < len(grid[check_y]):
                    if grid[check_y][check_x] == 'W':
                        near_water = True
                        break
            if near_water:
                break
        
        if not near_water:
            valid_stairs.append(stairs_pos)
    
    if not valid_stairs:
        return prompt, "\nSuggested action: UP, UP, UP, RIGHT, RIGHT, RIGHT, A"
    
    # Path to leftmost stairs
    leftmost_stairs = min(valid_stairs, key=lambda pos: pos[0])
    player_y_idx = grid_height - 1 - player_grid_y
    path = astar_pathfind(grid, (player_grid_x, player_y_idx), leftmost_stairs, location_name)
    
    if path and len(path) > 10:
        # Far from stairs - path to it
        path.extend(['UP'] * 8)
        path.append('A')
        return prompt, f"\nSuggested action: {', '.join(path)}"
    else:
        # Near stairs - go UP and RIGHT to avoid entering immediately
        return prompt, "\nSuggested action: UP, UP, UP, RIGHT, RIGHT, RIGHT, A"


# ============================================================================
# MAIN ROUTER
# ============================================================================

def _get_phase_6_navigation(state_data, objectives, location_name: str) -> Tuple[str, str]:
    """
    Main router for Phase 6 navigation.
    Returns (prompt, suggested_action) based on location and objectives.
    """
    loc_upper = location_name.upper() if location_name else ""
    
    # Check HP status
    hp_status = _get_pokemon_hp_status(state_data)
    
    # Check key objectives
    has_stone_badge = _is_objective_completed(objectives, 'FIRST_GYM_COMPLETE')
    entered_rustboro_gym = _is_objective_completed(objectives, 'RUSTBORO_GYM_ENTERED')
    
    print(f"[PHASE 6 ROUTER] Location: {location_name}, HP: {hp_status}, Badge: {has_stone_badge}, Gym: {entered_rustboro_gym}")
    
    # ========== RUSTBORO CITY ==========
    if "RUSTBORO" in loc_upper:
        # Inside Pokemon Center
        if "POKEMON CENTER" in loc_upper or "POKÉMON CENTER" in loc_upper:
            return _handle_rustboro_pokemon_center(state_data, objectives, location_name)
        
        # Inside Gym
        if "GYM" in loc_upper:
            if has_stone_badge:
                return _handle_rustboro_gym_after_badge(state_data, objectives, location_name)
            else:
                return _handle_rustboro_gym_before_badge(state_data, objectives, location_name)
        
        # In city - check HP
        if hp_status == 'low':
            return _handle_rustboro_low_hp(state_data, objectives, location_name)
        else:
            return _handle_rustboro_full_hp(state_data, objectives, location_name)
    
    # ========== ROUTE 104 ==========
    elif "ROUTE_104" in loc_upper or "ROUTE 104" in loc_upper:
        # Always use EAST → NORTH → WEST priority
        print("[PHASE 6 ROUTER] Detected Route 104, routing to _handle_route_104_north")
        return _handle_route_104_north(state_data, objectives, location_name)
    
    # ========== PETALBURG WOODS ==========
    elif "MAP" in loc_upper or "WOOD" in loc_upper or "PETALBURG" in location_name:
        return _handle_petalburg_woods(state_data, objectives, location_name)
    
    # ========== PETALBURG CITY ==========
    elif "PETALBURG" in loc_upper:
        if "GYM" in loc_upper:
            return _handle_gym(state_data, objectives, location_name)
        return _handle_petalburg(state_data, objectives, location_name)
    
    # ========== ROUTE 102 ==========
    elif "ROUTE_102" in loc_upper or "ROUTE 102" in loc_upper:
        return _handle_route_102(state_data, objectives, location_name)
    
    # ========== DEFAULT ==========
    else:
        prompt = """🎮 PHASE 6: Adventure Continues

- Follow the suggested action
- CHAIN THE ENTIRE SEQUENCE"""
        return prompt, ""


def get_phase_6_prompt(
    objectives=None,
    debug: bool = False,
    include_base_intro: bool = False,
    include_pathfinding_rules: bool = False,
    include_pathfinding_helper: bool = False,
    include_response_structure: bool = True,
    include_action_history: bool = False,
    include_location_history: bool = False,
    include_objectives: bool = False,
    include_movement_memory: bool = False,
    include_stuck_warning: bool = False,
    state_data=None,
    formatted_state='',
    **kwargs
) -> str:
    """
    Get the Phase 6 prompt template.
    Phase 6 is the FINAL PHASE - handles everything from Route 104 to end game.
    """
    # Get current location from formatted_state
    current_location = ''
    if formatted_state and "Current Location:" in formatted_state:
        for line in formatted_state.split('\n'):
            if line.strip().startswith("Current Location:"):
                current_location = line.split(":", 1)[1].strip()
                break
    
    # Check if in battle FIRST
    game_data = state_data.get('game', {}) if state_data else {}
    is_in_battle = game_data.get('is_in_battle', False) or game_data.get('in_battle', False)
    
    # Get battle action if in battle
    if is_in_battle:
        prompt = """🎮 PHASE 6: Adventure Continues

⚔️ BATTLE MODE
- Use your battle strategy
- CHAIN THE ENTIRE BATTLE SEQUENCE"""
        suggested_action = _get_battle_action()
    else:
        # Get location-based navigation
        prompt, suggested_action = _get_phase_6_navigation(state_data, objectives, current_location)
    
    print(f"[PHASE 6] Location: {current_location}, Battle: {is_in_battle}")
    print(f"[PHASE 6] Suggested action: {suggested_action}")
    
    return build_base_prompt(
        phase_intro=prompt,
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
        phase_intro_at_end=True,
        suggested_action_suffix=suggested_action,
        formatted_state=formatted_state,
        state_data=state_data,
        **kwargs
    )
