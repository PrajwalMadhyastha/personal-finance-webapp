#!/bin/bash

# Function to set up a directory
setup_directory() {
    local dir_name="$1" # Assign argument to a local variable for clarity

    # Check if a directory name was provided to the function
    if [ -z "$dir_name" ]; then
        echo "Function error: No directory name provided to setup_directory."
        return 1 # Indicate failure
    fi

    # 1. Check if a directory with that name already exists
    if [ -d "$dir_name" ]; then
        echo "Info: Directory '$dir_name' already exists."
        return 1 # Indicate "failure" in terms of not creating it anew, or a specific status
                 # Depending on strictness, you might choose a different return code or message.
    fi

    # 2. If it doesn't exist, try to create the directory
    echo "Attempting to create directory '$dir_name'..."
    mkdir "$dir_name"

    # 3. Check mkdir's exit status
    if [ "$?" -ne 0 ]; then
        echo "Error: Could not create directory '$dir_name'. Check permissions or path."
        return 1 # Indicate failure
    fi

    # 4. If mkdir was successful
    echo "Successfully created directory '$dir_name'."
    return 0 # Indicate success
}

# --- Main part of the script ---

# 1. Check if the user provided exactly one argument
if [ "$#" -ne 1 ]; then
    echo "Usage: $0 <directory_name>"
    exit 1
fi

TARGET_DIRECTORY_NAME="$1"

echo "--- Starting Directory Setup ---"
# 2. Call your setup_directory function
setup_directory "$TARGET_DIRECTORY_NAME"

# 3. Check the exit status of the setup_directory function call
function_exit_status="$?"

if [ "$function_exit_status" -ne 0 ]; then
    echo "Final status: Directory setup failed for '$TARGET_DIRECTORY_NAME'."
    exit 1 # Exit script with failure status
else
    echo "Final status: Directory setup successful for '$TARGET_DIRECTORY_NAME'."
    exit 0 # Exit script with success status
fi