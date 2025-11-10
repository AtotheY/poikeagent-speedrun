"""
Phase 4 prompt - Rival encounter
"""

from .common import build_base_prompt


def get_phase_4_prompt(
    debug: bool = False,
    include_pathfinding_rules: bool = True,
    include_response_structure: bool = True,
    include_action_history: bool = True,
    include_location_history: bool = True,
    include_objectives: bool = True,
    include_movement_memory: bool = True,
    include_stuck_warning: bool = True,
    **kwargs
) -> str:
    """
    Get the Phase 4 prompt template.
    
    Phase 4 covers: [PLACEHOLDER - describe what phase 4 covers]
    
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
    # Phase 4 Milestones: OLDALE_TOWN, ROUTE_103, RECEIVED_POKEDEX
    phase_intro = """🎮 PHASE 4: [PLACEHOLDER - Phase 4 Title]
[PLACEHOLDER - Describe what the agent should focus on in this phase]
- [PLACEHOLDER - Goal 1]
- [PLACEHOLDER - Goal 2]
- [PLACEHOLDER - Goal 3]"""
    
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

