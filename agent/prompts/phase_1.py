"""
Phase 1 prompt - Early game (title sequence through first gym)
"""

from .common import build_base_prompt




def get_phase_1_prompt(
    debug: bool = False,
    include_pathfinding_rules: bool = False,
    include_response_structure: bool = True,
    include_action_history: bool = False,
    include_location_history: bool = False,
    include_objectives: bool = False,
    include_movement_memory: bool = False,
    include_stuck_warning: bool = False,
    **kwargs
) -> str:
    """
    Get the Phase 1 prompt template.
    
    Phase 1 covers: [PLACEHOLDER - describe what phase 1 covers]
    
    Args:
        debug: If True, log the prompt to console
        include_pathfinding_rules: Include pathfinding rules (default: True)
        include_response_structure: Include response structure (default: True)
        include_action_history: Include action history (default: True)
        include_location_history: Include location history (default: True)
        include_objectives: Include objectives (default: True)
        include_movement_memory: Include movement memory (default: True)
        include_stuck_warning: Include stuck warning (default: True)
        **kwargs: All other prompt building arguments (passed to build_base_prompt)
        
    Returns:
        Complete formatted prompt string
    """
    # Phase 1 Milestones: GAME_RUNNING, PLAYER_NAME_SET, INTRO_CUTSCENE_COMPLETE
    phase_intro = """🎮 PHASE 1: Your goal is to simply progress through thet title screen and name selection as fast as possible.
    Spam A Until you're in the van, when you're in the moving van just move right a few times, 
    then spam A until the cutscene with mom is done."""
    
    return build_base_prompt(
        phase_intro=phase_intro,
        debug=debug,
        include_pathfinding_rules=include_pathfinding_rules,
        include_response_structure=include_response_structure,
        include_action_history=include_action_history,
        include_location_history=include_location_history,
        include_objectives=include_objectives,
        include_movement_memory=include_movement_memory,
        include_stuck_warning=include_stuck_warning,
        **kwargs
    )

