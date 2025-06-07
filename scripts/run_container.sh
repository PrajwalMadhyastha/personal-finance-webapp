#!/bin/bash
# This version uses the modern 'docker compose' (space) command provided by Docker Desktop.
set -e
COMMAND=${1:-up}
SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
PROJECT_ROOT="$SCRIPT_DIR/.."
cd "$PROJECT_ROOT"

if [ "$COMMAND" == "up" ]; then
    echo "--- Building/updating with Docker Desktop... ---"
    docker compose build
    echo "\n--- Starting application with Docker Desktop... ---"
    docker compose up -d
    echo "\n--- Application running. Logs: './scripts/run_container.sh logs', Stop: './scripts/run_container.sh down' ---"
elif [ "$COMMAND" == "down" ]; then
    docker compose down
    echo "--- Application stopped. ---"
elif [ "$COMMAND" == "logs" ]; then
    docker compose logs -f webapp
else
    echo "Usage: $0 [up|down|logs]"
    exit 1
fi