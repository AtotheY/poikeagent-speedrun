"""
Phase 5 prompt - Route 102 & Petalburg
"""

from typing import List, Any
from .common import build_base_prompt
from utils.state_formatter import find_path_around_obstacle


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


def _get_phase_5_conditional_prompts(objectives: List[Any], current_location: str = None) -> str:
    """
    Generate conditional prompt sections based on completed objectives.
    
    Phase 5 Objectives (in order):
    - ROUTE_102: Navigate through Route 102
    - PETALBURG_CITY: Reach Petalburg City
    - DAD_FIRST_MEETING: Talk to your dad at the gym
    
    Args:
        objectives: List of objective objects
        current_location: Current location name
        
    Returns:
        Conditional prompt text based on current progress
    """
    conditional_sections = []
    
    if not _is_objective_completed(objectives, "ROUTE_102"):
        # Still need to complete Route 102
        base_section = """
🗺️ ROUTE 102:
"""
        
        # Add location-specific subsections
        loc_upper = current_location.upper() if current_location else ""
        location_specific = ""
        
        if "BIRCH" in loc_upper and "LAB" in loc_upper:
            location_specific = """

📍 PROFESSOR BIRCH'S LAB:
You need to exit Birch's lab. You can do this by simply standing next to a D tile and going DOWN (even if it says it's blocked don't worry)

JUST RETURN "RIGHT, RIGHT, DOWN"""
        
        elif "LITTLEROOT" in loc_upper:
            location_specific = """

📍 LITTLEROOT TOWN:
You need to path straight NORTH. You should always try to go UP. If the path UP is blocked, just follow the suggested actions.
- ALWAYS ADD 'A' at the end of every action chain / individual action just incase you are in dialogue.
"""
        
        elif "ROUTE_101" in loc_upper or "ROUTE 101" in loc_upper:
            location_specific = """

📍 ROUTE 101:
You need to path straight NORTH. You should always try to go UP. If the path UP is blocked, just follow the suggested actions.
- ALWAYS ADD 'A' at the end of every action chain / individual action just incase you are in dialogue.
- WHEN IN BATTLE, ALWAYS DO: "A, B, LEFT, A, RIGHT, A" TO ATTACK. CHAIN THE ENTIRE THING IN ONE ACTION."""

        elif "OLDALE" in loc_upper:
            location_specific = """

📍 OLDALE TOWN:
You need to path straight WEST. You should always try to go LEFT. If the path LEFT is blocked, just follow the suggested actions to get around the obstacle.
- WHEN IN BATTLE, ALWAYS DO: "A, B, LEFT, A, RIGHT, A" TO ATTACK. CHAIN THE ENTIRE THING IN ONE ACTION."""
        
        conditional_sections.append(base_section + location_specific)
    
    elif not _is_objective_completed(objectives, "PETALBURG_CITY"):
        # Still need to reach Petalburg City
        conditional_sections.append("""
🏙️ PETALBURG CITY:
[PLACEHOLDER - Add instructions for Petalburg City here]""")
    
    elif not _is_objective_completed(objectives, "DAD_FIRST_MEETING"):
        # Still need to talk to dad
        conditional_sections.append("""
👨 TALK TO DAD:
[PLACEHOLDER - Add instructions for talking to dad here]""")
    
    return "\n".join(conditional_sections)


def _get_full_path_to_direction(state_data, target_direction: str, location_name: str = '') -> List[str]:
    """
    Get the full action sequence to reach the most extreme point in a direction.
    Always pathfinds to the extreme point, even if immediate path is clear.
    
    Args:
        state_data: Game state data
        target_direction: 'UP', 'DOWN', 'LEFT', or 'RIGHT'
        location_name: Current location for door-blocking logic
        
    Returns:
        List of action strings (e.g., ['UP', 'UP', 'RIGHT', 'UP'])
    """
    from utils.map_formatter import format_map_grid
    from utils.state_formatter import astar_pathfind, find_directional_goal
    
    try:
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
        
        # Convert to grid array index
        player_y_idx = grid_height - 1 - player_grid_y
        
        # Find the most extreme walkable point in target direction
        goal_pos = find_directional_goal(grid, (player_grid_x, player_y_idx), target_direction, location_name)
        
        if not goal_pos:
            return []
        
        # Use A* to find path
        path = astar_pathfind(grid, (player_grid_x, player_y_idx), goal_pos, location_name)
        
        return path if path else []
        
    except Exception:
        return []


