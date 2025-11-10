"""
Common prompt components shared across all phases
"""

import logging

logger = logging.getLogger(__name__)


def get_pathfinding_rules(context: str = "overworld") -> str:
    """
    Get pathfinding rules prompt section.
    
    Args:
        context: Current game context (title, overworld, battle, etc.)
        
    Returns:
        Pathfinding rules string (empty if in title sequence)
    """
    if context == "title":
        return ""
    
    return """
🚨 PATHFINDING RULES:
1. **SINGLE STEP FIRST**: Always prefer single actions (UP, DOWN, LEFT, RIGHT, A, B) unless you're 100% certain about multi-step paths
2. **CHECK EVERY STEP**: Before chaining movements, verify EACH step in your sequence using the MOVEMENT PREVIEW and map
3. **BLOCKED = STOP**: If ANY step shows BLOCKED in the movement preview, the entire sequence will fail
4. **NO BLIND CHAINS**: Never chain movements through areas you can't see or verify as walkable
5. **PERFORM PATHFINDING**: Find a path to a target location (X',Y') from the player position (X,Y) on the map. DO NOT TRAVERSE THROUGH OBSTACLES (#) -- it will not work.

💡 SMART MOVEMENT STRATEGY:
- Use MOVEMENT PREVIEW to see exactly what happens with each direction
- If your target requires multiple steps, plan ONE step at a time
- Only chain 2-3 moves if ALL intermediate tiles are confirmed WALKABLE
- When stuck, try a different direction rather than repeating the same blocked move
- After moving in a direction, you will be facing that direction for interactions with NPCs, etc.

EXAMPLE - DON'T DO THIS:
❌ "I want to go right 5 tiles" → "RIGHT, RIGHT, RIGHT, RIGHT, RIGHT" (may hit wall on step 2!)

EXAMPLE - DO THIS INSTEAD:
✅ Check movement preview → "RIGHT shows (X+1,Y) WALKABLE" → "RIGHT" (single safe step)
✅ Next turn, check again → "RIGHT shows (X+2,Y) WALKABLE" → "RIGHT" (another safe step)

💡 SMART NAVIGATION:
- The Player's sprite in the visual frame is located at the coordinates (X,Y) in the game state. Objects in the visual frame should be represented in relation to the Player's sprite.
- Check the VISUAL FRAME for NPCs (people/trainers) and other objects like clocks before moving - they're not always on the map! NPCs may block movement even when the movement preview shows them as walkable.
- Review MOVEMENT MEMORY for locations where you've failed to move before
- Only explore areas marked with ? (these are confirmed explorable edges)
- Avoid areas surrounded by # (walls) - they're fully blocked
- Use doors (D), stairs (S), or walk around obstacles when pathfinding suggests it

💡 NPC & OBSTACLE HANDLING:
- If you see NPCs in the image, avoid walking into them or interact with A/B if needed
- If a movement fails (coordinates don't change), that location likely has an NPC or obstacle
- Use your MOVEMENT MEMORY to remember problem areas and plan around them
- NPCs can trigger battles or dialogue, which may be useful for objectives
"""


def get_response_structure() -> str:
    """
    Get the response structure template for chain-of-thought reasoning.
    
    Returns:
        Response structure prompt section
    """
    return """IMPORTANT: Please think step by step before choosing your action. Structure your response like this:

ANALYSIS:
[Analyze what you see in the frame and current game state - what's happening? where are you? what should you be doing? 
IMPORTANT: Look carefully at the game image for objects (clocks, pokeballs, bags) and NPCs (people, trainers) that might not be shown on the map. NPCs appear as sprite characters and can block movement or trigger battles/dialogue. When you see them try determine their location (X,Y) on the map relative to the player and any objects.]

OBJECTIVES:
[Review your current objectives. You have main storyline objectives (story_*) that track overall Emerald progression - these are automatically verified and you CANNOT manually complete them.  There may be sub-objectives that you need to complete before the main milestone. You can create your own sub-objectives to help achieve the main goals. Do any need to be updated, added, or marked as complete?
- Add sub-objectives: ADD_OBJECTIVE: type:description:target_value (e.g., "ADD_OBJECTIVE: location:Find Pokemon Center in town:(15,20)" or "ADD_OBJECTIVE: item:Buy Pokeballs:5")
- Complete sub-objectives only: COMPLETE_OBJECTIVE: objective_id:notes (e.g., "COMPLETE_OBJECTIVE: my_sub_obj_123:Successfully bought Pokeballs")
- NOTE: Do NOT try to complete storyline objectives (story_*) - they auto-complete when milestones are reached]

PLAN:
[Think about your immediate goal - what do you want to accomplish in the next few actions? Consider your current objectives and recent history. 
Check MOVEMENT MEMORY for areas you've had trouble with before and plan your route accordingly.]

REASONING:
[Explain why you're choosing this specific action. Reference the MOVEMENT PREVIEW and MOVEMENT MEMORY sections. Check the visual frame for NPCs before moving. If you see NPCs in the image, avoid walking into them. Consider any failed movements or known obstacles from your memory.]

ACTION:
[Your final action choice - PREFER SINGLE ACTIONS like 'RIGHT' or 'A'. Only use multiple actions like 'UP, UP, RIGHT' if you've verified each step is WALKABLE in the movement preview and map.]"""


