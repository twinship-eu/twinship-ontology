# data/

This folder contains **vessel-specific Knowledge Graph (KG) instance data** — OWL individuals populated with real or proprietary vessel data.

These files are **gitignored** and will never be committed or pushed to GitHub, as they may contain commercially sensitive or confidential vessel information.

## What belongs here

- `.ttl` files with OWL individuals for specific vessels (e.g. RO-RO ferries, tankers)
- Instance data generated from AIS feeds, technical specifications, or operational records
- Experimental populations of the TwinShip ontology for testing and validation

## What is tracked

- `README.md` — this file only

All other files in this folder are gitignored and will never be committed.

## Usage

Load instance data alongside the ontology for reasoning or SPARQL queries:

```bash
# Example: load with a reasoner or SPARQL endpoint
# riot --validate data/my-vessel.ttl build/twinship-core-complete.ttl
```

New files added to this folder will remain local only.
