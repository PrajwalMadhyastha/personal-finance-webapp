#!/bin/bash
# A pre-commit hook to check for forbidden words like DEBUG or FIXME in staged files.

set -euo pipefail

# --- Configuration ---
# Use extended grep to search for multiple patterns.
# The '|' acts as an OR. Add more forbidden words here if needed.
FORBIDDEN_PATTERN="FIXME|DEBUG"
# ANSI color codes for better output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}--- Running Pre-Commit Hook: Checking for forbidden words ---${NC}"

# --- Main Logic ---
# Find all staged files that are text-based (added, copied, or modified).
# Then, use grep to search within them for the forbidden pattern.
# 'git diff --cached' lists changes staged for commit.
# '--name-only' gives us just the filenames.
# '--diff-filter=ACM' filters for Added, Copied, or Modified files.
# 'xargs --no-run-if-empty' passes these filenames to grep.
# 'grep --with-filename --line-number --color=always' makes the output very clear.
FORBIDDEN_FILES=$(git diff --cached --name-only --diff-filter=ACM | grep -v "scripts/pre-commit-hook.sh" | xargs --no-run-if-empty grep --with-filename --line-number -E "$FORBIDDEN_PATTERN" || true)

# Check if the grep command found any matching files.
if [ -n "$FORBIDDEN_FILES" ]; then
    echo -e "\n${RED}COMMIT REJECTED:${NC} Found forbidden words ('$FORBIDDEN_PATTERN') in the following files:"
    echo -e "${RED}------------------------------------------------------------${NC}"
    echo "$FORBIDDEN_FILES" # Print the detailed grep output
    echo -e "${RED}------------------------------------------------------------${NC}"
    echo "Please remove these words before committing."
    exit 1 # Exit with a non-zero status to abort the commit
else
    echo -e "${GREEN}✅ All checks passed. Proceeding with commit.${NC}"
    exit 0 # Exit with status 0 to allow the commit
fi