#!/bin/bash
# An enhanced management script for the Flask application and its services.
set -euo pipefail

# --- Color Codes ---
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

# --- Function to load .env file reliably ---
load_env() {
    if [ -f .env ]; then
        set -a
        source ./.env
        set +a
    else
        echo -e "${RED}Error: .env file not found. Please run './scripts/setup_env.sh' first.${NC}"
        exit 1
    fi
}

# --- USAGE FUNCTION ---
usage() {
    echo -e "${YELLOW}Usage: $0 {command}${NC}"
    echo ""
    echo "Local Environment Commands:"
    echo -e "  ${CYAN}start-db${NC}        : Starts the database container."
    echo -e "  ${CYAN}create-db${NC}       : Creates the application database inside the container."
    echo -e "  ${CYAN}start-app${NC}       : Builds and starts the web application."
    echo -e "  ${CYAN}stop-app${NC}        : Stops the web application container."
    echo -e "  ${CYAN}restart-app${NC}     : Restarts the web application container."
    echo -e "  ${CYAN}down${NC}            : Stops and removes all services."
    echo -e "  ${CYAN}logs [service]${NC}  : Tails logs. Service: 'app' or 'db'. Default: 'app'."
    echo ""
    echo "Management Commands:"
    echo -e "  ${CYAN}shell${NC}           : Opens a shell inside the running webapp container."
    echo -e "  ${CYAN}db <cmd> [msg]${NC}  : Runs a database command (migrate, upgrade)."
    echo -e "  ${CYAN}promote <email>${NC}  : Promotes a user to an admin."
    echo -e "  ${CYAN}demote <email>${NC}   : Demotes an admin to a regular user."
    exit 1
}

# --- MAIN LOGIC ---
if [ -z "$1" ]; then
    usage
fi

load_env

if [ -z "${DB_SA_PASSWORD:-}" ] || [ -z "${DB_NAME:-}" ]; then
    echo -e "${RED}Error: DB_SA_PASSWORD or DB_NAME is not set in your .env file.${NC}"
    exit 1
fi

COMPOSER="docker-compose"
if ! command -v docker-compose &> /dev/null; then
    if docker compose version &> /dev/null; then
        COMPOSER="docker compose"
    else
        echo -e "${RED}Error: Neither 'docker-compose' nor 'docker compose' found.${NC}"
        exit 1
    fi
fi

cd "$(dirname "$0")/.."

# --- Command Routing ---
case "$1" in
    start-db)
        echo -e "${GREEN}--- Starting database container... ---${NC}"
        $COMPOSER up -d db
        ;;
    
    create-db)
        echo -e "${YELLOW}--- Waiting for SQL Server to be ready... ---${NC}"
        SERVER_READY=false
        for i in {1..30}; do
            if $COMPOSER exec -T db /opt/mssql-tools18/bin/sqlcmd -S localhost -U sa -P "$DB_SA_PASSWORD" -Q "SELECT 1" -C -N &> /dev/null; then
                echo -e "\n${GREEN}SQL Server is ready.${NC}"
                SERVER_READY=true
                break
            fi
            echo -n "."
            sleep 2
        done
        
        if ! $SERVER_READY; then
            echo -e "\n${RED}Error: SQL Server did not become ready in time.${NC}"
            exit 1
        fi
        
        echo -e "${CYAN}--- Creating database: $DB_NAME ---${NC}"
        $COMPOSER exec -T db /opt/mssql-tools18/bin/sqlcmd \
            -S localhost -U sa -P "$DB_SA_PASSWORD" -C -N \
            -Q "IF DB_ID(N'$DB_NAME') IS NULL CREATE DATABASE [$DB_NAME];"
        echo -e "${GREEN}✅ Database created or already exists.${NC}"
        ;;

    start-app)
        echo -e "${GREEN}--- Building and starting webapp... ---${NC}"
        if [[ " ${@} " =~ " --build " ]]; then
            $COMPOSER up -d --build webapp
        else
            $COMPOSER up -d webapp
        fi
        ;;
    stop-app)
        echo -e "${YELLOW}--- Stopping webapp container... ---${NC}"
        $COMPOSER stop webapp
        ;;
    restart-app)
        echo -e "${YELLOW}--- Restarting webapp container... ---${NC}"
        $COMPOSER restart webapp
        ;;
    down)
        echo -e "${RED}--- Stopping and removing all services... ---${NC}"
        $COMPOSER down -v
        ;;
    logs)
        SERVICE="${2:-webapp}"
        echo -e "${GREEN}--- Tailing ${SERVICE} logs (Ctrl+C to stop)... ---${NC}"
        $COMPOSER logs -f "$SERVICE"
        ;;
    shell)
        echo -e "${CYAN}--- Opening a shell inside the webapp container... ---${NC}"
        $COMPOSER exec webapp bash
        ;;
    db)
        # --- THIS IS THE FIX ---
        echo -e "${GREEN}--- Ensuring webapp container is running... ---${NC}"
        $COMPOSER up -d webapp
        # --- END OF FIX ---
        
        shift
        if [ -z "$@" ]; then
            echo -e "${RED}Error: 'db' command requires a subcommand (e.g., migrate, upgrade).${NC}"
            usage
        fi
        echo -e "${CYAN}--- Running database command: flask db $@ ---${NC}"
        $COMPOSER exec webapp flask db "$@"
        ;;
    promote)
        EMAIL="${2:-}"
        if [ -z "$EMAIL" ]; then
            echo -e "${RED}Error: 'promote' command requires a user email.${NC}"
            usage
        fi
        echo -e "${CYAN}--- Promoting user: $EMAIL ---${NC}"
        $COMPOSER exec webapp python scripts/set_admin_status.py "$EMAIL" true
        ;;
    demote)
        EMAIL="${2:-}"
        if [ -z "$EMAIL" ]; then
            echo -e "${RED}Error: 'demote' command requires a user email.${NC}"
            usage
        fi
        echo -e "${CYAN}--- Demoting user: $EMAIL ---${NC}"
        $COMPOSER exec webapp python scripts/set_admin_status.py "$EMAIL" false
        ;;
    *)
        echo -e "${RED}Error: Unknown command '$1'${NC}"
        usage
        ;;
esac