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
# PHASE 6 MEMORY - Track last map state to detect when stuck
# ============================================================================

_LAST_MAP_STATE = None
_STUCK_COUNTER = 0
_LAST_PRIORITY_USED = None

# Movement tracking for adaptive priorities
_MOVEMENT_HISTORY = []  # List of recent movements
_CURRENT_PHASE = 0  # Current navigation phase
_PHASE_MOVE_COUNT = 0  # Moves in current phase

def _get_map_state_hash(state_data):
    """Generate a simple hash of the current map state to detect if stuck."""
    try:
        map_info = state_data.get('map', {})
        player = state_data.get('player', {})
        position = player.get('position', {})
        
        # Create a simple string representation of position + nearby tiles
        pos_x = position.get('x', 0)
        pos_y = position.get('y', 0)
        location = map_info.get('location_name', '')
        
        return f"{location}_{pos_x}_{pos_y}"
    except:
        return None

def _is_stuck(state_data):
    """Check if we're stuck (same map state as last time)."""
    global _LAST_MAP_STATE, _STUCK_COUNTER
    
    current_state = _get_map_state_hash(state_data)
    if current_state == _LAST_MAP_STATE:
        _STUCK_COUNTER += 1
        print(f"[PHASE 6 STUCK] Stuck counter: {_STUCK_COUNTER}")
    else:
        _STUCK_COUNTER = 0
        _LAST_MAP_STATE = current_state
    
    # Check if stuck (same position for 1+ iterations) OR all directions blocked
    if _STUCK_COUNTER >= 1:
        print("[PHASE 6 STUCK] ⚠️ DETECTED: Same position multiple times")
        return True
    
    # Also check if player is completely surrounded (all 4 directions blocked)
    try:
        map_info = state_data.get('map', {})
        raw_tiles = map_info.get('tiles', [])
        if raw_tiles and len(raw_tiles) > 0:
            # Player is at center
            center = len(raw_tiles) // 2
            if center > 0 and center < len(raw_tiles) and len(raw_tiles[center]) > center:
                up = raw_tiles[center - 1][center] if center > 0 else None
                down = raw_tiles[center + 1][center] if center < len(raw_tiles) - 1 else None
                left = raw_tiles[center][center - 1] if center > 0 else None
                right = raw_tiles[center][center + 1] if center < len(raw_tiles[0]) - 1 else None
                
                # Check if all blocked
                blocked_count = 0
                for tile in [up, down, left, right]:
                    if tile and len(tile) >= 3:
                        collision = tile[2]
                        if collision != 0:  # Blocked
                            blocked_count += 1
                
                if blocked_count >= 3:
                    print(f"[PHASE 6 STUCK] ⚠️ DETECTED: {blocked_count}/4 directions blocked")
                    return True
    except Exception as e:
        print(f"[PHASE 6 STUCK] Error checking surroundings: {e}")
    
    return False

def _reset_stuck():
    """Reset stuck detection after taking corrective action."""
    global _STUCK_COUNTER
    _STUCK_COUNTER = 0


def _track_movement(action_string: str):
    """Track movements from an action string to help with adaptive priorities."""
    global _MOVEMENT_HISTORY, _PHASE_MOVE_COUNT
    
    if not action_string:
        return
    
    # Extract movement commands from action string
    movements = []
    for action in action_string.split(','):
        action = action.strip().upper()
        if action in ['UP', 'DOWN', 'LEFT', 'RIGHT']:
            movements.append(action)
    
    # Add to history (keep last 100 moves)
    _MOVEMENT_HISTORY.extend(movements)
    _MOVEMENT_HISTORY = _MOVEMENT_HISTORY[-100:]
    _PHASE_MOVE_COUNT += len(movements)
    
    print(f"[PHASE 6 MOVEMENT] Tracked {len(movements)} moves, phase count: {_PHASE_MOVE_COUNT}")


def _get_dominant_direction():
    """Get the direction we've been moving most recently (last 10 moves)."""
    if len(_MOVEMENT_HISTORY) < 5:
        return None
    
    recent = _MOVEMENT_HISTORY[-10:]
    counts = {}
    for move in recent:
        counts[move] = counts.get(move, 0) + 1
    
    if not counts:
        return None
    
    dominant = max(counts.items(), key=lambda x: x[1])
    return dominant[0] if dominant[1] >= 3 else None