def _get_phase_5_suggested_action(state_data, current_location: str = None, objectives: List[Any] = None) -> str:
    """
    Calculate the suggested action for Phase 5 based on location.
    
    Location-specific pathing for ROUTE_102 objective:
    - Littleroot Town: Path NORTH (UP) using A* to avoid obstacles (including doors)
    - Route 101: Path NORTH (UP) using A* to avoid obstacles
    - Oldale Town: Path WEST (LEFT) using A* to avoid obstacles
    - Route 102: Path WEST (LEFT) using A* to avoid obstacles
    
    Note: No suggested actions for Birch's Lab (manual instructions provided)
    
    Args:
        state_data: Game state data
        current_location: Current location name
        objectives: Current objectives list
        
    Returns:
        Suggested action string to append at end of prompt
    """
    if not state_data:
        return ""
    
    route_102_done = objectives and _is_objective_completed(objectives, "ROUTE_102")
    
    # Location-specific handling for ROUTE_102 objective
    if not route_102_done and current_location:
        loc_upper = current_location.upper()
        
        # NO SUGGESTED ACTIONS for Birch's Lab - manual instructions only
        if "BIRCH" in loc_upper and "LAB" in loc_upper:
            return ""
        
        # LITTLEROOT TOWN - go north, always pathfind to most northern point
        if "LITTLEROOT" in loc_upper:
            # Get full path to most northern point
            action_seq = _get_full_path_to_direction(state_data, 'UP', current_location)
            if action_seq and len(action_seq) > 0:
                # Add 'A' at the end for dialogue/interaction
                action_seq.append('A')
                return f"\nSuggested action: {', '.join(action_seq)}"
            # Fallback if pathfinding fails
            return "\nSuggested action: UP, A"
        
        # ROUTE 101 - go north, always pathfind to most northern point
        elif "ROUTE_101" in loc_upper or "ROUTE 101" in loc_upper:
            # Get full path to most northern point
            action_seq = _get_full_path_to_direction(state_data, 'UP', current_location)
            if action_seq and len(action_seq) > 0:
                # Add 'A' at the end for dialogue/interaction
                action_seq.append('A')
                return f"\nSuggested action: {', '.join(action_seq)}"
            # Fallback if pathfinding fails
            return "\nSuggested action: UP, A"
        
        # OLDALE TOWN - go west, always pathfind to most western point
        elif "OLDALE" in loc_upper:
            # Get full path to most western point
            action_seq = _get_full_path_to_direction(state_data, 'LEFT', current_location)
            if action_seq and len(action_seq) > 0:
                # Add 'A' at the end for dialogue/interaction
                action_seq.append('A')
                return f"\nSuggested action: {', '.join(action_seq)}"
            # Fallback if pathfinding fails
            return "\nSuggested action: LEFT, A"
        
        # ROUTE 102 - go west, always pathfind to most western point
        elif "ROUTE_102" in loc_upper or "ROUTE 102" in loc_upper:
            # Get full path to most western point
            action_seq = _get_full_path_to_direction(state_data, 'LEFT', current_location)
            if action_seq and len(action_seq) > 0:
                # Add 'A' at the end for dialogue/interaction
                action_seq.append('A')
                return f"\nSuggested action: {', '.join(action_seq)}"
            # Fallback if pathfinding fails
            return "\nSuggested action: LEFT, A"
    
    return ""


def get_phase_5_prompt(
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
    formatted_state: str = None,  # To extract location
    state_data=None,  # For pathfinding helper
    **kwargs
) -> str:
    """
    Get the Phase 5 prompt template with conditional sections based on objectives.
    
    Phase 5 covers: Route 102 & Petalburg City
    
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
        # Extract location from "Current Location: ROUTE_102" line
        for line in formatted_state.split('\n'):
            if line.strip().startswith("Current Location:"):
                current_location = line.split(":", 1)[1].strip()
                break
    
    # If no location from formatted_state, try state_data
    if not current_location and state_data:
        current_location = state_data.get('player', {}).get('location', '')
    
    # Build base intro
    base_intro = "🎮 PHASE 5: Route 102 & Petalburg City"
    
    # Add conditional prompts based on objectives and location
    conditional_prompts = _get_phase_5_conditional_prompts(objectives or [], current_location)
    
    # Build phase intro
    phase_intro = f"""{base_intro}

{conditional_prompts}"""
    
    # Calculate suggested action for Phase 5
    suggested_action = _get_phase_5_suggested_action(state_data, current_location, objectives)
    
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

