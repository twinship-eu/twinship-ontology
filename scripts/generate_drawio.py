#!/usr/bin/env python3
"""
generate_drawio.py — Generate Graffoo-style draw.io diagrams from TwinShip TTL modules.

Outputs (in --out-dir, default: diagrams/):
  overview.drawio              — module packages with root classes and cross-module links
  vessel.drawio                — full vessel module diagram
  operational-context.drawio
  operational-modes.drawio
  weather-conditions.drawio
  predictions.drawio

Usage:
    uv run python scripts/generate_drawio.py
    uv run python scripts/generate_drawio.py --out-dir diagrams
"""

import argparse
import html as _html
from collections import defaultdict, deque
from pathlib import Path
from xml.etree import ElementTree as ET

from rdflib import BNode, Graph, Namespace, RDF, RDFS, OWL, URIRef

# ---------------------------------------------------------------------------
# Namespaces
# ---------------------------------------------------------------------------

TW_NS = "https://twin-ship.eu/twinship#"
TW    = Namespace(TW_NS)

MODULES: dict[str, str] = {
    "vessel":               "model/modules/vessel.ttl",
    "operational-context":  "model/modules/operational-context.ttl",
    "operational-modes":    "model/modules/operational-modes.ttl",
    "weather-conditions":   "model/modules/weather-conditions.ttl",
    "predictions":          "model/modules/predictions.ttl",
}

MOD_ORDER = ["vessel", "operational-context", "operational-modes",
             "weather-conditions", "predictions"]

# ---------------------------------------------------------------------------
# Graffoo colours
# ---------------------------------------------------------------------------

CLR_CLASS    = "#FFFF88"   # yellow — OWL class
CLR_EXTERNAL = "#F5F5F5"   # grey   — class from another module
CLR_INDIV    = "#FFFF88"   # yellow — named individual (ellipse)

MOD_CLR: dict[str, tuple[str, str]] = {   # (fill, stroke)
    "vessel":               ("#DAE8FC", "#6C8EBF"),
    "operational-context":  ("#D5E8D4", "#82B366"),
    "operational-modes":    ("#FFE6CC", "#D6B656"),
    "weather-conditions":   ("#E1D5E7", "#9673A6"),
    "predictions":          ("#FFF2CC", "#B85450"),
}

# ---------------------------------------------------------------------------
# Layout constants
# ---------------------------------------------------------------------------

CLS_W_MIN   = 190
CLS_H_BASE  = 40
CLS_H_PROP  = 16    # extra height per data property line
COL_GAP     = 240   # horizontal spacing between class columns
LEVEL_GAP   = 100   # vertical spacing between hierarchy levels
ROW_GAP     = 20    # spacing between classes on the same level
CONT_PAD    = 45    # padding inside module containers
OVERVIEW_W  = 500   # overview module container width

# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------

class ModuleData:
    def __init__(self) -> None:
        self.classes:            set[URIRef]                       = set()
        self.subclass_pairs:     list[tuple[URIRef, URIRef]]       = []  # (child, parent)
        self.obj_props:          list[tuple[str, URIRef, URIRef]]  = []  # (name, src, tgt)
        self.data_props_by_cls:  dict[URIRef, list[tuple[str,str]]] = defaultdict(list)
        self.individuals:        list[tuple[URIRef, URIRef]]       = []  # (ind, class)

# ---------------------------------------------------------------------------
# Parsing
# ---------------------------------------------------------------------------

def _local(uri: URIRef) -> str:
    s = str(uri)
    return s.split("#")[-1] if "#" in s else s.split("/")[-1]


def _cls_width(name: str) -> int:
    return max(CLS_W_MIN, len(name) * 9)


