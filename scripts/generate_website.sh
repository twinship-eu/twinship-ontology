#!/bin/bash

# Complete TwinShip Ontology Website Generation Pipeline
#
# This script generates a complete website for the TwinShip ontology including:
#   1. Comprehensive documentation (WIDOCO)
#   2. Interactive visualization (WebVOWL)
#   3. Combined landing page
#
# It orchestrates the full pipeline from modular sources to final website.
#
# Requirements:
#   - Python 3.9+ with rdflib (install: uv sync)
#   - Java 11+ (for WIDOCO)
#   - Node.js (optional, for local WebVOWL)
#
# Usage:
#   ./generate_website.sh [options]
#
# Options:
#   --source <file>        Source ontology file (default: model/twinship-core.ttl)
#   --output <dir>         Output directory (default: docs/website)
#   --skip-merge           Skip merge step (use existing complete file)
#   --skip-viz             Skip visualization conversion
#   --skip-widoco          Skip WIDOCO documentation generation
#   --skip-webvowl         Skip WebVOWL setup
#   --verbose              Verbose output
#   --help                 Show this help message

set -e  # Exit on error

# Default values
SOURCE="model/twinship-core.ttl"
OUTPUT_DIR="docs/website"
SKIP_MERGE=false
SKIP_VIZ=false
SKIP_WIDOCO=false
SKIP_WEBVOWL=false
VERBOSE=false
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(dirname "$SCRIPT_DIR")"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --source)
            SOURCE="$2"
            shift 2
            ;;
        --output)
            OUTPUT_DIR="$2"
            shift 2
            ;;
        --skip-merge)
            SKIP_MERGE=true
            shift
            ;;
        --skip-viz)
            SKIP_VIZ=true
            shift
            ;;
        --skip-widoco)
            SKIP_WIDOCO=true
            shift
            ;;
        --skip-webvowl)
            SKIP_WEBVOWL=true
            shift
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
            exit 1
            ;;
    esac
done

log() {
    if [ "$VERBOSE" = true ]; then
        echo -e "${BLUE}[INFO]${NC} $1"
    fi
}

step() {
    echo -e "\n${CYAN}▶ $1${NC}"
}

success() {
    echo -e "${GREEN}✓ $1${NC}"
}

error() {
    echo -e "${RED}✗ $1${NC}"
}

# Convert to absolute paths
cd "$REPO_ROOT"
SOURCE_ABS="$(pwd)/$SOURCE"
OUTPUT_ABS="$(pwd)/$OUTPUT_DIR"

echo "════════════════════════════════════════════════════════════════════"
echo "  TwinShip Ontology Website Generator"
echo "════════════════════════════════════════════════════════════════════"
echo ""
echo "Configuration:"
echo "  Source:      $SOURCE_ABS"
echo "  Output:      $OUTPUT_ABS"
echo ""

# Create build directory for intermediate files
mkdir -p "$REPO_ROOT/build"

# Step 1: Merge modules
SOURCE_BASENAME=$(basename "${SOURCE%.ttl}")
COMPLETE_FILE="$REPO_ROOT/build/${SOURCE_BASENAME}-complete.ttl"
if [ "$SKIP_MERGE" = false ]; then
    step "Step 1: Merging modular ontology into single file"
    log "Running: uv run python scripts/merge_modules.py --catalog model/catalog-v001.xml $SOURCE $COMPLETE_FILE"
    
    uv run python scripts/merge_modules.py --catalog model/catalog-v001.xml "$SOURCE" "$COMPLETE_FILE" || {
        error "Failed to merge modules"
        exit 1
    }
    success "Merged ontology created: $COMPLETE_FILE"
else
    log "Skipping merge step (using existing: $COMPLETE_FILE)"
fi

# Step 2: Generate visualization-friendly version
VIZ_FILE="${COMPLETE_FILE%.ttl}-viz.ttl"
if [ "$SKIP_VIZ" = false ]; then
    step "Step 2: Converting to visualization-friendly format"
    log "Running: uv run python scripts/generate_viz_ontology.py --auto $COMPLETE_FILE"
    
    uv run python scripts/generate_viz_ontology.py --auto "$COMPLETE_FILE" || {
        error "Failed to generate viz ontology"
        exit 1
    }
    success "Visualization ontology created: $VIZ_FILE"
else
    log "Skipping viz conversion (using existing: $VIZ_FILE)"
fi

# Step 2.5: Generate documentation-only version (TwinShip classes only)
DOCS_FILE="${COMPLETE_FILE%.ttl}-docs.ttl"
DOCS_VIZ_FILE="${DOCS_FILE%.ttl}-viz.ttl"
CLEAN_VIZ_FILE="${VIZ_FILE%.ttl}-clean.ttl"

step "Step 2.5: Creating documentation-only ontology (TwinShip classes only)"
log "Running: uv run python scripts/generate_docs_ontology.py -o $DOCS_FILE $COMPLETE_FILE"

