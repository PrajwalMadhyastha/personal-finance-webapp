#!/bin/bash
# This script finds all .sh files in the scripts/ directory and runs shellcheck on them.
# It exits with a non-zero status code if any script fails the linting check.

set -euo pipefail

# ANSI color codes for better output
RED='\033[0;31m'
GREEN='\033[0;32m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

echo -e "${CYAN}--- Running ShellCheck on all scripts in the 'scripts/' directory ---${NC}"

# Use 'find' to locate all files ending in .sh within the scripts/ directory.
# The script's own path is determined to avoid it linting itself if run from outside the root.
SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
SCRIPT_FILES=$(find "$SCRIPT_DIR" -type f -name "*.sh")

if [ -z "$SCRIPT_FILES" ]; then
    echo -e "${GREEN}No shell scripts found to lint.${NC}"
    exit 0
fi

# Run shellcheck on all found files. The '-x' flag tells shellcheck to follow
# any sourced scripts as well.
# We use a variable to track the overall exit code.
EXIT_CODE=0
shellcheck -x $SCRIPT_FILES || EXIT_CODE=$?

# Report the final status based on the exit code of the shellcheck command.
if [ $EXIT_CODE -eq 0 ]; then
    echo -e "\n${GREEN}✅ All scripts passed the ShellCheck analysis!${NC}"
else
    echo -e "\n${RED}❌ Some scripts have issues. Please review the ShellCheck output above.${NC}"
fi

# Exit with the code from shellcheck, which is crucial for CI/CD pipelines.
exit $EXIT_CODE