def parse_module(path: str) -> ModuleData:
    g = Graph()
    g.parse(path, format="turtle")
    md = ModuleData()

    tw_classes = {c for c in g.subjects(RDF.type, OWL.Class)
                  if str(c).startswith(TW_NS)}
    md.classes = tw_classes

    # Subclass pairs — TW→TW named classes only (skip blank-node restrictions)
    for child, parent in g.subject_objects(RDFS.subClassOf):
        if isinstance(parent, BNode):
            continue
        if child in tw_classes and parent in tw_classes:
            md.subclass_pairs.append((child, parent))

    # Object and data properties from OWL restrictions on each class
    seen_obj: set[tuple[str, URIRef, URIRef]] = set()
    for cls in tw_classes:
        for restr in g.objects(cls, RDFS.subClassOf):
            if not isinstance(restr, BNode):
                continue
            on_prop  = g.value(restr, OWL.onProperty)
            val_from = (g.value(restr, OWL.someValuesFrom)
                        or g.value(restr, OWL.allValuesFrom))
            if not (on_prop and val_from) or isinstance(val_from, BNode):
                continue

            is_data = (on_prop, RDF.type, OWL.DatatypeProperty) in g
            is_obj  = (on_prop, RDF.type, OWL.ObjectProperty) in g

            if is_data:
                xsd_t = _local(val_from)
                entry = (_local(on_prop), xsd_t)
                if entry not in md.data_props_by_cls[cls]:
                    md.data_props_by_cls[cls].append(entry)
            elif is_obj:
                triple = (_local(on_prop), cls, val_from)
                if triple not in seen_obj:
                    seen_obj.add(triple)
                    md.obj_props.append(triple)

    # Named individuals: typed as an owl:NamedIndividual, or typed as a TW class
    for ind in g.subjects(RDF.type, OWL.NamedIndividual):
        if not str(ind).startswith(TW_NS):
            continue
        for cls in g.objects(ind, RDF.type):
            if cls in tw_classes:
                md.individuals.append((ind, cls))
                break
        else:
            md.individuals.append((ind, URIRef(TW_NS + "Thing")))

    # Also pick up individuals typed directly as a TW class (no owl:NamedIndividual declaration)
    for cls in tw_classes:
        for ind in g.subjects(RDF.type, cls):
            if (not str(ind).startswith(TW_NS)
                    or isinstance(ind, BNode)
                    or (ind, RDF.type, OWL.Class) in g):
                continue
            entry = (ind, cls)
            if entry not in md.individuals:
                md.individuals.append(entry)

    return md


# ---------------------------------------------------------------------------
# Layout
# ---------------------------------------------------------------------------

def _compute_layout(
    classes: set[URIRef],
    subclass_pairs: list[tuple[URIRef, URIRef]],
    data_props_by_cls: dict[URIRef, list],
) -> dict[URIRef, tuple[int, int, int, int]]:
    """Return {class_uri: (x, y, w, h)} using a top-down level layout."""

    children: dict[URIRef, list[URIRef]] = defaultdict(list)
    tw_parents: dict[URIRef, set[URIRef]] = defaultdict(set)

    for child, parent in subclass_pairs:
        children[parent].append(child)
        tw_parents[child].add(parent)

    roots = sorted(
        [c for c in classes if not (tw_parents[c] & classes)],
        key=_local,
    )

    # BFS — assign depth level to each class
    levels: dict[URIRef, int] = {}
    queue: deque[tuple[URIRef, int]] = deque((r, 0) for r in roots)
    while queue:
        cls, depth = queue.popleft()
        if cls in levels:
            continue
        levels[cls] = depth
        for child in sorted(children[cls], key=_local):
            if child not in levels:
                queue.append((child, depth + 1))

    # Group by level
    by_level: dict[int, list[URIRef]] = defaultdict(list)
    for cls, lvl in levels.items():
        by_level[lvl].append(cls)
    for lvl in by_level:
        by_level[lvl].sort(key=_local)

    def _h(c: URIRef) -> int:
        n = len(data_props_by_cls.get(c, []))
        return CLS_H_BASE + CLS_H_PROP * n

    # Place: row = depth level (top→bottom), column = index within level
    positions: dict[URIRef, tuple[int, int, int, int]] = {}
    y = 0
    for lvl in sorted(by_level):
        cls_list = by_level[lvl]
        row_h = max(_h(c) for c in cls_list)
        for col, cls in enumerate(cls_list):
            w = _cls_width(_local(cls))
            x = col * COL_GAP
            positions[cls] = (x, y, w, _h(cls))
        y += row_h + LEVEL_GAP

    return positions


# ---------------------------------------------------------------------------
# draw.io XML helpers
# ---------------------------------------------------------------------------

_counter = 0


def _uid(prefix: str = "c") -> str:
    global _counter
    _counter += 1
    return f"{prefix}_{_counter}"


