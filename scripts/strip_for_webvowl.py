#!/usr/bin/env python3
"""
Strip ontology for clean WebVOWL visualization.

Removes all non-essential namespaces and annotations that create
extra nodes in WebVOWL visualization.

Keeps only:
- TwinShip classes and properties
- IDO classes and properties that are used
- Essential OWL/RDFS/XSD namespaces
- rdfs:label and rdfs:comment only
"""

import sys
from pathlib import Path
from rdflib import Graph, Namespace, RDF, RDFS, OWL, Literal, URIRef
from rdflib.namespace import XSD

# Essential namespaces to keep
ESSENTIAL_NAMESPACES = {
    'http://www.w3.org/2002/07/owl#',
    'http://www.w3.org/1999/02/22-rdf-syntax-ns#',
    'http://www.w3.org/2000/01/rdf-schema#',
    'http://www.w3.org/2001/XMLSchema#',
}

# Annotation properties to keep (minimal set for WebVOWL)
KEEP_ANNOTATIONS = {
    RDFS.label,
    RDFS.comment,
}


def strip_for_webvowl(input_file, output_file):
    """Strip ontology to minimal set for WebVOWL."""
    
    print(f"Loading: {input_file}")
    g = Graph()
    g.parse(input_file)
    
    print(f"Original: {len(g)} triples")
    
    # Create new graph with only essential namespaces
    clean = Graph()
    
    # Get TwinShip and IDO namespaces from input
    twinship_ns = None
    ido_ns = None
    
    for prefix, ns in g.namespaces():
        ns_str = str(ns)
        if 'twin-ship.eu' in ns_str or 'twinship' in ns_str.lower():
            twinship_ns = ns
            clean.bind(prefix, ns)
        elif 'posccaesar' in ns_str or 'lis14' in ns_str:
            ido_ns = ns
            clean.bind(prefix if prefix else 'ido', ns)
        elif ns_str in ESSENTIAL_NAMESPACES:
            clean.bind(prefix, ns)
    
    # Helper function to check if entity is from TwinShip or allowed external (like XSD)
    # We want to filter out IDO parent relationships to keep visualization clean
    def is_twinship_entity(uri):
        uri_str = str(uri)
        if twinship_ns and uri_str.startswith(str(twinship_ns)):
            return True
        # Allow XSD datatypes (essential for datatype properties)
        if uri_str.startswith('http://www.w3.org/2001/XMLSchema#'):
            return True
        return False
    
    print(f"TwinShip namespace: {twinship_ns}")
    print(f"IDO namespace: {ido_ns}")
    
    # Copy only essential triples
    skipped_subclass = 0
    skipped_subprop = 0
    skipped_external_class = 0
    skipped_external_prop = 0
    skipped_external_labels = 0
    skipped_external_domain_range = 0
    skipped_properties_with_external_domain = set()
    
    # First pass: identify properties with external domains/ranges
    for s, p, o in g:
        if p in [RDFS.domain, RDFS.range]:
            if isinstance(o, URIRef) and not is_twinship_entity(o):
                skipped_properties_with_external_domain.add(s)
    
    print(f"Found {len(skipped_properties_with_external_domain)} properties with external domains/ranges to skip")
    
    # Second pass: copy only TwinShip triples
    for s, p, o in g:
        # Skip all triples about properties with external domains/ranges
        if s in skipped_properties_with_external_domain:
            continue
        
        # Skip if predicate is from non-essential namespace
        if str(p) not in ESSENTIAL_NAMESPACES:
            p_ns = str(p).rsplit('#', 1)[0] + '#' if '#' in str(p) else str(p).rsplit('/', 1)[0] + '/'
            if p_ns not in ESSENTIAL_NAMESPACES:
                # Only keep rdfs:label and rdfs:comment annotations FOR TWINSHIP entities
                if p in KEEP_ANNOTATIONS:
                    if isinstance(s, URIRef) and not is_twinship_entity(s):
                        skipped_external_labels += 1
                        continue  # Skip labels/comments for external entities
                else:
                    continue  # Skip other non-essential predicates
        
        # Skip rdfs:subClassOf if object is external (not TwinShip)
        if p == RDFS.subClassOf:
            if isinstance(o, URIRef) and not is_twinship_entity(o):
                skipped_subclass += 1
                continue
        
        # Skip rdfs:subPropertyOf if object is external (not TwinShip)
        if p == RDFS.subPropertyOf:
            if isinstance(o, URIRef) and not is_twinship_entity(o):
                skipped_subprop += 1
                continue
        
        # Skip rdfs:domain/range if object is external (not TwinShip)
        if p in [RDFS.domain, RDFS.range]:
            if isinstance(o, URIRef) and not is_twinship_entity(o):
                skipped_external_domain_range += 1
                continue
        
        # Skip external class declarations (not TwinShip)
        if p == RDF.type and o == OWL.Class:
            if isinstance(s, URIRef) and not is_twinship_entity(s):
                skipped_external_class += 1
                continue
        
        # Skip external property declarations (not TwinShip)
        if p == RDF.type and o in [OWL.ObjectProperty, OWL.DatatypeProperty]:
            if isinstance(s, URIRef) and not is_twinship_entity(s):
                skipped_external_prop += 1
                continue
        
        # Always keep XSD datatype declarations (rdfs:Datatype) for WebVOWL
        if p == RDF.type and o == RDFS.Datatype:
            if isinstance(s, URIRef) and str(s).startswith('http://www.w3.org/2001/XMLSchema#'):
                clean.add((s, p, o))
                # Also keep labels for XSD datatypes
                for label_triple in g.triples((s, RDFS.label, None)):
                    clean.add(label_triple)
                continue
        
        # Add triple
        clean.add((s, p, o))
    
    print(f"Skipped {skipped_subclass} external subClassOf triples")
    print(f"Skipped {skipped_subprop} external subPropertyOf triples")
    print(f"Skipped {skipped_external_class} external class declarations")
    print(f"Skipped {skipped_external_prop} external property declarations")
    print(f"Skipped {skipped_external_labels} external labels/comments")
    print(f"Skipped {skipped_external_domain_range} external domain/range triples")
    
    print(f"Cleaned: {len(clean)} triples")
    
    # Count remaining entities
    classes = len(list(clean.subjects(RDF.type, OWL.Class)))
    obj_props = len(list(clean.subjects(RDF.type, OWL.ObjectProperty)))
    data_props = len(list(clean.subjects(RDF.type, OWL.DatatypeProperty)))
    
    print(f"  Classes: {classes}")
    print(f"  Object Properties: {obj_props}")
    print(f"  Datatype Properties: {data_props}")
    
    # Write output
    Path(output_file).parent.mkdir(parents=True, exist_ok=True)
    clean.serialize(destination=output_file, format='turtle')
    print(f"✓ Written: {output_file}")


if __name__ == '__main__':
    if len(sys.argv) < 3:
        print("Usage: python strip_for_webvowl.py <input.ttl> <output.ttl>")
        sys.exit(1)
    
    strip_for_webvowl(sys.argv[1], sys.argv[2])
