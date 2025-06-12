#!/bin/bash
# An interactive script to find a process by name and offer to show details or kill it.

set -euo pipefail

# --- Configuration & Argument Check ---
# ANSI color codes for better output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

if [ "$#" -ne 1 ]; then
    echo -e "${RED}Usage: $0 <process-name>${NC}"
    echo "Example: ./scripts/manage_process.sh 'Google Chrome'"
    exit 1
fi

PROCESS_NAME="$1"

# --- Find the Process ---
echo "🔎 Searching for processes matching '$PROCESS_NAME'..."

# Use pgrep to find PIDs. The output is stored in an array.
# The '|| true' prevents the script from exiting if pgrep finds no matches.
PIDS=($(pgrep -f "$PROCESS_NAME" || true))

# --- Handle Different Scenarios ---

# Case 1: No processes found
if [ ${#PIDS[@]} -eq 0 ]; then
    echo -e "${GREEN}✅ No running process found matching '$PROCESS_NAME'.${NC}"
    exit 0
fi

# Case 2: Multiple processes found
if [ ${#PIDS[@]} -gt 1 ]; then
    echo -e "${RED}❌ Found multiple processes matching '$PROCESS_NAME'. Please be more specific.${NC}"
    echo "Matching PIDs: ${PIDS[*]}"
    # Show brief details for all found PIDs to help the user
    ps -p "${PIDS[*]}"
    exit 1
fi

# Case 3: Exactly one process found
PID="${PIDS[0]}"
echo -e "${GREEN}✅ Found one matching process with PID: $PID${NC}"
ps -p "$PID" # Show brief details of the found process
echo ""

# --- User Interaction ---
# Prompt the user for their desired action.
# -n 1 means it will accept the first character and continue.
# -r prevents backslash interpretation.
read -p "Choose an action: [d]etails, [k]ill, or [c]ancel? " -n 1 -r
echo "" # Move to a new line after user input

# Use a case statement to handle the user's choice.
case $REPLY in
    [dD]) # Match lowercase 'd' or uppercase 'D'
        echo -e "\n${CYAN}--- Process Details for PID $PID ---${NC}"
        # Use ps with custom formatting for detailed output
        ps -o pid,user,%cpu,%mem,start,command -p "$PID"
        ;;
    [kK]) # Match lowercase 'k' or uppercase 'K'
        echo -e "\n${YELLOW}Terminating process $PID...${NC}"
        # Use kill command to terminate the process
        kill "$PID"
        echo -e "${GREEN}✅ Process $PID terminated.${NC}"
        ;;
    *)   # Any other input is treated as "cancel"
        echo -e "\nAction cancelled."
        ;;
esac

exit 0