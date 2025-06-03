#!/bin/bash

# Script to process expenses from a file and optionally ask for amounts.

INPUT_FILE="sample_expenses.txt"

# Check if the input file exists
if [ ! -f "$INPUT_FILE" ]; then
    echo "Error: Input file '$INPUT_FILE' not found."
    echo "Please create it with one expense description per line."
    exit 1
fi

echo "--- Processing Expenses from $INPUT_FILE ---"

# Use a while read loop to read the file line by line
# The `|| [[ -n "$line" ]]` part handles the case where the last line might not have a newline
while IFS= read -r line || [[ -n "$line" ]]; do
    # Basic processing: Print the description
    echo "Processing expense: $line"

    # Stretch Goal: Ask for the amount for this specific expense
    # Use command substitution with 'read' to capture input
    # -p prompts the user with the string
    # -r prevents backslashes from being interpreted
    read -p "Enter amount for '$line': $" expense_amount

    # You can then do something with the amount, e.g., print it
    if [[ -n "$expense_amount" ]]; then
        echo "  -> Amount entered for '$line': $expense_amount"
    else
        echo "  -> No amount entered for '$line'."
    fi
    echo # Add a blank line for better readability between expenses

done < "$INPUT_FILE"

echo "--- Finished processing all expenses. ---"

exit 0