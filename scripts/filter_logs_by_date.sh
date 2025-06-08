#!/bin/bash

# --- Script to filter a log file based on a date range ---
# It reads a log file and outputs only the lines that fall
# within the specified start and end dates.

# 1. Check for the correct number of arguments.
if [ "$#" -ne 3 ]; then
    echo "Usage: $0 <start_date> <end_date> <logfile>"
    echo "  - Dates should be in 'YYYY-MM-DD' format."
    echo "Example: ./scripts/filter_logs_by_date.sh 2025-06-07 2025-06-08 sample.log"
    exit 1
fi

# 2. Assign arguments to descriptive variables.
START_DATE_STR="$1"
END_DATE_STR="$2"
LOG_FILE="$3"

# 3. Validate that the log file exists and is readable.
if [ ! -r "$LOG_FILE" ]; then
    echo "Error: Log file '$LOG_FILE' not found or is not readable."
    exit 1
fi

# --- Date to Epoch Conversion Function ---
# This handles the frustrating differences between macOS (BSD) and Linux (GNU) date commands.
date_to_epoch() {
    local date_str="$1"
    # Check if the operating system is macOS (Darwin)
    if [[ "$(uname)" == "Darwin" ]]; then
        # Use the macOS/BSD `date` command syntax
        date -j -f "%Y-%m-%d %T" "$date_str" "+%s" 2>/dev/null
    else
        # Use the Linux/GNU `date` command syntax
        date -d "$date_str" "+%s" 2>/dev/null
    fi
}

# 4. Convert start and end dates to epoch timestamps for easy numerical comparison.
# We append time to ensure the range is inclusive for the entire day.
START_EPOCH=$(date_to_epoch "${START_DATE_STR} 00:00:00")
# For the end date, we use 23:59:59 to include the entire day.
END_EPOCH=$(date_to_epoch "${END_DATE_STR} 23:59:59")

# Validate that the date conversion was successful.
if [ -z "$START_EPOCH" ] || [ -z "$END_EPOCH" ]; then
    echo "Error: Invalid date format. Please use YYYY-MM-DD."
    exit 1
fi

echo "Filtering logs from $START_DATE_STR to $END_DATE_STR..."
echo "-------------------------------------------------"

# --- 5. Process the Log File ---
# Read the file line by line to handle large files efficiently without loading all into memory.
while IFS= read -r line; do
    # This script assumes a log format like: "YYYY-MM-DD HH:MM:SS - MESSAGE"
    # Extract the timestamp part from the beginning of the line.
    # We grab the first two "words" (date and time).
    log_timestamp_str=$(echo "$line" | cut -d' ' -f1,2)
    
    # Convert the log entry's timestamp to an epoch integer.
    log_epoch=$(date_to_epoch "$log_timestamp_str")

    # If log_epoch is valid (not empty), perform the numerical comparison.
    if [[ -n "$log_epoch" ]]; then
        # 6. Check if the log entry's timestamp is within the specified range.
        if (( log_epoch >= START_EPOCH && log_epoch <= END_EPOCH )); then
            # If it is, print the entire matching line.
            echo "$line"
        fi
    fi
done < "$LOG_FILE"

echo "-------------------------------------------------"
echo "Log filtering complete."