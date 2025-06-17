#!/bin/bash
# A helper script to start an interactive git rebase to squash commits.

set -euo pipefail

# --- Color Codes ---
RED='\033[0;31m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

# --- Main Logic ---

# 1. Check if an argument was provided.
if [ -z "$1" ]; then
    echo -e "${RED}Error: You must provide the number of commits to rebase.${NC}"
    echo -e "${YELLOW}Usage: $0 <number_of_commits>${NC}"
    echo -e "Example: ./scripts/git_squash.sh 3  (to edit the last 3 commits)"
    exit 1
fi

# 2. Check if the argument is a valid positive number.
if ! [[ "$1" =~ ^[1-9][0-9]*$ ]]; then
    echo -e "${RED}Error: The argument must be a positive number.${NC}"
    exit 1
fi

COMMIT_COUNT=$1

echo -e "${CYAN}--- Starting interactive rebase for the last $COMMIT_COUNT commits... ---${NC}"
echo "Your default editor will open. Change 'pick' to 'squash' or 'fixup' for the commits you want to merge."

# 3. Execute the git rebase command.
git rebase -i "HEAD~$COMMIT_COUNT"