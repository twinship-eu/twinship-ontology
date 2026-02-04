#!/usr/bin/env python3
"""
Generate Visualization-Friendly Ontology from Restrictions-Based Ontology

This script converts an OWL ontology that uses restrictions (owl:Restriction with 
owl:someValuesFrom) into a simplified version using rdfs:domain and rdfs:range.
The output is more suitable for visualization tools like OWLViz, WebVOWL, and UML diagrams.

Transformation rules:
1. Extract rdfs:domain from restrictions: Class -> Property association
2. Keep rdfs:range from property definitions or extract from someValuesFrom
3. Remove all blank node restrictions from class definitions
4. Keep only named superclass relationships
5. Preserve all property definitions and metadata

Usage:
    python generate_viz_ontology.py input.ttl output.ttl
    python generate_viz_ontology.py --format xml input.owl output.owl
"""

import argparse
import sys
from pathlib import Path
from rdflib import Graph, Namespace, RDF, RDFS, OWL, BNode, Literal
from rdflib.namespace import XSD


def extract_domain_from_restrictions(graph):
    """
    Extract rdfs:domain statements from owl:Restriction patterns.
    
    Returns a set of (property, class) tuples.
    """
    domains = set()
    
    # Find all classes with restrictions
    for cls in graph.subjects(RDF.type, OWL.Class):
        # Look for restrictions in subClassOf
        for parent in graph.objects(cls, RDFS.subClassOf):
            if isinstance(parent, BNode):
                # Check if it's a restriction
                if (parent, RDF.type, OWL.Restriction) in graph:
                    prop = graph.value(parent, OWL.onProperty)
                    if prop:
                        domains.add((prop, cls))
    
    return domains


def create_visualization_graph(source_graph):
    """
    Create a simplified graph suitable for visualization.
    """
    viz_graph = Graph()
    
    # Copy all namespace bindings
    for prefix, namespace in source_graph.namespaces():
        viz_graph.bind(prefix, namespace)
    
    # 1. Copy all property definitions (DataProperty and ObjectProperty)
    for prop_type in [OWL.DatatypeProperty, OWL.ObjectProperty]:
        for prop in source_graph.subjects(RDF.type, prop_type):
            # Copy all triples about this property
            for pred, obj in source_graph.predicate_objects(prop):
                viz_graph.add((prop, pred, obj))
    
    # 2. Extract and add domain information from restrictions
    domains = extract_domain_from_restrictions(source_graph)
    for prop, cls in domains:
        viz_graph.add((prop, RDFS.domain, cls))
    
    # 3. Copy class definitions (without blank node restrictions)
    for cls in source_graph.subjects(RDF.type, OWL.Class):
        # Add class type
        viz_graph.add((cls, RDF.type, OWL.Class))
        
        # Copy annotations (label, comment, etc.)
        for pred in [RDFS.label, RDFS.comment, RDFS.seeAlso, RDFS.isDefinedBy]:
            for obj in source_graph.objects(cls, pred):
                viz_graph.add((cls, pred, obj))
        
        # Copy only NAMED superclasses (skip blank node restrictions)
        for parent in source_graph.objects(cls, RDFS.subClassOf):
            if not isinstance(parent, BNode):
                viz_graph.add((cls, RDFS.subClassOf, parent))
    
    # 4. Copy ontology metadata
    for ontology in source_graph.subjects(RDF.type, OWL.Ontology):
        for pred, obj in source_graph.predicate_objects(ontology):
            viz_graph.add((ontology, pred, obj))
    
    # 5. Copy annotation properties
    for annot_prop in source_graph.subjects(RDF.type, OWL.AnnotationProperty):
        for pred, obj in source_graph.predicate_objects(annot_prop):
            viz_graph.add((annot_prop, pred, obj))
    
    # 6. Copy individuals (instances)
    for cls in source_graph.subjects(RDF.type, OWL.Class):
        for individual in source_graph.subjects(RDF.type, cls):
            if not isinstance(individual, BNode):
                for pred, obj in source_graph.predicate_objects(individual):
                    viz_graph.add((individual, pred, obj))
    
    return viz_graph


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
        description='Generate visualization-friendly ontology from restrictions-based ontology',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python generate_viz_ontology.py twinship-core.ttl twinship-core-viz.ttl
  python generate_viz_ontology.py --format xml input.owl output.owl
  python generate_viz_ontology.py --auto model/twinship-core.ttl

The --auto flag automatically creates output file with '-viz' suffix.
        """
    )
    
    parser.add_argument('input', help='Input ontology file (Turtle, RDF/XML, etc.)')
    parser.add_argument('output', nargs='?', help='Output ontology file')
    parser.add_argument('--format', choices=['turtle', 'xml', 'n3', 'nt', 'json-ld'],
                        help='Output format (default: auto-detect from extension)')
    parser.add_argument('--auto', action='store_true',
                        help='Auto-generate output filename with -viz suffix')
    parser.add_argument('--verbose', '-v', action='store_true',
                        help='Print verbose output')
    
    args = parser.parse_args()
    
    # Determine output file
    if args.auto:
        input_path = Path(args.input)
        output_path = input_path.parent / f"{input_path.stem}-viz{input_path.suffix}"
        args.output = str(output_path)
    elif not args.output:
        parser.error('Either provide output file or use --auto flag')
    
    # Determine formats
    input_format = get_format_from_extension(args.input)
    output_format = args.format or get_format_from_extension(args.output)
    
    if args.verbose:
        print(f"Input: {args.input} (format: {input_format})")
        print(f"Output: {args.output} (format: {output_format})")
    
    # Load source ontology
    try:
        if args.verbose:
            print("Loading source ontology...")
        source_graph = Graph()
        source_graph.parse(args.input, format=input_format)
        if args.verbose:
            print(f"  Loaded {len(source_graph)} triples")
    except Exception as e:
        print(f"Error loading input file: {e}", file=sys.stderr)
        sys.exit(1)
    
    # Generate visualization ontology
    try:
        if args.verbose:
            print("Generating visualization ontology...")
        viz_graph = create_visualization_graph(source_graph)
        if args.verbose:
            print(f"  Generated {len(viz_graph)} triples")
            
            # Count changes
            classes_before = len(list(source_graph.subjects(RDF.type, OWL.Class)))
            classes_after = len(list(viz_graph.subjects(RDF.type, OWL.Class)))
            domains_added = len(list(viz_graph.subject_objects(RDFS.domain)))
            
            print(f"\nStatistics:")
            print(f"  Classes: {classes_after}")
            print(f"  Domain assertions added: {domains_added}")
            print(f"  Triples reduced by: {len(source_graph) - len(viz_graph)}")
    except Exception as e:
        print(f"Error generating visualization ontology: {e}", file=sys.stderr)
        sys.exit(1)
    
    # Save output
    try:
        if args.verbose:
            print(f"\nSaving to {args.output}...")
        viz_graph.serialize(destination=args.output, format=output_format)
        if args.verbose:
            print("Done!")
    except Exception as e:
        print(f"Error saving output file: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
