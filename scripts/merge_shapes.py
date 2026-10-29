#!/usr/bin/env python3
"""Merge the SHACL shape files in shapes/ into a single Turtle file for release."""

import argparse
import sys
from pathlib import Path

from rdflib import Graph

REPO_ROOT = Path(__file__).resolve().parent.parent

PREFIXES = {
    "ido": "http://rds.posccaesar.org/ontology/lis14/rdl/",
    "tws": "https://twin-ship.eu/twinship#",
    "twsh": "https://twin-ship.eu/twinship/shapes#",
}


def merge_shapes(shapes_dir: Path, output: Path) -> int:
    files = sorted(shapes_dir.glob("*.ttl"))
    if not files:
        raise FileNotFoundError(f"No .ttl files found in {shapes_dir}")
    graph = Graph()
    for prefix, namespace in PREFIXES.items():
        graph.bind(prefix, namespace)
    for path in files:
        graph.parse(path, format="turtle")
    output.parent.mkdir(parents=True, exist_ok=True)
    graph.serialize(destination=output, format="turtle", encoding="utf-8")
    return len(files)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--shapes-dir", type=Path, default=REPO_ROOT / "shapes")
    parser.add_argument("--output", type=Path, default=REPO_ROOT / "build" / "twinship-shapes.ttl")
    args = parser.parse_args()
    try:
        count = merge_shapes(args.shapes_dir, args.output)
    except (FileNotFoundError, SyntaxError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    print(f"Merged {count} shape files into {args.output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
