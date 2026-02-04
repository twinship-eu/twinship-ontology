#!/bin/bash

# TwinShip Ontology Documentation Generation Pipeline
#
# This script generates complete documentation from modular ontology sources.
# It performs the following steps:
#   1. Merge all modules into a single complete ontology
#   2. Convert restrictions to domain/range for better visualization
#   3. Generate HTML documentation using LODE or Widoco
#
# Requirements:
#   - Python 3.7+ with rdflib
#   - LODE (https://github.com/essepuntato/LODE) or
#   - Widoco (https://github.com/dgarijo/Widoco)
#
# Usage:
#   ./generate_docs.sh [options]
#
# Options:
#   --tool <lode|widoco>   Documentation tool to use (default: auto-detect)
#   --source <file>        Source ontology file (default: model/twinship-core.ttl)
#   --output <dir>         Output directory (default: docs/ontology)
#   --verbose              Verbose output
#   --help                 Show this help message

set -e  # Exit on error

# Default values
TOOL="auto"
SOURCE="model/twinship-core.ttl"  # Uses aggregate ontology (imports base + modules)
OUTPUT_DIR="docs/ontology"
VERBOSE=false
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(dirname "$SCRIPT_DIR")"
BUILD_DIR="$REPO_ROOT/build"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --tool)
            TOOL="$2"
            shift 2
            ;;
        --source)
            SOURCE="$2"
            shift 2
            ;;
        --output)
            OUTPUT_DIR="$2"
            shift 2
            ;;
        --verbose)
            VERBOSE=true
            shift
            ;;
        --help)
            grep '^#' "$0" | grep -v '#!/bin/bash' | sed 's/^# \?//'
            exit 0
            ;;
        *)
            echo -e "${RED}Error: Unknown option $1${NC}"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# Verbose logging
log() {
    if [ "$VERBOSE" = true ]; then
        echo -e "${BLUE}[INFO]${NC} $1"
    fi
}

step() {
    echo -e "${GREEN}==>${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1" >&2
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# Change to repo root
cd "$REPO_ROOT"

# Verify source file exists
if [ ! -f "$SOURCE" ]; then
    error "Source file not found: $SOURCE"
    exit 1
fi

# Create build and output directories
mkdir -p "$BUILD_DIR"
mkdir -p "$OUTPUT_DIR"

# Step 1: Merge modules
step "Step 1/3: Merging ontology modules..."
SOURCE_BASENAME=$(basename "${SOURCE%.ttl}")
COMPLETE_FILE="$BUILD_DIR/${SOURCE_BASENAME}-complete.ttl"
log "Output: $COMPLETE_FILE"

MERGE_CMD="python scripts/merge_modules.py"
[ "$VERBOSE" = true ] && MERGE_CMD="$MERGE_CMD --verbose"
$MERGE_CMD "$SOURCE" "$COMPLETE_FILE"

if [ ! -f "$COMPLETE_FILE" ]; then
    error "Failed to create merged ontology"
    exit 1
fi

echo -e "  ${GREEN}✓${NC} Created: $COMPLETE_FILE"

# Step 2: Generate visualization-friendly version
step "Step 2/3: Converting to visualization-friendly format..."
VIZ_FILE="${COMPLETE_FILE%.ttl}-viz.ttl"
log "Output: $VIZ_FILE"

VIZ_CMD="python scripts/generate_viz_ontology.py"
[ "$VERBOSE" = true ] && VIZ_CMD="$VIZ_CMD --verbose"
$VIZ_CMD "$COMPLETE_FILE" "$VIZ_FILE"

if [ ! -f "$VIZ_FILE" ]; then
    error "Failed to create visualization ontology"
    exit 1
fi

echo -e "  ${GREEN}✓${NC} Created: $VIZ_FILE"

# Step 3: Generate documentation
step "Step 3/3: Generating HTML documentation..."

# Auto-detect tool if needed
if [ "$TOOL" = "auto" ]; then
    if command -v widoco &> /dev/null; then
        TOOL="widoco"
        log "Auto-detected: Widoco"
    elif command -v lode &> /dev/null; then
        TOOL="lode"
        log "Auto-detected: LODE"
    else
        warning "No documentation tool found (LODE or Widoco)"
        warning "Please install one of:"
        echo "  - LODE: https://github.com/essepuntato/LODE"
        echo "  - Widoco: https://github.com/dgarijo/Widoco"
        warning "Skipping documentation generation"
        warning "You can still use the generated files:"
        echo "  - Complete ontology: $COMPLETE_FILE"
        echo "  - Visualization version: $VIZ_FILE"
        exit 0
    fi
fi

# Generate documentation based on tool
case $TOOL in
    lode)
        log "Using LODE"
        lode -i "$VIZ_FILE" -o "$OUTPUT_DIR/index.html"
        ;;
    widoco)
        log "Using Widoco"
        widoco -ontFile "$VIZ_FILE" -outFolder "$OUTPUT_DIR" -getOntologyMetadata -rewriteAll
        ;;
    *)
        error "Unknown documentation tool: $TOOL"
        error "Supported tools: lode, widoco"
        exit 1
        ;;
esac

echo -e "  ${GREEN}✓${NC} Documentation created in: $OUTPUT_DIR"

# Summary
echo ""
step "Documentation generation complete!"
echo ""
echo "Generated files:"
echo "  📄 Merged ontology:      $COMPLETE_FILE"
echo "  📄 Visualization format: $VIZ_FILE"
echo "  📁 Documentation:        $OUTPUT_DIR"
echo ""
echo "View documentation:"
echo "  open $OUTPUT_DIR/index.html"
echo ""
