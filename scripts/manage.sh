#!/bin/bash
# An enhanced management script for the Flask application and its services.
set -euo pipefail

# --- Color Codes ---
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

# --- USAGE FUNCTION ---
usage() {
    echo -e "${YELLOW}Usage: $0 {command}${NC}"
    echo ""
    echo "Commands:"
    echo -e "  ${CYAN}start-db${NC}        : Starts only the database container in the background. (Run once)."
    echo -e "  ${CYAN}start-app${NC}       : Builds and starts the web application in the background."
    echo -e "  ${CYAN}stop-app${NC}        : Stops only the web application container."
    echo -e "  ${CYAN}restart-app${NC}     : Restarts the web application container."
    echo -e "  ${CYAN}down${NC}            : Stops and removes all containers and networks."
    echo -e "  ${CYAN}logs [service]${NC}  : Tails the logs. Service can be 'app' or 'db'. Default is 'app'."
    echo -e "  ${CYAN}shell${NC}           : Opens a bash shell inside the running webapp container."
    echo -e "  ${CYAN}db <cmd> [msg]${NC}  : Runs a database command (migrate, upgrade, etc.)."
    exit 1
}

# --- MAIN LOGIC ---
if [ -z "$1" ]; then
    usage
fi

# --- Find Docker Compose command ---
COMPOSER="docker-compose"
if ! command -v docker-compose &> /dev/null; then
    if docker compose version &> /dev/null; then
        COMPOSER="docker compose"
    else
        echo -e "${RED}Error: Neither 'docker-compose' nor 'docker compose' found.${NC}"
        exit 1
    fi
fi
# Change to project root to ensure docker-compose commands work
cd "$(dirname "$0")/.."

# --- Command Routing ---
case "$1" in
    start-db)
        echo -e "${GREEN}--- Starting database container in the background... ---${NC}"
        $COMPOSER up -d db
        echo "Database service started. It may take several minutes to become healthy."
        echo "Check status with: docker ps"
        ;;
    start-app)
        echo -e "${GREEN}--- Building and starting webapp container... ---${NC}"
        $COMPOSER up -d --build webapp
        echo -e "${GREEN}✅ Web application is running in the background.${NC}"
        echo -e "   -> Use './scripts/manage.sh logs' to see the output."
        ;;
    stop-app)
        echo -e "${YELLOW}--- Stopping webapp container... ---${NC}"
        $COMPOSER stop webapp
        ;;
    restart-app) # <-- NEW COMMAND
        echo -e "${YELLOW}--- Restarting webapp container (stopping, rebuilding, and starting)... ---${NC}"
        $COMPOSER restart webapp
        echo -e "${GREEN}✅ Web application restarted.${NC}"
        #$COMPOSER stop webapp
        #$COMPOSER up -d --build webapp
        #echo -e "${GREEN}✅ Web application has been restarted in the background.${NC}"
        ;;
    down)
        echo -e "${RED}--- Stopping and removing all containers, networks, and volumes... ---${NC}"
        $COMPOSER down -v
        ;;
    logs)
        SERVICE="${2:-app}"
        if [ "$SERVICE" == "app" ]; then
            echo -e "${GREEN}--- Tailing webapp logs (Press Ctrl+C to stop)... ---${NC}"
            $COMPOSER logs -f webapp
        elif [ "$SERVICE" == "db" ]; then
            echo -e "${GREEN}--- Tailing database logs (Press Ctrl+C to stop)... ---${NC}"
            $COMPOSER logs -f db
        else
            echo -e "${RED}Unknown service '$SERVICE'. Use 'app' or 'db'.${NC}"
        fi
        ;;
    shell)
        echo -e "${CYAN}--- Opening a shell inside the webapp container... ---${NC}"
        $COMPOSER exec webapp bash
        ;;
    db)
    DB_COMMAND="${2:-}"
    if [ -z "$DB_COMMAND" ]; then
        echo -e "${RED}Error: 'db' command requires a subcommand.${NC}"
        usage
    fi
    echo -e "${CYAN}--- Running database command: flask db $DB_COMMAND ---${NC}"

    # This now ensures the container is running WITHOUT forcing a rebuild.
    echo "Ensuring webapp container is running..."
    $COMPOSER up -d webapp

    echo "Executing command..."
    $COMPOSER exec -e FLASK_APP=run.py webapp flask db "${@:2}"

    echo -e "${GREEN}Database command finished.${NC}"
    ;;
esac