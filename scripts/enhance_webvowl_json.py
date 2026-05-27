#!/usr/bin/env python3
"""
Enhance WebVOWL JSON with SKOS and dcterms annotations.

Post-processes WIDOCO-generated WebVOWL ontology.json to add custom annotation
properties (skos:notation, skos:altLabel, dcterms:description) without modifying
the existing structure that WebVOWL expects.

This is a minimal-change approach that only adds "annotations" fields to existing
propertyAttribute and classAttribute objects, preserving all IDs, types, and links.
"""

import sys
import json
from pathlib import Path
from rdflib import Graph, Namespace

# Define namespaces
SKOS = Namespace("http://www.w3.org/2004/02/skos/core#")
DCTERMS = Namespace("http://purl.org/dc/terms/")


def load_annotations(ontology_file):
    """
    Load SKOS and dcterms annotations from the ontology file.
    
    Returns:
        dict: Mapping of entity IRI to annotations dict
              {
                  "https://...": {
                      "notation": ["IMO0654"],
                      "altLabel": ["Fuel type, coded"],
                      "description": ["A code representing..."]
                  }
              }
    """
    print(f"Loading annotations from: {ontology_file}")
    g = Graph()
    g.parse(ontology_file)
    
    annotations_map = {}
    
    # Define annotation properties to extract
    annotation_properties = [
        ("notation", SKOS.notation),
        ("altLabel", SKOS.altLabel),
        ("description", DCTERMS.description),
    ]
    
    # Get all entities (classes and properties)
    from rdflib import RDF, OWL
    entities = set()
    entities.update(g.subjects(RDF.type, OWL.Class))
    entities.update(g.subjects(RDF.type, OWL.ObjectProperty))
    entities.update(g.subjects(RDF.type, OWL.DatatypeProperty))
    
    for entity in entities:
        entity_iri = str(entity)
        annotations = {}
        
        for prop_name, prop_uri in annotation_properties:
            values = list(g.objects(entity, prop_uri))
            if values:
                annotations[prop_name] = [str(v) for v in values]
        
        if annotations:
            annotations_map[entity_iri] = annotations
    
    print(f"Found annotations for {len(annotations_map)} entities")
    return annotations_map


def format_annotations_for_webvowl(annotations_dict):
    """
    Convert flat annotations dict to WebVOWL's expected format.
    
    Input:  {"notation": ["IMO0654"], "altLabel": ["Fuel type"]}
    Output: {
        "notation": [{
            "identifier": "notation",
            "language": "undefined",
            "value": "IMO0654",
            "type": "label"
        }],
        ...
    }
    """
    webvowl_annotations = {}
    
    for prop_name, values in annotations_dict.items():
        webvowl_annotations[prop_name] = []
        for value in values:
            webvowl_annotations[prop_name].append({
                "identifier": prop_name,
                "language": "undefined",
                "value": value,
                "type": "label"
            })
    
    return webvowl_annotations


def enhance_webvowl_json(ontology_file, webvowl_json_file):
    """
    Add SKOS and dcterms annotations to WebVOWL JSON.
    
    Args:
        ontology_file: Path to TTL ontology file
        webvowl_json_file: Path to WIDOCO-generated ontology.json
    """
    # Load annotations from ontology
    annotations_map = load_annotations(ontology_file)
    
    if not annotations_map:
        print("No annotations found, skipping enhancement")
        return
    
    # Load WebVOWL JSON
    print(f"Loading WebVOWL JSON: {webvowl_json_file}")
    try:
        with open(webvowl_json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except UnicodeDecodeError:
        # WIDOCO on Windows may write the JSON in the system locale encoding
        # (e.g. cp1252) instead of UTF-8.  Re-read with the platform default
        # so we can at least process the file; the writer always emits UTF-8.
        import locale
        fallback = locale.getpreferredencoding(False)
        print(f"  Warning: JSON is not valid UTF-8, retrying with {fallback}")
        with open(webvowl_json_file, 'r', encoding=fallback, errors='replace') as f:
            data = json.load(f)
    
    # Enhance propertyAttribute objects
    enhanced_props = 0
    if 'propertyAttribute' in data:
        for prop_attr in data['propertyAttribute']:
            iri = prop_attr.get('iri')
            if iri and iri in annotations_map:
                prop_attr['annotations'] = format_annotations_for_webvowl(annotations_map[iri])
                enhanced_props += 1
    
    # Enhance classAttribute objects
    enhanced_classes = 0
    if 'classAttribute' in data:
        for class_attr in data['classAttribute']:
            iri = class_attr.get('iri')
            if iri and iri in annotations_map:
                class_attr['annotations'] = format_annotations_for_webvowl(annotations_map[iri])
                enhanced_classes += 1
    
    # Save enhanced JSON
    print(f"Writing enhanced JSON: {webvowl_json_file}")
    with open(webvowl_json_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    print(f"✓ Enhanced {enhanced_props} properties and {enhanced_classes} classes with annotations")


def main():
    if len(sys.argv) != 3:
        print("Usage: enhance_webvowl_json.py <ontology.ttl> <ontology.json>")
        print("\nEnhance WebVOWL JSON with SKOS and dcterms annotations")
        print("\nExample:")
        print("  python enhance_webvowl_json.py \\")
        print("    build/twinship-core-complete-viz-clean-minimal.ttl \\")
        print("    docs/website/documentation/webvowl/data/ontology.json")
        sys.exit(1)
    
    ontology_file = Path(sys.argv[1])
    webvowl_json_file = Path(sys.argv[2])
    
    if not ontology_file.exists():
        print(f"Error: Ontology file not found: {ontology_file}")
        sys.exit(1)
    
    if not webvowl_json_file.exists():
        print(f"Error: WebVOWL JSON file not found: {webvowl_json_file}")
        sys.exit(1)
    
    enhance_webvowl_json(ontology_file, webvowl_json_file)


if __name__ == '__main__':
    main()
