#!/bin/bash
# A pre-commit hook to check for forbidden words like DEBUG or FIXME in staged files.

set -euo pipefail

# --- Configuration ---
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

KEYWORDS_PATTERN="FIXME|DEBUG"
# A simple, space-separated list of filenames to completely ignore.
FILES_TO_EXCLUDE="pre-commit-hook.sh config.py"
# Known legitimate uses of keywords to exclude from the check.
EXCEPTIONS_PATTERN="logging.DEBUG"

echo -e "${YELLOW}--- Running Pre-Commit Hook: Checking for forbidden words ---${NC}"

# --- Main Logic ---
# This script now works in two stages:
# 1. Get a list of all staged files.
# 2. Filter out the excluded files to create a final list to check.
# 3. Grep ONLY the final list.

# Get all staged files
STAGED_FILES=$(git diff --cached --name-only --diff-filter=ACM)
if [ -z "$STAGED_FILES" ]; then
    echo -e "${GREEN}✅ No Python/Shell files staged. Skipping check.${NC}"
    exit 0
fi

FILES_TO_CHECK=""
for FILE_PATH in $STAGED_FILES; do
    # Get just the filename from the path
    FILENAME=$(basename "$FILE_PATH")
    # Assume we will check the file...
    SHOULD_CHECK=true
    # ...unless its name is in the exclusion list.
    for EXCLUDED_FILE in $FILES_TO_EXCLUDE; do
        if [ "$FILENAME" == "$EXCLUDED_FILE" ]; then
            SHOULD_CHECK=false
            break
        fi
    done

    if $SHOULD_CHECK; then
        FILES_TO_CHECK+="$FILE_PATH "
    fi
done

# If there are no files left to check, exit successfully.
if [ -z "$FILES_TO_CHECK" ]; then
    echo -e "${GREEN}✅ All staged files are excluded. Checks passed.${NC}"
    exit 0
fi

# Run the check ONLY on the filtered list of files.
# The '|| true' prevents the script from exiting if grep finds no matches.
FORBIDDEN_LINES=$(echo $FILES_TO_CHECK | xargs --no-run-if-empty grep --with-filename --line-number -E "$KEYWORDS_PATTERN" | grep -v -E "$EXCEPTIONS_PATTERN" || true)

# Check if the final list of forbidden lines is non-empty.
if [ -n "$FORBIDDEN_LINES" ]; then
    echo -e "\n${RED}COMMIT REJECTED:${NC} Found forbidden words ('$KEYWORDS_PATTERN') in the following files:"
    echo -e "${RED}------------------------------------------------------------${NC}"
    echo "$FORBIDDEN_LINES"
    echo -e "${RED}------------------------------------------------------------${NC}"
    echo "Please remove these words or add an exception to the pre-commit hook script."
    exit 1
else
    echo -e "${GREEN}✅ All checks passed. Proceeding with commit.${NC}"
    exit 0
fi