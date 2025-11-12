"""
Phase 5 prompt - Route 102 & Petalburg
"""

from .common import build_base_prompt


def get_phase_5_prompt(
    objectives=None,  # Accept objectives parameter for consistency
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
    state_data=None,  # For pathfinding helper
    **kwargs
) -> str:
    """
    Get the Phase 5 prompt template.
    
    Phase 5 covers: Route 102 & Petalburg City
    
    CLEAN PROMPT - Only includes:
    - Milestone-based instructions
    - Map / Legend / Map Tiles (from formatted_state)
    - Game State
    - Action input instructions
    - Pathfinding recommended actions (A* paths)
    
    Args:
        debug: If True, log the prompt to console
        state_data: Game state data for pathfinding helper
        **kwargs: All other prompt building arguments (passed to build_base_prompt)
        
    Returns:
        Complete formatted prompt string
    """
    # Phase 5 Milestones: ROUTE_102, PETALBURG_CITY, DAD_FIRST_MEETING, GYM_EXPLANATION
    phase_intro = """🎮 PHASE 5: Route 102 & Petalburg City
Navigate to Petalburg City and meet your dad at the gym.
Focus on progressing through Route 102 and reaching your dad."""
    
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
        state_data=state_data,
        **kwargs
    )

