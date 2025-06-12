#!/bin/bash
# A script to scan the project for common keywords that might indicate hardcoded secrets.

set -euo pipefail

# --- Configuration ---
# ANSI color codes for readable output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Keywords to search for, separated by a pipe '|' for the grep regex.
# Add more keywords here as needed (e.g., |private_key|aws_access).
KEYWORDS_PATTERN="password|secret|api_key|token|credentials"

# Directories to exclude from the scan.
EXCLUDE_DIRS=(".git" ".venv" "__pycache__" "node_modules" "*.db" "*.sqlite3")

echo -e "${YELLOW}--- Scanning for potential hardcoded secrets ---${NC}"
echo "Searching for keywords: $KEYWORDS_PATTERN"
echo "Excluding directories: ${EXCLUDE_DIRS[*]}"
echo "----------------------------------------------------"

# --- Build the grep command ---
# Start with the base grep command
GREP_CMD="grep -r -i -n -E '$KEYWORDS_PATTERN' ."

# Dynamically add --exclude-dir for each item in the EXCLUDE_DIRS array
for dir in "${EXCLUDE_DIRS[@]}"; do
    GREP_CMD+=" --exclude-dir='$dir'"
done

# --- Execute the Scan ---
# We use 'eval' to correctly interpret the command string with all its quoted arguments.
# '|| true' ensures that the script doesn't exit with an error if grep finds no matches.
SCAN_RESULTS=$(eval "$GREP_CMD" || true)

# --- Report Results ---
if [ -n "$SCAN_RESULTS" ]; then
    echo -e "${RED}POTENTIAL SECRETS FOUND:${NC}"
    echo "$SCAN_RESULTS"
    echo "----------------------------------------------------"
    echo -e "${YELLOW}Warning: Review the lines above carefully. Not all findings may be actual secrets.${NC}"
    # Exit with a non-zero status to indicate findings, useful for CI/CD systems
    exit 1
else
    echo -e "${GREEN}✅ No potential secrets found.${NC}"
    exit 0
fi