#!/usr/bin/env python3
"""
Merge Modular Ontology into Single Complete File

This script takes an ontology that imports multiple modules and merges everything
into a single, self-contained ontology file. It recursively resolves all owl:imports
and combines them into one graph.

This is useful for:
- Documentation generation tools (LODE, Widoco, pyLODE)
- Visualization tools that don't handle imports well
- Distribution as a single file
- Reasoners that prefer complete ontologies

Usage:
    python merge_modules.py input.ttl output-complete.ttl
    python merge_modules.py --base-uri https://twin-ship.eu/ input.ttl output.ttl
    python merge_modules.py --auto model/twinship-core.ttl
"""

import argparse
import sys
from pathlib import Path
from urllib.parse import urlparse
from rdflib import Graph, Namespace, RDF, RDFS, OWL, URIRef
from rdflib.namespace import XSD


def resolve_import_path(ontology_uri, base_path, catalog_file=None):
    """
    Resolve an import URI to a local file path.
    
    Tries multiple strategies:
    1. Check catalog-v001.xml for mappings
    2. Check if URI is a file:// URI
    3. Check relative to base_path
    4. Return URI as-is (will try to fetch from web)
    """
    # Strategy 1: Check catalog file
    if catalog_file and catalog_file.exists():
        try:
            import xml.etree.ElementTree as ET
            tree = ET.parse(catalog_file)
            root = tree.getroot()
            
            # Find matching URI in catalog
            for uri_elem in root.findall('.//{urn:oasis:names:tc:entity:xmlns:xml:catalog}uri'):
                if uri_elem.get('name') == str(ontology_uri):
                    rel_path = uri_elem.get('uri')
                    resolved = (catalog_file.parent / rel_path).resolve()
                    if resolved.exists():
                        return resolved
        except Exception as e:
            pass  # Catalog parsing failed, try other strategies
    
    # Strategy 2: file:// URI
    if str(ontology_uri).startswith('file://'):
        path = Path(urlparse(str(ontology_uri)).path)
        if path.exists():
            return path
    
    # Strategy 3: Relative to base path
    # Try common patterns
    uri_str = str(ontology_uri)
    
    # Extract filename from URI
    if '#' in uri_str:
        uri_str = uri_str.split('#')[0]
    
    possible_paths = [
        base_path / Path(urlparse(uri_str).path).name,  # Just filename
        base_path / 'modules' / Path(urlparse(uri_str).path).name,
        base_path / 'external' / Path(urlparse(uri_str).path).name,
    ]
    
    for path in possible_paths:
        if path.exists():
            return path
    
    # Strategy 4: Return URI (will attempt web fetch)
    return ontology_uri


def merge_ontology(source_file, base_path=None, catalog_file=None, visited=None, verbose=False):
    """
    Recursively merge an ontology and all its imports into a single graph.
    
    Args:
        source_file: Path to the main ontology file
        base_path: Base directory for resolving relative imports
        catalog_file: Path to catalog-v001.xml for URI resolution
        visited: Set of already processed files (to avoid cycles)
        verbose: Print verbose output
    
    Returns:
        rdflib.Graph containing merged ontology
    """
    if visited is None:
        visited = set()
    
    source_path = Path(source_file).resolve()
    
    # Avoid circular imports
    if source_path in visited:
        return Graph()
    
    visited.add(source_path)
    
    if base_path is None:
        base_path = source_path.parent
    
    if verbose:
        print(f"Processing: {source_path}")
    
    # Load the source ontology
    graph = Graph()
    try:
        graph.parse(source_path)
        if verbose:
            print(f"  Loaded {len(graph)} triples")
    except Exception as e:
        print(f"Error loading {source_path}: {e}", file=sys.stderr)
        return Graph()
    
    # Find all imports
    imports = list(graph.objects(predicate=OWL.imports))
    
    if verbose and imports:
        print(f"  Found {len(imports)} imports")
    
    # Process each import
    for import_uri in imports:
        if verbose:
            print(f"  Resolving import: {import_uri}")
        
        # Resolve to local file
        import_path = resolve_import_path(import_uri, base_path, catalog_file)
        
        if isinstance(import_path, Path):
            if import_path.exists():
                if verbose:
                    print(f"    → {import_path}")
                # Recursively merge imported ontology
                imported_graph = merge_ontology(
                    import_path, 
                    base_path, 
                    catalog_file, 
                    visited, 
                    verbose
                )
                # Add all triples from imported ontology
                graph += imported_graph
            else:
                print(f"Warning: Could not find import: {import_path}", file=sys.stderr)
        else:
            # Try to fetch from web
            try:
                if verbose:
                    print(f"    → Fetching from web")
                temp_graph = Graph()
                temp_graph.parse(import_uri)
                graph += temp_graph
                if verbose:
                    print(f"    → Loaded {len(temp_graph)} triples from web")
            except Exception as e:
                print(f"Warning: Could not load import {import_uri}: {e}", file=sys.stderr)
    
    return graph


