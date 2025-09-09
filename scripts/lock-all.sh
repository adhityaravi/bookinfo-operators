#!/bin/bash
# Script to update uv.lock files for all charms
# This locks dependencies for all bookinfo charms at once

set -e

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CHARMS=("bookinfo-details-k8s" "bookinfo-ratings-k8s" "bookinfo-reviews-k8s" "bookinfo-productpage-k8s" "bookinfo-libs-k8s")

echo "🔒 Updating uv.lock files for all charms..."

for charm in "${CHARMS[@]}"; do
    CHARM_DIR="$REPO_ROOT/charms/$charm"
    if [ -d "$CHARM_DIR" ]; then
        echo "  Locking $charm..."
        cd "$CHARM_DIR"
        uv lock --upgrade --no-cache
        cd "$REPO_ROOT"
    else
        echo "  ⚠️  Warning: $CHARM_DIR not found, skipping..."
    fi
done

echo "✅ Lock update complete!"