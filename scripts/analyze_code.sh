#!/bin/bash

# A script to perform a simple static analysis of the Python code
# in the finance_tracker directory.

set -e # Exit immediately if any command fails

# Define the directory to analyze.
TARGET_DIR="finance_tracker"

# Check if the target directory exists.
if [ ! -d "$TARGET_DIR" ]; then
    echo "Error: Directory '$TARGET_DIR' not found."
    echo "Please run this script from the project's root directory."
    exit 1
fi

echo "--- Running Code Analysis on '$TARGET_DIR' directory ---"
echo ""

# --- CALCULATIONS ---

# 1. Use 'find' to locate all .py files and pipe to 'wc -l' to count them.
TOTAL_FILES=$(find "$TARGET_DIR" -type f -name "*.py" | wc -l | xargs)

# 2. Use 'find' and 'xargs' with 'wc -l' to count lines in all files.
#    'tail -n 1' gets the "total" line from wc's output.
#    'awk' prints the first field (the number).
TOTAL_LINES=$(find "$TARGET_DIR" -type f -name "*.py" | xargs wc -l | tail -n 1 | awk '{print $1}')

# 3. Use 'find' and 'xargs' with 'cat' to stream all file content to 'grep'.
#    'grep -c' counts the number of matching lines.
#    '^\s*def ' matches lines that start with optional space, then 'def '.
TOTAL_FUNCTIONS=$(find "$TARGET_DIR" -type f -name "*.py" | xargs cat | grep -c '^\s*def ')

# 4. Same logic as above, but for class definitions.
TOTAL_CLASSES=$(find "$TARGET_DIR" -type f -name "*.py" | xargs cat | grep -c '^\s*class ')


# --- REPORTING ---
# Use 'printf' for nicely formatted, aligned output.
echo "Code Analysis Report:"
printf "%-25s %d\n" "Total Python files:" "$TOTAL_FILES"
printf "%-25s %d\n" "Total lines of code:" "$TOTAL_LINES"
printf "%-25s %d\n" "Total class definitions:" "$TOTAL_CLASSES"
printf "%-25s %d\n" "Total function definitions:" "$TOTAL_FUNCTIONS"
echo ""
echo "--- Analysis Complete ---"