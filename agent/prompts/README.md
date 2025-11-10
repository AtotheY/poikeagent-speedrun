# Prompts Module

This module contains all prompts for the SimpleAgent, organized by phase. The structure is designed to minimize code duplication - all shared logic is in `common.py`, and each phase file only contains the phase-specific intro text.

## Structure

- `common.py` - Shared prompt components and base template builder
  - `get_pathfinding_rules()` - Pathfinding rules section
  - `get_response_structure()` - Chain-of-thought response structure
  - `build_base_prompt()` - Main template builder (handles all shared logic)
- `phase_1.py` - Phase 1 prompt (only contains phase-specific intro)
- `phase_2.py` - Phase 2 prompt (only contains phase-specific intro)
- `phase_3.py` - Phase 3 prompt (only contains phase-specific intro)

## Usage

### Switching Phases

In your code, you can switch phases with one line:

```python
# Option 1: Direct assignment
agent.current_phase = 2

# Option 2: Using helper method
agent.set_phase(2)
```

### Debugging Prompts

To see what prompt is being sent to the VLM, enable debug mode:

```python
# Enable prompt debugging
agent.debug_prompts = True

# Or disable it
agent.debug_prompts = False
```

When enabled, the prompt will be logged to the console with:
- Phase-specific intro section
- Full complete prompt

### Adding New Phases

1. Create a new file `phase_N.py` in this directory
2. Implement `get_phase_N_prompt(debug=False, **kwargs)` function that:
   - Defines the `phase_intro` string (phase-specific content)
   - Calls `build_base_prompt(phase_intro=phase_intro, debug=debug, **kwargs)`
3. Add it to `PHASE_PROMPTS` dictionary in `__init__.py`

Example:

```python
# phase_4.py
from .common import build_base_prompt

def get_phase_4_prompt(debug: bool = False, **kwargs) -> str:
    phase_intro = """🎮 PHASE 4: Your Phase Title
    Your phase-specific instructions here
    - Goal 1
    - Goal 2"""
    
    return build_base_prompt(phase_intro=phase_intro, debug=debug, **kwargs)
```

Then in `__init__.py`:
```python
from .phase_4 import get_phase_4_prompt
PHASE_PROMPTS[4] = get_phase_4_prompt
```

### Controlling What Gets Included

Each phase function accepts boolean flags to control which sections are included in the prompt:

```python
# Example: Phase 1 without pathfinding rules and movement memory
def get_phase_1_prompt(debug=False, **kwargs):
    phase_intro = """🎮 PHASE 1: Title"""
    
    return build_base_prompt(
        phase_intro=phase_intro,
        debug=debug,
        include_pathfinding_rules=False,  # Don't include pathfinding rules
        include_movement_memory=False,     # Don't include movement memory
        **kwargs
    )
```

Available flags (all default to `True`):
- `include_pathfinding_rules` - Pathfinding rules section
- `include_response_structure` - Chain-of-thought response structure
- `include_action_history` - Recent action history
- `include_location_history` - Location/context history
- `include_objectives` - Current objectives
- `include_movement_memory` - Movement memory
- `include_stuck_warning` - Stuck warning

### Editing Prompts

- **Common/shared components**: Edit `common.py`
  - Base template structure: `build_base_prompt()` function
  - Pathfinding rules: `get_pathfinding_rules()` function
  - Response structure: `get_response_structure()` function
- **Phase-specific content**: Edit the `phase_intro` string in the corresponding `phase_N.py` file
- **Control what's included**: Set the `include_*` flags in your phase function
- **All prompts**: Automatically use the same base template - no duplication needed!

