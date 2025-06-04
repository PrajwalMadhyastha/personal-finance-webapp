#!/bin/bash

# Script to demonstrate getopts for command-line argument parsing.

# Initialize variables for our options
VERBOSE_MODE=false
FILENAME=""

# The optstring "vf:" tells getopts:
# - 'v' is a simple boolean option (no argument).
# - 'f' is an option that requires an argument (indicated by the ':').
# If the optstring started with a ':', getopts would handle missing option arguments
# by setting OPTION to ':' and OPTARG to the option character.
# Without the leading ':', getopts prints its own error message for missing args
# and sets OPTION to '?' (like an illegal option). For this example, we'll let it do that.

while getopts "vf:" OPTION; do
  case "$OPTION" in
    v)
      VERBOSE_MODE=true
      ;;
    f)
      FILENAME="$OPTARG" # OPTARG contains the argument for the option
      ;;
    \?) # Handles unknown options or options missing required arguments (if optstring doesn't start with ':')
      echo "Error: Invalid option or missing argument." >&2
      # getopts already prints an error message, so this is additional context if needed.
      # exit 1 # You might want to exit if an invalid option is critical
      ;;
    # If optstring started with ':', you'd also handle ':' for missing arguments specifically:
    # :)
    #   echo "Error: Option -$OPTARG requires an argument." >&2
    #   exit 1
    #   ;;
  esac
done

# Shift the processed options out of the argument list
# OPTIND is the index of the next argument to be processed.
shift $((OPTIND - 1))

# Now, $@ contains only the non-option arguments (positional arguments)

# Display the parsed options and remaining arguments
echo "--- Parsed Options ---"
echo "Verbose mode: $VERBOSE_MODE"
if [ -n "$FILENAME" ]; then
  echo "Filename: $FILENAME"
else
  echo "Filename: Not specified"
fi

echo ""
echo "--- Remaining Positional Arguments ---"
if [ "$#" -gt 0 ]; then
  echo "Number of remaining arguments: $#"
  COUNT=1
  for ARG in "$@"; do
    echo "Argument $COUNT: $ARG"
    COUNT=$((COUNT + 1))
  done
else
  echo "No positional arguments remaining."
fi

exit 0