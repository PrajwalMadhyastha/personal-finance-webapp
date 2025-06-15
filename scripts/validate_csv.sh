#!/bin/bash
# Validates that a given CSV file has the correct header row for transaction imports.

set -euo pipefail

# --- Configuration & Color Codes ---
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# This is the exact header string we expect in the CSV file.
EXPECTED_HEADER="Date,Description,Amount,Account Name,Account Type,Category"

# --- Argument & File Checks ---
if [ "$#" -ne 1 ]; then
    echo -e "${RED}Usage: $0 <path-to-csv-file>${NC}"
    echo "Example: ./scripts/validate_csv.sh my_transactions.csv"
    exit 1
fi

FILE_PATH="$1"

if [ ! -f "$FILE_PATH" ]; then
    echo -e "${RED}Error: File not found at '$FILE_PATH'.${NC}"
    exit 1
fi

# --- Main Logic ---
echo -e "${YELLOW}--- Validating CSV Header for: $FILE_PATH ---${NC}"

# Read only the first line (the header) of the file.
# The 'tr -d "\r"' removes any potential carriage return characters for cross-platform compatibility.
ACTUAL_HEADER=$(head -n 1 "$FILE_PATH" | tr -d '\r')

# Compare the actual header with the expected header.
if [ "$ACTUAL_HEADER" == "$EXPECTED_HEADER" ]; then
    echo -e "${GREEN}✅ Success: The CSV header is valid.${NC}"
    exit 0
else
    echo -e "${RED}❌ Error: CSV header does not match.${NC}"
    echo "   Expected: \"$EXPECTED_HEADER\""
    echo "   Actual:   \"$ACTUAL_HEADER\""
    exit 1
fi