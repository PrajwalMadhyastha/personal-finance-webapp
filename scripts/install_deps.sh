#!/bin/bash
# Checks for required development tools and attempts to install them if missing.

set -euo pipefail

# --- Configuration ---
# ANSI color codes for better output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# An array of required commands to check for.
REQUIRED_TOOLS=("git" "docker" "tflint" "jq")

# A flag to track if all dependencies are met
ALL_DEPS_MET=true

echo -e "${CYAN}--- Checking for required development dependencies ---${NC}"

# --- OS Detection ---
OS=""
case "$(uname -s)" in
    Darwin)
        OS='macOS'
        ;;
    Linux)
        # Check for Debian/Ubuntu specifically
        if [ -f /etc/os-release ] && grep -q -E 'ID=ubuntu|ID=debian' /etc/os-release; then
            OS='Linux'
        else
            OS='Unsupported Linux'
        fi
        ;;
    *)
        OS='Unsupported'
        ;;
esac
echo "Detected OS: $OS"
echo "----------------------------------------------------"


# --- Dependency Check Loop ---
for tool in "${REQUIRED_TOOLS[@]}"; do
    if ! command -v "$tool" &> /dev/null; then
        # If a command is not found, set the flag to false
        ALL_DEPS_MET=false
        echo -e "${YELLOW}⚠️  '$tool' is not installed.${NC}"

        # Attempt to install based on OS
        case "$OS" in
            'macOS')
                if ! command -v brew &> /dev/null; then
                    echo -e "${RED}Error: Homebrew (brew) is not installed. Please install it to continue.${NC}"
                    break # Exit the loop if brew isn't present
                fi
                
                if [ "$tool" == "docker" ]; then
                    echo -e "   -> To install Docker on macOS, please download Docker Desktop or install Colima:"
                    echo -e "      ${CYAN}https://www.docker.com/products/docker-desktop/${NC}"
                else
                    read -p "   -> Attempt to install '$tool' with Homebrew? (y/n) " -n 1 -r
                    echo
                    if [[ $REPLY =~ ^[Yy]$ ]]; then
                        brew install "$tool"
                    fi
                fi
                ;;

            'Linux')
                if [ "$tool" == "docker" ]; then
                    echo -e "   -> To install Docker on Linux, please follow the official guide:"
                    echo -e "      ${CYAN}https://docs.docker.com/engine/install/ubuntu/${NC}"
                elif [ "$tool" == "tflint" ]; then
                     echo -e "   -> To install tflint on Linux, please follow the official guide:"
                     echo -e "      ${CYAN}https://github.com/terraform-linters/tflint#installation${NC}"
                else
                    read -p "   -> Attempt to install '$tool' with apt-get? (y/n) " -n 1 -r
                    echo
                    if [[ $REPLY =~ ^[Yy]$ ]]; then
                        sudo apt-get update && sudo apt-get install -y "$tool"
                    fi
                fi
                ;;

            *)
                echo -e "${RED}   -> Unsupported OS. Please install '$tool' manually.${NC}"
                ;;
        esac
        echo "----------------------------------------------------"
    else
        echo -e "${GREEN}✅ '$tool' is installed.${NC}"
    fi
done


# --- Final Summary ---
echo ""
if [ "$ALL_DEPS_MET" = true ]; then
    echo -e "${GREEN}🎉 All dependencies are installed!${NC}"
else
    echo -e "${YELLOW}🔔 Some dependencies were missing. Please review the output above and install any remaining tools manually.${NC}"
fi