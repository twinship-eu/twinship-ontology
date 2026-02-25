#!/usr/bin/env python3
"""
Generate Documentation-Only Ontology

Creates a version of the TwinShip ontology suitable for documentation
that ONLY includes TwinShip-defined classes, properties, and individuals.

External ontology content (IDO, QUDT, GeoSPARQL, etc.) is excluded, but
the imports are kept so references still work.

Usage:
    python generate_docs_ontology.py model/twinship-core-complete.ttl
    python generate_docs_ontology.py -o output.ttl model/twinship-core-complete.ttl
"""

import argparse
import sys
from pathlib import Path
from rdflib import Graph, Namespace, RDF, RDFS, OWL, URIRef
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


def is_twinship_resource(uri):
    """Check if a resource belongs to TwinShip ontology."""
    if not isinstance(uri, URIRef):
        return False
    uri_str = str(uri)
    # Check if it starts with the TwinShip base or any specific namespace
    return uri_str.startswith(TWINSHIP_BASE)


def generate_docs_ontology(input_file, output_file):
    """
    Generate documentation-friendly ontology with only TwinShip content.
    """
    print(f"Loading ontology: {input_file}")
    g = Graph()
    g.parse(input_file)
    
    print(f"Original graph: {len(g)} triples")
    
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
    
    # First pass: Find all TwinShip resources
    twinship_resources = set()
    
    for s, p, o in g:
        # Keep if subject is a TwinShip resource
        if isinstance(s, URIRef) and is_twinship_resource(s):
            twinship_resources.add(s)
        # Keep if object is a TwinShip class/property being defined
        if isinstance(o, URIRef) and is_twinship_resource(o):
            if p in [RDFS.subClassOf, RDFS.subPropertyOf, RDFS.domain, RDFS.range]:
                twinship_resources.add(o)
    
    print(f"Found {len(twinship_resources)} TwinShip resources")
    
    # Second pass: Collect blank nodes related to TwinShip resources
    related_bnodes = set()
    
    for s, p, o in g:
        # If subject is a TwinShip resource and object is a blank node
        if isinstance(s, URIRef) and is_twinship_resource(s):
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
    
    # Find external properties used in TwinShip restrictions (e.g. IDO properties)
    # and include their type declarations so WebVOWL can render them
    external_props = set()
    for bnode in all_bnodes:
        if (bnode, RDF.type, OWL.Restriction) in g:
            prop = g.value(bnode, OWL.onProperty)
            if prop and isinstance(prop, URIRef) and not is_twinship_resource(prop):
                external_props.add(prop)
    twinship_resources.update(external_props)

    # Third pass: Copy all triples about TwinShip resources and related blank nodes
    for s, p, o in g:
        # Skip triples where subject is NOT a TwinShip resource or related blank node
        if isinstance(s, URIRef) and not is_twinship_resource(s) and s not in twinship_resources:
            continue
        
        # Include blank nodes that are related to TwinShip resources
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
            if p != OWL.imports:  # We'll handle imports specially
                docs_graph.add((main_ontology, p, o))
        
        # Add imports (but they won't be merged in the docs)
        external_imports = [
            "http://purl.org/ido/ido-core",
            "http://purl.org/pav/",
            "http://qudt.org/schema/qudt/",
            "http://www.w3.org/2006/time",
            "http://www.opengis.net/ont/geosparql",
        ]
        
        for import_uri in external_imports:
            docs_graph.add((main_ontology, OWL.imports, URIRef(import_uri)))
    
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
        description="Generate documentation-friendly ontology with only TwinShip content",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Auto-generate output filename
  python generate_docs_ontology.py model/twinship-core-complete.ttl
  
  # Specify output file
  python generate_docs_ontology.py -o docs.ttl model/twinship-core-complete.ttl
  
Output will contain ONLY TwinShip classes, properties, and individuals.
External ontologies (IDO, QUDT, etc.) are referenced but not included.
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
