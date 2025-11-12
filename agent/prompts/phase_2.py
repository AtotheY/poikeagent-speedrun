"""
Phase 2 prompt - Mid game (after first gym through mid-game milestones)
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


def _get_phase_2_conditional_prompts(objectives: List[Any], current_location: str = None) -> str:
    """
    Generate conditional prompt sections based on completed objectives.
    
    Phase 2 Objectives (in order):
    - story_intro_complete: Complete intro cutscene with moving van
    - story_player_house: Enter player's house for the first time
    - story_player_bedroom: Go upstairs to player's bedroom
    - story_clock_set: Set the clock on the wall in the player's bedroom
    - story_rival_house: Visit May's house next door
    - story_rival_bedroom: Go to May's bedroom (upstairs in her house)
    
    Args:
        objectives: List of objective objects
        current_location: Current location name (to detect moving van)
        
    Returns:
        Conditional prompt text based on current progress
    """
    conditional_sections = []
    
    # Check if in moving van by location name (most reliable)
    if current_location and "MOVING_VAN" in current_location.upper():
        conditional_sections.append("""
🚚 MOVING VAN:
- You're inside the moving van
- ONLY MOVE RIGHT - DO "RIGHT, RIGHT, RIGHT, RIGHT, RIGHT" to exit the truck""")
    
    # Otherwise check objectives
    elif not _is_objective_completed(objectives, "story_intro_complete"):
        # Also moving van if objective not complete
        conditional_sections.append("""
🚚 MOVING VAN:
- You're inside the moving van
- ONLY MOVE RIGHT - DO "RIGHT, RIGHT, RIGHT, RIGHT, RIGHT" to exit the truck""")
    
    elif not _is_objective_completed(objectives, "story_player_house"):
        conditional_sections.append("""
🏘️ LITTLEROOT TOWN:
- Press A to advance dialogue""")
    
    elif not _is_objective_completed(objectives, "story_player_bedroom"):
        conditional_sections.append("""
🏠 PLAYER'S HOUSE - 1ST FLOOR:
- Go upstairs to your bedroom
- Find the stairs tile (S) on the map
- Move ONTO the stairs tile to go up
- MOVE UP ONLY! "UP, UP, UP, UP, UP, UP, A"
""")
    
    elif not _is_objective_completed(objectives, "story_clock_set"):
                conditional_sections.append("""
🛏️ PLAYER'S BEDROOM - 2ND FLOOR:
- you need tO LEAVE THE HOUSE. FIRST getg to the stairs and move UP. Then when you are on 1F, aka floor 1, go DOWN to D 
""")

#         conditional_sections.append("""
# 🛏️ PLAYER'S BEDROOM - 2ND FLOOR:
# - You need to set the clock on the wall
# - IF YOU ARE NOT DIRECTLY FACING THE CLOCK, MOVE TO IT BY GOING LEFT!. IT IS NOTED BYT K ON THE MAP.
# - Press UP ONLY if you are DIRECTLY below the clock. 
# - PRESS A to interact with the clock
# - Then press: A, UP, A, START to set it
# - You can tell the clock has been set because START will be in your history
# - Then go back downstairs and exit the house""")
    
    elif not _is_objective_completed(objectives, "story_rival_house"):
        conditional_sections.append("""
🏘️ LITTLEROOT TOWN:
- If you are in BRENDENS house, get to the door and go DOWN. If you are in Littleroute, go right until you see a door and go UP into it.""")
    
    elif not _is_objective_completed(objectives, "story_rival_bedroom"):
        conditional_sections.append("""
🏠 MAY'S HOUSE:
- Go upstairs to May's bedroom (Brendan's house)
- Find the stairs tile (S) on the map
- Move ONTO the stairs tile to go up
- On 2F (second floor), you must interact with the clock at coordinate (5,1)""")
    
    else:
        # All phase 2 objectives complete
        conditional_sections.append("""
✅ PHASE 2 COMPLETE:
- All initial house objectives are done
- Continue with your next objectives""")
    
    return "\n".join(conditional_sections)


def get_phase_2_prompt(
    objectives: List[Any] = None,
    debug: bool = False,
    include_base_intro: bool = False,  # Control base game introduction
    include_pathfinding_rules: bool = False,
    include_response_structure: bool = True,
    include_action_history: bool = True,
    include_location_history: bool = False,
    include_objectives: bool = False,
    include_movement_memory: bool = False,
    include_stuck_warning: bool = True,
    include_phase_tips: bool = False,  # Control tips section
    formatted_state: str = None,  # To extract location
    **kwargs
) -> str:
    """
    Get the Phase 2 prompt template with conditional sections based on objectives.
    
    Phase 2 covers: Initial game setup from moving van through setting up in Littleroot Town
    
    Args:
        objectives: List of current objective objects (for conditional prompts)
        debug: If True, log the prompt to console
        include_pathfinding_rules: Include pathfinding rules (default: False)
        include_response_structure: Include response structure (default: True)
        include_action_history: Include action history (default: True)
        include_location_history: Include location history (default: False)
        include_objectives: Include objectives (default: False)
        include_movement_memory: Include movement memory (default: False)
        include_stuck_warning: Include stuck warning (default: True)
        include_phase_tips: Include phase-specific tips section (default: False)
        formatted_state: Formatted state string to extract location from
        **kwargs: All other prompt building arguments (passed to build_base_prompt)
        
    Returns:
        Complete formatted prompt string
    """
    # Extract current location from formatted_state if available
    current_location = None
    if formatted_state and "Current Location:" in formatted_state:
        # Extract location from "Current Location: MOVING_VAN" line
        for line in formatted_state.split('\n'):
            if line.strip().startswith("Current Location:"):
                current_location = line.split(":", 1)[1].strip()
                break
    
    # Build base intro
    base_intro = "🎮 PHASE 2: Initial Setup in Littleroot Town"
    
    # Add conditional prompts based on objectives and location
    conditional_prompts = _get_phase_2_conditional_prompts(objectives or [], current_location)
    
    # Build phase intro - only add tips if requested
    if include_phase_tips:
        phase_intro = f"""{base_intro}

{conditional_prompts}

💡 IMPORTANT TIPS:
- Always end actions with "A" when you need to advance dialogue
- When going upstairs, move ONTO the stairs tile (S)
- Use the coordinate system to find specific objects (like clocks)
- Check the visual map to see where stairs (S) and doors (D) are located"""
    else:
        phase_intro = f"""{base_intro}

{conditional_prompts}"""
    
    return build_base_prompt(
        phase_intro=phase_intro,
        debug=debug,
        include_base_intro=include_base_intro,
        include_pathfinding_rules=include_pathfinding_rules,
        include_response_structure=include_response_structure,
        include_action_history=include_action_history,
        include_location_history=include_location_history,
        include_objectives=include_objectives,
        include_movement_memory=include_movement_memory,
        include_stuck_warning=include_stuck_warning,
        formatted_state=formatted_state,
        **kwargs
    )

