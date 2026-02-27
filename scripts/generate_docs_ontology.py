#!/usr/bin/env python3
"""
Generate Documentation-Only Ontology

Creates a version of the TwinShip ontology suitable for documentation
that includes TwinShip-defined classes, properties, individuals, and 
external properties (IDO) that are actually used by TwinShip classes.

Other external ontology content (QUDT, GeoSPARQL, time, etc.) is excluded.
Import statements are also removed to prevent WIDOCO from following them.

Usage:
    python generate_docs_ontology.py model/twinship-core-complete.ttl
    python generate_docs_ontology.py -o output.ttl model/twinship-core-complete.ttl
"""

import argparse
import sys
from pathlib import Path
from rdflib import Graph, Namespace, RDF, RDFS, OWL, URIRef, BNode
from rdflib.namespace import SKOS, DCTERMS


# TwinShip namespaces
TWINSHIP_BASE = "https://twin-ship.eu/twinship"
TWINSHIP_NAMESPACES = [
    "https://twin-ship.eu/twinship",
    "https://twin-ship.eu/twinship/base",
    "https://twin-ship.eu/twinship/core", 
    "https://twin-ship.eu/twinship/vessel",
    "https://twin-ship.eu/twinship/weatherconditions",
    "https://twin-ship.eu/twinship/draft_time_mode",
    "https://twin-ship.eu/twinship#",  # Hash URI namespace
]

# IDO namespace - we want to include properties from here that are used
IDO_NAMESPACE = "http://rds.posccaesar.org/ontology/lis14/rdl/"


def is_twinship_resource(uri):
    """Check if a resource belongs to TwinShip ontology."""
    if not isinstance(uri, URIRef):
        return False
    uri_str = str(uri)
    # Check if it starts with the TwinShip base or any specific namespace
    return uri_str.startswith(TWINSHIP_BASE)


def extract_used_external_entities(graph):
    """
    Extract which external properties and classes are actually used by TwinShip classes.
    Returns sets of used external property URIs, class URIs, and annotation properties.
    """
    used_external_properties = set()
    used_external_classes = set()
    used_annotation_properties = set()
    
    # Find all annotation properties actually used
    for s, p, o in graph:
        # If predicate is an annotation property, include it
        if (p, RDF.type, OWL.AnnotationProperty) in graph:
            # Only include if it's used on a TwinShip resource
            if isinstance(s, URIRef) and is_twinship_resource(s):
                used_annotation_properties.add(p)
    
    # Find all TwinShip classes with restrictions
    for cls in graph.subjects(RDF.type, OWL.Class):
        # Only process TwinShip classes
        cls_str = str(cls) if isinstance(cls, URIRef) else ""
        if not cls_str.startswith(TWINSHIP_BASE):
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
                    if prop and isinstance(prop, URIRef):
                        prop_str = str(prop)
                        # Track external properties used in TwinShip classes
                        if prop_str.startswith(IDO_NAMESPACE):
                            used_external_properties.add(prop)
                        
                        # Also extract range from someValuesFrom or allValuesFrom
                        range_class = graph.value(parent, OWL.someValuesFrom)
                        if not range_class:
                            range_class = graph.value(parent, OWL.allValuesFrom)
                        
                        # Track external classes used in ranges
                        if range_class and isinstance(range_class, URIRef):
                            range_str = str(range_class)
                            if range_str.startswith(IDO_NAMESPACE):
                                used_external_classes.add(range_class)
    
    return used_external_properties, used_external_classes, used_annotation_properties


