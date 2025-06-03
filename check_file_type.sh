#!/bin/bash

# Script to check if a given path is a file, directory, or something else.

# 1. Check if exactly one argument was provided.
if [ "$#" -ne 1 ]; then
    echo "Usage: $0 <path>"
    exit 1
fi

# Assign the first argument to a variable for better readability
TARGET_PATH="$1"

# 2. Check if the provided path is a regular file, a directory, or something else.
if [ -f "$TARGET_PATH" ]; then
    echo "$TARGET_PATH is a regular file."
elif [ -d "$TARGET_PATH" ]; then
    echo "$TARGET_PATH is a directory."
else
    echo "$TARGET_PATH is something else or does not exist."
fi

exit 0