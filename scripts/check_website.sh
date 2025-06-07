#!/bin/bash

# --- Script to check the HTTP status of a website ---
# It takes a URL as an argument and checks if it returns a 200 OK status code.

# 1. Check if exactly one argument (the URL) was provided.
if [ "$#" -ne 1 ]; then
    echo "Usage: $0 <URL>"
    echo "Example: ./scripts/check_website.sh https://www.google.com"
    exit 1
fi

# 2. Assign the URL argument to a variable for clarity.
TARGET_URL="$1"

echo "Checking website status for: $TARGET_URL"

# 3. Use curl to get ONLY the HTTP status code.
# -s: Silent mode (don't show progress meter or errors).
# -o /dev/null: Redirect the response body (the HTML content) to nowhere.
# -w "%{http_code}": This special flag tells curl to write out only the HTTP status code.
HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" "$TARGET_URL")

# Capture the exit code of the curl command itself.
# If curl can't even connect (e.g., DNS error), its exit code will be non-zero.
CURL_EXIT_CODE=$?

# 4. Check if the curl command itself failed.
if [ "$CURL_EXIT_CODE" -ne 0 ]; then
    echo "FAILURE: curl command failed. Could not reach the URL."
    echo "Please check the URL spelling or your network connection."
    exit 1
fi

# 5. Check if the HTTP status code is 200.
if [ "$HTTP_STATUS" -eq 200 ]; then
    echo "SUCCESS: $TARGET_URL is online and returned Status Code 200 OK."
    exit 0
else
    echo "FAILURE: $TARGET_URL is reachable but returned a non-200 status code: $HTTP_STATUS"
    exit 1
fi