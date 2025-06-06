#!/bin/bash

# Script to process categories from a file and demonstrate nested loops.

INPUT_FILE="sample_categories.txt"

# Check if the input file exists
if [ ! -f "$INPUT_FILE" ]; then
    echo "Error: Input file '$INPUT_FILE' not found."
    echo "Please create it with one expense category per line."
    exit 1
fi

echo "--- Processing Categories from $INPUT_FILE ---"

# Use a while read loop to read the file line by line
# The `|| [[ -n "$category_line" ]]` part handles the case where the last line might not have a newline
while IFS= read -r category_line || [[ -n "$category_line" ]]; do
    # Basic processing: Print the category found
    echo "Found category: $category_line"

    # Stretch Goal: Print the category name three times using a for loop
    echo "  Repeating '$category_line' three times:"
    # Option 1: Iterating over a fixed list of numbers
    for i in 1 2 3; do
    # Option 2: Using sequence expression (Bash 3.0+)
    # for i in {1..3}; do
    # Option 3: C-style for loop
    # for (( j=1; j<=3; j++ )); do
        echo "    -> $category_line (Repetition $i)" # Using $i or $j from the loop
    done
    echo # Add a blank line for better readability between categories

done < "$INPUT_FILE"

echo "--- Finished processing all categories. ---"

exit 0