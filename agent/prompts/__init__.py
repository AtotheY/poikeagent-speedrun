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
from .phase_4 import get_phase_4_prompt
from .phase_5 import get_phase_5_prompt
from .phase_6 import get_phase_6_prompt
from .phase_7 import get_phase_7_prompt

# Phase prompt getters - easy to extend
PHASE_PROMPTS = {
    1: get_phase_1_prompt,
    2: get_phase_2_prompt,
    3: get_phase_3_prompt,
    4: get_phase_4_prompt,
    5: get_phase_5_prompt,
    6: get_phase_6_prompt,
    7: get_phase_7_prompt,
}

def get_phase_prompt(
    phase: int,
    debug: bool = False,
    **kwargs
) -> str:
    """
    Get the prompt for a specific phase.
    
    Each phase file controls its own include_* flags via function defaults.
    This function just passes through debug and other kwargs to the phase function.
    
    Args:
        phase: Phase number (1, 2, 3, etc.)
        debug: If True, log the prompt to console for debugging
        **kwargs: Arguments to pass to the phase prompt function (recent_actions_str, etc.)
        
    Returns:
        Formatted prompt string
    """
    if phase not in PHASE_PROMPTS:
        # Default to phase 1 if phase not found
        logger.warning(f"Phase {phase} not found, defaulting to phase 1")
        phase = 1
    
    # Just pass through debug and kwargs - each phase file sets its own include_* defaults
    return PHASE_PROMPTS[phase](debug=debug, **kwargs)

