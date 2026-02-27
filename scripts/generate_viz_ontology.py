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
from rdflib import Graph, Namespace, RDF, RDFS, OWL, BNode, Literal, URIRef
from rdflib.namespace import XSD

# Define namespaces to include in visualization
TWINSHIP_NAMESPACE = "https://twin-ship.eu/twinship"
IDO_NAMESPACE = "http://rds.posccaesar.org/ontology/lis14/rdl/"

# Namespaces to exclude from visualization (external ontologies)
EXCLUDED_NAMESPACES = [
    "http://www.w3.org/2006/time",
    "http://www.opengis.net/ont/geosparql",
    "http://qudt.org/",
    "http://purl.org/pav/",
    "http://www.vesselAI-project.eu/vesselai",
    "http://www.ontologydesignpatterns.org/ont/dul/",
    "http://rds.posccaesar.org/ontology/lis14/ont/core",
]


def should_include_entity(uri, is_property=False, used_external_properties=None, used_external_classes=None):
    """
    Determine if an entity (class or property) should be included in visualization.
    
    Args:
        uri: The URI to check
        is_property: Whether the URI represents a property
        used_external_properties: Set of external properties actually used in TwinShip
        used_external_classes: Set of external classes actually used in TwinShip
    
    Returns:
        True if entity should be included, False otherwise
    """
    if not isinstance(uri, URIRef):
        return False
    
    uri_str = str(uri)
    
    # Always include TwinShip entities
    if uri_str.startswith(TWINSHIP_NAMESPACE):
        return True
    
    # Always include XSD datatypes for datatype property ranges
    if uri_str.startswith('http://www.w3.org/2001/XMLSchema#'):
        return True
    
    # For properties: include IDO properties that are actually used
    if is_property and used_external_properties:
        if uri in used_external_properties:
            return True
    
    # For classes: include IDO classes that are actually used
    if not is_property and used_external_classes:
        if uri in used_external_classes:
            return True
    
    # Exclude entities from external ontologies
    for excluded_ns in EXCLUDED_NAMESPACES:
        if uri_str.startswith(excluded_ns):
            return False
    
    # For anything else (including IDO classes not explicitly used), exclude
    # This ensures we only show what's directly relevant to TwinShip
    return False


def extract_domain_range_from_restrictions(graph):
    """
    Extract rdfs:domain and rdfs:range from owl:Restriction patterns.
    Also identifies external properties and classes that are used with TwinShip classes.
    
    Returns:
        domains: set of (property, domain_class) tuples
        ranges: set of (property, range_class) tuples
        used_external_properties: set of external property URIs used in TwinShip
        used_external_classes: set of external class URIs used in TwinShip
    """
    domains = set()
    ranges = set()
    used_external_properties = set()
    used_external_classes = set()
    
    # Find all classes with restrictions
    for cls in graph.subjects(RDF.type, OWL.Class):
        # Only process TwinShip classes
        cls_str = str(cls) if isinstance(cls, URIRef) else ""
        if not cls_str.startswith(TWINSHIP_NAMESPACE):
            continue
            
        # Check superclasses for external classes
        for parent in graph.objects(cls, RDFS.subClassOf):
            if isinstance(parent, URIRef):
                parent_str = str(parent)
                if parent_str.startswith(IDO_NAMESPACE):
                    used_external_classes.add(parent)
            elif isinstance(parent, BNode):
                # Check if it's a restriction
                if (parent, RDF.type, OWL.Restriction) in graph:
                    prop = graph.value(parent, OWL.onProperty)
                    if prop:
                        # Track external properties used in TwinShip classes
                        if isinstance(prop, URIRef):
                            prop_str = str(prop)
                            if not prop_str.startswith(TWINSHIP_NAMESPACE):
                                if prop_str.startswith(IDO_NAMESPACE):
                                    used_external_properties.add(prop)
                        
                        domains.add((prop, cls))
                        
                        # Also extract range from someValuesFrom or allValuesFrom
                        range_class = graph.value(parent, OWL.someValuesFrom)
                        if not range_class:
                            range_class = graph.value(parent, OWL.allValuesFrom)
                        
                        # Track all ranges including XSD datatypes
                        if range_class and isinstance(range_class, URIRef):
                            range_str = str(range_class)
                            ranges.add((prop, range_class))
                            # Track external classes (non-XSD)
                            if not range_str.startswith('http://www.w3.org/2001/XMLSchema#'):
                                if range_str.startswith(IDO_NAMESPACE):
                                    used_external_classes.add(range_class)
    
    return domains, ranges, used_external_properties, used_external_classes


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


