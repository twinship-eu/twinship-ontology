#!/usr/bin/env python3
"""
Generate Ontology Statistics File

Writes STATISTICS.md (or a custom path) with a summary table and detailed
sections for the TwinShip ontology.  Object properties are always listed in
full when the count is fewer than 10.

Usage:
    uv run python scripts/generate_stats_table.py
    uv run python scripts/generate_stats_table.py --output STATISTICS.md
    uv run python scripts/generate_stats_table.py --docs-viz build/twinship-core-complete-docs-viz.ttl
    uv run python scripts/generate_stats_table.py --examples 10
"""

import argparse
import sys
from datetime import date
from pathlib import Path
from rdflib import Graph, Namespace, RDF, RDFS, OWL, URIRef
from rdflib.namespace import DCTERMS, SKOS

# ── Namespace constants ──────────────────────────────────────────────────────

TWINSHIP_NS = "https://twin-ship.eu/twinship#"
IDO_NS = "http://rds.posccaesar.org/ontology/lis14/rdl/"
PAV = Namespace("http://purl.org/pav/")

# Human-readable labels for imported ontology URIs
IMPORT_LABELS = {
    "http://purl.org/pav/": "PAV",
    "http://qudt.org/vocab/unit/": "QUDT Unit",
    "http://qudt.org/vocab/quantitykind/": "QUDT QuantityKind",
    "http://rds.posccaesar.org/ontology/lis14/ont/core/1.0": "IDO (LIS14)",
    "http://www.vesselAI-project.eu/vesselai": "VesselAI (DUL/Time)",
}

# Threshold: list all object properties when count is below this
LIST_ALL_THRESHOLD = 10


# ── Helpers ──────────────────────────────────────────────────────────────────

def short_name(uri: str) -> str:
    """Return the local name from a URI."""
    s = str(uri)
    if "#" in s:
        return s.split("#")[-1]
    return s.rstrip("/").split("/")[-1]


def get_label(graph: Graph, uri: URIRef) -> str:
    """Return rdfs:label if present, otherwise the local name."""
    label = graph.value(uri, RDFS.label)
    if label:
        return str(label)
    alt = graph.value(uri, SKOS.altLabel)
    if alt:
        return str(alt)
    return short_name(str(uri))


def get_comment(graph: Graph, uri: URIRef) -> str:
    """Return rdfs:comment if present, otherwise empty string."""
    comment = graph.value(uri, RDFS.comment)
    return str(comment).strip() if comment else ""


def collect_ontology_meta(graph: Graph) -> dict:
    """Read version/date metadata from the ontology resource."""
    meta = {"version": None, "last_updated": None, "title": None}
    for s in graph.subjects(RDF.type, OWL.Ontology):
        meta["version"] = str(graph.value(s, PAV.version) or graph.value(s, OWL.versionInfo) or "")
        meta["last_updated"] = str(graph.value(s, PAV.lastUpdateOn) or "")[:10]  # date only
        meta["title"] = str(graph.value(s, DCTERMS.title) or graph.value(s, RDFS.label) or "TwinShip Ontology")
        break
    return meta


def collect_imports(base_ttl: Path) -> list[tuple[str, str]]:
    """Read owl:imports from the source base TTL. Returns [(uri, label)] sorted by label."""
    g = Graph()
    g.parse(base_ttl, format="turtle")
    results = []
    for _s, _p, o in g.triples((None, OWL.imports, None)):
        uri = str(o)
        label = IMPORT_LABELS.get(uri, short_name(uri))
        results.append((uri, label))
    return sorted(results, key=lambda x: x[1].lower())


def collect_classes(graph: Graph) -> list[str]:
    """TwinShip-namespaced OWL/RDFS classes, sorted by local name."""
    uris = set()
    for s in graph.subjects(RDF.type, OWL.Class):
        if str(s).startswith(TWINSHIP_NS):
            uris.add(str(s))
    for s in graph.subjects(RDF.type, RDFS.Class):
        if str(s).startswith(TWINSHIP_NS):
            uris.add(str(s))
    return sorted(uris, key=short_name)


def collect_object_properties(graph: Graph) -> list[str]:
    """
    All owl:ObjectProperty declarations in the graph.
    Matches what WIDOCO reports: includes TwinShip and any external properties
    (e.g. IDO) declared inline in the docs-viz artifact.
    """
    uris = set()
    for s in graph.subjects(RDF.type, OWL.ObjectProperty):
        uris.add(str(s))
    return sorted(uris, key=short_name)


def collect_data_properties(graph: Graph) -> list[str]:
    """TwinShip-namespaced owl:DatatypeProperty declarations."""
    uris = set()
    for s in graph.subjects(RDF.type, OWL.DatatypeProperty):
        if str(s).startswith(TWINSHIP_NS):
            uris.add(str(s))
    return sorted(uris, key=short_name)


def top_classes_by_refs(graph: Graph, classes: list[str], n: int) -> list[str]:
    """Return up to n classes ranked by how many times they are referenced in the graph."""
    from collections import Counter
    class_set = set(classes)
    refs = Counter()
    for _s, _p, o in graph:
        if str(o) in class_set:
            refs[str(o)] += 1
    # Classes not referenced at all get count 0; sort by (-count, local name)
    ranked = sorted(classes, key=lambda u: (-refs[u], short_name(u)))
    return ranked[:n]


def top_data_props_by_domains(graph: Graph, data_props: list[str], n: int) -> list[str]:
    """Return up to n data properties ranked by number of rdfs:domain assignments."""
    from collections import Counter
    dom_count = Counter()
    for uri in data_props:
        for _s, _p, _o in graph.triples((URIRef(uri), RDFS.domain, None)):
            dom_count[uri] += 1
    ranked = sorted(data_props, key=lambda u: (-dom_count[u], short_name(u)))
    return ranked[:n]


