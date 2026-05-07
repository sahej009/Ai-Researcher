#!/usr/bin/env bash
# Exit on error
set -o errexit

echo "🔥 Bypassing Render Default Pip..."
pip install uv

echo "⚡ Installing dependencies at lightspeed..."
uv pip install --python /opt/render/project/src/.venv/bin/python -r render-reqs.txt

echo "✅ Build Complete!"