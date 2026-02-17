#!/usr/bin/env python3
"""
Prepare Ontology for WebVOWL Visualization

WebVOWL is an interactive graph-based visualization tool for ontologies.
This script prepares the ontology and sets up WebVOWL for local or web deployment.

Requirements:
    - Python 3.9+ with rdflib (install: uv sync)
    - Node.js and npm (for local WebVOWL setup)
    - OR use online version at http://vowl.visualdataweb.org/webvowl.html
    
Usage:
    # Prepare for online WebVOWL
    python setup_webvowl.py model/twinship-core-complete-viz.ttl
    
    # Install local WebVOWL
    python setup_webvowl.py --install-local model/twinship-core-complete-viz.ttl
    
Output:
    docs/webvowl/
    ├── ontology.json         # WebVOWL-compatible format
    ├── index.html            # Viewer page
    └── webvowl/              # WebVOWL application (if --install-local)
"""

import argparse
import json
import subprocess
import sys
import shutil
from pathlib import Path
from rdflib import Graph, RDF, RDFS, OWL, Namespace


def convert_to_webvowl_json(input_file, output_file):
    """
    Convert ontology to WebVOWL JSON format.
    
    WebVOWL expects a specific JSON structure with:
    - classes: list of class objects
    - properties: list of property objects  
    - propertyAttributes: additional property info
    """
    print(f"Converting {input_file} to WebVOWL JSON format...")
    
    g = Graph()
    g.parse(input_file)
    
    # Extract namespaces
    namespaces = {prefix: str(ns) for prefix, ns in g.namespaces()}
    
    # Helper function to shorten URIs
    def shorten_uri(uri):
        uri_str = str(uri)
        for prefix, ns in namespaces.items():
            if uri_str.startswith(ns):
                return f"{prefix}:{uri_str[len(ns):]}"
        return uri_str
    
    # Extract classes
    classes = []
    class_map = {}
    
    for i, cls in enumerate(g.subjects(RDF.type, OWL.Class)):
        if isinstance(cls, str) or str(cls).startswith('http'):
            label = g.value(cls, RDFS.label) or shorten_uri(cls)
            comment = g.value(cls, RDFS.comment) or ""
            
            class_obj = {
                "id": str(i),
                "type": "owl:Class",
                "iri": str(cls),
                "baseIri": str(cls).rsplit('/', 1)[0] if '/' in str(cls) else str(cls),
                "label": {"IRI-based": shorten_uri(cls), "undefined": str(label)},
                "comment": {"undefined": str(comment)} if comment else {}
            }
            
            # Add superclasses
            superclasses = list(g.objects(cls, RDFS.subClassOf))
            superclasses = [s for s in superclasses if not isinstance(s, type(None)) and str(s).startswith('http')]
            if superclasses:
                class_obj["subClassOf"] = [str(s) for s in superclasses]
            
            classes.append(class_obj)
            class_map[str(cls)] = str(i)
    
    # Extract properties (both object and datatype properties)
    properties = []
    prop_id = 0
    
    for prop_type in [OWL.ObjectProperty, OWL.DatatypeProperty]:
        for prop in g.subjects(RDF.type, prop_type):
            if isinstance(prop, str) or str(prop).startswith('http'):
                label = g.value(prop, RDFS.label) or shorten_uri(prop)
                comment = g.value(prop, RDFS.comment) or ""
                
                prop_obj = {
                    "id": str(prop_id),
                    "type": "owl:ObjectProperty" if prop_type == OWL.ObjectProperty else "owl:DatatypeProperty",
                    "iri": str(prop),
                    "baseIri": str(prop).rsplit('/', 1)[0] if '/' in str(prop) else str(prop),
                    "label": {"IRI-based": shorten_uri(prop), "undefined": str(label)},
                    "comment": {"undefined": str(comment)} if comment else {}
                }
                
                # Add domain and range
                domains = list(g.objects(prop, RDFS.domain))
                if domains and str(domains[0]).startswith('http'):
                    domain_id = class_map.get(str(domains[0]))
                    if domain_id:
                        prop_obj["domain"] = domain_id
                
                ranges = list(g.objects(prop, RDFS.range))
                if ranges:
                    range_uri = str(ranges[0])
                    if range_uri.startswith('http'):
                        range_id = class_map.get(range_uri)
                        if range_id:
                            prop_obj["range"] = range_id
                        else:
                            # External class or datatype
                            prop_obj["range"] = "external"
                
                properties.append(prop_obj)
                prop_id += 1
    
    # Build WebVOWL JSON structure
    webvowl_data = {
        "header": {
            "languages": ["en"],
            "title": {"en": "TwinShip Ontology"},
            "description": {"en": "Digital Twin Ontology for Maritime Vessels"},
            "iri": "https://twin-ship.eu/twinship-core"
        },
        "namespace": list(namespaces.values()),
        "class": classes,
        "property": properties
    }
    
    # Write to file
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with output_path.open('w', encoding='utf-8') as f:
        json.dump(webvowl_data, f, indent=2, ensure_ascii=False)
    
    print(f"✓ WebVOWL JSON created: {output_path}")
    print(f"  Classes: {len(classes)}")
    print(f"  Properties: {len(properties)}")
    
    return output_path