uv run python scripts/generate_docs_ontology.py -o "$DOCS_FILE" "$COMPLETE_FILE" || {
    error "Failed to generate docs ontology"
    exit 1
}

# Generate docs-viz WITHOUT virtual properties (so WIDOCO shows single properties with multiple domains)
uv run python scripts/generate_viz_ontology.py --no-virtual-properties --auto "$DOCS_FILE" || {
    error "Failed to generate docs viz ontology"

    exit 1
}
success "Documentation ontology created: $DOCS_VIZ_FILE"

# Step 2.6: Clean the visualization ontology (remove external ontologies for WebVOWL)
step "Step 2.6: Cleaning visualization ontology for WebVOWL"
log "Running: uv run python scripts/generate_docs_ontology.py -o $CLEAN_VIZ_FILE $VIZ_FILE"

uv run python scripts/generate_docs_ontology.py -o "$CLEAN_VIZ_FILE" "$VIZ_FILE" || {
    error "Failed to clean viz ontology"
    exit 1
}
success "Clean visualization ontology created: $CLEAN_VIZ_FILE"

# Step 2.7: Strip external parent relationships for clean WebVOWL
step "Step 2.7: Stripping external parent relationships (IDO) from visualization"
MINIMAL_VIZ_FILE="${CLEAN_VIZ_FILE%.ttl}-minimal.ttl"
log "Running: uv run python scripts/strip_for_webvowl.py $CLEAN_VIZ_FILE $MINIMAL_VIZ_FILE"

uv run python scripts/strip_for_webvowl.py "$CLEAN_VIZ_FILE" "$MINIMAL_VIZ_FILE" || {
    error "Failed to strip external relationships"
    exit 1
}
success "Minimal visualization ontology created: $MINIMAL_VIZ_FILE"

# Use minimal viz file for WebVOWL generation
WEBVOWL_SOURCE="$MINIMAL_VIZ_FILE"

# Step 3: Generate WIDOCO documentation
if [ "$SKIP_WIDOCO" = false ]; then
    step "Step 3: Generating documentation with WIDOCO"
    
    WIDOCO_OUTPUT="$OUTPUT_ABS/documentation"
    log "Running: uv run python scripts/generate_widoco_docs.py -o $WIDOCO_OUTPUT $DOCS_VIZ_FILE"
    
    uv run python scripts/generate_widoco_docs.py -o "$WIDOCO_OUTPUT" "$DOCS_VIZ_FILE" || {
        error "Failed to generate WIDOCO documentation"
        exit 1
    }
    success "WIDOCO documentation created: $WIDOCO_OUTPUT"
    
    # Step 3.5: Enhance HTML with additional annotation properties (SKOS, dcterms:description)
    step "Step 3.5: Enhancing documentation with SKOS and dcterms annotations"
    log "Running: uv run python scripts/enhance_widoco_html.py $WIDOCO_OUTPUT/index-en.html $DOCS_VIZ_FILE"
    
    uv run python scripts/enhance_widoco_html.py "$WIDOCO_OUTPUT/index-en.html" "$DOCS_VIZ_FILE" || {
        error "Failed to enhance HTML (continuing anyway)"
    }
    success "Enhanced documentation with additional annotations"
else
    log "Skipping WIDOCO documentation"
fi

# Step 4: Generate WebVOWL visualization using WIDOCO
if [ "$SKIP_WEBVOWL" = false ]; then
    step "Step 4: Generating WebVOWL visualization with WIDOCO"
    
    WEBVOWL_TEMP_OUTPUT="$OUTPUT_ABS/webvowl_temp"
    # Use the MINIMAL viz file with virtual properties, no external ontologies, and no IDO parent relationships
    log "Running: uv run python scripts/generate_widoco_docs.py -o $WEBVOWL_TEMP_OUTPUT $WEBVOWL_SOURCE"
    
    uv run python scripts/generate_widoco_docs.py -o "$WEBVOWL_TEMP_OUTPUT" "$WEBVOWL_SOURCE" || {
        error "Failed to generate WebVOWL"
        exit 1
    }
    
    # Step 4.5: Replace WIDOCO's embedded WebVOWL with clean visualization
    step "Step 4.5: Replacing WIDOCO embedded WebVOWL with clean visualization"
    
    if [ -d "$WEBVOWL_TEMP_OUTPUT/webvowl" ] && [ -d "$OUTPUT_ABS/documentation/webvowl" ]; then
        # Replace the entire webvowl folder
        rm -rf "$OUTPUT_ABS/documentation/webvowl"
        cp -r "$WEBVOWL_TEMP_OUTPUT/webvowl" "$OUTPUT_ABS/documentation/webvowl" || {
            error "Failed to copy WebVOWL folder"
        }
        
        # Clean up temp output
        rm -rf "$WEBVOWL_TEMP_OUTPUT"
        
        # WebVOWL replacement complete - datatype properties will show their specific XSD types
        success "WebVOWL visualization replaced with clean version"
    else
        log "Skipping WIDOCO WebVOWL replacement (folders not found)"
    fi
