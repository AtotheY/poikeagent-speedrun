"""
Phase 3 prompt - Professor Birch & Starter Pokemon
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


def _get_phase_3_conditional_prompts(objectives: List[Any], current_location: str = None) -> str:
    """
    Generate conditional prompt sections based on completed objectives.
    
    Phase 3 Objectives (in order):
    - ROUTE_101: Reach Route 101 and encounter Professor Birch
    - STARTER_CHOSEN: Choose your starter Pokemon (Treecko, Torchic, or Mudkip)
    - BIRCH_LAB_VISITED: Visit Professor Birch's lab in Littleroot Town
    
    Args:
        objectives: List of objective objects
        current_location: Current location name
        
    Returns:
        Conditional prompt text based on current progress
    """
    conditional_sections = []

    if not _is_objective_completed(objectives, "STARTER_CHOSEN"):
        conditional_sections.append("""
🌿 ROUTE 101:
- You need to reach Professor Birch who is being attacked by a wild Pokemon
- THE BAG IS AT (3,9) GET TO THAT AND FACE IT AND PRESS A REPEATEDLY TO CHOOSE YOUR a
- it will be in the center of the map so move around there
- Press A to advance dialogue when you encounter Birch""")


    
    elif not _is_objective_completed(objectives, "BIRCH_LAB_VISITED"):
        conditional_sections.append("""
🔬 RETURN TO BIRCH'S LAB:
- Return to Littleroot Town
- Find and enter Professor Birch's lab
- The lab is a separate building in Littleroot Town
- Move to the door (D) and press UP to enter
- Press A to advance dialogue with Birch""")
    
    else:
        # All phase 3 objectives complete
        conditional_sections.append("""
✅ PHASE 3 COMPLETE:
- You have your starter Pokemon!
- Birch's lab has been visited
- Continue with your next objectives""")
    
    return "\n".join(conditional_sections)


def get_phase_3_prompt(
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
    state_data = None,  # For pathfinding helper
    **kwargs
) -> str:
    """
    Get the Phase 3 prompt template with conditional sections based on objectives.
    
    Phase 3 covers: Getting starter Pokemon from Professor Birch on Route 101
    
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
        # Extract location from "Current Location: ROUTE_101" line
        for line in formatted_state.split('\n'):
            if line.strip().startswith("Current Location:"):
                current_location = line.split(":", 1)[1].strip()
                break
    
    # Build base intro
    base_intro = "🎮 PHASE 3: Professor Birch & Starter Pokemon"
    
    # Add conditional prompts based on objectives and location
    conditional_prompts = _get_phase_3_conditional_prompts(objectives or [], current_location)
    
    # Build phase intro - only add tips if requested
    if include_phase_tips:
        phase_intro = f"""{base_intro}

{conditional_prompts}

💡 IMPORTANT TIPS:
- Always end actions with "A" when you need to advance dialogue
- In battles, select your attack by pressing A on the attack menu
- Navigate menus by using UP/DOWN and confirming with A
- Check your map to understand where you need to go"""
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
        state_data=state_data,
        **kwargs
    )