def _advance_phase():
    """Advance to next navigation phase and reset counter."""
    global _CURRENT_PHASE, _PHASE_MOVE_COUNT
    _CURRENT_PHASE += 1
    _PHASE_MOVE_COUNT = 0
    print(f"[PHASE 6 ADAPTIVE] Advanced to phase {_CURRENT_PHASE}")


def _reset_phases():
    """Reset phases when changing contexts (e.g., entering new location)."""
    global _CURRENT_PHASE, _PHASE_MOVE_COUNT, _MOVEMENT_HISTORY
    _CURRENT_PHASE = 0
    _PHASE_MOVE_COUNT = 0
    _MOVEMENT_HISTORY = []
    print("[PHASE 6 ADAPTIVE] Reset all phases")


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

# Direction definitions for generalized pathfinding
DIRECTION_FILTERS = {
    'NORTH': lambda px, py, tx, ty: ty >= py + 2,
    'SOUTH': lambda px, py, tx, ty: ty <= py - 2,
    'EAST': lambda px, py, tx, ty: tx >= px + 2,
    'WEST': lambda px, py, tx, ty: tx <= px - 2,
    'NORTHEAST': lambda px, py, tx, ty: tx > px and (ty >= py + 2 or tx >= px + 2),
    'NORTHWEST': lambda px, py, tx, ty: tx < px and (ty >= py + 2 or tx <= px - 2),
    'SOUTHEAST': lambda px, py, tx, ty: tx > px and (ty <= py - 2 or tx >= px + 2),
    'SOUTHWEST': lambda px, py, tx, ty: tx < px and (ty <= py - 2 or tx <= px - 2),
}

DIRECTION_SCORING = {
    # Cardinal directions: prefer staying on same row/column
    'NORTH': lambda px, py, tx, ty: ((ty - py) * 1000000) - (abs(tx - px) * 1000),
    'SOUTH': lambda px, py, tx, ty: ((py - ty) * 1000000) - (abs(tx - px) * 1000),
    'EAST': lambda px, py, tx, ty: ((tx - px) * 1000000) - (abs(ty - py) * 1000),
    'WEST': lambda px, py, tx, ty: ((px - tx) * 1000000) - (abs(ty - py) * 1000),
    # Diagonal directions: prioritize primary direction
    'NORTHEAST': lambda px, py, tx, ty: ((ty - py) * 100000) + ((tx - px) * 1000),
    'NORTHWEST': lambda px, py, tx, ty: ((ty - py) * 100000) + ((px - tx) * 1000),
    'SOUTHEAST': lambda px, py, tx, ty: ((py - ty) * 100000) + ((tx - px) * 1000),
    'SOUTHWEST': lambda px, py, tx, ty: ((py - ty) * 100000) + ((px - tx) * 1000),
}


def _is_dead_end(grid, pos, direction: str) -> bool:
    """
    Check if a position is a dead end (has very limited walkable neighbors).
    
    Args:
        grid: 2D grid
        pos: (x, y) position to check
        direction: The direction we approached from (to allow backward movement)
    
    Returns:
        True if position is a dead end (< 2 walkable neighbors in forward directions)
    """
    if not grid or not pos:
        return False
    
    height = len(grid)
    width = len(grid[0]) if grid else 0
    x, y = pos
    
    if not (0 <= x < width and 0 <= y < height):
        return False
    
    # Count walkable neighbors in forward directions
    # (not counting the direction we came from)
    forward_walkable = 0
    
    # Define which directions are "forward" based on our approach direction
    check_directions = []
    if direction in ['NORTH', 'NORTHEAST', 'NORTHWEST']:
        # Going north - check north, east, west (not south)
        check_directions = [(0, -1), (1, 0), (-1, 0)]
    elif direction in ['SOUTH', 'SOUTHEAST', 'SOUTHWEST']:
        # Going south - check south, east, west (not north)
        check_directions = [(0, 1), (1, 0), (-1, 0)]
    elif direction == 'EAST':
        # Going east - check east, north, south (not west)
        check_directions = [(1, 0), (0, -1), (0, 1)]
    elif direction == 'WEST':
        # Going west - check west, north, south (not east)
        check_directions = [(-1, 0), (0, -1), (0, 1)]
    else:
        # Default: check all directions
        check_directions = [(0, -1), (0, 1), (-1, 0), (1, 0)]
    
    for dx, dy in check_directions:
        nx, ny = x + dx, y + dy
        if 0 <= nx < width and 0 <= ny < height:
            tile = grid[ny][nx]
            # Walkable tiles
            if tile not in ['#', 'W', ' ', None]:
                forward_walkable += 1
    
    # Dead end if < 2 forward walkable neighbors
    is_dead_end = forward_walkable < 2
    
    if is_dead_end:
        print(f"[PHASE 6 DEADEND] Position ({x}, {y}) is a dead end (only {forward_walkable} forward paths)")
    
    return is_dead_end


