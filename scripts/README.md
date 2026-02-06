# TwinShip Ontology Scripts

This directory contains utility scripts for working with the TwinShip modular ontology.

## TwinShip Ontology Structure

The TwinShip ontology uses a **modular architecture**:
- **twinship-base.ttl** - Foundation ontology (base classes, properties)
- **twinship-core.ttl** - Complete aggregate (imports base + all modules)
- **modules/** - Domain-specific modules (vessel.ttl, weatherconditions.ttl, etc.)

The scripts help process this modular structure for documentation and visualization.

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

```bash# Using uv (creates venv and installs deps automatically)
uv sync

# Or manually with traditional toolspython -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## Quick Start: Documentation Generation

The complete workflow for generating documentation from modular ontology sources:

```bash
# One-command documentation generation (uses twinship-core.ttl as source)
./scripts/generate_docs.sh --verbose

# Or step-by-step:
# 1. Merge all imports into single file
python scripts/merge_modules.py --auto --verbose model/twinship-core.ttl
# Creates: model/twinship-core-complete.ttl

# 2. Convert to visualization-friendly format
python scripts/generate_viz_ontology.py --auto --verbose model/twinship-core-complete.ttl
# Creates: model/twinship-core-complete-viz.ttl

# 3. Generate HTML docs with LODE/Widoco
# Use model/twinship-core-complete-viz.ttl as input
```

**Note**: `twinship-core.ttl` already aggregates everything via imports. The merge script resolves these imports into a single physical file for tools that don't support imports.

## Scripts

## Scripts Overview

### Production Scripts (Primary Workflow)

These scripts form the main documentation generation pipeline:

- **`generate_website.sh`** - Complete website generation (WIDOCO + WebVOWL)
- **`generate_docs.sh`** - Documentation generation (older, LODE/WIDOCO)
- **`merge_modules.py`** - Merge modular ontology files
- **`generate_viz_ontology.py`** - Convert restrictions to domain/range
- **`generate_docs_ontology.py`** - Filter to TwinShip-only content
- **`generate_widoco_docs.py`** - Generate WIDOCO documentation
- **`setup_webvowl.py`** - Setup WebVOWL visualization

### Development/Debug Scripts

These scripts were used during development and have been removed.

### generate_docs.sh

**Complete documentation generation pipeline** - orchestrates the entire process from modular sources to HTML documentation.

**What it does:**
1. Merges all ontology modules into a single complete file
2. Converts restrictions to domain/range for visualization
3. Generates HTML documentation using LODE or Widoco

**Requirements:**
- Python 3.7+ with rdflib (for merge and viz scripts)
- LODE (https://github.com/essepuntato/LODE) or Widoco (https://github.com/dgarijo/Widoco)

**Usage:**

```bash
# Basic usage (auto-detects tool)
./scripts/generate_docs.sh

# Specify tool explicitly
./scripts/generate_docs.sh --tool widoco --verbose

# Custom source and output
./scripts/generate_docs.sh \
    --source model/twinship-core.ttl \
    --output docs/ontology \
    --verbose
```

**Output:**
- `model/twinship-core-complete.ttl` - Merged ontology
- `model/twinship-core-complete-viz.ttl` - Visualization-friendly version
- `docs/ontology/` - HTML documentation


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
cd docs/website && python -m http.server 8000
# Then open: http://localhost:8000
```

### Output Structure

```
docs/website/
├── index.html                    # Landing page
├── documentation/                # WIDOCO-generated docs
│   ├── index-en.html            # Main documentation
│   ├── sections/                # Individual sections
│   └── resources/               # CSS, diagrams, images
└── visualization/                # WebVOWL setup
    ├── index.html               # Instructions & viewer
    └── ontology.json            # Graph data
```

### Available Scripts

#### generate_website.sh - Master Pipeline

Orchestrates the complete website generation.

**Options:**
```bash
--source <file>      # Source ontology (default: model/twinship-core.ttl)
--output <dir>       # Output directory (default: docs/website)
--skip-merge         # Skip merge step
--skip-viz           # Skip viz conversion
--skip-widoco        # Skip WIDOCO documentation
--skip-webvowl       # Skip WebVOWL setup
--verbose            # Verbose output
```

**Example:**
```bash
./scripts/generate_website.sh --verbose
```

#### generate_widoco_docs.py - Documentation Generator

Generates comprehensive HTML documentation using WIDOCO.

**Requirements:**
- Java 11+ (WIDOCO jar downloaded automatically on first run)

**Usage:**
```bash
# Basic usage
python scripts/generate_widoco_docs.py model/twinship-core-complete-viz.ttl

# Custom output
python scripts/generate_widoco_docs.py -o docs/my-docs model/twinship-core-complete-viz.ttl

# Skip diagrams (faster)
python scripts/generate_widoco_docs.py --no-diagram model/twinship-core-complete-viz.ttl
```

#### setup_webvowl.py - Visualization Setup

Prepares ontology for WebVOWL interactive visualization.

**Usage:**
```bash
# Prepare for online WebVOWL (easiest)
python scripts/setup_webvowl.py model/twinship-core-complete-viz.ttl

# Custom output
python scripts/setup_webvowl.py -o docs/my-viz model/twinship-core-complete-viz.ttl
```

**Viewing Options:**
1. Upload `ontology.json` to http://vowl.visualdataweb.org/webvowl.html
2. Serve locally: `cd docs/webvowl && python -m http.server 8000`

### Complete Documentation

See [docs/WEBSITE_GENERATION.md](../docs/WEBSITE_GENERATION.md) for:
- Detailed tool comparison (WIDOCO vs LODE)
- Customization options
- Troubleshooting guide
- Integration with CI/CD

## Ontology Processing Scripts

### merge_modules.py

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
