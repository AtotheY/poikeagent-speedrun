#!/bin/bash
# Save a phase checkpoint with proper milestone files
# Usage: ./save_phase_checkpoint.sh phase1

if [ -z "$1" ]; then
    echo "Usage: ./save_phase_checkpoint.sh <phase_name>"
    echo "Example: ./save_phase_checkpoint.sh phase1"
    exit 1
fi

PHASE_NAME="$1"
CACHE_DIR=".pokeagent_cache"

# Check if checkpoint files exist
if [ ! -f "$CACHE_DIR/checkpoint.state" ]; then
    echo "❌ Error: checkpoint.state not found in $CACHE_DIR"
    exit 1
fi

if [ ! -f "$CACHE_DIR/checkpoint_milestones.json" ]; then
    echo "❌ Error: checkpoint_milestones.json not found in $CACHE_DIR"
    exit 1
fi

# Copy checkpoint files to phase-specific names
cp "$CACHE_DIR/checkpoint.state" "$CACHE_DIR/${PHASE_NAME}.state"
cp "$CACHE_DIR/checkpoint_milestones.json" "$CACHE_DIR/${PHASE_NAME}_milestones.json"

# Also save map data if it exists
if [ -f "$CACHE_DIR/map_stitcher_data.json" ]; then
    cp "$CACHE_DIR/map_stitcher_data.json" "$CACHE_DIR/${PHASE_NAME}_map_stitcher.json"
fi

# Save the most recent recording with phase name
LATEST_RECORDING=$(ls -t pokegent_recording_*.mp4 2>/dev/null | head -1)
if [ -n "$LATEST_RECORDING" ]; then
    cp "$LATEST_RECORDING" "${PHASE_NAME}.mp4"
    echo "✅ Phase checkpoint saved:"
    echo "   - ${PHASE_NAME}.state"
    echo "   - ${PHASE_NAME}_milestones.json"
    echo "   - ${PHASE_NAME}.mp4 (recording)"
else
    echo "✅ Phase checkpoint saved:"
    echo "   - ${PHASE_NAME}.state"
    echo "   - ${PHASE_NAME}_milestones.json"
    echo "   ⚠️  No recording found to save"
fi

if [ -f "$CACHE_DIR/${PHASE_NAME}_map_stitcher.json" ]; then
    echo "   - ${PHASE_NAME}_map_stitcher.json"
fi

