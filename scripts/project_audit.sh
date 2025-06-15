#!/bin/bash
# A script to perform various quality and health checks on the project codebase.

set -euo pipefail

# --- Color Codes & Helpers ---
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

print_header() {
    echo ""
    echo -e "${YELLOW}=====================================================${NC}"
    echo -e "${YELLOW}  $1${NC}"
    echo -e "${YELLOW}=====================================================${NC}"
}

# --- Check Functions ---

check_large_files() {
    echo "Searching for files larger than 1MB..."
    
    # This now also excludes the .terraform directory
    local large_files
    large_files=$(find . -type f -size +1M \
        -not \( -path "./.git/*" -o -path "./.venv/*" -o -path "*/__pycache__/*" -o -path "./instance/*" -o -path "./.terraform/*" \) || true)

    if [ -z "$large_files" ]; then
        echo -e "${GREEN}✅ No large files found (outside of ignored directories).${NC}"
    else
        echo -e "${RED}Found large files that should probably be added to .gitignore:${NC}"
        echo "$large_files"
    fi
}

find_todos() {
    echo "Searching for action items like TODO: and FIXME:..."

    # IMPROVED: 
    # -I ignores binary files.
    # --exclude excludes the script itself.
    local action_items
    action_items=$(grep -rniE 'TODO:|FIXME:' . \
        -I \
        --exclude-dir=".git" \
        --exclude-dir=".venv" \
        --exclude-dir="__pycache__" \
        --exclude-dir="instance" \
        --exclude="project_audit.sh" || true)

    if [ -z "$action_items" ]; then
        echo -e "${GREEN}✅ No pending action items found.${NC}"
    else
        echo -e "${RED}Found pending action items:${NC}"
        echo "$action_items" | sed 's/^/  /'
    fi
}

# --- Main Execution ---
cd "$(dirname "$0")/.."

print_header "Project Code Audit"
check_large_files
find_todos

echo ""
echo -e "${GREEN}Audit complete.${NC}"