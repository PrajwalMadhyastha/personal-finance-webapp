#!/bin/bash
# The single, powerful management script for the Flask application.
set -euo pipefail

# --- USAGE FUNCTION ---
usage() {
    echo "Usage: $0 {start|stop|logs|shell|db}"
    echo "  start           : Builds image and starts the application."
    echo "  stop            : Stops the application."
    echo "  logs            : Tails the application logs."
    echo "  shell           : Opens a bash shell inside a new temporary container."
    echo "  db <cmd>        : Runs a database command."
    echo "    db commands: init, migrate, upgrade, downgrade, reset-db, clear-expenses"
    echo ""
    echo "DB command example: ./scripts/manage.sh db migrate 'Add notes'"
    exit 1
}

# --- MAIN LOGIC ---
if [ -z "$1" ]; then
    usage
fi

COMMAND="$1"

# --- DYNAMIC PATHS and DOCKER COMPOSE COMMAND ---
SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
PROJECT_ROOT="$SCRIPT_DIR/.."
cd "$PROJECT_ROOT"

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
        $COMPOSER up --build -d
        echo "Application is running in the background."
        ;;
    stop)
        echo "--- Stopping application ---"
        $COMPOSER down
        ;;
    logs)
        echo "--- Tailing application logs ---"
        $COMPOSER logs -f webapp
        ;;
    shell)
        echo "--- Starting a new container and opening a shell session... ---"
        $COMPOSER run --rm -e FLASK_APP=run.py webapp bash
        ;;
    db)
        DB_COMMAND="${2:-}"
        if [ -z "$DB_COMMAND" ]; then
            echo "Error: 'db' command requires a subcommand."
            usage
        fi
        
        echo "Running 'flask $DB_COMMAND' command inside the container..."
        
        # Ensure container service is running before executing commands
        $COMPOSER up -d --no-build

        # This block now correctly handles all our different command types
        if [ "$DB_COMMAND" == "migrate" ]; then
            MIGRATE_MESSAGE="${3:-"New migration"}"
            $COMPOSER exec -e FLASK_APP=run.py webapp flask db migrate -m "$MIGRATE_MESSAGE"
        elif [ "$DB_COMMAND" == "reset-db" ] || [ "$DB_COMMAND" == "clear-expenses" ]; then
            # This handles our custom top-level commands
            $COMPOSER exec -e FLASK_APP=run.py webapp flask "$DB_COMMAND"
        else
            # For standard Flask-Migrate commands like 'upgrade', 'downgrade', 'init'
            $COMPOSER exec -e FLASK_APP=run.py webapp flask db "$DB_COMMAND"
        fi
        ;;
    *)
        echo "Error: Unknown command '$COMMAND'"
        usage
        ;;
esac