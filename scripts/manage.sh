#!/bin/bash
# A management script for the application, adapted for a Docker workflow.
set -euo pipefail

# --- USAGE FUNCTION ---
usage() {
    echo "Usage: $0 {start|stop|logs|db}"
    echo "  start       : Builds and starts the application via Docker Compose."
    echo "  stop        : Stops the application."
    echo "  logs        : Tails the application logs."
    echo "  db <cmd>    : Runs a database migration command inside the container."
    echo "    db commands: init, migrate, upgrade, downgrade"
    echo "    Example: ./scripts/manage.sh db migrate 'Add new user field'"
    exit 1
}

# --- MAIN LOGIC ---
if [ -z "$1" ]; then
    usage
fi

COMMAND="$1"

# Ensure docker compose is available
if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    echo "Error: 'docker-compose' or 'docker compose' not found. Please ensure Docker is installed and running."
    exit 1
fi
# Use the available compose command
COMPOSER="docker-compose"
if ! command -v docker-compose &> /dev/null; then
    COMPOSER="docker compose"
fi

case "$COMMAND" in
    start)
        echo "Starting application via Docker Compose..."
        # We can call your existing script!
        ./scripts/run_container.sh up
        ;;
    stop)
        echo "Stopping application..."
        ./scripts/run_container.sh down
        ;;
    logs)
        echo "Tailing application logs..."
        ./scripts/run_container.sh logs
        ;;
    db)
        # Handle database migration commands
        DB_COMMAND="${2:-}" # Get the second argument (init, migrate, etc.)
        if [ -z "$DB_COMMAND" ]; then
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
    *)
        echo "Error: Unknown command '$COMMAND'"
        usage
        ;;
esac