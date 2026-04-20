#!/usr/bin/env bash
# Build the React frontend and prepare for deployment.
# Run this before deploying to Databricks Apps.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "=== Building frontend ==="
cd "$SCRIPT_DIR/frontend"

if [ ! -d "node_modules" ]; then
  echo "Installing dependencies..."
  npm install
fi

npm run build
echo "Frontend built to frontend/dist/"

echo ""
echo "=== Ready to deploy ==="
echo "Run these commands from the repo root (Lakebase-Workshop/):"
echo "  databricks bundle validate"
echo "  databricks bundle deploy --target dev"
