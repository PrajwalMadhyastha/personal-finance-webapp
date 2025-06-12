#!/bin/bash
# Creates a compressed tar.gz archive of the application source code for release,
# excluding development-related files and directories.

set -euo pipefail

# --- Configuration & Argument Check ---
# ANSI color codes for better output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

if [ "$#" -ne 1 ]; then
    echo -e "${RED}Usage: $0 <version-number>${NC}"
    echo "Example: ./scripts/create_release.sh v1.0.0"
    exit 1
fi

VERSION="$1"
# The name of the project root directory
PROJECT_DIR_NAME=$(basename "$PWD")
OUTPUT_FILE="${PROJECT_DIR_NAME}-${VERSION}.tar.gz"

# --- List of files and directories to exclude ---
EXCLUDE_PATTERNS=(
    "--exclude='.git'"
    "--exclude='.venv'"
    "--exclude='*/__pycache__'"
    "--exclude='instance'"
    "--exclude='infra'"
    "--exclude='*.pyc'"
    "--exclude='*.db'"
    "--exclude='.env'"
    "--exclude='terraform.tfstate*'"
    "--exclude='${OUTPUT_FILE}'" # Exclude the output file itself
)

echo -e "${YELLOW}--- Creating Release Archive ---${NC}"
echo "Version: $VERSION"
echo "Output file: $OUTPUT_FILE"
echo "--------------------------------"

# --- Main Logic ---
# Use tar to create the gzipped archive.
# -c: create
# -z: gzip compression
# -v: verbose (list files as they are added)
# -f: specify the output filename
# The final '.' means "archive the current directory"
tar -czvf "$OUTPUT_FILE" "${EXCLUDE_PATTERNS[@]}" .

echo "--------------------------------"
echo -e "${GREEN}✅ Successfully created release archive: $OUTPUT_FILE${NC}"