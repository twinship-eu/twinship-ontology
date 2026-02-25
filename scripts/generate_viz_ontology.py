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


def extract_domain_range_from_restrictions(graph):
    """
    Extract rdfs:domain and rdfs:range from owl:Restriction patterns.
    
    Returns:
        domains: set of (property, domain_class) tuples
        ranges: set of (property, range_class) tuples
    """
    domains = set()
    ranges = set()
    
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
                        
                        # Also extract range from someValuesFrom or allValuesFrom
                        range_class = graph.value(parent, OWL.someValuesFrom)
                        if not range_class:
                            range_class = graph.value(parent, OWL.allValuesFrom)
                        
                        # Only add named classes (not blank nodes, literals, or datatypes)
                        if range_class and not isinstance(range_class, BNode):
                            # Check if it's a class (not a datatype like xsd:string)
                            range_str = str(range_class)
                            if not range_str.startswith('http://www.w3.org/2001/XMLSchema#'):
                                ranges.add((prop, range_class))
    
    return domains, ranges


def extract_union_classes(graph, union_node):
    """
    Extract all classes from an owl:unionOf structure.
    Returns a list of URIRefs for the classes in the union.
    """
    classes = []
    union_list = graph.value(union_node, OWL.unionOf)
    if union_list:
        # Traverse the RDF list
        from rdflib.collection import Collection
        try:
            for item in Collection(graph, union_list):
                if not isinstance(item, BNode):
                    classes.append(item)
        except:
            # Fallback: manual list traversal
            current = union_list
            while current and current != RDF.nil:
                first = graph.value(current, RDF.first)
                if first and not isinstance(first, BNode):
                    classes.append(first)
                current = graph.value(current, RDF.rest)
    return classes


def create_visualization_graph(source_graph):
    """
    Create a simplified graph suitable for visualization.
    Flattens owl:unionOf in domain/range to avoid blank nodes in WebVOWL.
    """
    viz_graph = Graph()
    
    # Copy all namespace bindings
    for prefix, namespace in source_graph.namespaces():
        viz_graph.bind(prefix, namespace)
    
    # Track which properties already have domain/range to avoid multiples
    # WIDOCO creates unionOf nodes when it sees multiple domain/range assertions
    property_domains = {}
    property_ranges = {}
    
    # 1. Copy all property definitions (DataProperty and ObjectProperty)
    # Handle domain/range with special care for unionOf
    for prop_type in [OWL.DatatypeProperty, OWL.ObjectProperty]:
        for prop in source_graph.subjects(RDF.type, prop_type):
            # Copy all triples about this property, except domain/range
            for pred, obj in source_graph.predicate_objects(prop):
                if pred == RDFS.domain:
                    # Only add ONE domain per property to avoid WIDOCO creating unions
                    if prop not in property_domains:
                        # Check if it's a blank node with unionOf
                        if isinstance(obj, BNode):
                            union_classes = extract_union_classes(source_graph, obj)
                            if union_classes:
                                # Pick ONLY THE FIRST class
                                viz_graph.add((prop, pred, union_classes[0]))
                                property_domains[prop] = union_classes[0]
                        else:
                            # Regular named class - add as is
                            viz_graph.add((prop, pred, obj))
                            property_domains[prop] = obj
                elif pred == RDFS.range:
                    # Only add ONE range per property to avoid WIDOCO creating unions
                    if prop not in property_ranges:
                        # Check if it's a blank node with unionOf
                        if isinstance(obj, BNode):
                            union_classes = extract_union_classes(source_graph, obj)
                            if union_classes:
                                # Pick ONLY THE FIRST class
                                viz_graph.add((prop, pred, union_classes[0]))
                                property_ranges[prop] = union_classes[0]
                        else:
                            # Regular named class - add as is
                            viz_graph.add((prop, pred, obj))
                            property_ranges[prop] = obj
                else:
                    # Copy other properties as is
                    viz_graph.add((prop, pred, obj))
    
    # 2. Extract and add domain/range information from restrictions
    # Only add if not already set (to avoid multiple domains/ranges -> union nodes)
    domains, ranges = extract_domain_range_from_restrictions(source_graph)
    
    # Collect all properties found in restrictions
    restriction_properties = set()
    
    for prop, cls in domains:
        restriction_properties.add(prop)
        if prop not in property_domains:
            viz_graph.add((prop, RDFS.domain, cls))
            property_domains[prop] = cls
    
    for prop, cls in ranges:
        restriction_properties.add(prop)
        if prop not in property_ranges:
            viz_graph.add((prop, RDFS.range, cls))
            property_ranges[prop] = cls
    
    # Ensure properties from restrictions are typed as ObjectProperty
    # (They might be from external ontologies without explicit type in merged file)
    for prop in restriction_properties:
        # Check if property doesn't have a type yet in viz_graph
        if not (prop, RDF.type, OWL.ObjectProperty) in viz_graph and \
           not (prop, RDF.type, OWL.DatatypeProperty) in viz_graph:
            # Add it as ObjectProperty (since it connects classes)
            viz_graph.add((prop, RDF.type, OWL.ObjectProperty))
            # Try to copy label and comment from source
            for pred in [RDFS.label, RDFS.comment]:
                for obj in source_graph.objects(prop, pred):
                    viz_graph.add((prop, pred, obj))
    
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
    
    # 4. Copy ontology metadata - prefer the core ontology for documentation
    core_ontology = None
    all_ontologies = list(source_graph.subjects(RDF.type, OWL.Ontology))
    
    # First, look for the core ontology
    for ontology in all_ontologies:
        if str(ontology).endswith("/core"):
            core_ontology = ontology
            break
    
    # If core not found, use the first one
    if not core_ontology and all_ontologies:
        core_ontology = all_ontologies[0]
    
    # Copy only the core/main ontology metadata
    if core_ontology:
        for pred, obj in source_graph.predicate_objects(core_ontology):
            viz_graph.add((core_ontology, pred, obj))
    
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
