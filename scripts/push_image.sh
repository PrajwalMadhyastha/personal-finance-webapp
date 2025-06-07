#!/bin/bash

# A script to build and push the image to GHCR, using the repository name as the package name.
set -e

# --- CONFIGURATION ---
# The username and the package name are now consistent.
GITHUB_USERNAME="prajwalmadhyastha"
IMAGE_NAME="personal-finance-webapp" # This now matches your repo name


# --- DYNAMIC PATHS & TAGS ---
SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_source[0]}" )" &> /dev/null && pwd )
PROJECT_ROOT="$SCRIPT_DIR/.."
GIT_VERSION=$(git rev-parse --short HEAD)


# --- SCRIPT LOGIC ---
echo "--- Building the Docker image: $IMAGE_NAME ---"
docker build -t $IMAGE_NAME "$PROJECT_ROOT"


# --- CONSTRUCT THE FULL GHCR TAG ---
# Using the format: ghcr.io/OWNER/IMAGE_NAME
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