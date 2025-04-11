#!/bin/bash
# Start the MCP PostgreSQL server

echo "Installing MCP dependencies..."
pip install -r mcp-requirements.txt

echo "Starting MCP PostgreSQL server..."
python -m app.mcp.server