def _reset() -> None:
    global _counter
    _counter = 0


def _make_graph() -> tuple[ET.Element, ET.Element]:
    """Return (mxfile, root) where root is the <root> layer element."""
    mxfile  = ET.Element("mxfile")
    diagram = ET.SubElement(mxfile, "diagram", name="diagram")
    graph   = ET.SubElement(
        diagram, "mxGraphModel",
        dx="1422", dy="762", grid="1", gridSize="10",
        guides="1", tooltips="1", connect="1", arrows="1",
        fold="1", page="1", pageScale="1",
        pageWidth="1654", pageHeight="1169",
        math="0", shadow="0",
    )
    root_el = ET.SubElement(graph, "root")
    ET.SubElement(root_el, "mxCell", id="0")
    ET.SubElement(root_el, "mxCell", id="1", parent="0")
    return mxfile, root_el


def _geo(parent: ET.Element, x: int, y: int, w: int, h: int) -> None:
    ET.SubElement(parent, "mxGeometry",
                  x=str(x), y=str(y), width=str(w), height=str(h),
                  **{"as": "geometry"})


def _geo_rel(parent: ET.Element) -> None:
    ET.SubElement(parent, "mxGeometry", relative="1", **{"as": "geometry"})


def add_container(root: ET.Element, cid: str, label: str,
                  x: int, y: int, w: int, h: int,
                  fill: str, stroke: str,
                  parent: str = "1") -> None:
    style = (
        f"swimlane;startSize=30;fillColor={fill};strokeColor={stroke};"
        "fontStyle=1;fontSize=13;rounded=1;arcSize=4;"
    )
    cell = ET.SubElement(root, "mxCell",
                         id=cid, value=label, style=style,
                         vertex="1", parent=parent)
    _geo(cell, x, y, w, h)


def add_class_box(root: ET.Element, cid: str, name: str,
                  x: int, y: int, w: int, h: int,
                  data_props: list[tuple[str, str]],
                  fill: str = CLR_CLASS,
                  stroke: str = "#333333",
                  parent: str = "1") -> None:
    if data_props:
        rows = "".join(
            f"<br/><font style='font-size:10px;'>"
            f"{_html.escape(p)} : {_html.escape(t)}</font>"
            for p, t in data_props
        )
        label = f"<b>{_html.escape(name)}</b>{rows}"
    else:
        label = f"<b>{_html.escape(name)}</b>"

    style = (
        f"rounded=1;whiteSpace=wrap;fillColor={fill};strokeColor={stroke};"
        "fontStyle=0;arcSize=10;html=1;verticalAlign=top;align=center;"
        "spacingTop=4;spacingLeft=4;spacingRight=4;"
    )
    cell = ET.SubElement(root, "mxCell",
                         id=cid, value=label, style=style,
                         vertex="1", parent=parent)
    _geo(cell, x, y, w, h)


def add_individual(root: ET.Element, cid: str, name: str,
                   x: int, y: int,
                   parent: str = "1") -> None:
    style = (
        f"ellipse;whiteSpace=wrap;fillColor={CLR_INDIV};strokeColor=#333333;"
        "fontStyle=1;html=1;"
    )
    cell = ET.SubElement(root, "mxCell",
                         id=cid, value=_html.escape(name), style=style,
                         vertex="1", parent=parent)
    _geo(cell, x, y, 130, 40)


def add_subclass_edge(root: ET.Element, cid: str,
                      source: str, target: str,
                      parent: str = "1") -> None:
    # dashed line, hollow open-triangle head (child → parent = subClassOf)
    style = (
        "endArrow=block;endFill=0;dashed=1;"
        "edgeStyle=orthogonalEdgeStyle;rounded=0;strokeColor=#333333;"
    )
    cell = ET.SubElement(root, "mxCell",
                         id=cid, value="", style=style,
                         edge="1", source=source, target=target,
                         parent=parent)
    _geo_rel(cell)


