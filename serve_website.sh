#!/bin/bash

# Script to serve the TwinShip Ontology website locally

PORT=8000
DIR="docs/website"

echo "════════════════════════════════════════════════════════════════════"
echo "  TwinShip Ontology - Local Web Server"
echo "════════════════════════════════════════════════════════════════════"
echo ""
echo "Starting server on port $PORT..."
echo ""
echo "URLs:"
echo "  • Main page:        http://localhost:$PORT/"
echo "  • Documentation:    http://localhost:$PORT/documentation/index-en.html"
echo "  • WebVOWL:          http://localhost:$PORT/documentation/webvowl/"
echo ""
echo "Press Ctrl+C to stop the server"
echo "════════════════════════════════════════════════════════════════════"
echo ""

cd "$DIR" && python3 -m http.server $PORT
