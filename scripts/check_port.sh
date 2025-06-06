#!/bin/bash

# --- Script to check if a specific TCP port is open on a host ---

# 1. Check if exactly two arguments were provided.
if [ "$#" -ne 2 ]; then
    echo "Usage: $0 <hostname_or_ip> <port>"
    echo "Example: ./check_port.sh google.com 443"
    exit 1
fi

# 2. Assign arguments to descriptive variables.
HOST="$1"
PORT="$2"

# 3. Add validation to ensure the port is a number.
if ! [[ "$PORT" =~ ^[0-9]+$ ]] || [ "$PORT" -lt 1 ] || [ "$PORT" -gt 65535 ]; then
    echo "Error: Port ('$PORT') must be a valid number between 1 and 65535."
    exit 1
fi

echo "Checking connection to $HOST on port $PORT..."

# 4. Use the nc (netcat) command to perform the check.
#    -z: Zero-I/O mode (scanning). Makes nc report status without sending data.
#    -w 3: Sets a timeout of 3 seconds for the connection attempt.
#    We redirect stdout and stderr ('>/dev/null 2>&1') because we only care about
#    the exit code, not the command's output.
nc -z -w 3 "$HOST" "$PORT" >/dev/null 2>&1

# 5. Check the exit status of the last command ($?).
#    'nc' returns an exit code of 0 if the port is open, and 1 if it is closed or unreachable.
if [ "$?" -eq 0 ]; then
    echo "SUCCESS: Port $PORT is open on $HOST."
    exit 0
else
    echo "FAILED: Port $PORT is closed or host is unreachable on $HOST."
    exit 1
fi