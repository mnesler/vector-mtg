#!/bin/bash
# Start a split tmux session with monitoring pane

SESSION_NAME="claude-work"

# Check if tmux is installed
if ! command -v tmux &> /dev/null; then
    echo "tmux is not installed. Install it with: sudo apt install tmux"
    exit 1
fi

# Check if session already exists
if tmux has-session -t $SESSION_NAME 2>/dev/null; then
    echo "Session $SESSION_NAME already exists. Attaching..."
    tmux attach-session -t $SESSION_NAME
    exit 0
fi

# Create new session
tmux new-session -d -s $SESSION_NAME -n main

# Split window vertically (70% left, 30% right)
tmux split-window -h -t $SESSION_NAME:0 -p 30

# Left pane (main work area) - stay in current directory
tmux send-keys -t $SESSION_NAME:0.0 "cd /home/maxwell/vector-mtg" C-m
tmux send-keys -t $SESSION_NAME:0.0 "clear" C-m

# Right pane (monitor) - run the status monitor
tmux send-keys -t $SESSION_NAME:0.1 "cd /home/maxwell/vector-mtg" C-m
tmux send-keys -t $SESSION_NAME:0.1 "./scripts/monitor-status.sh" C-m

# Select the left pane as active
tmux select-pane -t $SESSION_NAME:0.0

# Attach to session
tmux attach-session -t $SESSION_NAME
