#!/usr/bin/env python3
"""
Generate Web Documentation for TwinShip Ontology using WIDOCO

WIDOCO (WIzard for DOCumenting Ontologies) generates comprehensive HTML documentation
including diagrams, cross-references, and metadata. It's the most complete tool for
ontology documentation.

Requirements:
    - Python 3.9+ with rdflib (install: uv sync)
    - Java 11+ installed
    - WIDOCO jar file (downloaded automatically if not present)
    - Input: Merged and visualization-friendly ontology file

Usage:
    python generate_widoco_docs.py model/twinship-core-complete-viz.ttl
    python generate_widoco_docs.py --output docs/website model/twinship-core-complete-viz.ttl
    
Output:
    docs/website/
    ├── index-en.html         # Main documentation page
    ├── sections/             # Individual sections
    ├── resources/            # CSS, images, diagrams
    └── provenance/           # Provenance information
"""

import argparse
import subprocess
import sys
import urllib.request
from pathlib import Path
import shutil
import os


# WIDOCO version and download URL
WIDOCO_VERSION = "1.4.25"
WIDOCO_JAR = f"widoco-{WIDOCO_VERSION}-jar-with-dependencies_JDK-17.jar"
WIDOCO_URL = f"https://github.com/dgarijo/Widoco/releases/download/v{WIDOCO_VERSION}/{WIDOCO_JAR}"


def check_java():
    """Check if Java is installed and get version."""
    try:
        result = subprocess.run(['java', '-version'], 
                              capture_output=True, 
                              text=True, 
                              check=True)
        version_output = result.stderr.split('\n')[0]
        print(f"✓ Java found: {version_output}")
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("✗ Error: Java not found. Please install Java 11 or later.")
        print("  Download from: https://adoptium.net/")
        return False


def download_widoco(tools_dir):
    """Download WIDOCO jar if not present."""
    jar_path = tools_dir / WIDOCO_JAR
    
    if jar_path.exists():
        print(f"✓ WIDOCO jar already downloaded: {jar_path}")
        return jar_path
    
    print(f"Downloading WIDOCO {WIDOCO_VERSION}...")
    print(f"  From: {WIDOCO_URL}")
    print(f"  To: {jar_path}")
    
    tools_dir.mkdir(parents=True, exist_ok=True)
    
    try:
        urllib.request.urlretrieve(WIDOCO_URL, jar_path)
        print(f"✓ Downloaded WIDOCO successfully")
        return jar_path
    except Exception as e:
        print(f"✗ Error downloading WIDOCO: {e}")
        print(f"  Please download manually from:")
        print(f"  {WIDOCO_URL}")
        return None


