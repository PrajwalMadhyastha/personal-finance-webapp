#!/bin/bash

# --- Script to simulate checking the status of a list of servers ---

# 1. Define an array of server hostnames.
# In a real-world scenario, this list might come from a file or an API call.
SERVERS=(
    "app-prod-01.centralindia.cloudapp.azure.com"
    "app-prod-02.centralindia.cloudapp.azure.com"
    "db-primary-01.centralindia.cloudapp.azure.com"
    "api-gateway.internal.finance.org"
    "cache-server-01.internal.finance.org"
    "failed-server.example.com" # A server we can imagine often fails
)

# 2. Create a function to check the status of a single server.
check_server_status() {
    # The function takes one argument: the hostname to check.
    local hostname="$1"

    # Check if a hostname was provided to the function.
    if [ -z "$hostname" ]; then
        echo "Error: No hostname provided to check_server_status function."
        return 1 # Return a non-zero status to indicate error
    fi

    # 3. Simulate a health check using a random number.
    # $RANDOM is a shell variable that gives a random number between 0 and 32767.
    # We'll use the modulo operator (%) to get a number between 0 and 9.
    # Let's simulate an 80% success rate (0-7 is pass, 8-9 is fail).
    
    local random_status=$(( RANDOM % 10 ))
    local status_message
    local return_code

    # -lt stands for "less than"
    if [ "$random_status" -lt 8 ]; then
        status_message="OK"
        return_code=0 # Success
    else
        status_message="FAILED"
        return_code=1 # Failure
    fi

    # Print the status in a nicely formatted way.
    # 'printf' gives us more control over formatting than 'echo'.
    printf "%-50s [%s]\n" "Checking status of $hostname..." "$status_message"
    
    return $return_code
}

# --- Main Script Logic ---
# Loop through the array of servers and check each one.

echo "--- Starting Server Health Checks ---"
echo "Timestamp: $(date)"
echo "-------------------------------------"

# Using "${SERVERS[@]}" is the standard way to iterate over all elements in an array.
# The quotes are important to handle any names with spaces correctly.
for server in "${SERVERS[@]}"; do
    # Call our function for each server.
    check_server_status "$server"
    # We could add logic here to handle a failure, e.g., send an alert.
done

echo "-------------------------------------"
echo "All server checks complete."