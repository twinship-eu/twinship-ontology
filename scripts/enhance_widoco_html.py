#!/usr/bin/env python3
"""
Enhance WIDOCO HTML with Additional Annotation Properties

WIDOCO only displays a limited set of annotation properties by default.
This script post-processes the generated HTML to add skos:notation, 
skos:altLabel, and dcterms:description annotations.

Usage:
    python enhance_widoco_html.py input.html ontology.ttl output.html
"""

import argparse
import sys
from pathlib import Path
from rdflib import Graph, URIRef, Namespace, RDF, RDFS
from bs4 import BeautifulSoup

# Namespaces
SKOS = Namespace("http://www.w3.org/2004/02/skos/core#")
DCTERMS = Namespace("http://purl.org/dc/terms/")


def load_annotations(ontology_file):
    """Load skos and dcterms annotations from ontology."""
    print(f"Loading ontology: {ontology_file}")
    g = Graph()
    g.parse(ontology_file)
    
    annotations = {}
    
    for s in g.subjects():
        if not isinstance(s, URIRef):
            continue
        
        uri_str = str(s)
        entity_annotations = {}
        
        # Get SKOS annotations
        notation = g.value(s, SKOS.notation)
        if notation:
            entity_annotations['notation'] = str(notation)
        
        alt_label = g.value(s, SKOS.altLabel)
        if alt_label:
            entity_annotations['altLabel'] = str(alt_label)
        
        # Get dcterms:description
        description = g.value(s, DCTERMS.description)
        if description:
            entity_annotations['description'] = str(description)
        
        if entity_annotations:
            annotations[uri_str] = entity_annotations
    
    print(f"Found annotations for {len(annotations)} entities")
    return annotations


def enhance_html(html_file, annotations, output_file):
    """Enhance HTML with additional annotation properties."""
    print(f"Processing HTML: {html_file}")
    
    with open(html_file, 'r', encoding='utf-8') as f:
        soup = BeautifulSoup(f, 'html.parser')
    
    enhanced_count = 0
    
    # Find all entity divs (classes, properties)
    for entity_div in soup.find_all('div', class_='entity'):
        # Get the entity ID (URI)
        entity_id = entity_div.get('id')
        if not entity_id or entity_id not in annotations:
            continue
        
        entity_annots = annotations[entity_id]
        
        # Find the definedBy section (where dcterms:source is shown)
        defined_by = entity_div.find('dl', class_='definedBy')
        
        if not defined_by:
            # Create definedBy section if it doesn't exist
            comment_div = entity_div.find('div', class_='comment')
            if comment_div:
                defined_by = soup.new_tag('dl', **{'class': 'definedBy'})
                comment_div.insert_after(defined_by)
        
        if defined_by:
            # Add SKOS notation
            if 'notation' in entity_annots:
                dt = soup.new_tag('dt')
                dt.string = "Notation"
                dd = soup.new_tag('dd')
                code = soup.new_tag('code')
                code.string = entity_annots['notation']
                dd.append(code)
                defined_by.append(dt)
                defined_by.append(dd)
                enhanced_count += 1
            
            # Add SKOS alternative label
            if 'altLabel' in entity_annots:
                dt = soup.new_tag('dt')
                dt.string = "Alternative Label"
                dd = soup.new_tag('dd')
                dd.string = entity_annots['altLabel']
                defined_by.append(dt)
                defined_by.append(dd)
                enhanced_count += 1
            
            # Add dcterms:description
            if 'description' in entity_annots:
                dt = soup.new_tag('dt')
                dt.string = "Description"
                dd = soup.new_tag('dd')
                dd.string = entity_annots['description']
                defined_by.append(dt)
                defined_by.append(dd)
                enhanced_count += 1
    
    print(f"Enhanced {enhanced_count} annotations")
    
    # Write output
    print(f"Writing enhanced HTML: {output_file}")
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(str(soup))
    
    print("✓ Done!")


def main():
    parser = argparse.ArgumentParser(description='Enhance WIDOCO HTML with additional annotation properties')
    parser.add_argument('html_file', help='Input HTML file from WIDOCO')
    parser.add_argument('ontology_file', help='Ontology file (TTL) with annotations')
    parser.add_argument('-o', '--output', help='Output HTML file (default: overwrites input)')
    
    args = parser.parse_args()
    
    html_path = Path(args.html_file)
    ontology_path = Path(args.ontology_file)
    output_path = Path(args.output) if args.output else html_path
    
    if not html_path.exists():
        print(f"Error: HTML file not found: {html_path}")
        return 1
    
    if not ontology_path.exists():
        print(f"Error: Ontology file not found: {ontology_path}")
        return 1
    
    annotations = load_annotations(ontology_path)
    enhance_html(html_path, annotations, output_path)
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
