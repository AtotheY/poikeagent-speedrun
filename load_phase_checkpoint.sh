#!/bin/bash
# Restore a phase checkpoint and reset milestone cache before loading
# Usage: ./load_phase_checkpoint.sh phase1

if [ -z "$1" ]; then
    echo "Usage: ./load_phase_checkpoint.sh <phase_name>"
    echo "Example: ./load_phase_checkpoint.sh phase1"
    exit 1
fi

PHASE_NAME="$1"
CACHE_DIR=".pokeagent_cache"

# Check if phase checkpoint exists
if [ ! -f "$CACHE_DIR/${PHASE_NAME}.state" ]; then
    echo "❌ Error: ${PHASE_NAME}.state not found in $CACHE_DIR"
    exit 1
fi

if [ ! -f "$CACHE_DIR/${PHASE_NAME}_milestones.json" ]; then
    echo "❌ Error: ${PHASE_NAME}_milestones.json not found in $CACHE_DIR"
    exit 1
fi

# IMPORTANT: Copy phase milestones to runtime cache BEFORE starting
# This ensures the milestone tracker starts with the correct phase state
cp "$CACHE_DIR/${PHASE_NAME}_milestones.json" "$CACHE_DIR/milestones_progress.json"

echo "✅ Phase checkpoint loaded:"
echo "   - Milestone cache reset to ${PHASE_NAME}_milestones.json"
echo ""
echo "Now run:"
echo "   python run.py --scaffold simple --backend openrouter --model-name \"openai/gpt-4o-mini\" --no-ocr --agent-auto --record --load-state .pokeagent_cache/${PHASE_NAME}.state"

