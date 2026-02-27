#!/usr/bin/env python3
"""
Clean WebVOWL JSON by merging duplicate rdfs:Literal nodes.

OWL2VOWL creates a separate Literal node for each datatype property.
This script merges them into a single Literal node and updates property references.
"""

import sys
import json
from pathlib import Path


def clean_webvowl_json(input_file, output_file):
    """Merge duplicate Literal nodes in WebVOWL JSON."""
    
    print(f"Loading: {input_file}")
    with open(input_file, 'r') as f:
        data = json.load(f)
    
    # Find all Literal nodes
    literal_nodes = []
    literal_iri = 'http://www.w3.org/2000/01/rdf-schema#Literal'
    
    class_attrs = data.get('classAttribute', [])
    print(f"Original classes: {len(class_attrs)}")
    
    # Identify all Literal nodes
    for node in class_attrs:
        if node.get('iri') == literal_iri:
            literal_nodes.append(node['id'])
    
    print(f"Found {len(literal_nodes)} Literal nodes: {literal_nodes[:10]}...")
    
    if len(literal_nodes) <= 1:
        print("No duplicates to merge")
        return
    
    # Keep first Literal node, map others to it
    primary_literal = literal_nodes[0]
    id_mapping = {lit_id: primary_literal for lit_id in literal_nodes[1:]}
    
    print(f"Keeping Literal node #{primary_literal}, merging {len(literal_nodes)-1} duplicates")
    
    # Remove duplicate Literal nodes
    data['classAttribute'] = [
        node for node in class_attrs 
        if node['id'] not in id_mapping
    ]
    
    # Update property references
    prop_attrs = data.get('propertyAttribute', [])
    for prop in prop_attrs:
        if 'range' in prop and prop['range'] in id_mapping:
            prop['range'] = id_mapping[prop['range']]
        if 'domain' in prop and prop['domain'] in id_mapping:
            prop['domain'] = id_mapping[prop['domain']]
    
    print(f"Cleaned classes: {len(data['classAttribute'])}")
    print(f"Properties: {len(prop_attrs)}")
    
    # Write output
    Path(output_file).parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, 'w') as f:
        json.dump(data, f, indent=2)
    
    print(f"✓ Written: {output_file}")


if __name__ == '__main__':
    if len(sys.argv) < 3:
        print("Usage: python clean_webvowl_json.py <input.json> <output.json>")
        sys.exit(1)
    
    clean_webvowl_json(sys.argv[1], sys.argv[2])