def run_widoco(jar_path, input_file, output_dir, include_diagram=True, 
               include_crossref=True, lang="en"):
    """Run WIDOCO to generate documentation."""
    
    input_path = Path(input_file).resolve()
    output_path = Path(output_dir).resolve()
    
    if not input_path.exists():
        print(f"✗ Error: Input file not found: {input_path}")
        return False
    
    # Create output directory
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Build WIDOCO command
    cmd = [
        'java', '-Dfile.encoding=UTF-8', '-Dstdout.encoding=UTF-8', '-jar', str(jar_path),
        '-ontFile', str(input_path),
        '-outFolder', str(output_path),
        '-lang', lang,
        '-uniteSections',  # Combine sections into single page
        '-rewriteAll',     # Overwrite existing files
        '-getOntologyMetadata',  # Only document main ontology metadata
        '-noPlaceHolderText',    # Don't add placeholder text
    ]
    
    if include_diagram:
        cmd.append('-includeAnnotationProperties')
        cmd.append('-webVowl')  # Generate WebVOWL visualization data
    
    if not include_crossref:
        cmd.append('-excludeIntroduction')
    
    print(f"\nGenerating WIDOCO documentation...")
    print(f"  Input: {input_path.name}")
    print(f"  Output: {output_path}")
    print(f"  Options: diagram={include_diagram}, crossref={include_crossref}, lang={lang}")
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print(f"\n✓ Documentation generated successfully!")
        print(f"  Open: {output_path / 'index-en.html'}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"\n✗ Error running WIDOCO:")
        print(e.stderr)
        return False


def create_index_redirect(output_dir):
    """Create a simple index.html that redirects to index-en.html."""
    index_path = Path(output_dir) / "index.html"
    
    html_content = """<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta http-equiv="refresh" content="0; url=index-en.html">
    <title>TwinShip Ontology Documentation</title>
</head>
<body>
    <p>Redirecting to <a href="index-en.html">TwinShip Ontology Documentation</a>...</p>
</body>
</html>
"""
    
    index_path.write_text(html_content)
    print(f"✓ Created index redirect: {index_path}")


def fix_webvowl_iframe_height(output_dir):
    """Post-process the generated HTML to increase WebVOWL iframe height."""
    index_file = Path(output_dir) / "index-en.html"
    
    if not index_file.exists():
        print(f"⚠ Warning: Could not find {index_file} to fix iframe height")
        return
    
    try:
        html_content = index_file.read_text(encoding='utf-8')
        
        # Replace the bare iframe tag with styled version
        original = '<iframe src="webvowl/index.html"></iframe>'
        replacement = '<iframe src="webvowl/index.html" style="width: 100%; height: 800px; border: 1px solid #ddd; border-radius: 4px;"></iframe>'
        
        if original in html_content:
            html_content = html_content.replace(original, replacement)
            index_file.write_text(html_content, encoding='utf-8')
            print(f"✓ Increased WebVOWL iframe height to 800px")
        else:
            print(f"⚠ Warning: Could not find iframe tag to modify")
    except Exception as e:
        print(f"⚠ Warning: Failed to fix iframe height: {e}")


def fix_ontology_title(output_dir):
    """Post-process the generated HTML to change title from 'TwinShip Core Ontology (Complete)' to 'TwinShip Ontology'."""
    index_file = Path(output_dir) / "index-en.html"
    
    if not index_file.exists():
        print(f"⚠ Warning: Could not find {index_file} to fix title")
        return
    
    try:
        html_content = index_file.read_text(encoding='utf-8')
        
        # Replace all occurrences of the complete title
        html_content = html_content.replace('TwinShip Core Ontology (Complete)', 'TwinShip Ontology')
        
        index_file.write_text(html_content, encoding='utf-8')
        print(f"✓ Changed title to 'TwinShip Ontology'")
    except Exception as e:
        print(f"⚠ Warning: Failed to fix title: {e}")


def main():
    parser = argparse.ArgumentParser(
        description="Generate comprehensive web documentation using WIDOCO",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic usage
  python generate_widoco_docs.py model/twinship-core-complete-viz.ttl
  
  # Custom output directory
  python generate_widoco_docs.py -o docs/website model/twinship-core-complete-viz.ttl
  
  # Skip diagram generation (faster)
  python generate_widoco_docs.py --no-diagram model/twinship-core-complete-viz.ttl
  
Note: Requires Java 11 or later. WIDOCO jar will be downloaded automatically.
        """
    )
    
    parser.add_argument('input', help='Input ontology file (use merged+viz version)')
    parser.add_argument('-o', '--output', default='docs/website',
                       help='Output directory (default: docs/website)')
    parser.add_argument('--tools-dir', default='tools',
                       help='Directory for WIDOCO jar (default: tools)')
    parser.add_argument('--no-diagram', action='store_true',
                       help='Skip diagram generation (faster)')
    parser.add_argument('--no-crossref', action='store_true',
                       help='Skip cross-reference generation')
    parser.add_argument('--lang', default='en',
                       help='Documentation language (default: en)')
    
    args = parser.parse_args()
    
    print("=" * 70)
    print("TwinShip Ontology Documentation Generator (WIDOCO)")
    print("=" * 70)
    
    # Check Java
    if not check_java():
        return 1
    
    # Download WIDOCO if needed
    tools_dir = Path(args.tools_dir)
    jar_path = download_widoco(tools_dir)
    if not jar_path:
        return 1
    
    # Generate documentation
    success = run_widoco(
        jar_path=jar_path,
        input_file=args.input,
        output_dir=args.output,
        include_diagram=not args.no_diagram,
        include_crossref=not args.no_crossref,
        lang=args.lang
    )
    
    if success:
        create_index_redirect(args.output)
        fix_ontology_title(args.output)
        fix_webvowl_iframe_height(args.output)
        print("\n" + "=" * 70)
        print("Documentation generation complete!")
        print("=" * 70)
        print(f"\nTo view the documentation:")
        print(f"  1. Open: {Path(args.output).resolve() / 'index.html'}")
        print(f"  2. Or serve locally:")
        print(f"     cd {args.output} && python -m http.server 8000")
        print(f"     Then open: http://localhost:8000")
        return 0
    else:
        return 1


if __name__ == '__main__':
    sys.exit(main())
