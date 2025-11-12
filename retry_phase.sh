#!/bin/bash
# Retry a phase from a checkpoint with fresh milestones
# Usage: ./retry_phase.sh phase1 [additional run.py args]

if [ -z "$1" ]; then
    echo "Usage: ./retry_phase.sh <phase_name> [additional args]"
    echo "Example: ./retry_phase.sh phase1"
    echo "Example: ./retry_phase.sh phase1 --debug"
    echo "Example: ./retry_phase.sh phase1 --model-name 'openai/gpt-4o'"
    exit 1
fi

PHASE_NAME="$1"
shift  # Remove phase name from args, rest are passed to run.py

# Default model name
MODEL_NAME="openai/gpt-4o-mini"

# Check if --model-name is provided in the arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --model-name)
            MODEL_NAME="$2"
            shift 2
            ;;
        *)
            # Store remaining args to pass to run.py
            EXTRA_ARGS="$EXTRA_ARGS $1"
            shift
            ;;
    esac
done

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

echo "🔄 Resetting milestones to ${PHASE_NAME} checkpoint..."
# Copy phase milestones to runtime cache (not symlink, to avoid interference with fresh runs)
cp "$CACHE_DIR/${PHASE_NAME}_milestones.json" "$CACHE_DIR/milestones_progress.json"
echo "⚠️  Note: To save progress back to ${PHASE_NAME}, manually save checkpoint when done"

# Delete the most recent recording to avoid accumulation
LATEST_RECORDING=$(ls -t pokegent_recording_*.mp4 2>/dev/null | head -1)
if [ -n "$LATEST_RECORDING" ]; then
    echo "🗑️  Deleting previous recording: $LATEST_RECORDING"
    rm "$LATEST_RECORDING"
fi

echo "✅ Milestones reset to ${PHASE_NAME} state"
echo "🚀 Starting game from ${PHASE_NAME}.state with model: $MODEL_NAME..."
echo ""

# Run the game with the phase checkpoint
python run.py --scaffold simple --backend openrouter --model-name "$MODEL_NAME" --no-ocr --agent-auto --record --load-state "$CACHE_DIR/${PHASE_NAME}.state" $EXTRA_ARGS

