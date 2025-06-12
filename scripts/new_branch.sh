#!/bin/bash
# A helper script to safely create and switch to a new git branch.
# It prevents creating a branch if one with the same name already exists.

set -euo pipefail

# --- Argument Check ---
# Ensure exactly one argument (the branch name) is provided.
if [ "$#" -ne 1 ]; then
    echo "Usage: $0 <branch-name>"
    echo "Example: ./scripts/new_branch.sh feature/user-profile-page"
    exit 1
fi

BRANCH_NAME="$1"

# --- Main Logic ---

# Check if a branch with the given name already exists locally.
# The 'git branch --list' command will output the branch name if it exists.
# We check if the output of that command is non-empty.
if [ -n "$(git branch --list "$BRANCH_NAME")" ]; then
    # If the branch exists, print an error and exit.
    echo "❌ Error: A branch named '$BRANCH_NAME' already exists."
    echo "Please choose a different name."
    exit 1
else
    # If the branch does not exist, create it and switch to it.
    echo "✅ Branch '$BRANCH_NAME' does not exist. Creating and switching to it..."
    git checkout -b "$BRANCH_NAME"
    echo "🚀 Switched to a new branch '$BRANCH_NAME'."
fi