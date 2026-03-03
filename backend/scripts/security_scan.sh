#!/bin/bash
# Run Bandit security scan on the Shadow backend
set -e

cd "$(dirname "$0")/.."

echo "=== Shadow Security Scan (Bandit) ==="
echo ""

bandit -r app/ -c .bandit.yml -ll -ii

echo ""
echo "=== Scan complete ==="