else
    log "Skipping WebVOWL setup"
fi

# Step 5: Create landing page
step "Step 5: Creating website landing page"

cat > "$OUTPUT_ABS/index.html" << 'EOF'
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>TwinShip Ontology - Documentation & Visualization</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 40px 20px;
        }
        .header {
            text-align: center;
            color: white;
            margin-bottom: 50px;
        }
        h1 {
            font-size: 3em;
            font-weight: 700;
            margin-bottom: 15px;
            text-shadow: 0 2px 4px rgba(0,0,0,0.2);
        }
        .subtitle {
            font-size: 1.3em;
            opacity: 0.95;
            font-weight: 300;
        }
        .cards {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 30px;
            margin-bottom: 40px;
        }
        .card {
            background: white;
            border-radius: 12px;
            padding: 30px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
            transition: transform 0.3s, box-shadow 0.3s;
        }
        .card:hover {
            transform: translateY(-5px);
            box-shadow: 0 15px 40px rgba(0,0,0,0.3);
        }
        .card-icon {
            font-size: 3em;
            margin-bottom: 15px;
        }
        h2 {
            color: #667eea;
            margin-bottom: 15px;
            font-size: 1.5em;
        }
        p {
            color: #666;
            margin-bottom: 20px;
        }
        .button {
            display: inline-block;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 12px 30px;
            text-decoration: none;
            border-radius: 8px;
            font-weight: 500;
            transition: opacity 0.3s;
        }
        .button:hover {
            opacity: 0.9;
        }
        .features {
            background: rgba(255,255,255,0.95);
            border-radius: 12px;
            padding: 30px;
            margin-top: 30px;
        }
        .features h3 {
            color: #667eea;
            margin-bottom: 20px;
        }
        .feature-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
        }
        .feature-item {
            padding: 15px;
            background: #f8f9fa;
            border-radius: 8px;
            border-left: 4px solid #667eea;
        }
        .feature-item strong {
            color: #667eea;
            display: block;
            margin-bottom: 5px;
        }
        footer {
            text-align: center;
            color: white;
            margin-top: 50px;
            padding: 20px;
            opacity: 0.9;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>TwinShip Ontology</h1>
            <p class="subtitle">Digital Twin Ontology for Maritime Vessels</p>
        </div>
        
        <div class="cards">
            <div class="card">
                <div class="card-icon">📚</div>
                <h2>Documentation</h2>
                <p>Comprehensive HTML documentation generated with WIDOCO including class hierarchies, property details, cross-references, and UML diagrams.</p>
                <a href="documentation/index-en.html" class="button">View Documentation →</a>
            </div>
            
            <div class="card">
                <div class="card-icon">🌐</div>
                <h2>Interactive Visualization</h2>
                <p>Explore the ontology structure with WebVOWL's interactive force-directed graph. Filter, zoom, and navigate through classes and properties.</p>
                <a href="visualization/index.html" class="button">Launch Visualization →</a>
            </div>
        </div>
        
        <div class="features">
            <h3>TwinShip Ontology Features</h3>
            <div class="feature-grid">
                <div class="feature-item">
                    <strong>Modular Architecture</strong>
                    Foundation (base) + domain modules (engine, hull)
                </div>
                <div class="feature-item">
                    <strong>Standards-Based</strong>
                    Built on IDO (ISO 15926-14), QUDT, and OWL 2
                </div>
                <div class="feature-item">
                    <strong>Comprehensive Coverage</strong>
                    Vessels, propulsion, engines, fuel, sensors, weather
                </div>
                <div class="feature-item">
                    <strong>Restriction Patterns</strong>
                    Precise cardinality and value constraints
                </div>
            </div>
        </div>
        
        <footer>
            <p>TwinShip Ontology | Version 0.0.1</p>
            <p style="font-size: 0.9em; margin-top: 10px;">Generated with WIDOCO & WebVOWL</p>
        </footer>
    </div>
</body>
</html>
EOF

success "Landing page created: $OUTPUT_ABS/index.html"

# Final summary
echo ""
echo "════════════════════════════════════════════════════════════════════"
echo -e "${GREEN}✓ Website generation complete!${NC}"
echo "════════════════════════════════════════════════════════════════════"
echo ""
echo "Website location: $OUTPUT_ABS"
echo ""
echo "To view the website:"
echo "  1. Start local server (RECOMMENDED):"
echo "     cd \$(dirname \$0)/.. && ./serve_website.sh"
echo "     Then open: http://localhost:8000"
echo ""
echo "  2. Or manually:"
echo "     cd $OUTPUT_DIR && python -m http.server 8000"
echo "     Then open: http://localhost:8000"
echo ""
echo "Contents:"
echo "  • Landing page:     $OUTPUT_ABS/index.html"
echo "  • Documentation:    $OUTPUT_ABS/documentation/index-en.html"
echo "  • WebVOWL:          $OUTPUT_ABS/documentation/webvowl/index.html"
echo ""
