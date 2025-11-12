"""
Phase 4 prompt - Rival Battle & Pokedex
"""

from typing import List, Any
from .common import build_base_prompt


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
    
    # Check if in Oldale Town
    if current_location and "OLDALE" in current_location.upper():
        if not _is_objective_completed(objectives, "OLDALE_TOWN"):
            conditional_sections.append("""
🏙️ OLDALE TOWN:
- You've reached Oldale Town!
- This is your first new town
- Press A to advance any dialogue
- Explore and head north towards Route 103""")
    
    # Check if on Route 103
    if current_location and "ROUTE_103" in current_location.upper():
        if not _is_objective_completed(objectives, "ROUTE_103"):
            conditional_sections.append("""
🌊 ROUTE 103:
- You're on Route 103
- Your rival (May/Brendan) is waiting here for a battle
- Navigate north through the route
- Press A to initiate dialogue and battle""")
    
    if not _is_objective_completed(objectives, "OLDALE_TOWN"):
        # Still need to reach Oldale Town
        conditional_sections.append("""
🗺️ HEADING TO OLDALE TOWN:
- Once you are in Littleroot town, continue NORTH through the safe spots on the map.
- Safe walkable spots on the map are denoted as "." while blocked spots are denoted as "#".
- Keep going north as far as you can. Note this may mean you have to go around blocked spots by going left then right.
- You may encounter pokemon battles - if you do press over and over until the battle is over.
- If you are under a D door tile, going up will bring you inside. WE DO NOT WANT THAT! GO AROUND THE BUILDING!
- PATH UPWARDS AS BEST AS YOU CAN NORTH BY AVOIDING ALL OBSTACLES AND BLOCKED PATHS IN YOUR WAY.
- IF THE CURRENT LOCATION IS: "LITTLEROOT TOWN PROFESSOR BIRCHS LAB" GO DOWN! JUST DOWN!.

""")
    
    elif not _is_objective_completed(objectives, "ROUTE_103"):
        conditional_sections.append("""
⚔️ FIND YOUR RIVAL:
- From Oldale Town, head north to Route 103
- Your rival is waiting on Route 103 which is straight NORTH for a Pokemon battle
- Safe walkable spots on the map are denoted as "." while blocked spots are denoted as "#".
- Keep going north as far as you can. Note this may mean you have to go around blocked spots by going left then right.
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
    
    # Build base intro
    base_intro = "🎮 PHASE 4: Rival Battle & Pokedex"
    
    # Add conditional prompts based on objectives and location
    conditional_prompts = _get_phase_4_conditional_prompts(objectives or [], current_location)
    
    # Build phase intro - only add tips if requested
    if include_phase_tips:
        phase_intro = f"""{base_intro}

{conditional_prompts}

💡 IMPORTANT TIPS:
- In battle, select your strongest move against your rival
- Your rival has the starter Pokemon strong against yours (type advantage)
- Use healing items if your Pokemon's HP gets low
- Always press A to advance dialogue and select menu options
- After battles, you may need to navigate back to previous locations"""
    else:
        phase_intro = f"""{base_intro}

{conditional_prompts}"""
    
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
        formatted_state=formatted_state,
        state_data=state_data,
        **kwargs
    )

