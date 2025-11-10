"""
Prompts module for SimpleAgent

Provides phase-specific prompts and common prompt components.
"""

import logging

logger = logging.getLogger(__name__)

from .common import get_pathfinding_rules, get_response_structure
from .phase_1 import get_phase_1_prompt
from .phase_2 import get_phase_2_prompt
from .phase_3 import get_phase_3_prompt

# Phase prompt getters - easy to extend
PHASE_PROMPTS = {
    1: get_phase_1_prompt,
    2: get_phase_2_prompt,
    3: get_phase_3_prompt,
}

def get_phase_prompt(
    phase: int,
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
    Get the prompt for a specific phase.
    
    Args:
        phase: Phase number (1, 2, 3, etc.)
        debug: If True, log the prompt to console for debugging
        include_pathfinding_rules: Include pathfinding rules (default: True)
        include_response_structure: Include response structure (default: True)
        include_action_history: Include action history (default: True)
        include_location_history: Include location history (default: True)
        include_objectives: Include objectives (default: True)
        include_movement_memory: Include movement memory (default: True)
        include_stuck_warning: Include stuck warning (default: True)
        **kwargs: Other arguments to pass to the phase prompt function
        
    Returns:
        Formatted prompt string
    """
    if phase not in PHASE_PROMPTS:
        # Default to phase 1 if phase not found
        logger.warning(f"Phase {phase} not found, defaulting to phase 1")
        phase = 1
    
    return PHASE_PROMPTS[phase](
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