def clean_merged_ontology(graph, remove_imports=True):
    """
    Clean up the merged ontology.
    
    Args:
        graph: The merged RDF graph
        remove_imports: If True, remove owl:imports statements (default: True)
    
    Returns:
        Cleaned graph
    """
    if remove_imports:
        # Remove all owl:imports statements since everything is now merged
        graph.remove((None, OWL.imports, None))
    
    return graph


def get_format_from_extension(filepath):
    """Determine RDF format from file extension."""
    ext = Path(filepath).suffix.lower()
    format_map = {
        '.ttl': 'turtle',
        '.rdf': 'xml',
        '.owl': 'xml',
        '.n3': 'n3',
        '.nt': 'nt',
        '.jsonld': 'json-ld',
    }
    return format_map.get(ext, 'turtle')


def main():
    parser = argparse.ArgumentParser(
        description='Merge modular ontology into single complete file',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python merge_modules.py model/twinship-core.ttl model/twinship-complete.ttl
  python merge_modules.py --auto model/twinship-core.ttl
  python merge_modules.py --catalog model/catalog-v001.xml model/twinship-core.ttl output.ttl
  python merge_modules.py --keep-imports --verbose input.ttl output.ttl

The --auto flag automatically creates output file with '-complete' suffix.
        """
    )
    
    parser.add_argument('input', help='Input ontology file (with imports)')
    parser.add_argument('output', nargs='?', help='Output merged ontology file')
    parser.add_argument('--catalog', help='Path to catalog-v001.xml for URI resolution')
    parser.add_argument('--format', choices=['turtle', 'xml', 'n3', 'nt', 'json-ld'],
                        help='Output format (default: auto-detect from extension)')
    parser.add_argument('--auto', action='store_true',
                        help='Auto-generate output filename with -complete suffix')
    parser.add_argument('--keep-imports', action='store_true',
                        help='Keep owl:imports statements in merged file (default: remove)')
    parser.add_argument('--verbose', '-v', action='store_true',
                        help='Print verbose output')
    
    args = parser.parse_args()
    
    # Determine output file
    if args.auto:
        input_path = Path(args.input)
        output_path = input_path.parent / f"{input_path.stem}-complete{input_path.suffix}"
        args.output = str(output_path)
    elif not args.output:
        parser.error('Either provide output file or use --auto flag')
    
    # Determine catalog file
    catalog_file = None
    if args.catalog:
        catalog_file = Path(args.catalog)
    else:
        # Try to find catalog-v001.xml in same directory as input
        default_catalog = Path(args.input).parent / 'catalog-v001.xml'
        if default_catalog.exists():
            catalog_file = default_catalog
            if args.verbose:
                print(f"Using catalog: {catalog_file}")
    
    # Determine formats
    input_format = get_format_from_extension(args.input)
    output_format = args.format or get_format_from_extension(args.output)
    
    if args.verbose:
        print(f"Input: {args.input} (format: {input_format})")
        print(f"Output: {args.output} (format: {output_format})")
        print()
    
    # Merge ontologies
    try:
        merged_graph = merge_ontology(
            args.input,
            catalog_file=catalog_file,
            verbose=args.verbose
        )
        
        if args.verbose:
            print(f"\nMerged ontology statistics:")
            print(f"  Total triples: {len(merged_graph)}")
            print(f"  Classes: {len(list(merged_graph.subjects(RDF.type, OWL.Class)))}")
            print(f"  Data properties: {len(list(merged_graph.subjects(RDF.type, OWL.DatatypeProperty)))}")
            print(f"  Object properties: {len(list(merged_graph.subjects(RDF.type, OWL.ObjectProperty)))}")
        
        # Clean up
        merged_graph = clean_merged_ontology(merged_graph, remove_imports=not args.keep_imports)
        
        # Save output
        if args.verbose:
            print(f"\nSaving to {args.output}...")
        merged_graph.serialize(destination=args.output, format=output_format)
        
        if args.verbose:
            print("Done!")
        
    except Exception as e:
        print(f"Error merging ontologies: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
