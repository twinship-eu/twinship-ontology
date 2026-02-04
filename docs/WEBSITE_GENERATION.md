# TwinShip Ontology - Website Generation

This directory contains scripts to generate a complete website for the TwinShip ontology with professional documentation and interactive visualizations.

## 🎯 Overview

The website generation pipeline uses industry-standard tools:

- **[WIDOCO](https://github.com/dgarijo/Widoco)** - Comprehensive HTML documentation with diagrams, cross-references, and metadata
- **[WebVOWL](http://vowl.visualdataweb.org/webvowl.html)** - Interactive force-directed graph visualization

## 📋 Prerequisites

### Required
- **Python 3.7+** with `rdflib` library
- **Java 11+** (for WIDOCO)
  - Download: https://adoptium.net/
  - Check: `java -version`

### Optional
- **Node.js & npm** (for local WebVOWL installation)

### Installation

```bash
# Install uv (fast, modern Python package manager)
curl -LsSf https://astral.sh/uv/install.sh | sh
# Or: brew install uv

# Install Python dependencies
uv sync

# Verify Java is installed
java -version
```

## 🚀 Quick Start

### Generate Complete Website

```bash
# Install dependencies
uv sync

# Generate everything: documentation + visualization + landing page
./scripts/generate_website.sh

# View the website
open docs/website/index.html

# Or serve locally
cd docs/website && python -m http.server 8000
# Then open: http://localhost:8000
```

### Generate Only Documentation

```bash
# Uses WIDOCO to generate comprehensive HTML docs
python scripts/generate_widoco_docs.py model/twinship-core-complete-viz.ttl

# Custom output directory
python scripts/generate_widoco_docs.py -o docs/documentation model/twinship-core-complete-viz.ttl

# View result
open docs/website/index-en.html
```

### Generate Only Visualization

```bash
# Prepares ontology for WebVOWL
python scripts/setup_webvowl.py model/twinship-core-complete-viz.ttl

# Custom output directory
python scripts/setup_webvowl.py -o docs/visualization model/twinship-core-complete-viz.ttl

# View result
open docs/webvowl/index.html
```

## 📊 Pipeline Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    TwinShip Website Generation                  │
└─────────────────────────────────────────────────────────────────┘

Input: Modular Ontology Files
│
├── model/twinship-base.ttl         (foundation)
├── model/modules/engine.ttl        (domain)
├── model/modules/hull.ttl          (domain)
└── model/twinship-core.ttl         (aggregate)
    │
    ▼
┌─────────────────────────────────────────┐
│  STEP 1: Merge Modules                  │
│  Script: merge_modules.py               │
│  Output: twinship-core-complete.ttl     │
└─────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────┐
│  STEP 2: Generate Viz Ontology          │
│  Script: generate_viz_ontology.py       │
│  Output: twinship-core-complete-viz.ttl │
└─────────────────────────────────────────┘
    │
    ├─────────────────────┬──────────────────────┐
    ▼                     ▼                      ▼
┌──────────────┐   ┌──────────────┐   ┌──────────────────┐
│ STEP 3a:     │   │ STEP 3b:     │   │ STEP 3c:         │
│ WIDOCO Docs  │   │ WebVOWL Viz  │   │ Landing Page     │
│              │   │              │   │                  │
│ Tools:       │   │ Tools:       │   │ Tools:           │
│ • WIDOCO jar │   │ • RDFLib     │   │ • HTML template  │
│ • Java       │   │ • JSON conv. │   │                  │
└──────────────┘   └──────────────┘   └──────────────────┘
    │                     │                      │
    ▼                     ▼                      ▼
┌─────────────────────────────────────────────────────────┐
│               Final Website Structure                    │
├─────────────────────────────────────────────────────────┤
│ docs/website/                                            │
│ ├── index.html                    (landing page)        │
│ ├── documentation/                                       │
│ │   ├── index-en.html             (WIDOCO docs)         │
│ │   ├── sections/                 (doc sections)        │
│ │   └── resources/                (CSS, diagrams)       │
│ └── visualization/                                       │
│     ├── index.html                (WebVOWL viewer)      │
│     └── ontology.json             (graph data)          │
└─────────────────────────────────────────────────────────┘
```

## 📁 Output Structure

After running `generate_website.sh`, you'll have:

```
docs/website/
├── index.html                          # Landing page with links to docs & viz
│
├── documentation/                      # WIDOCO-generated documentation
│   ├── index.html                      # Redirect to index-en.html
│   ├── index-en.html                   # Main documentation page
│   ├── sections/                       # Documentation sections
│   │   ├── description-en.html         # Overview
│   │   ├── crossref-en.html            # Class/property reference
│   │   └── introduction-en.html        # Introduction
│   ├── resources/                      # Assets
│   │   ├── images/                     # UML diagrams
│   │   ├── css/                        # Stylesheets
│   │   └── primer.css                  # W3C styling
│   └── provenance/                     # Metadata
│
└── visualization/                      # WebVOWL visualization
    ├── index.html                      # Instructions & viewer
    └── ontology.json                   # WebVOWL graph data
```

## 🔧 Script Reference

### generate_website.sh

Master script that runs the complete pipeline.

```bash
./scripts/generate_website.sh [options]

Options:
  --source <file>      Source ontology (default: model/twinship-core.ttl)
  --output <dir>       Output directory (default: docs/website)
  --skip-merge         Skip merge step
  --skip-viz           Skip viz conversion
  --skip-widoco        Skip WIDOCO documentation
  --skip-webvowl       Skip WebVOWL setup
  --verbose            Verbose output
```

**Examples:**

```bash
# Generate everything with defaults
./scripts/generate_website.sh

# Verbose output
./scripts/generate_website.sh --verbose

# Skip steps if files already exist
./scripts/generate_website.sh --skip-merge --skip-viz

# Custom source and output
./scripts/generate_website.sh --source model/twinship-core.ttl --output public/ontology
```

### generate_widoco_docs.py

Generates comprehensive HTML documentation using WIDOCO.

**Features:**
- Class and property hierarchies
- Cross-reference tables
- UML diagrams
- Metadata and provenance
- Multi-language support
- WebVOWL integration

**Usage:**

```bash
python scripts/generate_widoco_docs.py [options] <input-file>

Options:
  -o, --output <dir>     Output directory (default: docs/website)
  --tools-dir <dir>      WIDOCO jar directory (default: tools)
  --no-diagram           Skip diagram generation
  --no-crossref          Skip cross-references
  --lang <code>          Language code (default: en)
```

**Examples:**

```bash
# Basic usage
python scripts/generate_widoco_docs.py model/twinship-core-complete-viz.ttl

# Custom output
python scripts/generate_widoco_docs.py -o public/docs model/twinship-core-complete-viz.ttl

# Faster generation (no diagrams)
python scripts/generate_widoco_docs.py --no-diagram model/twinship-core-complete-viz.ttl
```

**First Run:**
- WIDOCO jar (~40MB) is downloaded automatically to `tools/` directory
- Requires internet connection for first-time download
- Subsequent runs use cached jar file

### setup_webvowl.py

Prepares ontology for WebVOWL interactive visualization.

**Features:**
- Converts OWL/Turtle to WebVOWL JSON format
- Creates viewer HTML with instructions
- Supports online and local WebVOWL
- Interactive graph navigation

**Usage:**

```bash
python scripts/setup_webvowl.py [options] <input-file>

Options:
  -o, --output <dir>     Output directory (default: docs/webvowl)
  --install-local        Clone local WebVOWL (requires Node.js)
```

**Examples:**

```bash
# Prepare for online WebVOWL (easiest)
python scripts/setup_webvowl.py model/twinship-core-complete-viz.ttl

# Custom output
python scripts/setup_webvowl.py -o public/viz model/twinship-core-complete-viz.ttl
```

**Viewing Options:**
1. **Online** (recommended): Upload `ontology.json` to http://vowl.visualdataweb.org/webvowl.html
2. **Local server**: `cd docs/webvowl && python -m http.server 8000`
3. **Local install**: Clone WebVOWL repo (requires Node.js)

## 🔍 Tool Comparison

### WIDOCO vs LODE

| Feature | WIDOCO | LODE |
|---------|--------|------|
| **Documentation Completeness** | ⭐⭐⭐⭐⭐ Most complete | ⭐⭐⭐ Basic |
| **UML Diagrams** | ✅ Auto-generated | ❌ None |
| **Cross-references** | ✅ Comprehensive | ✅ Basic |
| **Metadata/Provenance** | ✅ Full support | ⚠️ Limited |
| **Multi-language** | ✅ Yes | ✅ Yes |
| **Installation** | Java required | Web service available |
| **Customization** | ⭐⭐⭐⭐ High | ⭐⭐ Limited |
| **Recommendation** | **Primary choice** | Alternative |

**Verdict:** Use **WIDOCO** for TwinShip ontology (most complete, better diagrams, rich metadata)

### WebVOWL Features

- **Interactive Graph**: Force-directed layout with drag & zoom
- **Filtering**: By class type, property type, namespace
- **Search**: Find classes and properties quickly
- **Export**: SVG/PNG for presentations
- **Statistics**: Metrics on classes, properties, individuals
- **Standards**: Implements VOWL visual notation

## 🎨 Customization

### WIDOCO Customization

Edit generated files in `docs/website/documentation/`:

```bash
# Customize styling
docs/website/documentation/resources/primer.css

# Add custom introduction
# Create: docs/website/documentation/sections/introduction-en.html
```

### Landing Page Customization

Edit `scripts/generate_website.sh` and modify the HTML template in Step 5.

## 🐛 Troubleshooting

### Java not found

```bash
# macOS (using Homebrew)
brew install openjdk@17
sudo ln -sfn $(brew --prefix)/opt/openjdk@17/libexec/openjdk.jdk \
  /Library/Java/JavaVirtualMachines/openjdk-17.jdk

# Or download from https://adoptium.net/
```

### WIDOCO download fails

Download manually:
```bash
mkdir -p tools
cd tools
curl -L -O https://github.com/dgarijo/Widoco/releases/download/v1.4.25/widoco-1.4.25-jar-with-dependencies.jar
```

### WebVOWL shows empty graph

- Ensure you're using the **viz-friendly** ontology (output of `generate_viz_ontology.py`)
- Check browser console for errors
- Try uploading to online WebVOWL: http://vowl.visualdataweb.org/webvowl.html

### Permission denied

```bash
chmod +x scripts/generate_website.sh
chmod +x scripts/generate_widoco_docs.py
chmod +x scripts/setup_webvowl.py
```

## 📚 Additional Resources

- **WIDOCO**: https://github.com/dgarijo/Widoco
- **WebVOWL**: http://vowl.visualdataweb.org/
- **VOWL Specification**: http://vowl.visualdataweb.org/v2/
- **OWL 2 Primer**: https://www.w3.org/TR/owl2-primer/

## 🤝 Integration with Existing Pipeline

The website generation integrates seamlessly with the existing ontology pipeline:

```bash
# 1. Work with modular sources
vim model/modules/engine.ttl

# 2. Generate merged ontology
python scripts/merge_modules.py --auto --catalog model/catalog-v001.xml \
  model/twinship-core.ttl

# 3. Generate viz-friendly version
python scripts/generate_viz_ontology.py --auto model/twinship-core-complete.ttl

# 4. Generate complete website
./scripts/generate_website.sh

# 5. View result
open docs/website/index.html
```

Or use the all-in-one script:

```bash
# Everything in one command
./scripts/generate_website.sh --verbose
```

## 📝 Version Information

- **WIDOCO Version**: 1.4.25
- **WebVOWL**: Online version (latest)
- **Target OWL**: OWL 2 / RDF 1.1
- **Output Format**: HTML5 + JSON

---

**Last Updated**: February 2026  
**Maintainer**: TwinShip Ontology Team