def generate_docs_ontology(input_file, output_file):
    """
    Generate documentation-friendly ontology with TwinShip content and used external properties.
    """
    print(f"Loading ontology: {input_file}")
    g = Graph()
    g.parse(input_file)
    
    print(f"Original graph: {len(g)} triples")
    
    # Extract which external properties and classes are actually used
    used_external_properties, used_external_classes, used_annotation_properties = extract_used_external_entities(g)
    print(f"Found {len(used_external_properties)} used external properties")
    print(f"Found {len(used_external_classes)} used external classes")
    print(f"Found {len(used_annotation_properties)} used annotation properties")
    
    # Create new graph for documentation
    docs_graph = Graph()
    
    # Copy all namespaces
    for prefix, namespace in g.namespaces():
        docs_graph.bind(prefix, namespace)
    
    # Track statistics
    stats = {
        'classes': 0,
        'object_properties': 0,
        'datatype_properties': 0,
        'annotation_properties': 0,
        'individuals': 0,
        'other_triples': 0,
    }
    
    # First pass: Find all TwinShip resources and used external entities
    resources_to_include = set()
    
    for s, p, o in g:
        # Include TwinShip resources
        if isinstance(s, URIRef) and is_twinship_resource(s):
            resources_to_include.add(s)
        # Include used external properties, classes, and annotation properties
        if isinstance(s, URIRef):
            if s in used_external_properties or s in used_external_classes or s in used_annotation_properties:
                resources_to_include.add(s)
        # Keep if object is a TwinShip class/property being defined
        if isinstance(o, URIRef) and is_twinship_resource(o):
            if p in [RDFS.subClassOf, RDFS.subPropertyOf, RDFS.domain, RDFS.range]:
                resources_to_include.add(o)
        # Include XSD datatypes used in ranges (for WebVOWL compatibility)
        if p == RDFS.range and isinstance(o, URIRef):
            if str(o).startswith('http://www.w3.org/2001/XMLSchema#'):
                resources_to_include.add(o)
    
    print(f"Found {len(resources_to_include)} resources to include (TwinShip + used external)")
    
    # Second pass: Collect blank nodes related to resources we're including
    related_bnodes = set()
    
    for s, p, o in g:
        # If subject is a resource we're including and object is a blank node
        if isinstance(s, URIRef) and s in resources_to_include:
            if not isinstance(o, URIRef):  # Blank node or literal
                if hasattr(o, 'n3') and o.n3().startswith('_:'):  # It's a blank node
                    related_bnodes.add(o)
    
    # Recursively find all blank nodes referenced by restrictions
    def find_nested_bnodes(bnode):
        """Recursively find all blank nodes nested within a blank node."""
        nested = set()
        for s, p, o in g.triples((bnode, None, None)):
            if hasattr(o, 'n3') and o.n3().startswith('_:'):
                nested.add(o)
                nested.update(find_nested_bnodes(o))
        return nested
    
    # Expand to include nested blank nodes
    all_bnodes = set(related_bnodes)
    for bnode in related_bnodes:
        all_bnodes.update(find_nested_bnodes(bnode))
    
    print(f"Found {len(all_bnodes)} related blank nodes (restrictions, etc.)")
    
    # Third pass: Copy all triples about included resources and related blank nodes
    for s, p, o in g:
        # Skip triples where subject is NOT an included resource or related blank node
        if isinstance(s, URIRef) and s not in resources_to_include:
            continue
        
        # Include blank nodes that are related to included resources
        if hasattr(s, 'n3') and s.n3().startswith('_:') and s not in all_bnodes:
            continue
        
        # Skip owl:imports - we'll add these separately
        if p == OWL.imports:
            continue
            
        # Add the triple
        docs_graph.add((s, p, o))
        
        # Count by type
        if p == RDF.type:
            if o == OWL.Class or o == RDFS.Class:
                stats['classes'] += 1
            elif o == OWL.ObjectProperty:
                stats['object_properties'] += 1
            elif o == OWL.DatatypeProperty:
                stats['datatype_properties'] += 1
            elif o == OWL.AnnotationProperty:
                stats['annotation_properties'] += 1
            elif o == OWL.NamedIndividual:
                stats['individuals'] += 1
        else:
            stats['other_triples'] += 1
    
    # Add back owl:imports for external ontologies (for reference)
    # Find the main ontology URI - prefer the "core" ontology
    main_ontology = None
    core_ontology = URIRef("https://twin-ship.eu/twinship/core")
    
    # First, check if the core ontology exists
    for s in g.subjects(RDF.type, OWL.Ontology):
        if s == core_ontology:
            main_ontology = core_ontology
            break
    
    # If core not found, fall back to any TwinShip ontology
    if not main_ontology:
        for s in g.subjects(RDF.type, OWL.Ontology):
            if is_twinship_resource(s):
                main_ontology = s
                break
    
    if main_ontology:
        # Add ontology declaration
        docs_graph.add((main_ontology, RDF.type, OWL.Ontology))
        
        # Copy ontology metadata
        for p, o in g.predicate_objects(main_ontology):
            if p != OWL.imports:  # Skip imports to avoid WIDOCO pulling in external ontologies
                docs_graph.add((main_ontology, p, o))
        
        # Note: We intentionally do NOT add owl:imports for external ontologies
        # because WIDOCO follows these imports and includes all their classes
        # in the embedded WebVOWL visualization, which creates visual clutter.
    
    print(f"\nDocumentation graph: {len(docs_graph)} triples")
    print(f"  Classes: {stats['classes']}")
    print(f"  Object Properties: {stats['object_properties']}")
    print(f"  Datatype Properties: {stats['datatype_properties']}")
    print(f"  Annotation Properties: {stats['annotation_properties']}")
    print(f"  Individuals: {stats['individuals']}")
    print(f"  Other triples: {stats['other_triples']}")
    
    # Serialize
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    print(f"\nWriting to: {output_path}")
    docs_graph.serialize(output_path, format='turtle')
    print(f"✓ Documentation ontology created: {output_path}")
    
    return output_path


def main():
    parser = argparse.ArgumentParser(
        description="Generate documentation-friendly ontology with TwinShip content and used external properties",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Auto-generate output filename
  python generate_docs_ontology.py model/twinship-core-complete.ttl
  
  # Specify output file
  python generate_docs_ontology.py -o docs.ttl model/twinship-core-complete.ttl
  
Output will contain TwinShip classes/properties and external properties (IDO) that are actually used.
Other external ontologies (QUDT, time, geosparql, etc.) are excluded.
        """
    )
    
    parser.add_argument('input', help='Input merged ontology file')
    parser.add_argument('-o', '--output', help='Output file path')
    
    args = parser.parse_args()
    
    # Determine output filename
    if args.output:
        output_file = args.output
    else:
        input_path = Path(args.input)
        output_file = input_path.parent / f"{input_path.stem}-docs.ttl"
    
    try:
        generate_docs_ontology(args.input, output_file)
        return 0
    except Exception as e:
        print(f"\n✗ Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