def _path_to_direction(state_data, direction: str, location_name: str = '') -> List[str]:
    """
    Generic pathfinding for a single direction.
    Supports: NORTH, SOUTH, EAST, WEST, NORTHEAST, NORTHWEST, SOUTHEAST, SOUTHWEST
    Returns empty list if direction is blocked.
    """
    if direction not in DIRECTION_FILTERS:
        print(f"[PHASE 6 PATHFINDING] Invalid direction: {direction}")
        return []
    
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
        player_y_idx = None
        player_visual_y = None
        for y_idx, row in enumerate(grid):
            for x_idx, symbol in enumerate(row):
                if symbol == 'P':
                    player_grid_x = x_idx
                    player_y_idx = y_idx
                    player_visual_y = grid_height - 1 - y_idx
                    break
            if player_grid_x is not None:
                break
        
        if player_grid_x is None:
            return []
        
        # Find walkable tiles matching direction filter
        walkable_tiles = ['.', '~', 'S']
        candidates = []
        direction_filter = DIRECTION_FILTERS[direction]
        direction_score = DIRECTION_SCORING[direction]
        
        for y_idx, row in enumerate(grid):
            for x_idx, symbol in enumerate(row):
                if symbol in walkable_tiles:
                    grid_y = grid_height - 1 - y_idx
                    
                    # Apply direction filter
                    if direction_filter(player_grid_x, player_visual_y, x_idx, grid_y):
                        score = direction_score(player_grid_x, player_visual_y, x_idx, grid_y)
                        candidates.append((score, (x_idx, y_idx)))
        
        candidates.sort(reverse=True, key=lambda x: x[0])
        
        if len(candidates) == 0:
            return []
        
        # Try to path to candidates, checking for dead ends
        for i, (score, goal_pos) in enumerate(candidates[:20]):
            path = astar_pathfind(grid, (player_grid_x, player_y_idx), goal_pos, location_name)
            if path and len(path) > 0:
                # Check if destination is a dead end
                if _is_dead_end(grid, goal_pos, direction):
                    print(f"[PHASE 6 PATHFINDING] ⚠️ Candidate #{i+1} is a dead end, skipping")
                    continue
                return path
        
        return []
        
    except Exception as e:
        import traceback
        print(f"[PHASE 6 PATHFINDING ERROR] {e}")
        traceback.print_exc()
        return []


def _parse_priority_with_coefficients(priority_str: str) -> Tuple[str, Dict[str, float]]:
    """
    Parse priority string with optional coefficients.
    
    Examples:
        "NORTHEAST" -> ("NORTHEAST", {})
        "N2E3" -> ("NORTHEAST", {"NORTH": 2.0, "EAST": 3.0})
        "N1.5W7" -> ("NORTHWEST", {"NORTH": 1.5, "WEST": 7.0})
    
    Returns:
        (direction, coefficients_dict)
    """
    import re
    
    # Simple direction (no coefficients)
    if priority_str in DIRECTION_FILTERS:
        return priority_str, {}
    
    # Parse coefficients like N2E3, N1.5W7, etc.
    direction_map = {
        'N': 'NORTH',
        'S': 'SOUTH',
        'E': 'EAST',
        'W': 'WEST'
    }
    
    # Extract direction letters and their coefficients
    # Pattern: N2E3 -> [('N', '2'), ('E', '3')]
    matches = re.findall(r'([NSEW])(\d+\.?\d*)', priority_str.upper())
    
    if not matches:
        return priority_str, {}
    
    # Build direction name and coefficients
    direction_parts = []
    coefficients = {}
    
    for letter, coeff in matches:
        full_dir = direction_map[letter]
        direction_parts.append(letter)
        coefficients[full_dir] = float(coeff)
    
    # Determine combined direction
    direction_str = ''.join(direction_parts)
    direction_name = {
        'N': 'NORTH',
        'S': 'SOUTH',
        'E': 'EAST',
        'W': 'WEST',
        'NE': 'NORTHEAST',
        'NW': 'NORTHWEST',
        'SE': 'SOUTHEAST',
        'SW': 'SOUTHWEST',
    }.get(direction_str, priority_str)
    
    return direction_name, coefficients