def create_viewer_html(output_dir, json_file):
    """Create HTML page for viewing with online WebVOWL."""
    
    html_content = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>TwinShip Ontology - WebVOWL Visualization</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            max-width: 1200px;
            margin: 40px auto;
            padding: 0 20px;
            line-height: 1.6;
        }
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            border-radius: 8px;
            margin-bottom: 30px;
        }
        h1 { margin: 0 0 10px 0; }
        .subtitle { opacity: 0.9; }
        .card {
            background: #f8f9fa;
            border: 1px solid #dee2e6;
            border-radius: 8px;
            padding: 25px;
            margin-bottom: 20px;
        }
        .button {
            display: inline-block;
            background: #667eea;
            color: white;
            padding: 12px 24px;
            text-decoration: none;
            border-radius: 6px;
            font-weight: 500;
            margin: 10px 10px 10px 0;
            transition: background 0.3s;
        }
        .button:hover { background: #5568d3; }
        .button-secondary {
            background: #6c757d;
        }
        .button-secondary:hover { background: #5a6268; }
        code {
            background: #e9ecef;
            padding: 2px 6px;
            border-radius: 3px;
            font-family: 'Monaco', 'Courier New', monospace;
            font-size: 0.9em;
        }
        pre {
            background: #f8f9fa;
            padding: 15px;
            border-radius: 5px;
            overflow-x: auto;
        }
        .info {
            background: #d1ecf1;
            border-left: 4px solid #0c5460;
            padding: 15px;
            margin: 20px 0;
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>TwinShip Ontology</h1>
        <p class="subtitle">Interactive Graph Visualization with WebVOWL</p>
    </div>
    
    <div class="card">
        <h2>⚠️ Security Notice</h2>
        <p style="background: #fff3cd; padding: 15px; border-left: 4px solid #856404; border-radius: 4px;">
            <strong>Warning:</strong> The official WebVOWL online service at <code>vowl.visualdataweb.org</code> 
            appears to have been compromised and now redirects to malicious sites. <strong>DO NOT USE IT.</strong>
            Please use the local visualization methods below instead.
        </p>
    </div>
    
    <div class="card">
        <h2>💻 Local Server</h2>
        <p>For better performance, serve this directory locally:</p>
        <pre><code># Using Python
cd docs/webvowl
python -m http.server 8000

# Then open: http://localhost:8000
# And load ontology.json in WebVOWL</code></pre>
    </div>
    
    <div class="card">
        <h2>📦 Local Installation (Advanced)</h2>
        <p>Install WebVOWL locally for offline use:</p>
        <pre><code># Clone WebVOWL repository
git clone https://github.com/VisualDataWeb/WebVOWL.git
cd WebVOWL

# Install dependencies and build
npm install
npm run build

# Copy your ontology.json to deploy/data/
cp ../ontology.json deploy/data/

# Serve
cd deploy
python -m http.server 8000</code></pre>
        <p>
            Or use the provided script:<br>
            <code>python scripts/setup_webvowl.py --install-local model/twinship-core-complete-viz.ttl</code>
        </p>
    </div>
    
    <div class="info">
        <strong>ℹ️ About WebVOWL</strong><br>
        WebVOWL provides an interactive force-directed graph visualization of ontologies.
        It shows classes as nodes and properties as edges, making it easy to explore
        the structure and relationships in your ontology.
        <br><br>
        <strong>Features:</strong>
        <ul style="margin: 10px 0 0 20px;">
            <li>Interactive node dragging and zoom</li>
            <li>Filter by class, property type, or namespace</li>
            <li>Export visualization as SVG/PNG</li>
            <li>Statistics and metrics</li>
        </ul>
    </div>
    
    <div class="card">
        <h2>📄 Files</h2>
        <ul>
            <li><code>ontology.json</code> - WebVOWL-compatible ontology data</li>
            <li><code>index.html</code> - This instruction page</li>
        </ul>
    </div>
    
    <footer style="text-align: center; margin-top: 40px; padding: 20px; color: #6c757d;">
        <p>TwinShip Ontology | Generated with WebVOWL setup script</p>
    </footer>
</body>
</html>
"""
    
    index_path = Path(output_dir) / "index.html"
    index_path.write_text(html_content, encoding="utf-8")
    print(f"✓ Created viewer page: {index_path}")


def main():
    parser = argparse.ArgumentParser(
        description="Prepare ontology for WebVOWL visualization",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Prepare for online WebVOWL (easiest)
  python setup_webvowl.py model/twinship-core-complete-viz.ttl
  
  # Custom output directory
  python setup_webvowl.py -o docs/visualization model/twinship-core-complete-viz.ttl
  
  # Install local WebVOWL (requires Node.js)
  python setup_webvowl.py --install-local model/twinship-core-complete-viz.ttl

Note: For best results, use the visualization-friendly ontology (output of generate_viz_ontology.py)
        """
    )
    
    parser.add_argument('input', help='Input ontology file (use viz version)')
    parser.add_argument('-o', '--output', default='docs/webvowl',
                       help='Output directory (default: docs/webvowl)')
    parser.add_argument('--install-local', action='store_true',
                       help='Clone and setup local WebVOWL (requires Node.js)')
    
    args = parser.parse_args()
    
    print("=" * 70)
    print("TwinShip Ontology - WebVOWL Setup")
    print("=" * 70)
    
    # Convert to WebVOWL JSON
    output_dir = Path(args.output)
    json_file = convert_to_webvowl_json(
        args.input,
        output_dir / "ontology.json"
    )
    
    # Create viewer HTML
    create_viewer_html(output_dir, json_file)
    
    print("\n" + "=" * 70)
    print("WebVOWL setup complete!")
    print("=" * 70)
    print(f"\nOutput directory: {output_dir.resolve()}")
    print(f"\nTo visualize:")
    print(f"  1. Open: {output_dir.resolve() / 'index.html'}")
    print(f"  2. Follow the instructions to load ontology.json")
    
    if args.install_local:
        print("\n⚠️  Local WebVOWL installation not yet implemented.")
        print("   Please use the online version or clone manually.")
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
