#!/bin/bash
# A pre-commit hook to check for forbidden words like DEBUG or FIXME in staged files.

set -euo pipefail

# --- Configuration ---
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

KEYWORDS_PATTERN="FIXME|DEBUG"
# A pattern of script filenames to exclude from the check
SCRIPTS_TO_EXCLUDE="pre-commit-hook.sh|project_audit.sh"
# Known legitimate uses of the keywords to exclude
EXCEPTIONS_PATTERN="logging.DEBUG"

echo -e "${YELLOW}--- Running Pre-Commit Hook: Checking for forbidden words ---${NC}"

# --- Main Logic ---
# Find files with forbidden words, then filter out the known exceptions.
FORBIDDEN_FILES=$(git diff --cached --name-only --diff-filter=ACM \
    | grep -v -E "scripts/($SCRIPTS_TO_EXCLUDE)" \
    | xargs --no-run-if-empty grep --with-filename --line-number -E "$KEYWORDS_PATTERN" \
    | grep -v -E "$EXCEPTIONS_PATTERN" || true)

# Check if the final list of files is non-empty.
if [ -n "$FORBIDDEN_FILES" ]; then
    echo -e "\n${RED}COMMIT REJECTED:${NC} Found forbidden words ('$KEYWORDS_PATTERN') in the following files:"
    echo -e "${RED}------------------------------------------------------------${NC}"
    echo "$FORBIDDEN_FILES"
    echo -e "${RED}------------------------------------------------------------${NC}"
    echo "Please remove these words or add an exception to the pre-commit hook script."
    exit 1
else
    echo -e "${GREEN}✅ All checks passed. Proceeding with commit.${NC}"
    exit 0
fi