def _apply_movement_coefficients(path: List[str], coefficients: Dict[str, float]) -> List[str]:
    """
    Apply coefficients to ADD extra movements at the end of the path.
    
    Example:
        path = ['UP', 'UP', 'RIGHT', 'RIGHT', 'RIGHT']
        coefficients = {'NORTH': 1.5, 'EAST': 2.0}
        
        Original: 2 UPs, 3 RIGHTs
        Extra: ceil(2 * 0.5) = 1 UP, ceil(3 * 1.0) = 3 RIGHTs
        Result: ['UP', 'UP', 'RIGHT', 'RIGHT', 'RIGHT', 'UP', 'RIGHT', 'RIGHT', 'RIGHT']
    """
    if not coefficients:
        return path
    
    import math
    
    direction_to_movement = {
        'NORTH': 'UP',
        'SOUTH': 'DOWN',
        'EAST': 'RIGHT',
        'WEST': 'LEFT'
    }
    
    # Count movements in each direction
    movement_counts = {}
    for move in path:
        movement_counts[move] = movement_counts.get(move, 0) + 1
    
    print(f"[PHASE 6 PATHFINDING] Original path counts: {movement_counts}")
    print(f"[PHASE 6 PATHFINDING] Applying coefficients: {coefficients}")
    
    # Calculate extra movements to add
    extra_movements = []
    for direction, coeff in coefficients.items():
        movement = direction_to_movement.get(direction)
        if movement and movement in movement_counts:
            original_count = movement_counts[movement]
            # Extra movements = original * (coeff - 1.0), rounded up
            extra_count = math.ceil(original_count * (coeff - 1.0))
            if extra_count > 0:
                extra_movements.extend([movement] * extra_count)
                print(f"[PHASE 6 PATHFINDING] {movement}: {original_count} + {extra_count} extra ({coeff}x)")
    
    # Return original path + extra movements at the end
    result = path + extra_movements
    print(f"[PHASE 6 PATHFINDING] Final path length: {len(path)} -> {len(result)}")
    return result


def _get_zigzag_pattern(direction: str, length: int = 8) -> List[str]:
    """
    Get a zigzag pattern to avoid getting stuck when going in diagonal directions.
    
    Patterns designed to always progress in the target direction without backtracking:
    - NORTHEAST: UP, UP, RIGHT, DOWN (net: UP, RIGHT, progress northeast)
    - NORTHWEST: UP, UP, LEFT, DOWN (net: UP, LEFT, progress northwest)  
    - SOUTHEAST: DOWN, DOWN, RIGHT, UP (net: DOWN, RIGHT, progress southeast)
    - SOUTHWEST: DOWN, DOWN, LEFT, UP (net: DOWN, LEFT, progress southwest)
    """
    patterns = {
        'NORTHEAST': ['UP', 'UP', 'RIGHT', 'DOWN'],
        'NORTHWEST': ['UP', 'UP', 'LEFT', 'DOWN'],
        'SOUTHEAST': ['DOWN', 'DOWN', 'RIGHT', 'UP'],
        'SOUTHWEST': ['DOWN', 'DOWN', 'LEFT', 'UP'],
        # For cardinal directions, just repeat the movement
        'NORTH': ['UP', 'UP', 'UP', 'UP'],
        'SOUTH': ['DOWN', 'DOWN', 'DOWN', 'DOWN'],
        'EAST': ['RIGHT', 'RIGHT', 'RIGHT', 'RIGHT'],
        'WEST': ['LEFT', 'LEFT', 'LEFT', 'LEFT'],
    }
    
    base_pattern = patterns.get(direction, ['UP'])
    # Repeat pattern to reach desired length
    result = []
    while len(result) < length:
        result.extend(base_pattern)
    
    return result[:length]


