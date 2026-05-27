# TwinShip Ontology Scripts

This directory contains utility scripts for working with the TwinShip modular ontology.

## Overview

The TwinShip ontology uses a **modular architecture** with a **two-pipeline build process**:

### Modular Architecture
- **twinship-base.ttl** - Foundation ontology (base classes, properties)
- **twinship-core.ttl** - Complete aggregate (imports base + all modules)
- **modules/** - Domain-specific modules (vessel.ttl, weather-conditions.ttl, etc.)

### Two-Pipeline Build Process

The website generation uses separate optimized ontologies for documentation and visualization:

1. **Documentation Pipeline** (WIDOCO)
   - Source: `complete-docs-viz.ttl` 
   - Original properties with multiple domains (shown clearly in property tables)
   - TwinShip classes only + used external properties
   
2. **Visualization Pipeline** (WebVOWL)
   - Source: `complete-viz-clean-minimal.ttl`
   - Virtual properties with single domains (eliminates blank union nodes)
   - TwinShip + IDO classes only, no external parent relationships

This separation ensures comprehensive documentation while maintaining a clean, navigable visualization.

## Setup

**Prerequisites**: The merge script uses `model/catalog-v001.xml` to resolve TwinShip URIs to local files. The catalog is already configured with entries for `twinship-base`, `twinship-core`, and all modules.

### Install uv (recommended)

```bash
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Or with Homebrew
brew install uv

# Or with pip
pip install uv
```

### Install dependencies

```bash
# Using uv (fast, modern, recommended)
uv sync

# Or with traditional pip
pip install -r requirements.txt
```

## Quick Start: Website Generation

The complete workflow uses a **two-pipeline architecture** that generates documentation and visualization separately:

```bash
# One command generates everything
./scripts/generate_website.sh --verbose
```

### Two-Pipeline Architecture

The pipeline creates separate optimized ontologies for documentation and visualization:

**Pipeline 1: Documentation (WIDOCO)**
- Uses `complete-docs-viz.ttl` - TwinShip classes only, original properties with multiple domains
- Shows comprehensive property tables without confusion from virtual properties

**Pipeline 2: Visualization (WebVOWL)**  
- Uses `complete-viz-clean-minimal.ttl` - TwinShip + IDO classes, virtual properties, no external parents
- Clean graph without blank union nodes or external ontology clutter

### Build Process

The pipeline creates multiple intermediate files in `build/`:

1. **complete.ttl** - All modules merged
2. **complete-viz.ttl** - With virtual properties for clean visualization
3. **complete-docs.ttl** - TwinShip classes only (no external ontologies)
4. **complete-docs-viz.ttl** - Documentation-friendly (no virtual properties)
5. **complete-viz-clean.ttl** - Visualization-friendly (virtual properties, TwinShip+IDO only)
6. **complete-viz-clean-minimal.ttl** - Final WebVOWL source (no external parent relationships)

**Note**: Virtual properties are created for properties with multiple domains to eliminate blank union nodes in WebVOWL (e.g., `partOf_viz1`, `partOf_viz2` instead of single `partOf` with union domain).

## Scripts Overview

### Production Scripts (Primary Workflow)

These scripts form the main website generation pipeline:

- **`generate_website.sh`** - Master pipeline orchestrating the complete two-pipeline architecture
- **`merge_modules.py`** - Merge modular ontology files into single complete file
- **`generate_viz_ontology.py`** - Convert OWL restrictions to domain/range + create virtual properties
- **`generate_docs_ontology.py`** - Filter to TwinShip-only content (remove external ontologies)
- **`strip_for_webvowl.py`** - Remove external parent relationships and preserve annotations for clean WebVOWL graph
- **`generate_widoco_docs.py`** - Generate WIDOCO documentation with built-in OWL2VOWL
- **`enhance_widoco_html.py`** - Post-process WIDOCO HTML to add SKOS and dcterms annotations
- **`enhance_webvowl_json.py`** - Post-process WebVOWL JSON to add SKOS and dcterms annotations
- **`clean_webvowl_json.py`** - Post-process WebVOWL JSON to merge duplicate Literal nodes

### Legacy Scripts

- **`generate_docs.sh`** - Older documentation generation script (superseded by generate_website.sh)
- **`setup_webvowl.py`** - Legacy WebVOWL setup (superseded by WIDOCO's built-in converter)

### Development/Debug Scripts

These scripts were used during development and have been removed.

### generate_website.sh - Master Pipeline

**Complete two-pipeline website generation** - orchestrates documentation and visualization generation with optimized ontologies for each purpose.

**What it does:**

**Stage 1: Build Artifacts**
1. Merge all modules → `complete.ttl`
2. Add domain/range + virtual properties → `complete-viz.ttl`
3. Extract TwinShip entities → `complete-docs.ttl`
4. Generate doc-friendly version → `complete-docs-viz.ttl` (no virtual properties)
5. Clean viz ontology → `complete-viz-clean.ttl` (no external ontologies)
6. Strip external parents → `complete-viz-clean-minimal.ttl` (final WebVOWL source)

**Stage 2: Documentation Pipeline**
7. Generate WIDOCO documentation from `complete-docs-viz.ttl`
   - Shows original properties with multiple domains in property tables
   - Includes only TwinShip classes and used external properties
8. Enhance WIDOCO HTML with additional annotations
   - Post-processes HTML to add `skos:notation`, `skos:altLabel`, and `dcterms:description`
   - WIDOCO only displays a limited set of annotation properties by default

**Stage 3: Visualization Pipeline**
9. Generate WebVOWL with WIDOCO from `complete-viz-clean-minimal.ttl`
   - Uses virtual properties to eliminate blank union nodes
   - Shows only TwinShip (33) + IDO (3) classes for clean graph
10. Replace WIDOCO's embedded WebVOWL viewer with clean visualization
11. Enhance WebVOWL JSON with annotations
   - Post-processes WIDOCO-generated ontology.json to add custom annotations
   - Preserves all WebVOWL structure (IDs, types, links)
   - Adds `skos:notation`, `skos:altLabel`, `dcterms:description` to propertyAttribute objects
   - Annotations appear in WebVOWL sidebar when clicking properties

**Stage 4: Landing Page**
12. Create landing page linking to documentation and visualization

**Requirements:**
- Python 3.9+ with rdflib (install: `uv sync`)
- Java 11+ (for WIDOCO) — the build passes `-Dfile.encoding=UTF-8` to Java automatically, which is required on Windows to prevent WIDOCO writing `ontology.json` in cp1252 instead of UTF-8

**Usage:**

```bash
# Full website generation
./scripts/generate_website.sh --verbose

# Skip specific steps
./scripts/generate_website.sh --skip-merge --skip-viz

# Custom source and output
./scripts/generate_website.sh \
    --source model/twinship-core.ttl \
    --output docs/website \
    --verbose
```

**Output:**
- `build/*.ttl` - All intermediate ontology files
- `docs/website/index.html` - Landing page
- `docs/website/documentation/` - WIDOCO-generated documentation
- `docs/website/documentation/webvowl/` - Clean WebVOWL visualization


## Website Generation

### Overview

The TwinShip ontology uses **industry-standard tools** for documentation and visualization:

- **[WIDOCO](https://github.com/dgarijo/Widoco)** (WIzard for DOCumenting Ontologies) - Most complete documentation generator
  - Comprehensive HTML documentation with cross-references
  - Auto-generated UML diagrams
  - Full metadata and provenance support
  
- **[WebVOWL](http://vowl.visualdataweb.org/)** - Interactive graph visualization
  - Force-directed graph layout
  - Filter by class/property type
  - Search and export capabilities

### Quick Start

```bash
# Generate complete website (documentation + visualization + landing page)
./scripts/generate_website.sh

# View the result
open docs/website/index.html

# Or serve locally
../serve_website.sh
# Then open: http://localhost:8000
```

### Output Structure

```
build/                                          # Intermediate ontology files
├── twinship-core-complete.ttl                 # All modules merged
├── twinship-core-complete-viz.ttl             # With virtual properties
├── twinship-core-complete-docs.ttl            # TwinShip classes only
├── twinship-core-complete-docs-viz.ttl        # For documentation (no virtual props)
├── twinship-core-complete-viz-clean.ttl       # TwinShip+IDO only
└── twinship-core-complete-viz-clean-minimal.ttl # Final WebVOWL source

docs/website/
├── index.html                                  # Landing page
└── documentation/                              # WIDOCO output
    ├── index-en.html                          # Main documentation
    ├── sections/                              # Documentation sections
    ├── resources/                             # CSS, diagrams, images
    └── webvowl/                               # Clean WebVOWL visualization
        ├── index.html                         # WebVOWL viewer
        └── data/ontology.json                 # Graph data (38 nodes)
```

## Individual Script Documentation

### generate_widoco_docs.py - WIDOCO Documentation Generator

Generates comprehensive HTML documentation using WIDOCO with built-in OWL2VOWL for WebVOWL visualization.

**What it does:**
- Generates complete HTML documentation with cross-references, diagrams, and metadata
- Automatically generates WebVOWL visualization using WIDOCO's built-in OWL2VOWL converter
- Creates embedded WebVOWL viewer in documentation

**Requirements:**
- Java 11+ (WIDOCO jar downloaded automatically on first run)
- Python 3.9+ with rdflib

**Usage:**
```bash
# Generate documentation (includes embedded WebVOWL)
python scripts/generate_widoco_docs.py build/twinship-core-complete-docs-viz.ttl

# Custom output directory
python scripts/generate_widoco_docs.py -o docs/custom-docs build/twinship-core-complete-viz-clean.ttl

# Skip diagrams for faster generation
python scripts/generate_widoco_docs.py --no-diagram model.ttl
```

**Output:**
- `documentation/index-en.html` - Main documentation
- `documentation/webvowl/` - Embedded WebVOWL visualization
- `documentation/sections/` - Individual documentation sections

### enhance_widoco_html.py - WIDOCO HTML Enhancer

Post-processes WIDOCO-generated HTML to add additional annotation properties that WIDOCO doesn't display by default.

**What it does:**
- Adds `skos:notation` (e.g., IMO codes like "IMO0654") to property definitions
- Adds `skos:altLabel` (alternative labels) to property definitions
- Adds `dcterms:description` (detailed descriptions) to property definitions
- WIDOCO only displays a limited set of annotations by default (rdfs:label, rdfs:comment, dcterms:source)
- This enhancement makes metadata more visible in the HTML documentation

**Important**: This only affects the WIDOCO HTML documentation, not the WebVOWL interactive visualization.

**Requirements:**
- Python 3.9+ with beautifulsoup4 and lxml

**Usage:**
```bash
# Enhance WIDOCO HTML with additional annotations
python scripts/enhance_widoco_html.py \
    docs/website/documentation/index-en.html \
    build/twinship-core-complete-docs-viz.ttl

# Specify output file (default: overwrites input)
python scripts/enhance_widoco_html.py \
    input.html \
    ontology.ttl \
    -o output.html
```

**Output:**
Enhanced HTML with additional annotation properties displayed in the "definedBy" section of each entity.

### enhance_webvowl_json.py - WebVOWL JSON Enhancer

Post-processes WIDOCO-generated WebVOWL JSON to add SKOS and dcterms annotations without breaking the visualization structure.

**What it does:**
- Loads annotations from the ontology TTL file
- Adds `annotations` field to propertyAttribute and classAttribute objects in WebVOWL JSON
- Preserves all existing WebVOWL structure (IDs, types, domains, ranges, links)
- Follows WebVOWL's annotation format: `{identifier, language, value, type}`
- Minimal-change approach: only adds fields, never modifies existing data

**Why this approach:**
- WIDOCO's OWL2VOWL converter generates WebVOWL JSON but doesn't include custom annotations
- Regenerating the entire JSON breaks subtle structural details WebVOWL expects
- Post-processing preserves the working structure while adding missing data

**Requirements:**
- Python 3.9+ with rdflib

**Usage:**
```bash
# Enhance WebVOWL JSON with annotations
python scripts/enhance_webvowl_json.py \
    build/twinship-core-complete-viz-clean-minimal.ttl \
    docs/website/documentation/webvowl/data/ontology.json
```

**Output:**
WebVOWL JSON with annotations that appear in the sidebar when users click on properties/classes in the interactive visualization.

### generate_viz_ontology.py - Visualization Ontology Generator

Converts OWL restrictions to explicit domain/range assertions and creates virtual properties to eliminate blank union nodes in WebVOWL.

**What it does:**
- Extracts domain/range from OWL restrictions (`owl:someValuesFrom`, `owl:allValuesFrom`)
- Creates virtual properties with single domains for multi-domain properties
- Optionally skips virtual property generation for documentation-friendly output

**Usage:**
```bash
# Generate with virtual properties (for WebVOWL)
python scripts/generate_viz_ontology.py --auto build/twinship-core-complete.ttl
# Creates: build/twinship-core-complete-viz.ttl

# Generate without virtual properties (for documentation)
python scripts/generate_viz_ontology.py --no-virtual-properties --auto build/twinship-core-complete-docs.ttl
# Creates: build/twinship-core-complete-docs-viz.ttl
```

### generate_docs_ontology.py - TwinShip Entity Extractor

Filters ontology to include only TwinShip classes and used external properties, removing entire external ontologies.

**What it does:**
- Extracts only TwinShip namespace entities (`https://twin-ship.eu/twinship#`)
- Includes used IDO classes (3 classes: InanimatePhysicalObject, Object, etc.)
- Includes used external properties (directlyConnectedTo, connectedTo, partOf)
- Removes owl:imports statements
- Reduces from 600+ to 36 classes total

**Usage:**
```bash
# Filter to TwinShip entities only
python scripts/generate_docs_ontology.py -o build/clean.ttl build/complete.ttl
```

### strip_for_webvowl.py - External Parent Stripper

Removes rdfs:subClassOf relationships pointing to external ontologies for cleaner WebVOWL visualization.

**What it does:**
- Removes parent class relationships to external ontologies (e.g., `rdfs:subClassOf ido:InanimatePhysicalObject`)
- Keeps TwinShip internal class hierarchies intact
- Results in a flatter, cleaner WebVOWL graph

**Usage:**
```bash
# Strip external parent relationships
python scripts/strip_for_webvowl.py input.ttl output.ttl
```

### clean_webvowl_json.py - WebVOWL JSON Post-processor

Merges duplicate rdfs:Literal nodes in WebVOWL JSON generated by OWL2VOWL.

**What it does:**
- OWL2VOWL creates separate Literal nodes for each datatype property (causes 172 "classes")
- Merges all duplicate Literal nodes into a single node
- Updates property references to point to the merged node
- Reduces node count from 172 to 38 (33 TwinShip + 3 IDO + 1 Literal + 1 owl:Thing)

**Note:** Currently not integrated in the pipeline but available for manual post-processing if needed.

**Usage:**
```bash
# Clean WebVOWL JSON
python scripts/clean_webvowl_json.py input.json output.json
```

### merge_modules.py - Module Merger

Merges a modular ontology (with owl:imports) into a single self-contained file by recursively resolving all imports.

**Use case for TwinShip**: The `twinship-core.ttl` file imports `twinship-base.ttl` and all modules. This script resolves those imports into a single physical file for tools that don't handle imports well (e.g., some documentation generators).

**What it does:**
- Recursively follows and resolves all `owl:imports`
- Uses catalog-v001.xml for URI-to-file mapping (important for TwinShip!)
- Handles both local files and web URIs
- Prevents circular import loops
- Optionally removes import statements from merged file

**Usage:**

```bash
# Merge twinship-core.ttl (base + all modules) into single file
python scripts/merge_modules.py --auto model/twinship-core.ttl
# Creates: model/twinship-core-complete.ttl

# Merge with explicit catalog
python scripts/merge_modules.py \
    --catalog model/catalog-v001.xml \
    --auto model/twinship-core.ttl

# Use specific catalog file
python scripts/merge_modules.py \
    --catalog model/catalog-v001.xml \
    model/twinship-core.ttl \
    output.ttl

# Keep import statements (default removes them)
python scripts/merge_modules.py --keep-imports input.ttl output.ttl

# Verbose output
python scripts/merge_modules.py --verbose --auto model/twinship-core.ttl
```

**Example transformation:**

Before (modular):
```turtle
# twinship-core.ttl
@prefix : <https://twin-ship.eu/> .
:twinship-core a owl:Ontology ;
    owl:imports <https://twin-ship.eu/modules/engine> ,
                <https://twin-ship.eu/modules/hull> .
```

After (merged):
```turtle
# twinship-complete.ttl - single file with all content
@prefix : <https://twin-ship.eu/> .
:twinship-core a owl:Ontology .
# All engine module content here
# All hull module content here
```

### generate_viz_ontology.py

Converts restriction-based ontologies to simplified domain/range versions for better visualization in tools like OWLViz, WebVOWL, and Protégé.

**What it does:**
- Extracts `rdfs:domain` from `owl:Restriction` patterns
- Removes verbose blank node restrictions from class definitions
- Preserves all property definitions and metadata
- Keeps only named superclass relationships
- Maintains ontology annotations and individuals

**Usage:**

```bash
# Basic usage
python generate_viz_ontology.py input.ttl output.ttl

# Auto-generate output filename (adds '-viz' suffix)
python generate_viz_ontology.py --auto model/twinship-core.ttl
# Creates: model/twinship-core-viz.ttl

# Specify output format explicitly
python generate_viz_ontology.py --format xml input.ttl output.owl

# Verbose output
python generate_viz_ontology.py --verbose --auto model/twinship-core.ttl
```

**Example transformation:**

Before (with restrictions):
```turtle
:twDisplacementMaxInMT a owl:DatatypeProperty ;
    rdfs:range xsd:double .

:VesselSystem a owl:Class ;
    rdfs:subClassOf :TwinShipInanimatePhysicalObject,
        [ owl:onProperty :twDisplacementMaxInMT ;
          owl:someValuesFrom xsd:double ],
        [ owl:onProperty :twVesselDraftAftMaxInM ;
          owl:someValuesFrom xsd:double ] .
```

After (visualization-friendly):
```turtle
:twDisplacementMaxInMT a owl:DatatypeProperty ;
    rdfs:domain :VesselSystem ;
    rdfs:range xsd:double .

:twVesselDraftAftMaxInM a owl:DatatypeProperty ;
    rdfs:domain :VesselSystem ;
    rdfs:range xsd:double .

:VesselSystem a owl:Class ;
    rdfs:subClassOf :TwinShipInanimatePhysicalObject .
```

## Typical Workflows

### Complete Documentation Generation (Recommended)

```bash
# One command for everything
./scripts/generate_docs.sh --verbose

# Opens: docs/ontology/index.html
```

### Step-by-Step (Advanced)

```bash
# 1. Maintain modular ontology (for development)
#    model/modules/engine.ttl
#    model/modules/hull.ttl
#    model/twinship-core.ttl (imports all)

# 2. Merge modules into complete file
python scripts/merge_modules.py --auto --verbose model/twinship-core.ttl
# → Creates: model/twinship-core-complete.ttl

# 3. Generate visualization-friendly version
python scripts/generate_viz_ontology.py --auto --verbose model/twinship-core-complete.ttl
# → Creates: model/twinship-core-complete-viz.ttl

# 4. Generate documentation with your preferred tool
# Using LODE:
lode -i model/twinship-core-complete-viz.ttl -o docs/ontology/index.html

# Using Widoco:
widoco -ontFile model/twinship-core-complete-viz.ttl -outFolder docs/ontology

# Using pyLODE:
pylode -i model/twinship-core-complete-viz.ttl -o docs/ontology/index.html
```

## Working with Modular Structure

### Processing Individual Modules

```bash
# Generate documentation for just the engine module
python scripts/merge_modules.py --auto model/modules/engine.ttl
python scripts/generate_viz_ontology.py --auto model/modules/engine-complete.ttl
# Creates: model/modules/engine-complete.ttl and engine-complete-viz.ttl

# Generate documentation for just the hull module
python scripts/merge_modules.py --auto model/modules/hull.ttl
python scripts/generate_viz_ontology.py --auto model/modules/hull-complete.ttl
```

### Processing Complete Ontology

```bash
# Generate documentation for complete TwinShip ontology (recommended)
python scripts/merge_modules.py --auto model/twinship-core.ttl
python scripts/generate_viz_ontology.py --auto model/twinship-core-complete.ttl
# Creates: model/twinship-core-complete.ttl and twinship-core-complete-viz.ttl
```

### Development vs. Distribution

```bash
# For DEVELOPMENT (maintain these files):
model/twinship-base.ttl            # Foundation ontology
model/twinship-core.ttl            # Aggregate (imports base + modules)
model/modules/engine.ttl           # Engine module with restrictions
model/modules/hull.ttl             # Hull module with restrictions

# For DISTRIBUTION (generate these as needed):
model/twinship-core-complete.ttl      # Single-file, all imports merged
model/twinship-core-complete-viz.ttl  # + domain/range for visualization

# For DOCUMENTATION (generate from viz version):
docs/ontology/index.html           # Human-readable HTML docs
```

### Understanding the Pipeline

```
┌─────────────────────────────────────────────────────────────┐
│ Source: Modular Structure                                    │
├─────────────────────────────────────────────────────────────┤
│ twinship-base.ttl  (foundation)                             │
│ twinship-core.ttl  (imports base + modules)                 │
│ modules/engine.ttl (restriction-based)                      │
│ modules/hull.ttl   (restriction-based)                      │
└────────────────┬────────────────────────────────────────────┘
                 │
                 ▼ merge_modules.py
┌─────────────────────────────────────────────────────────────┐
│ Intermediate: Complete Merged File                          │
├─────────────────────────────────────────────────────────────┤
│ twinship-core-complete.ttl                                  │
│ (Single file with all content, restriction-based)           │
└────────────────┬────────────────────────────────────────────┘
                 │
                 ▼ generate_viz_ontology.py
┌─────────────────────────────────────────────────────────────┐
│ Output: Visualization-Friendly                              │
├─────────────────────────────────────────────────────────────┤
│ twinship-core-complete-viz.ttl                              │
│ (Single file, domain/range instead of restrictions)         │
└────────────────┬────────────────────────────────────────────┘
                 │
                 ▼ LODE/Widoco
┌─────────────────────────────────────────────────────────────┐
│ Final: HTML Documentation                                   │
├─────────────────────────────────────────────────────────────┤
│ docs/ontology/index.html                                    │
└─────────────────────────────────────────────────────────────┘
```

## Adding New Scripts

When adding new scripts to this directory:

1. Add appropriate shebang: `#!/usr/bin/env python3`
2. Include docstring with usage examples
3. Update this README
4. Add any new dependencies to `requirements.txt`
5. Make script executable: `chmod +x script_name.py`

## Development

To contribute or modify scripts:

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run tests (if available)
python -m pytest tests/

# Format code
black scripts/
```

## License

These scripts are part of the TwinShip ontology project.
