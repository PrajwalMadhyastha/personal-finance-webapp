#!/bin/bash
# A script to run all local quality checks (linting and testing).

# Exit immediately if any command fails
set -e

# --- Color Codes for better output ---
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${YELLOW}--- Running Linter (flake8)... ---${NC}"
# Run the linter on your main application directory
flake8 finance_tracker/

echo -e "\n${YELLOW}--- Running Test Suite (pytest)... ---${NC}"
# Run the full test suite
pytest

# If the script reaches this point, all previous commands have succeeded
echo -e "\n${GREEN}✅ All local checks passed! You are ready to commit.${NC}"