def build_base_prompt(
    phase_intro: str,
    recent_actions_str: str,
    history_summary: str,
    objectives_summary: str,
    formatted_state: str,
    movement_memory: str,
    stuck_warning: str,
    actions_display_count: int,
    history_display_count: int,
    context: str,
    coords: tuple = None,
    debug: bool = False,
    # Flags to control what gets included
    include_pathfinding_rules: bool = True,
    include_response_structure: bool = True,
    include_action_history: bool = True,
    include_location_history: bool = True,
    include_objectives: bool = True,
    include_movement_memory: bool = True,
    include_stuck_warning: bool = True,
) -> str:
    """
    Build the complete prompt using base template with phase-specific intro.
    
    Args:
        phase_intro: Phase-specific introduction text (what to focus on, etc.)
        recent_actions_str: Recent actions history string
        history_summary: Location/context history summary
        objectives_summary: Current objectives summary
        formatted_state: Formatted game state
        movement_memory: Movement memory string
        stuck_warning: Stuck warning string
        actions_display_count: Number of actions to display
        history_display_count: Number of history entries to display
        context: Current game context
        coords: Player coordinates tuple (optional)
        debug: If True, log the prompt to console
        include_pathfinding_rules: Include pathfinding rules section (default: True)
        include_response_structure: Include response structure template (default: True)
        include_action_history: Include recent action history (default: True)
        include_location_history: Include location/context history (default: True)
        include_objectives: Include current objectives (default: True)
        include_movement_memory: Include movement memory (default: True)
        include_stuck_warning: Include stuck warning (default: True)
        
    Returns:
        Complete formatted prompt string
    """
    # Conditionally build sections
    pathfinding_rules = get_pathfinding_rules(context) if include_pathfinding_rules else ""
    response_structure = get_response_structure() if include_response_structure else ""
    
    coords_str = f"({coords[0]}, {coords[1]})" if coords else "Unknown"
    
    # Build sections conditionally
    action_history_section = f"""RECENT ACTION HISTORY (last {actions_display_count} actions):
{recent_actions_str}

""" if include_action_history else ""
    
    location_history_section = f"""LOCATION/CONTEXT HISTORY (last {history_display_count} steps):
{history_summary}

""" if include_location_history else ""
    
    objectives_section = f"""CURRENT OBJECTIVES:
{objectives_summary}

""" if include_objectives else ""
    
    movement_memory_section = f"""{movement_memory}

""" if include_movement_memory and movement_memory else ""
    
    stuck_warning_section = f"""{stuck_warning}

""" if include_stuck_warning and stuck_warning else ""
    
    response_structure_section = f"""{response_structure}

""" if include_response_structure else ""
    
    pathfinding_rules_section = f"""{pathfinding_rules}

""" if include_pathfinding_rules and pathfinding_rules else ""
    
    prompt = f"""You are playing as the Protagonist in Pokemon Emerald. Progress quickly to the milestones by balancing exploration and exploitation of things you know, but have fun for the Twitch stream while you do it. 
Based on the current game frame and state information, think through your next move and choose the best button action. 
If you notice that you are repeating the same action sequences over and over again, you definitely need to try something different since what you are doing is wrong! Try exploring different new areas or interacting with different NPCs if you are stuck.

{phase_intro}

{action_history_section}{location_history_section}{objectives_section}CURRENT GAME STATE:
{formatted_state}

{movement_memory_section}{stuck_warning_section}Available actions: A, B, START, SELECT, UP, DOWN, LEFT, RIGHT

{response_structure_section}{pathfinding_rules_section}Context: {context} | Coords: {coords_str}"""
    
    if debug:
        logger.info("=" * 120)
        logger.info("🔍 PROMPT DEBUG (Phase-specific content):")
        logger.info("=" * 120)
        logger.info(f"Phase Intro:\n{phase_intro}\n")
        logger.info("=" * 120)
        logger.info("🔍 PROMPT CONFIGURATION:")
        logger.info(f"  include_pathfinding_rules: {include_pathfinding_rules}")
        logger.info(f"  include_response_structure: {include_response_structure}")
        logger.info(f"  include_action_history: {include_action_history}")
        logger.info(f"  include_location_history: {include_location_history}")
        logger.info(f"  include_objectives: {include_objectives}")
        logger.info(f"  include_movement_memory: {include_movement_memory}")
        logger.info(f"  include_stuck_warning: {include_stuck_warning}")
        logger.info("=" * 120)
        logger.info("🔍 FULL PROMPT:")
        logger.info("=" * 120)
        logger.info(prompt)
        logger.info("=" * 120)
    
    return prompt