def _path_with_priority_list(state_data, priority_list: List[str], location_name: str = '') -> str:
    """
    Generalized pathfinding with priority list and optional coefficients.
    
    Tries each direction/target in order until one succeeds.
    Detects if stuck and applies corrective actions (B presses + secondary priority).
    
    Supported directions:
    - Cardinal: NORTH, SOUTH, EAST, WEST
    - Diagonal: NORTHEAST, NORTHWEST, SOUTHEAST, SOUTHWEST
    - With coefficients: N2E3 (2x north, 3x east), N1.5W7 (1.5x north, 7x west)
    - Special: DOOR_NORTH, DOOR_NORTHEAST, etc. (future)
    
    Examples:
        _path_with_priority_list(state_data, ['NORTHEAST', 'WEST'], location_name)
        _path_with_priority_list(state_data, ['N2E3', 'N2W7'], location_name)
    """
    global _LAST_PRIORITY_USED
    
    print(f"[PHASE 6 PATHFINDING] Priority list: {priority_list}")
    
    # Check if stuck
    stuck = _is_stuck(state_data)
    if stuck:
        print("[PHASE 6 PATHFINDING] ⚠️ STUCK DETECTED! Using zigzag recovery")
        _reset_stuck()
        
        # Use zigzag pattern in primary direction to escape
        primary = priority_list[0] if priority_list else 'NORTH'
        direction, _ = _parse_priority_with_coefficients(primary)
        
        # Longer zigzag for stuck situations (16 moves)
        zigzag = _get_zigzag_pattern(direction, length=16)
        action = f"B, B, B, {', '.join(zigzag)}, A"
        print(f"[PHASE 6 PATHFINDING] Zigzag recovery ({direction}): {action}")
        _LAST_PRIORITY_USED = f"STUCK_ZIGZAG_{direction}"
        return f"\nSuggested action (STUCK - zigzag {direction}): {action}"
    
    # Try each priority in order
    for i, priority in enumerate(priority_list):
        # Handle special targets (doors, etc.)
        if priority.startswith('DOOR_'):
            # TODO: Implement door pathfinding
            continue
        
        # Parse direction and coefficients
        direction, coefficients = _parse_priority_with_coefficients(priority)
        
        # Handle directional pathfinding
        print(f"[PHASE 6 PATHFINDING] Trying {priority} -> direction={direction}, coefficients={coefficients}")
        path = _path_to_direction(state_data, direction, location_name)
        
        if path and len(path) > 0:
            print(f"[PHASE 6 PATHFINDING] ✓ Found base path: {path}")
            
            # Apply coefficients to amplify movements
            if coefficients:
                path = _apply_movement_coefficients(path, coefficients)
                print(f"[PHASE 6 PATHFINDING] ✓ Amplified path: {path}")
            
            path.append('A')
            action = ', '.join(path)
            _LAST_PRIORITY_USED = priority
            return f"\nSuggested action (priority: {priority}): {action}"
        else:
            print(f"[PHASE 6 PATHFINDING] ✗ {priority} blocked")
    
    # All priorities failed - use zigzag fallback for primary direction
    print("[PHASE 6 PATHFINDING] ⚠️ All priorities failed, using zigzag fallback")
    primary = priority_list[0] if priority_list else 'NORTH'
    direction, _ = _parse_priority_with_coefficients(primary)
    zigzag = _get_zigzag_pattern(direction, length=8)
    zigzag.append('A')
    action = ', '.join(zigzag)
    _LAST_PRIORITY_USED = f"ZIGZAG_FALLBACK_{primary}"
    return f"\nSuggested action (ZIGZAG fallback - {primary}): {action}"

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