def add_obj_edge(root: ET.Element, cid: str, label: str,
                 source: str, target: str,
                 cross_module: bool = False,
                 parent: str = "1") -> None:
    # solid open arrowhead; dashed for cross-module references
    dash = "dashed=1;" if cross_module else ""
    style = (
        f"endArrow=open;endSize=8;{dash}"
        "edgeStyle=orthogonalEdgeStyle;rounded=0;strokeColor=#333333;"
        "fontSize=10;"
    )
    cell = ET.SubElement(root, "mxCell",
                         id=cid, value=_html.escape(label), style=style,
                         edge="1", source=source, target=target,
                         parent=parent)
    _geo_rel(cell)


def write_drawio(mxfile: ET.Element, path: Path) -> None:
    ET.indent(mxfile, space="  ")
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write('<?xml version="1.0" encoding="UTF-8"?>\n')
        ET.ElementTree(mxfile).write(f, encoding="unicode", xml_declaration=False)
    print(f"  ✓ {path}")


# ---------------------------------------------------------------------------
# Overview diagram
# ---------------------------------------------------------------------------

def generate_overview(all_data: dict[str, ModuleData], out_path: Path) -> None:
    _reset()
    mxfile, root = _make_graph()

    # Root classes per module (no TW parent within that module)
    def _roots(md: ModuleData) -> list[URIRef]:
        has_tw_parent = {child for child, _ in md.subclass_pairs}
        return sorted([c for c in md.classes if c not in has_tw_parent], key=_local)

    # Global class → module index
    cls_to_mod: dict[URIRef, str] = {}
    for mod_name, md in all_data.items():
        for c in md.classes:
            cls_to_mod[c] = mod_name

    mod_cell_ids:   dict[str, str]     = {}
    class_cell_ids: dict[URIRef, str]  = {}

    # Layout: 2-column grid of module containers
    cx, cy     = 20, 20
    row_max_h  = 0

    for i, mod_name in enumerate(MOD_ORDER):
        if mod_name not in all_data:
            continue
        md    = all_data[mod_name]
        roots = _roots(md)
        fill, stroke = MOD_CLR.get(mod_name, ("#F5F5F5", "#666666"))

        # Container height — 2-column grid of root class boxes inside
        cols        = 2
        n_rows      = max(1, (len(roots) + cols - 1) // cols)
        inner_h     = n_rows * (CLS_H_BASE + ROW_GAP) - ROW_GAP
        cont_h      = CONT_PAD + 30 + inner_h + CONT_PAD  # 30 = swimlane header

        cid = f"mod_{mod_name.replace('-', '_')}"
        add_container(root, cid, mod_name, cx, cy,
                      OVERVIEW_W, cont_h, fill, stroke)
        mod_cell_ids[mod_name] = cid

        # Place root classes inside the container
        col_w = (OVERVIEW_W - 2 * CONT_PAD) // cols
        for j, cls in enumerate(roots):
            row = j // cols
            col = j % cols
            rx  = CONT_PAD + col * col_w
            ry  = CONT_PAD + row * (CLS_H_BASE + ROW_GAP)
            cls_cid = _uid("ov_cls")
            add_class_box(root, cls_cid, _local(cls),
                          rx, ry, col_w - 10, CLS_H_BASE, [],
                          parent=cid)
            class_cell_ids[cls] = cls_cid

        row_max_h = max(row_max_h, cont_h)

        if i % 2 == 0:
            cx += OVERVIEW_W + 40
        else:
            cx  = 20
            cy += row_max_h + 40
            row_max_h = 0

    # Cross-module object property arrows (overview layer, between root class boxes)
    drawn: set[tuple[str, str]] = set()
    for mod_name, md in all_data.items():
        for prop_name, src_cls, tgt_cls in md.obj_props:
            if cls_to_mod.get(src_cls) == cls_to_mod.get(tgt_cls):
                continue
            src_cid = class_cell_ids.get(src_cls)
            tgt_cid = class_cell_ids.get(tgt_cls)
            if not src_cid or not tgt_cid:
                continue
            key = (src_cid, tgt_cid)
            if key in drawn:
                continue
            drawn.add(key)
            add_obj_edge(root, _uid("ov_e"), prop_name,
                         src_cid, tgt_cid)

    write_drawio(mxfile, out_path)


# ---------------------------------------------------------------------------
# Per-module diagram
# ---------------------------------------------------------------------------

def generate_module_diagram(
    mod_name: str,
    md: ModuleData,
    cls_to_mod: dict[URIRef, str],
    out_path: Path,
) -> None:
    _reset()
    mxfile, root = _make_graph()

    positions   = _compute_layout(md.classes, md.subclass_pairs, md.data_props_by_cls)
    cell_ids:   dict[URIRef, str] = {}
    ext_ids:    dict[URIRef, str] = {}

    # Draw all TW classes in this module
    for cls, (x, y, w, h) in positions.items():
        cid   = _uid("cls")
        cell_ids[cls] = cid
        props = sorted(md.data_props_by_cls.get(cls, []), key=lambda p: p[0])
        add_class_box(root, cid, _local(cls),
                      x + CONT_PAD, y + CONT_PAD, w, h, props)

    # Subclass edges
    for child, parent in md.subclass_pairs:
        if child in cell_ids and parent in cell_ids:
            add_subclass_edge(root, _uid("sub"),
                              cell_ids[child], cell_ids[parent])

    # External classes needed by object properties
    ext_classes: set[URIRef] = {
        tgt for _, src, tgt in md.obj_props
        if src in cell_ids and tgt not in cell_ids
    }
    max_x = (
        max((x + w for x, y, w, h in positions.values()), default=0)
        + CONT_PAD + 80
    )
    ext_y = CONT_PAD
    for ext_cls in sorted(ext_classes, key=_local):
        cid = _uid("ext")
        ext_ids[ext_cls] = cid
        origin = cls_to_mod.get(ext_cls, "?")
        label  = f"{_local(ext_cls)}\n({origin})"
        w      = _cls_width(_local(ext_cls))
        add_class_box(root, cid, label,
                      max_x, ext_y, w, CLS_H_BASE, [],
                      fill=CLR_EXTERNAL, stroke="#666666")
        ext_y += CLS_H_BASE + ROW_GAP + 20

    # Object property edges
    for prop_name, src_cls, tgt_cls in md.obj_props:
        src_cid = cell_ids.get(src_cls)
        tgt_cid = cell_ids.get(tgt_cls) or ext_ids.get(tgt_cls)
        if src_cid and tgt_cid:
            add_obj_edge(root, _uid("prop"), prop_name,
                         src_cid, tgt_cid,
                         cross_module=(tgt_cls not in cell_ids))

    # Named individuals — placed below main diagram
    if md.individuals:
        bottom_y = (
            max((y + h for x, y, w, h in positions.values()), default=0)
            + CONT_PAD + LEVEL_GAP
        )
        # Group by class for layout
        by_class: dict[URIRef, list[URIRef]] = defaultdict(list)
        for ind, cls in md.individuals:
            by_class[cls].append(ind)

        ix = CONT_PAD
        for cls, inds in sorted(by_class.items(), key=lambda kv: _local(kv[0])):
            for ind in sorted(inds, key=_local):
                cid = _uid("ind")
                add_individual(root, cid, _local(ind), ix, bottom_y)
                # dashed edge from individual to its class
                if cls in cell_ids:
                    add_obj_edge(root, _uid("ityp"), "a",
                                 cid, cell_ids[cls],
                                 cross_module=True)
                ix += 150

    write_drawio(mxfile, out_path)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--out-dir", default="diagrams",
                        help="Output directory for .drawio files (default: diagrams)")
    args = parser.parse_args()

    out_dir = Path(args.out_dir)

    print("Parsing modules...")
    all_data: dict[str, ModuleData] = {}
    for mod_name, rel_path in MODULES.items():
        path = Path(rel_path)
        if not path.exists():
            print(f"  WARNING: {path} not found, skipping")
            continue
        print(f"  {mod_name}")
        all_data[mod_name] = parse_module(str(path))

    cls_to_mod: dict[URIRef, str] = {}
    for mod_name, md in all_data.items():
        for c in md.classes:
            cls_to_mod[c] = mod_name

    print(f"\nGenerating diagrams → {out_dir}/")
    generate_overview(all_data, out_dir / "overview.drawio")
    for mod_name, md in all_data.items():
        generate_module_diagram(mod_name, md, cls_to_mod,
                                out_dir / f"{mod_name}.drawio")

    print(f"\nDone — {len(all_data) + 1} files written.")
    print("Open in draw.io (diagrams.net) to tune layout before exporting to PDF/SVG.")


if __name__ == "__main__":
    main()
