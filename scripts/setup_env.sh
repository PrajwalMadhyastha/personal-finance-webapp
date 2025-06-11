#!/bin/bash
# A helper script to create the local .env configuration file from the example template.
set -euo pipefail

# --- DYNAMIC PATHS ---
# Get the directory where the script is located
SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
# Navigate up to the project root from the script's location
PROJECT_ROOT="$SCRIPT_DIR/.."

# Define the full paths for the files
ENV_FILE="$PROJECT_ROOT/.env"
EXAMPLE_FILE="$PROJECT_ROOT/.env.example"

# --- MAIN LOGIC ---

# First, ensure the example file actually exists.
if [ ! -f "$EXAMPLE_FILE" ]; then
    echo "❌ Error: The template file '.env.example' could not be found in the project root."
    echo "Please ensure the file exists before running this script."
    exit 1
fi

# Check if the real .env file already exists.
if [ -f "$ENV_FILE" ]; then
    echo "✅ Configuration file '.env' already exists. No action taken."
else
    echo "🔧 Configuration file '.env' not found. Creating one from the template..."
    # Copy the example file to create the real .env file
    cp "$EXAMPLE_FILE" "$ENV_FILE"
    echo "✅ Successfully created the '.env' file in your project root."
    echo ""
    echo "➡️  NEXT STEP: Open the new '.env' file and fill in your actual database credentials and a secret key."
fi