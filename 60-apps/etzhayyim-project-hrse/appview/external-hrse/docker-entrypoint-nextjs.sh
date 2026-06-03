#!/bin/bash
set -e

echo "Starting Next.js development server..."

# Ensure node_modules are installed (in case of volume mount override)
if [ ! -d "node_modules" ] || [ ! -f "node_modules/.pnpm/lock.yaml" ]; then
    echo "Installing dependencies..."
    pnpm install
fi

# Run Next.js dev server
exec pnpm dev

