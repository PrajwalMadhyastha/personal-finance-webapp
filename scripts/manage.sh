#!/bin/bash
# The single management script for the Flask application, using Docker Compose.
set -euo pipefail

# --- USAGE FUNCTION ---
usage() {
    echo "Usage: $0 {start|stop|logs|db|shell}"
    echo "  start       : Builds and starts the application in the background."
    echo "  stop        : Stops and removes the application containers."
    echo "  logs        : Tails the application logs."
    echo "  db <cmd>    : Runs a database migration command (e.g., init, migrate, upgrade)."
    echo "  shell       : Opens a bash shell inside the running webapp container."
    echo ""
    echo "DB command example: ./scripts/manage.sh db migrate 'Add notes to expense model'"
    exit 1
}

# --- MAIN LOGIC ---
if [ -z "$1" ]; then
    usage
fi

COMMAND="$1"

# --- DYNAMIC PATHS ---
# This makes the script runnable from anywhere by finding the project root.
SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
PROJECT_ROOT="$SCRIPT_DIR/.."
# Always run docker-compose from the project root where the .yml file is
cd "$PROJECT_ROOT"

# --- DETECT DOCKER COMPOSE COMMAND ---
# Find the correct docker compose command ('docker-compose' or 'docker compose')
COMPOSER="docker-compose"
if ! command -v docker-compose &> /dev/null; then
    if docker compose version &> /dev/null; then
        COMPOSER="docker compose"
    else
        echo "Error: Neither 'docker-compose' nor 'docker compose' seems to be installed or working."
        exit 1
    fi
fi

# --- COMMAND ROUTING ---
case "$COMMAND" in
    start)
        echo "--- Building image (if needed) and starting application ---"
        # The --build flag rebuilds the image only if there are changes.
        # The -d flag runs the containers in detached mode (in the background).
        $COMPOSER up --build -d
        echo ""
        echo "Application is running in the background."
        echo "View logs with: ./scripts/manage.sh logs"
        ;;

    stop)
        echo "--- Stopping and removing application containers ---"
        $COMPOSER down
        ;;

    logs)
        echo "--- Tailing application logs (Press Ctrl+C to stop) ---"
        # The -f flag "follows" the log output.
        $COMPOSER logs -f webapp
        ;;

    db)
        # Handle database migration commands
        DB_COMMAND="${2:-}" # Get the second argument (init, migrate, etc.)
        if [ -z "$DB_COMMAND" ]; then
            echo "Error: 'db' command requires a subcommand (e.g., init, migrate, upgrade)."
            usage
        fi
        
        echo "Running 'flask db $DB_COMMAND' inside the container..."
        # Use 'docker compose exec' to run a command inside the 'webapp' service container
        if [ "$DB_COMMAND" == "migrate" ]; then
            # Allows for a custom migration message
            MIGRATE_MESSAGE="${3:-"New migration"}"
            $COMPOSER exec webapp flask db migrate -m "$MIGRATE_MESSAGE"
        else
            $COMPOSER exec webapp flask db "$DB_COMMAND"
        fi
        ;;

    shell)
        echo "--- Opening a shell inside the webapp container ---"
        echo "--- Type 'exit' to return to your normal terminal ---"
        $COMPOSER exec webapp bash
        ;;

    *)
        echo "Error: Unknown command '$COMMAND'"
        usage
        ;;
esac