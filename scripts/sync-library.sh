#!/bin/bash
# Script to synchronize the bookinfo_lib across all charms
# This maintains a single source of truth while keeping charms self-contained

set -e

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
LIB_SOURCE="$REPO_ROOT/charms/bookinfo-libs-k8s/lib/charms/bookinfo_lib"
CHARMS=("bookinfo-details-k8s" "bookinfo-ratings-k8s" "bookinfo-reviews-k8s" "bookinfo-productpage-k8s")

for charm in "${CHARMS[@]}"; do
    DEST="$REPO_ROOT/charms/$charm/lib/charms/bookinfo_lib"
    echo "  Syncing to $charm..."
    
    # Remove existing library
    rm -rf "$DEST"
    
    # Copy the library
    mkdir -p "$(dirname "$DEST")"
    cp -r "$LIB_SOURCE" "$DEST"
done

echo "Library sync complete!"
