#!/bin/bash

# A script to build, tag, and push the application's Docker image to GHCR.
# This version pushes the image as a user-scoped package.

set -e

# --- CONFIGURATION ---
# Update this variable with your GitHub username (all lowercase)
GITHUB_USERNAME="prajwalmadhyastha"
# This will be the name of your package on GitHub
IMAGE_NAME="personal-finance-app"


# --- DYNAMIC PATHS & TAGS ---
SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
PROJECT_ROOT="$SCRIPT_DIR/.."
GIT_VERSION=$(git rev-parse --short HEAD)


# --- SCRIPT LOGIC ---
echo "--- Building the Docker image: $IMAGE_NAME ---"
# Build from the project root. Caching is now enabled for faster builds.
docker build -t $IMAGE_NAME "$PROJECT_ROOT"


# --- CONSTRUCT THE FULL GHCR TAG ---
# Using the simple format: ghcr.io/OWNER/IMAGE_NAME
FULL_IMAGE_NAME="ghcr.io/$GITHUB_USERNAME/$IMAGE_NAME"

echo "\n--- Tagging image for GHCR ---"
docker tag $IMAGE_NAME "$FULL_IMAGE_NAME:latest"
docker tag $IMAGE_NAME "$FULL_IMAGE_NAME:$GIT_VERSION"
echo "Tagged as: $FULL_IMAGE_NAME:latest and :$GIT_VERSION"


echo "\n--- Pushing images to GHCR ---"
docker push "$FULL_IMAGE_NAME:latest"
docker push "$FULL_IMAGE_NAME:$GIT_VERSION"


echo "\n--- Push successful! ---"
echo "View your package at: https://github.com/users/$GITHUB_USERNAME/packages/container/package/$IMAGE_NAME"