# Phase 2 Prompt Controls

## Overview

Phase 2 now has fine-grained control over what gets included in prompts.

## Controlling Sections

### Disable Base Introduction

Set `include_base_intro=False` (this is the default):

```python
prompt = get_phase_prompt(
    phase=2,
    include_base_intro=False,  # Won't show "You are playing as the Protagonist..." intro
    ...
)
```

### Disable Action History

Set `include_action_history=False` (this is the default):

```python
prompt = get_phase_prompt(
    phase=2,
    include_action_history=False,  # Won't show "RECENT ACTION HISTORY" section
    ...
)
```

### Disable Objectives Section

Set `include_objectives=False` (this is already the default):

```python
prompt = get_phase_prompt(
    phase=2,
    include_objectives=False,  # Won't show "CURRENT OBJECTIVES:" section
    ...
)
```

### Disable Phase Tips Section

Set `include_phase_tips=False` (this is the default):

```python
prompt = get_phase_prompt(
    phase=2,
    include_phase_tips=False,  # Won't show "💡 IMPORTANT TIPS:" section
    ...
)
```

### What Gets Shown

With Phase 2 defaults (minimal prompt):

```
🎮 PHASE 2: Initial Setup in Littleroot Town

🚚 MOVING VAN:
- You're inside the moving van
- ONLY MOVE RIGHT - DO "RIGHT, RIGHT, RIGHT, RIGHT, RIGHT" to exit the truck

CURRENT GAME STATE:
...map and movement preview...

Available actions: A, B, START, SELECT, UP, DOWN, LEFT, RIGHT

...response format...

Context: overworld | Coords: (7, 2)
```

**What's NOT included by default:**
- ✗ Base intro ("You are playing as the Protagonist...")
- ✗ Action history
- ✗ Objectives section
- ✗ Movement memory
- ✗ Phase tips

**What IS included:**
- ✓ Conditional phase guidance (moving van, house, etc.)
- ✓ Current game state
- ✓ Response structure
- ✓ Stuck warning (if stuck)

With tips enabled:

```
🎮 PHASE 2: Initial Setup in Littleroot Town

🚚 MOVING VAN:
- You're inside the moving van
- ONLY MOVE RIGHT - DO "RIGHT, RIGHT, RIGHT, RIGHT, RIGHT" to exit the truck

💡 IMPORTANT TIPS:
- Always end actions with "A" when you need to advance dialogue
- When going upstairs, move ONTO the stairs tile (S)
- Use the coordinate system to find specific objects (like clocks)
- Check the visual map to see where stairs (S) and doors (D) are located
```

## Location Detection

The prompt now automatically detects your current location from the formatted state:

- **In MOVING_VAN**: Shows van exit instructions
- **In LITTLEROOT TOWN**: Shows town navigation
- **In PLAYER'S HOUSE 1F**: Shows stairs instructions
- **In PLAYER'S BEDROOM 2F**: Shows clock setting instructions
- **In MAY'S HOUSE**: Shows rival house objectives

The detection works in two ways:
1. **By location name** (most reliable): Checks if "MOVING_VAN" is in current location
2. **By objectives**: Falls back to checking which objectives are completed

## Customizing Defaults

To change defaults for Phase 2, edit `/agent/prompts/phase_2.py`:

```python
def get_phase_2_prompt(
    objectives: List[Any] = None,
    debug: bool = False,
    include_pathfinding_rules: bool = False,  # Change this to True to always show
    include_response_structure: bool = True,
    include_action_history: bool = True,
    include_location_history: bool = False,
    include_objectives: bool = False,          # Change to True to show objectives
    include_movement_memory: bool = False,
    include_stuck_warning: bool = True,
    include_phase_tips: bool = False,          # Change to True to show tips
    ...
)
```

## Example: Clean Minimal Prompt

For a super clean prompt with just the conditional guidance:

```python
prompt = get_phase_prompt(
    phase=2,
    objectives=all_objectives,
    formatted_state=formatted_state,
    # All these are already False by default
    include_pathfinding_rules=False,
    include_objectives=False,
    include_movement_memory=False,
    include_phase_tips=False,
    include_location_history=False,
    # These stay on
    include_action_history=True,
    include_response_structure=True,
    include_stuck_warning=True,
    ...
)
```

This will give you:
- Base context (game name, basic instructions)
- Conditional section (moving van, house, etc.)
- Action history
- Response format
- Stuck warning
- **NO** objectives list
- **NO** pathfinding rules
- **NO** movement memory
- **NO** tips section

