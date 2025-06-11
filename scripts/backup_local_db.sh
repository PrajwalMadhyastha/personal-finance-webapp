#!/bin/bash

# A simple script to create a timestamped backup of the local SQLite database.

# --- 1. Define Variables ---
# The source database file we want to back up.
SOURCE_DB="instance/finance.db"

# The directory where we will store the backups.
BACKUP_DIR="local_backups"


# --- Script Logic ---
echo "--- Starting Local Database Backup ---"

# Check if the source database file exists before proceeding.
if [ ! -f "$SOURCE_DB" ]; then
    echo "Error: Source database file not found at '$SOURCE_DB'"
    echo "Please ensure you are running this script from the project root."
    exit 1
fi

# 2. Check if the backup directory exists and create it if it doesn't.
# The '-p' flag tells mkdir to create parent directories as needed and
# prevents errors if the directory already exists.
echo "Checking for backup directory at '$BACKUP_DIR'..."
mkdir -p "$BACKUP_DIR"

# 3. Construct a unique backup filename with a timestamp.
# Format: YYYY-MM-DD_HHMMSS
TIMESTAMP=$(date +"%Y-%m-%d_%H%M%S")
BACKUP_FILENAME="finance_backup_${TIMESTAMP}.db"
FULL_BACKUP_PATH="${BACKUP_DIR}/${BACKUP_FILENAME}"

echo "Creating backup file: $FULL_BACKUP_PATH"

# 4. Use the 'cp' command to copy the source file to the backup path.
# The '-v' (verbose) flag makes 'cp' print a confirmation message.
cp -v "$SOURCE_DB" "$FULL_BACKUP_PATH"

# 5. Print a final success message.
echo ""
echo "--- Backup Successful! ---"
echo "Database backed up to: $FULL_BACKUP_PATH"