def create_visualization_graph(source_graph, create_virtual_properties=True):
    """
    Create a simplified graph suitable for visualization.
    Filters external ontologies to show only TwinShip and used IDO properties/classes.
    Preserves multiple domains/ranges per property to show all relationships.
    
    Args:
        source_graph: The source RDF graph to process
        create_virtual_properties: If True, creates virtual duplicate properties (prop_viz1, prop_viz2)
                                   for properties with multiple domains to avoid blank union nodes.
                                   If False, adds all domains directly (for documentation).
    """
    viz_graph = Graph()
    
    # Copy all namespace bindings
    for prefix, namespace in source_graph.namespaces():
        viz_graph.bind(prefix, namespace)
    
    # First pass: extract domain/range from restrictions to identify used external entities
    domains, ranges, used_external_properties, used_external_classes = extract_domain_range_from_restrictions(source_graph)
    
    # Track which properties have which domains/ranges (don't add to graph yet)
    property_domains = {}  # prop -> set of domain classes
    property_ranges = {}   # prop -> set of range classes
    
    # 1. Copy property definitions (DataProperty and ObjectProperty) - with filtering
    # Collect domain/range info but don't add to graph yet (to handle duplicates later)
    for prop_type in [OWL.DatatypeProperty, OWL.ObjectProperty]:
        for prop in source_graph.subjects(RDF.type, prop_type):
            # Filter: only include TwinShip properties and used external properties
            if not should_include_entity(prop, is_property=True, used_external_properties=used_external_properties):
                continue
            
            # Initialize sets for this property
            if prop not in property_domains:
                property_domains[prop] = set()
            if prop not in property_ranges:
                property_ranges[prop] = set()
            
            # Copy property type and metadata (but NOT domain/range yet)
            for pred, obj in source_graph.predicate_objects(prop):
                if pred == RDFS.domain:
                    # Track domain (don't add to viz_graph yet)
                    if isinstance(obj, BNode):
                        union_classes = extract_union_classes(source_graph, obj)
                        for cls in union_classes:
                            if should_include_entity(cls, used_external_classes=used_external_classes):
                                property_domains[prop].add(cls)
                    else:
                        if should_include_entity(obj, used_external_classes=used_external_classes):
                            property_domains[prop].add(obj)
                elif pred == RDFS.range:
                    # Track range (don't add to viz_graph yet)
                    if isinstance(obj, BNode):
                        union_classes = extract_union_classes(source_graph, obj)
                        for cls in union_classes:
                            if should_include_entity(cls, used_external_classes=used_external_classes):
                                property_ranges[prop].add(cls)
                    else:
                        if should_include_entity(obj, used_external_classes=used_external_classes):
                            property_ranges[prop].add(obj)
                else:
                    # Copy other properties (type, labels, comments, etc.)
                    viz_graph.add((prop, pred, obj))
    
    # Add domain/range from restrictions to the tracking sets
    for prop, cls in domains:
        if not should_include_entity(prop, is_property=True, used_external_properties=used_external_properties):
            continue
        if not should_include_entity(cls, used_external_classes=used_external_classes):
            continue
        
        if prop not in property_domains:
            property_domains[prop] = set()
        property_domains[prop].add(cls)
    
    for prop, cls in ranges:
        if not should_include_entity(prop, is_property=True, used_external_properties=used_external_properties):
            continue
        if not should_include_entity(cls, used_external_classes=used_external_classes):
            continue
        
        if prop not in property_ranges:
            property_ranges[prop] = set()
        property_ranges[prop].add(cls)
    
    # 2. Handle properties with multiple domains
    # If create_virtual_properties=True: create virtual duplicates to avoid blank union nodes in WebVOWL
    # If create_virtual_properties=False: add all domains directly (for documentation)
    
    # Get all properties from both domains and ranges
    all_properties = set(property_domains.keys()) | set(property_ranges.keys())
    
    for prop in all_properties:
        domains_list = list(property_domains.get(prop, set()))
        ranges_list = list(property_ranges.get(prop, set()))
        
        # Get property metadata
        prop_label = viz_graph.value(prop, RDFS.label) or source_graph.value(prop, RDFS.label)
        prop_comment = viz_graph.value(prop, RDFS.comment) or source_graph.value(prop, RDFS.comment)
        prop_type = viz_graph.value(prop, RDF.type) or source_graph.value(prop, RDF.type)
        if prop_type not in [OWL.ObjectProperty, OWL.DatatypeProperty]:
            prop_type = OWL.ObjectProperty
        
        if len(domains_list) <= 1:
            # Single or no domain - add normally to the original property
            # Ensure property has type in viz_graph
            if not (prop, RDF.type, prop_type) in viz_graph:
                viz_graph.add((prop, RDF.type, prop_type))
            
            if domains_list:
                viz_graph.add((prop, RDFS.domain, domains_list[0]))
            if ranges_list:
                viz_graph.add((prop, RDFS.range, ranges_list[0]))
        elif create_virtual_properties:
            # Multiple domains - create ONLY virtual duplicates for each (for WebVOWL)
            # Remove the base property from viz_graph (it's already there from step 1)
            viz_graph.remove((prop, RDF.type, prop_type))
            # Remove any other metadata of base property
            for pred, obj in list(viz_graph.predicate_objects(prop)):
                viz_graph.remove((prop, pred, obj))
            
            # Use single range (first one) for all virtual properties
            prop_range = ranges_list[0] if ranges_list else None
            
            for idx, domain in enumerate(domains_list):
                # Create virtual property URI in TwinShip namespace
                # Extract local name from property (works for both # and / URIs)
                prop_str = str(prop)
                if '#' in prop_str:
                    local_name = prop_str.split('#')[-1]
                elif '/' in prop_str:
                    local_name = prop_str.split('/')[-1]
                else:
                    local_name = prop_str
                virtual_prop = URIRef(f"{TWINSHIP_NAMESPACE}#{local_name}_viz{idx + 1}")
                
                # Add property type
                viz_graph.add((virtual_prop, RDF.type, prop_type))
                
                # Copy label and comment (same for all duplicates)
                if prop_label:
                    viz_graph.add((virtual_prop, RDFS.label, prop_label))
                if prop_comment:
                    viz_graph.add((virtual_prop, RDFS.comment, prop_comment))
                
                # Add single domain and range
                viz_graph.add((virtual_prop, RDFS.domain, domain))
                if prop_range:
                    viz_graph.add((virtual_prop, RDFS.range, prop_range))
                
                # Copy other property assertions from original  
                for pred in [RDFS.subPropertyOf, RDFS.seeAlso, RDFS.isDefinedBy]:
                    if (prop, pred, URIRef) in source_graph:
                        for obj in source_graph.objects(prop, pred):
                            viz_graph.add((virtual_prop, pred, obj))
        else:
            # Multiple domains - add all directly to original property (for WIDOCO)
            # Ensure property has type in viz_graph
            if not (prop, RDF.type, prop_type) in viz_graph:
                viz_graph.add((prop, RDF.type, prop_type))
            
            for domain in domains_list:
                viz_graph.add((prop, RDFS.domain, domain))
            # Add single range (or first one if multiple)
            if ranges_list:
                viz_graph.add((prop, RDFS.range, ranges_list[0]))
    
    # 3. Copy class definitions (without blank node restrictions) - with filtering
    for cls in source_graph.subjects(RDF.type, OWL.Class):
        # Filter: only include TwinShip and actually used external classes
        if not should_include_entity(cls, used_external_classes=used_external_classes):
            continue
            
        # Add class type
        viz_graph.add((cls, RDF.type, OWL.Class))
        
        # Copy annotations (label, comment, etc.)
        for pred in [RDFS.label, RDFS.comment, RDFS.seeAlso, RDFS.isDefinedBy]:
            for obj in source_graph.objects(cls, pred):
                viz_graph.add((cls, pred, obj))
        
        # Copy only NAMED superclasses (skip blank node restrictions) - with filtering
        for parent in source_graph.objects(cls, RDFS.subClassOf):
            if not isinstance(parent, BNode) and should_include_entity(parent, used_external_classes=used_external_classes):
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
    
    # 5. Copy annotation properties - include all since they don't affect visualization
    # but are important for documentation (skos:notation, skos:altLabel, dcterms:description, etc.)
    for annot_prop in source_graph.subjects(RDF.type, OWL.AnnotationProperty):
        # Include TwinShip properties and any other annotation properties in the source
        # (they've already been filtered by generate_docs_ontology.py if needed)
        for pred, obj in source_graph.predicate_objects(annot_prop):
            viz_graph.add((annot_prop, pred, obj))
    
    # 6. Copy individuals (instances) - with filtering
    for cls in source_graph.subjects(RDF.type, OWL.Class):
        # Only process TwinShip and used external classes
        if not should_include_entity(cls, used_external_classes=used_external_classes):
            continue
        for individual in source_graph.subjects(RDF.type, cls):
            if not isinstance(individual, BNode) and should_include_entity(individual, used_external_classes=used_external_classes):
                for pred, obj in source_graph.predicate_objects(individual):
                    viz_graph.add((individual, pred, obj))
    
    # 7. Declare XSD datatypes that are used in rdfs:range for WebVOWL compatibility
    # Collect all unique XSD datatypes used as ranges
    xsd_datatypes_used = set()
    for s, p, o in viz_graph.triples((None, RDFS.range, None)):
        if isinstance(o, URIRef) and str(o).startswith('http://www.w3.org/2001/XMLSchema#'):
            xsd_datatypes_used.add(o)
    
    # Declare each XSD datatype as rdfs:Datatype so OWL2VOWL recognizes them
    for xsd_type in xsd_datatypes_used:
        viz_graph.add((xsd_type, RDF.type, RDFS.Datatype))
        # Add label for WebVOWL display
        type_name = str(xsd_type).split('#')[-1]
        viz_graph.add((xsd_type, RDFS.label, Literal(type_name)))
    
    if xsd_datatypes_used:
        print(f"Declared {len(xsd_datatypes_used)} XSD datatypes: {sorted([str(x).split('#')[-1] for x in xsd_datatypes_used])}")
    
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
    parser.add_argument('--no-virtual-properties', action='store_true',
                        help='Do not create virtual duplicate properties for multi-domain properties (for WIDOCO docs)')
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
            print("  Filtering external ontologies (time, geosparql, qudt, etc.)")
            print("  Keeping TwinShip classes and used IDO properties...")
            if args.no_virtual_properties:
                print("  Adding all domains directly (no virtual properties)")
            else:
                print("  Creating virtual duplicate properties for multi-domain properties...")
        viz_graph = create_visualization_graph(source_graph, create_virtual_properties=not args.no_virtual_properties)
        if args.verbose:
            print(f"  Generated {len(viz_graph)} triples")
            
            # Count changes
            classes_before = len(list(source_graph.subjects(RDF.type, OWL.Class)))
            classes_after = len(list(viz_graph.subjects(RDF.type, OWL.Class)))
            props_after = len(list(viz_graph.subjects(RDF.type, OWL.ObjectProperty))) + \
                         len(list(viz_graph.subjects(RDF.type, OWL.DatatypeProperty)))
            domains_added = len(list(viz_graph.subject_objects(RDFS.domain)))
            
            print(f"\nStatistics:")
            print(f"  Classes: {classes_after} (filtered from {classes_before})")
            print(f"  Properties: {props_after}")
            print(f"  Domain assertions: {domains_added}")
            print(f"  Triples: {len(viz_graph)} (reduced from {len(source_graph)})")
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
