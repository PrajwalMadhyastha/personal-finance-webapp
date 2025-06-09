#!/bin/bash

# A script to read a simple 'key=value' configuration file.

# 1. Check if a config file was provided as an argument.
if [ "$#" -ne 1 ]; then
    echo "Usage: $0 <path_to_config_file>"
    echo "Example: ./scripts/read_config.sh data/app.conf"
    exit 1
fi

CONFIG_FILE="$1"

# 2. Check if the file exists and is readable.
if [ ! -f "$CONFIG_FILE" ]; then
    echo "Error: Configuration file not found at '$CONFIG_FILE'"
    exit 1
fi

echo "--- Reading configuration from: $CONFIG_FILE ---"

# 3. Read the file line by line.
# The `while` loop is efficient for large files.
# `IFS=` and `-r` prevent trimming of whitespace and backslash interpretation.
while IFS= read -r line || [[ -n "$line" ]]; do
    # 4. Skip empty lines and lines that start with a '#' (comments).
    # This regex checks for lines that are either empty or start with optional
    # whitespace followed by a '#'.
    if [[ "$line" =~ ^\s*# || -z "$line" ]]; then
        continue
    fi

    # 5. Parse the key and value.
    # This uses parameter expansion to safely split the line at the first '='.
    key="${line%%=*}"
    value="${line#*=}"

    # 6. Trim leading/trailing whitespace from the key and value.
    # This is a common way to trim whitespace in bash.
    key_trimmed=$(echo "$key" | xargs)
    value_trimmed=$(echo "$value" | xargs)
    
    # 7. Print the result.
    echo "Found: Key='${key_trimmed}', Value='${value_trimmed}'"

done < "$CONFIG_FILE"

echo "--- Finished reading configuration. ---"