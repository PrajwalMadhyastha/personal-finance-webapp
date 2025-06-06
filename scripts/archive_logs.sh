#!/bin/bash

# --- Script to find and archive old log files ---
# This script archives .log files older than a specified number of days
# from a target directory into a compressed tarball.

# --- 1. Error Checking for Arguments ---

# Check if exactly two arguments were provided.
if [ "$#" -ne 2 ]; then
    echo "Usage: $0 <target_directory> <days_old>"
    echo "Example: ./archive_logs.sh /var/log/my_app 30"
    exit 1
fi

# --- 2. Assign Arguments to Variables ---

TARGET_DIR="$1"
DAYS_OLD="$2"

# --- 3. Additional Input Validation ---

# Check if the target directory actually exists.
if [ ! -d "$TARGET_DIR" ]; then
    echo "Error: Directory '$TARGET_DIR' does not exist."
    exit 1
fi

# Check if DAYS_OLD is a valid number.
if ! [[ "$DAYS_OLD" =~ ^[0-9]+$ ]]; then
    echo "Error: Days old ('$DAYS_OLD') must be a positive integer."
    exit 1
fi

# --- 4. Find the Files to Archive ---

echo "Searching for .log files older than $DAYS_OLD days in '$TARGET_DIR'..."

# Use find to locate files based on the criteria.
# -type f: Only find files.
# -name "*.log": Only files ending with .log.
# -mtime +$DAYS_OLD: Only files modified more than DAYS_OLD days ago.
# The `find` command is robust and its output will be piped to tar.
# We use -print0 to handle filenames with spaces or special characters safely.
FILES_FOUND=$(find "$TARGET_DIR" -type f -name "*.log" -mtime +"$DAYS_OLD")

# Check if any files were found before proceeding.
if [ -z "$FILES_FOUND" ]; then
    echo "No log files found to archive."
    exit 0
fi

# --- 5. Create the Archive ---

# Create a unique filename for the archive based on the current date and time.
ARCHIVE_FILENAME="log_archive_$(date +%Y-%m-%d_%H-%M-%S).tar.gz"

echo "The following files will be archived into '$ARCHIVE_FILENAME':"
# Print the list of files that will be archived.
echo "$FILES_FOUND"
echo # Add a blank line for readability

# Pipe the output of find to tar using xargs.
# find ... -print0: Prints the full file path followed by a null character. This is the safest way to handle filenames.
# xargs -0: Reads null-terminated input. This ensures files with spaces or special characters are handled correctly.
# tar -czvf:
#   c: create a new archive
#   z: compress the archive with gzip
#   v: verbose (list files as they are processed)
#   f: specifies the archive filename
find "$TARGET_DIR" -type f -name "*.log" -mtime +"$DAYS_OLD" -print0 | xargs -0 tar -czvf "$ARCHIVE_FILENAME"

# Check the exit status of the tar command to confirm success.
if [ "$?" -eq 0 ]; then
    echo ""
    echo "Archive '$ARCHIVE_FILENAME' created successfully."
else
    echo ""
    echo "Error: Archive creation failed."
    exit 1
fi

# --- 6. Optional: Delete Original Files (Use with caution!) ---
# After confirming the archive is created and valid, you might want to delete the original files.
# Uncomment the following lines to enable deletion.
# WARNING: Make sure your archive is being created correctly before enabling this.
# echo "Deleting original log files..."
# find "$TARGET_DIR" -type f -name "*.log" -mtime +"$DAYS_OLD" -print0 | xargs -0 rm
# echo "Original log files deleted."

exit 0