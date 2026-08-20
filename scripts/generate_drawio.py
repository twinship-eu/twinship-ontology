#!/usr/bin/env python3
"""
generate_drawio.py — Generate Graffoo-style draw.io diagrams from TwinShip TTL modules.

Outputs (in --out-dir, default: diagrams/):
  modules.drawio               — module dependency graph (imports, Figure 2 style)
  overview.drawio              — essential classes with cross-module links (Figure 3 style)
  vessel.drawio                — full vessel module diagram
  operational-context.drawio
  operational-modes.drawio
  weather-conditions.drawio
  predictions.drawio

All diagrams use A4 landscape canvas. Open in draw.io, tune layout, export to PDF/SVG.

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

# Import dependencies between domain modules (excluding base, which all import)
MOD_DEPS: dict[str, list[str]] = {
    "vessel":               [],
    "operational-modes":    [],
    "weather-conditions":   [],
    "operational-context":  ["operational-modes", "weather-conditions"],
    "predictions":          ["operational-modes", "operational-context", "weather-conditions"],
}

# Module descriptions shown in the modules diagram
MOD_DESC: dict[str, str] = {
    "vessel":               "Vessel systems, engines,\npropulsion, fuel, gearbox",
    "operational-context":  "Voyage, leg, port, route,\nprofiles, observations",
    "operational-modes":    "Operating states,\nengine/draft/trim modes",
    "weather-conditions":   "Weather, wind, wave\nand current conditions",
    "predictions":          "ML predictions, estimations,\nmodel cards (MCRO)",
}

# Maximum number of classes to show in per-module diagrams.
# Modules already within this limit show all classes.
# Larger modules are filtered to the most connected classes.
MODULE_MAX_CLASSES: dict[str, int] = {
    "vessel":               14,
    "operational-context":  12,
    "operational-modes":    10,   # only 5 classes — no filtering needed
    "weather-conditions":   10,   # only 4 classes — no filtering needed
    "predictions":          13,
}
DEFAULT_MAX_CLASSES = 12

# Semantic links that are important for the overview but not encoded as OWL
# restrictions (e.g. because the modules don't import each other).
# Shown as dashed arrows labelled with (†) in the overview diagram.
MANUAL_LINKS: list[tuple[str, str, str]] = [
    # (source_class_local_name, target_class_local_name, property_label)
    ("VoyageLeg", "VesselSystem", "isForVessel†"),
]

# Fixed spatial positions for each module group in the overview diagram.
# Values are (x, y) top-left corner of the group's class cluster.
# Designed for A4 landscape so VoyageLeg sits at the centre.
OVERVIEW_GROUP_POS: dict[str, tuple[int, int]] = {
    "operational-modes":    (180,  50),
    "weather-conditions":   (720,  50),
    "vessel":               (30,  310),
    "operational-context":  (400, 270),
    "predictions":          (640, 460),
}

# ---------------------------------------------------------------------------
# Graffoo colours
# ---------------------------------------------------------------------------

CLR_CLASS    = "#FFFF88"   # yellow — OWL class (default, overridden in overview)
CLR_EXTERNAL = "#F5F5F5"   # grey   — class from another module
CLR_INDIV    = "#FFFF88"   # yellow — named individual (ellipse)
CLR_BASE     = "#E8E8E8"   # light grey — twinship-base box in modules diagram

MOD_CLR: dict[str, tuple[str, str]] = {   # (fill, stroke)
    "vessel":               ("#DAE8FC", "#6C8EBF"),
    "operational-context":  ("#D5E8D4", "#82B366"),
    "operational-modes":    ("#FFE6CC", "#D6B656"),
    "weather-conditions":   ("#E1D5E7", "#9673A6"),
    "predictions":          ("#FFF2CC", "#B85450"),
}

# ---------------------------------------------------------------------------
# A4 landscape canvas
# ---------------------------------------------------------------------------

A4_W = 1123   # A4 landscape width in pixels at 96 dpi
A4_H = 794

# ---------------------------------------------------------------------------
# Layout constants
# ---------------------------------------------------------------------------

CLS_W_MIN   = 180
CLS_H_BASE  = 40
CLS_H_PROP  = 16    # extra height per data property line
COL_GAP     = 220   # horizontal spacing between class columns
LEVEL_GAP   = 90    # vertical spacing between hierarchy levels
ROW_GAP     = 16    # spacing between classes on the same level
CONT_PAD    = 40    # padding inside module containers
MARGIN      = 30    # canvas margin

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


def parse_module(path: str,
                 global_obj_props: frozenset[URIRef] = frozenset()) -> ModuleData:
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

    # Merge locally-declared properties with the global registry so that
    # cross-module restrictions (where the property lives in an imported
    # module) are still classified correctly.
    local_obj_props  = frozenset(g.subjects(RDF.type, OWL.ObjectProperty))
    local_data_props = frozenset(g.subjects(RDF.type, OWL.DatatypeProperty))
    all_obj_props    = local_obj_props | global_obj_props

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

            is_data = on_prop in local_data_props
            is_obj  = on_prop in all_obj_props

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
# Central class selection for per-module diagrams
# ---------------------------------------------------------------------------

def select_central_classes(
    classes: set[URIRef],
    subclass_pairs: list[tuple[URIRef, URIRef]],
    obj_props: list[tuple[str, URIRef, URIRef]],
    individuals: list[tuple[URIRef, URIRef]],
    max_classes: int,
) -> set[URIRef]:
    """Return the most connected subset of classes, up to max_classes."""
    if len(classes) <= max_classes:
        return set(classes)

    from collections import defaultdict
    scores: dict[URIRef, int] = {c: 0 for c in classes}
    tw_parents: set[URIRef] = {child for child, _ in subclass_pairs}
    tw_children: dict[URIRef, int] = defaultdict(int)
    for child, parent in subclass_pairs:
        tw_children[parent] += 1

    prop_sources: set[URIRef] = {src for _, src, _ in obj_props if src in classes}
    prop_targets: set[URIRef] = {tgt for _, _, tgt in obj_props if tgt in classes}
    ind_classes:  set[URIRef] = {cls for _, cls in individuals if cls in classes}

    for cls in classes:
        if cls not in tw_parents:        # root class
            scores[cls] += 4
        scores[cls] += tw_children[cls]  # has named subclasses
        if cls in prop_sources:
            scores[cls] += 3             # initiates object property
        if cls in prop_targets:
            scores[cls] += 3             # is target of object property
        if cls in ind_classes:
            scores[cls] += 2             # has named individuals

    return set(sorted(classes, key=lambda c: scores[c], reverse=True)[:max_classes])


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

    # Place: row = depth level (top→bottom), columns wrap within A4 width
    max_cols = max(1, (A4_W - 2 * MARGIN) // COL_GAP)

    positions: dict[URIRef, tuple[int, int, int, int]] = {}
    y = 0
    for lvl in sorted(by_level):
        cls_list = by_level[lvl]
        # Wrap long rows into sub-rows to stay within A4 width
        for chunk_start in range(0, len(cls_list), max_cols):
            chunk = cls_list[chunk_start:chunk_start + max_cols]
            row_h = max(_h(c) for c in chunk)
            for col, cls in enumerate(chunk):
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


def _make_graph(name: str = "diagram") -> tuple[ET.Element, ET.Element]:
    """Return (mxfile, root) where root is the <root> layer element."""
    mxfile  = ET.Element("mxfile")
    diagram = ET.SubElement(mxfile, "diagram", name=name)
    graph   = ET.SubElement(
        diagram, "mxGraphModel",
        dx="1422", dy="762", grid="1", gridSize="10",
        guides="1", tooltips="1", connect="1", arrows="1",
        fold="1", page="1", pageScale="1",
        pageWidth=str(A4_W), pageHeight=str(A4_H),   # A4 landscape
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


def add_module_boundary(root: ET.Element, cid: str, label: str,
                        x: int, y: int, w: int, h: int,
                        fill: str, stroke: str,
                        parent: str = "1") -> None:
    """Dashed module boundary box drawn behind class boxes (SSN Figure 3 style)."""
    style = (
        f"rounded=1;whiteSpace=wrap;dashed=1;dashPattern=8 4;"
        f"fillColor={fill};strokeColor={stroke};strokeWidth=2;"
        "fontStyle=1;fontSize=11;verticalAlign=top;align=left;"
        "spacingLeft=8;spacingTop=4;"
    )
    cell = ET.SubElement(root, "mxCell",
                         id=cid, value=_html.escape(label), style=style,
                         vertex="1", parent=parent)
    _geo(cell, x, y, w, h)


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
# Modules diagram (Figure 2 style) — dependency graph only, no classes
# ---------------------------------------------------------------------------

def generate_modules_diagram(out_path: Path) -> None:
    """Module dependency graph: boxes for each module + import arrows."""
    _reset()
    mxfile, root = _make_graph("TwinShip Modules")

    # Fixed positions chosen to fill A4 landscape cleanly
    MOD_W, MOD_H = 200, 80
    BASE_W        = 220

    positions: dict[str, tuple[int, int]] = {
        "twinship-base":      (A4_W // 2 - BASE_W // 2, 40),
        "vessel":             (60,  220),
        "operational-modes":  (310, 220),
        "weather-conditions": (700, 220),
        "operational-context":(450, 380),
        "predictions":        (450, 540),
    }

    cell_ids: dict[str, str] = {}

    # Base box (special styling)
    bx, by = positions["twinship-base"]
    cid = "mod_base"
    cell_ids["twinship-base"] = cid
    style = (
        f"rounded=1;whiteSpace=wrap;fillColor={CLR_BASE};strokeColor=#555555;"
        "fontStyle=1;fontSize=13;html=1;"
    )
    cell = ET.SubElement(root, "mxCell",
                         id=cid,
                         value="<b>twinship-base</b><br/>"
                               "<font style='font-size:10px;'>IDO · QUDT · PAV</font>",
                         style=style, vertex="1", parent="1")
    _geo(cell, bx, by, BASE_W, MOD_H)

    # Domain module boxes
    for mod_name in MOD_ORDER:
        x, y = positions[mod_name]
        fill, stroke = MOD_CLR.get(mod_name, ("#F5F5F5", "#666666"))
        cid = f"mod_{mod_name.replace('-', '_')}"
        cell_ids[mod_name] = cid
        desc = MOD_DESC.get(mod_name, "")
        label = (
            f"<b>{_html.escape(mod_name)}</b><br/>"
            f"<font style='font-size:10px;'>{_html.escape(desc)}</font>"
        )
        style = (
            f"rounded=1;whiteSpace=wrap;fillColor={fill};strokeColor={stroke};"
            "fontStyle=0;fontSize=12;html=1;verticalAlign=middle;align=center;"
        )
        cell = ET.SubElement(root, "mxCell",
                             id=cid, value=label, style=style,
                             vertex="1", parent="1")
        _geo(cell, x, y, MOD_W, MOD_H)

    # Import arrows: all modules → base
    for mod_name in MOD_ORDER:
        add_obj_edge(root, _uid("imp"), "imports",
                     cell_ids[mod_name], cell_ids["twinship-base"],
                     cross_module=True)

    # Cross-module import arrows between domain modules
    for mod_name, deps in MOD_DEPS.items():
        for dep in deps:
            if mod_name in cell_ids and dep in cell_ids:
                add_obj_edge(root, _uid("dep"), "imports",
                             cell_ids[mod_name], cell_ids[dep])

    write_drawio(mxfile, out_path)


# ---------------------------------------------------------------------------
# Overview diagram (Figure 3 style) — connected classes, dashed module boxes
# ---------------------------------------------------------------------------

def generate_overview(all_data: dict[str, ModuleData], out_path: Path) -> None:
    """
    SSN Figure 3 style: essential classes that have at least one cross-module
    link, colour-coded by module, surrounded by dashed module boundary boxes.
    VesselSystem is included via a manually-defined semantic link (dashed arrow).
    """
    _reset()
    mxfile, root = _make_graph("TwinShip Overview")

    # ── 1. Build global lookups ─────────────────────────────────────────────
    cls_to_mod:   dict[URIRef, str]  = {}
    name_to_uri:  dict[str, URIRef] = {}
    for mod_name, md in all_data.items():
        for c in md.classes:
            cls_to_mod[c] = mod_name
            name_to_uri[_local(c)] = c

    # ── 2. Collect all cross-module OWL links ───────────────────────────────
    cross_links: list[tuple[str, URIRef, URIRef]] = []  # (prop, src, tgt)
    for mod_name, md in all_data.items():
        for prop_name, src_cls, tgt_cls in md.obj_props:
            if cls_to_mod.get(src_cls) != cls_to_mod.get(tgt_cls):
                cross_links.append((prop_name, src_cls, tgt_cls))

    # ── 3. Derive essential classes (those that appear in cross-module links)
    essential_uris: set[URIRef] = set()
    for _, src, tgt in cross_links:
        essential_uris.add(src)
        if tgt in cls_to_mod:   # skip external-to-TW targets
            essential_uris.add(tgt)

    # Add VesselSystem manually (central concept, not OWL-linked cross-module)
    vs_uri = name_to_uri.get("VesselSystem")
    if vs_uri:
        essential_uris.add(vs_uri)

    # Drop classes with no visible connections: iteratively remove any class
    # that has zero links where both endpoints are in the shown set.
    manual_src = {name_to_uri.get(s) for s, _, _ in MANUAL_LINKS}
    manual_tgt = {name_to_uri.get(t) for _, t, _ in MANUAL_LINKS}
    for _ in range(10):   # iterate to convergence
        connected: set[URIRef] = set()
        for _, src, tgt in cross_links:
            if src in essential_uris and tgt in essential_uris:
                connected.add(src); connected.add(tgt)
        for s_uri, t_uri in zip(manual_src, manual_tgt):
            if s_uri and t_uri and s_uri in essential_uris and t_uri in essential_uris:
                connected.add(s_uri); connected.add(t_uri)
        if connected >= essential_uris:
            break
        essential_uris &= connected
        if not essential_uris:
            break

    # Group essential classes by module
    by_module: dict[str, list[URIRef]] = defaultdict(list)
    for uri in essential_uris:
        mod = cls_to_mod.get(uri)
        if mod:
            by_module[mod].append(uri)
    for mod in by_module:
        by_module[mod].sort(key=_local)

    # ── 4. Lay out class boxes per module group ─────────────────────────────
    BOX_PAD    = 18   # padding inside module boundary box
    LABEL_H    = 22   # space for module name label at top of boundary box
    CLS_COL_W  = CLS_W_MIN + 12
    GROUP_COLS = 2

    group_boxes:  dict[str, tuple[int, int, int, int]] = {}  # mod → (x,y,w,h)
    class_cell_ids: dict[URIRef, str] = {}

    # Pass 1: compute bounding box sizes (before drawing, so boundary boxes
    # can be emitted first to render behind class boxes)
    group_layouts: dict[str, list[tuple[URIRef, int, int]]] = {}
    for mod_name, cls_list in by_module.items():
        if mod_name not in OVERVIEW_GROUP_POS:
            continue
        gx, gy = OVERVIEW_GROUP_POS[mod_name]
        layout = []
        for j, cls_uri in enumerate(cls_list):
            col = j % GROUP_COLS
            row = j // GROUP_COLS
            lx  = gx + BOX_PAD + col * (CLS_COL_W + 10)
            ly  = gy + BOX_PAD + LABEL_H + row * (CLS_H_BASE + ROW_GAP)
            layout.append((cls_uri, lx, ly))
        n_rows = (len(cls_list) + GROUP_COLS - 1) // GROUP_COLS
        bw = GROUP_COLS * (CLS_COL_W + 10) - 10 + 2 * BOX_PAD
        bh = LABEL_H + n_rows * (CLS_H_BASE + ROW_GAP) - ROW_GAP + 2 * BOX_PAD
        group_boxes[mod_name]   = (gx, gy, bw, bh)
        group_layouts[mod_name] = layout

    # Pass 2: emit module boundary boxes FIRST (renders behind class boxes)
    for mod_name, (bx, by, bw, bh) in group_boxes.items():
        fill, stroke = MOD_CLR.get(mod_name, ("#F5F5F5", "#666666"))
        add_module_boundary(root, f"bnd_{mod_name.replace('-','_')}",
                            mod_name, bx, by, bw, bh, fill, stroke)

    # Pass 3: emit class boxes on top of boundary boxes
    for mod_name, layout in group_layouts.items():
        fill, stroke = MOD_CLR.get(mod_name, ("#F5F5F5", "#666666"))
        for cls_uri, lx, ly in layout:
            cid = _uid("ov_cls")
            class_cell_ids[cls_uri] = cid
            add_class_box(root, cid, _local(cls_uri),
                          lx, ly, CLS_COL_W, CLS_H_BASE, [],
                          fill=fill, stroke=stroke)

    # ── 5. Draw cross-module OWL object property arrows ─────────────────────
    drawn: set[tuple[str, str]] = set()
    for prop_name, src_cls, tgt_cls in cross_links:
        src_cid = class_cell_ids.get(src_cls)
        tgt_cid = class_cell_ids.get(tgt_cls)
        if not (src_cid and tgt_cid):
            continue
        key = (src_cid, tgt_cid)
        if key in drawn:
            continue
        drawn.add(key)
        add_obj_edge(root, _uid("ov_e"), prop_name, src_cid, tgt_cid)

    # ── 6. Draw manual semantic links (dashed) ───────────────────────────────
    for src_name, tgt_name, prop_label in MANUAL_LINKS:
        src_uri = name_to_uri.get(src_name)
        tgt_uri = name_to_uri.get(tgt_name)
        src_cid = class_cell_ids.get(src_uri) if src_uri else None
        tgt_cid = class_cell_ids.get(tgt_uri) if tgt_uri else None
        if src_cid and tgt_cid:
            add_obj_edge(root, _uid("ov_manual"), prop_label,
                         src_cid, tgt_cid, cross_module=True)

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
    mxfile, root = _make_graph(mod_name)

    fill, stroke = MOD_CLR.get(mod_name, ("#FFFF88", "#333333"))
    max_cls = MODULE_MAX_CLASSES.get(mod_name, DEFAULT_MAX_CLASSES)

    # Filter to central classes when the module is too large for a paper figure
    shown = select_central_classes(
        md.classes, md.subclass_pairs, md.obj_props, md.individuals, max_cls
    )

    # Restrict subclass pairs and object props to the shown set
    shown_subclass = [(c, p) for c, p in md.subclass_pairs
                      if c in shown and p in shown]
    shown_obj = [(n, s, t) for n, s, t in md.obj_props if s in shown]

    positions   = _compute_layout(shown, shown_subclass, md.data_props_by_cls)
    cell_ids:   dict[URIRef, str] = {}
    ext_ids:    dict[URIRef, str] = {}

    # Draw shown TW classes in module colour
    for cls, (x, y, w, h) in positions.items():
        cid   = _uid("cls")
        cell_ids[cls] = cid
        props = sorted(md.data_props_by_cls.get(cls, []), key=lambda p: p[0])
        add_class_box(root, cid, _local(cls),
                      x + CONT_PAD, y + CONT_PAD, w, h, props,
                      fill=fill, stroke=stroke)

    # Subclass edges
    for child, parent in shown_subclass:
        if child in cell_ids and parent in cell_ids:
            add_subclass_edge(root, _uid("sub"),
                              cell_ids[child], cell_ids[parent])

    # External classes: only truly cross-module targets, not same-module
    # classes that were simply filtered out by select_central_classes.
    ext_classes: set[URIRef] = {
        tgt for _, src, tgt in shown_obj
        if src in cell_ids
        and tgt not in cell_ids
        and cls_to_mod.get(tgt, mod_name) != mod_name
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
    for prop_name, src_cls, tgt_cls in shown_obj:
        src_cid = cell_ids.get(src_cls)
        tgt_cid = cell_ids.get(tgt_cls) or ext_ids.get(tgt_cls)
        if src_cid and tgt_cid:
            add_obj_edge(root, _uid("prop"), prop_name,
                         src_cid, tgt_cid,
                         cross_module=(tgt_cls not in cell_ids))

    # Named individuals — wrapped within A4 width, linked to their class
    if md.individuals:
        bottom_y = (
            max((y + h for x, y, w, h in positions.values()), default=0)
            + CONT_PAD + LEVEL_GAP
        )
        by_class: dict[URIRef, list[URIRef]] = defaultdict(list)
        for ind, cls in md.individuals:
            by_class[cls].append(ind)

        IND_W, IND_H = 140, 40
        IND_GAP = 10
        max_ind_cols = max(1, (A4_W - 2 * CONT_PAD) // (IND_W + IND_GAP))

        all_inds = [
            (ind, cls)
            for cls in sorted(by_class, key=_local)
            for ind in sorted(by_class[cls], key=_local)
        ]
        for i, (ind, cls) in enumerate(all_inds):
            col = i % max_ind_cols
            row = i // max_ind_cols
            ix  = CONT_PAD + col * (IND_W + IND_GAP)
            iy  = bottom_y + row * (IND_H + IND_GAP)
            cid = _uid("ind")
            add_individual(root, cid, _local(ind), ix, iy)
            parent_cid = cell_ids.get(cls)
            if parent_cid:
                add_obj_edge(root, _uid("ityp"), "a",
                             cid, parent_cid, cross_module=True)

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
    # Pass 1: collect all object property URIs across modules + key external files
    # This is needed so IDO properties (ido:partOf, ido:connectedTo, etc.) and
    # base vocabulary properties are recognised when scanning module restrictions.
    global_obj_props: set[URIRef] = set()
    for src in [
        *Path("model/modules").glob("*.ttl"),
        *Path("model").glob("*.ttl"),
        Path("model/external/IDO_20240503.ttl"),
    ]:
        if src.exists():
            g = Graph()
            g.parse(str(src), format="turtle")
            global_obj_props.update(g.subjects(RDF.type, OWL.ObjectProperty))

    frozen_obj_props = frozenset(global_obj_props)

    # Pass 2: full parse with the global object-property registry
    all_data: dict[str, ModuleData] = {}
    for mod_name, rel_path in MODULES.items():
        path = Path(rel_path)
        if not path.exists():
            print(f"  WARNING: {path} not found, skipping")
            continue
        print(f"  {mod_name}")
        all_data[mod_name] = parse_module(str(path), frozen_obj_props)

    cls_to_mod: dict[URIRef, str] = {}
    for mod_name, md in all_data.items():
        for c in md.classes:
            cls_to_mod[c] = mod_name

    print(f"\nGenerating diagrams → {out_dir}/")
    generate_modules_diagram(out_dir / "modules.drawio")
    generate_overview(all_data, out_dir / "overview.drawio")
    for mod_name, md in all_data.items():
        generate_module_diagram(mod_name, md, cls_to_mod,
                                out_dir / f"{mod_name}.drawio")

    print(f"\nDone — {len(all_data) + 2} files written.")
    print("Open in draw.io (diagrams.net) to tune layout before exporting to PDF/SVG.")


if __name__ == "__main__":
    main()