def _get_route_104_northeast_path(state_data, location_name: str = '') -> str:
    """
    Route 104 specific pathfinding: Target NORTHEAST corner.
    Prioritizes NORTH over EAST in scoring.
    If northeast fails, try FAR WEST as backup.
    """
    print("[PHASE 6] Route 104 custom pathfinding: targeting NORTHEAST")
    
    if not state_data:
        return ""
    
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
        grid_width = len(grid[0]) if grid else 0
        
        # Find player on grid
        player_grid_x = None
        player_y_idx = None
        player_visual_y = None
        for y_idx, row in enumerate(grid):
            for x_idx, symbol in enumerate(row):
                if symbol == 'P':
                    player_grid_x = x_idx
                    player_y_idx = y_idx
                    player_visual_y = grid_height - 1 - y_idx
                    break
            if player_grid_x is not None:
                break
        
        if player_grid_x is None:
            return ""
        
        # Find walkable tiles in NORTHEAST direction
        # MUST be EAST of player (not west!)
        # Score: prioritize NORTH first, then EAST
        # Score = (Y * 100000) + (X * 1000)
        walkable_tiles = ['.', '~', 'S']
        candidates = []
        
        for y_idx, row in enumerate(grid):
            for x_idx, symbol in enumerate(row):
                if symbol in walkable_tiles:
                    grid_y = grid_height - 1 - y_idx
                    
                    # Must be EAST of player (x_idx > player_grid_x)
                    # And either north OR east by at least 2 tiles
                    if x_idx > player_grid_x and (grid_y >= player_visual_y + 2 or x_idx >= player_grid_x + 2):
                        # Score: prioritize NORTH (Y) over EAST (X)
                        north_score = (grid_y - player_visual_y) * 100000
                        east_score = (x_idx - player_grid_x) * 1000
                        score = north_score + east_score
                        candidates.append((score, (x_idx, y_idx)))
        
        candidates.sort(reverse=True, key=lambda x: x[0])
        
        print(f"[PHASE 6 ROUTE 104] Found {len(candidates)} northeast candidates")
        if len(candidates) > 0:
            print(f"[PHASE 6 ROUTE 104] Top 3 candidates:")
            for i, (score, pos) in enumerate(candidates[:3]):
                visual_y = grid_height - 1 - pos[1]
                print(f"  #{i+1}: score={score}, pos=({pos[0]}, {visual_y})")
        
        # Try to path to candidates
        for i, (score, goal_pos) in enumerate(candidates[:20]):
            path = astar_pathfind(grid, (player_grid_x, player_y_idx), goal_pos, location_name)
            if path and len(path) > 0:
                print(f"[PHASE 6 ROUTE 104] ✓ Found northeast path: {path}")
                path.append('A')
                return f"\nSuggested action: {', '.join(path)}"
        
        # Backup: try FAR WEST
        print("[PHASE 6 ROUTE 104] Northeast blocked, trying FAR WEST")
        west_path = _get_full_path_to_direction(state_data, 'LEFT', location_name)
        if west_path and len(west_path) > 0:
            west_path.append('A')
            return f"\nSuggested action: {', '.join(west_path)}"
        
        # Ultimate fallback
        return "\nSuggested action: UP, A"
        
    except Exception as e:
        import traceback
        print(f"[PHASE 6 ROUTE 104 PATHFINDING ERROR] {e}")
        traceback.print_exc()
        return "\nSuggested action: UP, A"


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
    Route 104 North navigation with adaptive phases.
    
    Each phase targets a direction in the CURRENT window:
    - Phase 0: NORTHEAST (1 screen, ~10 moves)
    - Phase 1: EAST (2 screens, ~20 moves)
    - Phase 2: NORTH (1 screen, ~10 moves)
    - Phase 3: WEST (1 screen, ~10 moves)
    - Phase 4: NORTH (3 screens, ~30 moves)
    """
    global _CURRENT_PHASE, _PHASE_MOVE_COUNT
    
    print(f"[PHASE 6] _handle_route_104_north called (Phase {_CURRENT_PHASE}, moves: {_PHASE_MOVE_COUNT})")
    
    # Each phase = one target direction within current window
    phases = [
        {'name': 'Northeast 1 screen', 'threshold': 10, 'targets': ['NORTHEAST', 'NORTH', 'EAST']},
        {'name': 'East 2 screens', 'threshold': 20, 'targets': ['EAST', 'NORTHEAST', 'SOUTHEAST']},
        {'name': 'North 1 screen', 'threshold': 10, 'targets': ['NORTH', 'NORTHEAST', 'NORTHWEST']},
        {'name': 'West 1 screen', 'threshold': 10, 'targets': ['WEST', 'NORTHWEST', 'SOUTHWEST']},
        {'name': 'North 3 screens', 'threshold': 999, 'targets': ['NORTH', 'NORTHEAST', 'NORTHWEST']},
    ]
    
    # Clamp phase to valid range
    if _CURRENT_PHASE >= len(phases):
        _CURRENT_PHASE = len(phases) - 1
    
    current_phase_config = phases[_CURRENT_PHASE]
    targets = current_phase_config['targets']
    threshold = current_phase_config['threshold']
    
    print(f"[PHASE 6 ROUTE 104] Phase: {current_phase_config['name']}, Targets: {targets}")
    
    # Check if we should advance to next phase
    if _PHASE_MOVE_COUNT >= threshold:
        _advance_phase()
        # Recursive call with new phase
        return _handle_route_104_north(state_data, objectives, location_name)
    
    prompt = """🎮 PHASE 6: Road to Rustboro City