# ── Markdown builders ─────────────────────────────────────────────────────────

def md_table(headers: list[str], rows: list[tuple]) -> str:
    """Render a Markdown table. Last column is not padded."""
    all_rows = [tuple(headers)] + [tuple(r) for r in rows]
    widths = [max(len(str(r[i])) for r in all_rows) for i in range(len(headers) - 1)]

    def fmt(row: tuple) -> str:
        parts = [str(row[i]).ljust(widths[i]) for i in range(len(widths))]
        parts.append(str(row[-1]))
        return "| " + " | ".join(parts) + " |"

    sep = "| " + " | ".join("-" * w for w in widths) + " | " + "-" * len(headers[-1]) + " |"
    return "\n".join([fmt(tuple(headers)), sep] + [fmt(r) for r in rows])


def build_markdown(
    graph: Graph,
    meta: dict,
    classes: list[str],
    obj_props: list[str],
    data_props: list[str],
    imports: list[tuple[str, str]],
    examples_n: int,
    docs_viz_path: Path,
) -> str:
    today = date.today().isoformat()
    version = meta.get("version") or "unknown"
    last_updated = meta.get("last_updated") or today
    title = meta.get("title") or "TwinShip Ontology"

    # Examples: always show all when below threshold, otherwise top-N by usage
    if len(obj_props) < LIST_ALL_THRESHOLD:
        obj_prop_examples = "<br>".join(short_name(u) for u in obj_props)
    else:
        obj_prop_examples = "<br>".join(short_name(u) for u in top_classes_by_refs(graph, obj_props, examples_n))

    class_examples = "<br>".join(
        short_name(u) for u in top_classes_by_refs(graph, classes, examples_n)
    )
    data_prop_examples = "<br>".join(
        short_name(u) for u in top_data_props_by_domains(graph, data_props, examples_n)
    )

    summary_rows = [
        ("Classes", len(classes), class_examples),
        ("Object properties", len(obj_props), obj_prop_examples),
        ("Data properties", len(data_props), data_prop_examples),
        ("Imported ontologies", len(imports), "<br>".join(lbl for _, lbl in imports)),
    ]

    lines = [
        f"# {title} — Statistics",
        "",
        f"> **Version:** {version}  ",
        f"> **Ontology last updated:** {last_updated}  ",
        f"> **Statistics generated:** {today}  ",
        f"> **Source:** `{docs_viz_path}`",
        "",
        "## Summary",
        "",
        md_table(["Metric", "Count", "Illustrative examples"], summary_rows),
        "",
    ]

    # ── Object Properties (full list when < threshold) ────────────────────────
    lines += [
        "## Object Properties",
        "",
        f"*{len(obj_props)} properties — {'all listed below' if len(obj_props) < LIST_ALL_THRESHOLD else f'showing {examples_n} examples above'}*",
        "",
    ]
    if len(obj_props) < LIST_ALL_THRESHOLD:
        op_rows = []
        for u in obj_props:
            ref = URIRef(u)
            ns = "IDO" if u.startswith(IDO_NS) else "TwinShip"
            label = get_label(graph, ref)
            comment = get_comment(graph, ref)
            op_rows.append((f"`{short_name(u)}`", ns, label, comment))
        lines += [
            md_table(["Property", "Namespace", "Label", "Description"], op_rows),
            "",
        ]
    else:
        for u in obj_props:
            lines.append(f"- `{short_name(u)}`")
        lines.append("")

    # ── Imported Ontologies ────────────────────────────────────────────────────
    lines += [
        "## Imported Ontologies",
        "",
        md_table(["Ontology", "URI"], [(lbl, f"<{uri}>") for uri, lbl in imports]),
        "",
    ]

    return "\n".join(lines)


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(description="Generate STATISTICS.md for the TwinShip ontology.")
    parser.add_argument(
        "--output",
        default="STATISTICS.md",
        metavar="FILE",
        help="Output file path (default: STATISTICS.md)",
    )
    parser.add_argument(
        "--docs-viz",
        default="build/twinship-core-complete-docs-viz.ttl",
        metavar="FILE",
        help="Docs-viz build artifact (default: build/twinship-core-complete-docs-viz.ttl)",
    )
    parser.add_argument(
        "--base",
        default="model/twinship-base.ttl",
        metavar="FILE",
        help="Source base TTL to read owl:imports from (default: model/twinship-base.ttl)",
    )
    parser.add_argument(
        "--examples",
        type=int,
        default=10,
        metavar="N",
        help="Illustrative examples per row in summary table (default: 10)",
    )
    args = parser.parse_args()

    docs_viz_path = Path(args.docs_viz)
    base_path = Path(args.base)
    output_path = Path(args.output)

    print(f"📊 Loading: {docs_viz_path}", file=sys.stderr)
    graph = Graph()
    graph.parse(docs_viz_path, format="turtle")

    print(f"📥 Reading imports from: {base_path}", file=sys.stderr)
    imports = collect_imports(base_path)

    meta = collect_ontology_meta(graph)
    classes = collect_classes(graph)
    obj_props = collect_object_properties(graph)
    data_props = collect_data_properties(graph)

    content = build_markdown(
        graph, meta, classes, obj_props, data_props, imports, args.examples, docs_viz_path
    )

    output_path.write_text(content, encoding="utf-8")
    print(f"✅ Written: {output_path}  ({len(classes)} classes, {len(obj_props)} object props, {len(data_props)} data props)", file=sys.stderr)


if __name__ == "__main__":
    main()
