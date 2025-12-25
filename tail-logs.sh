#!/bin/bash

SESSION="container-logs"

tmux new-session -d -s $SESSION

tmux send-keys "docker logs -f vigorous_neumann" C-m
tmux split-window -h
tmux send-keys "docker logs -f nifty_robinson" C-m
tmux split-window -v
tmux send-keys "docker logs -f focused_beaver" C-m
tmux select-pane -t 0
tmux split-window -v
tmux send-keys "docker logs -f inspiring_chandrasekhar" C-m

tmux select-layout tiled
tmux attach -t $SESSION