📍 ROUTE 104 NORTH
- Follow the suggested action EXACTLY. DO NOT TRY AND CHANGE IT YOURSELF.
- CHAIN THE ENTIRE ACTION SEQUENCE"""
    
    # Use directional A* with target priorities
    action = _path_with_priority_list(state_data, targets, location_name)
    
    # Track this movement for adaptive priority
    _track_movement(action)
    
    print(f"[PHASE 6] Route 104 North final action: {action}")
    return prompt, action


def _handle_rustboro_low_hp(state_data, objectives, location_name: str) -> Tuple[str, str]:
    """
    Rustboro City with low HP - need to heal at Pokemon Center.
    Adaptive phases:
    - Phase 0: Go NORTH for ~20 moves (2 screens)
    - Phase 1: Enter closest door (Pokemon Center)
    """
    global _CURRENT_PHASE, _PHASE_MOVE_COUNT
    
    print(f"[PHASE 6 RUSTBORO LOW HP] Phase {_CURRENT_PHASE}, moves: {_PHASE_MOVE_COUNT}")
    
    prompt = """🎮 PHASE 6: Rustboro City

📍 RUSTBORO CITY - LOW HP
- Follow the suggested action
- CHAIN THE ENTIRE ACTION SEQUENCE"""
    
    # Phase 0: Go north for 2 screens
    if _CURRENT_PHASE == 0:
        if _PHASE_MOVE_COUNT >= 20:
            _advance_phase()
            return _handle_rustboro_low_hp(state_data, objectives, location_name)
        
        action = _path_with_priority_list(state_data, ['NORTH', 'NORTHEAST', 'NORTHWEST'], location_name)
        _track_movement(action)
        return prompt, action
    
    # Phase 1: Find and enter door with healing sequence
    else:
        action = _find_door_and_path(
            state_data, 
            location_name, 
            door_filter='any',
            append_sequence=['UP', 'UP', 'UP', 'UP', 'A', 'A', 'A', 'A', 'A', 'A', 'A']
        )
        
        if not action:
            # Still go north if door not found
            action = _path_with_priority_list(state_data, ['NORTH'], location_name)
        
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
    Adaptive phases:
    - Phase 0: Go NORTH for ~20 moves (2 screens)
    - Phase 1: Enter closest door (Gym)
    """
    global _CURRENT_PHASE, _PHASE_MOVE_COUNT
    
    print(f"[PHASE 6 RUSTBORO FULL HP] Phase {_CURRENT_PHASE}, moves: {_PHASE_MOVE_COUNT}")
    
    prompt = """🎮 PHASE 6: Rustboro City

📍 RUSTBORO CITY - FULL HP
- Follow the suggested action
- CHAIN THE ENTIRE ACTION SEQUENCE"""
    
    # Phase 0: Go north for 2 screens
    if _CURRENT_PHASE == 0:
        if _PHASE_MOVE_COUNT >= 20:
            _advance_phase()
            return _handle_rustboro_full_hp(state_data, objectives, location_name)
        
        action = _path_with_priority_list(state_data, ['NORTH', 'NORTHEAST', 'NORTHWEST'], location_name)
        _track_movement(action)
        return prompt, action
    
    # Phase 1: Find and enter door (gym entrance)
    else:
        action = _find_door_and_path(
            state_data,
            location_name,
            door_filter='any',
            append_sequence=[]  # No extra sequence for gym entrance
        )
        
        if not action:
            # Still go north if door not found
            action = _path_with_priority_list(state_data, ['NORTH'], location_name)
        
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
    
    action = _path_with_priority_list(state_data, ['WEST'], location_name)
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
