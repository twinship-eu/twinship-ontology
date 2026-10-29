"""Consistency tests for the SHACL shapes in shapes/ against the merged ontology."""

from pathlib import Path

import pytest
from rdflib import Graph, Namespace, URIRef
from rdflib.namespace import RDF, RDFS

ROOT = Path(__file__).parent.parent
SHAPES_DIR = ROOT / "shapes"
ONTOLOGY_PATH = ROOT / "build" / "twinship-core-complete.ttl"
TEST_DATA_PATH = Path(__file__).parent / "data" / "twinship-test-instances.ttl"

SH = Namespace("http://www.w3.org/ns/shacl#")
TWS = "https://twin-ship.eu/twinship#"
IDO = "http://rds.posccaesar.org/ontology/lis14/rdl/"
SHAPES_NS = "https://twin-ship.eu/twinship/shapes#"
SHAPE_FILES = sorted(SHAPES_DIR.glob("*.ttl"))


@pytest.fixture(scope="module")
def ontology() -> Graph:
    if not ONTOLOGY_PATH.exists():
        pytest.skip(
            f"Merged ontology not found at {ONTOLOGY_PATH}. Run 'uv run python "
            "scripts/merge_modules.py --catalog model/catalog-v001.xml "
            "model/twinship-core.ttl build/twinship-core-complete.ttl' first."
        )
    return Graph().parse(ONTOLOGY_PATH, format="turtle")


@pytest.fixture(scope="module")
def shapes() -> Graph:
    graph = Graph()
    for path in SHAPE_FILES:
        graph.parse(path, format="turtle")
    return graph


def _range_of(ontology: Graph, prop: URIRef) -> set[URIRef]:
    """Return rdfs:range of prop, inherited from the nearest super-property if absent."""
    queue, seen = [prop], set()
    while queue:
        current = queue.pop(0)
        if current in seen:
            continue
        seen.add(current)
        ranges = set(ontology.objects(current, RDFS.range))
        if ranges:
            return ranges
        queue.extend(ontology.objects(current, RDFS.subPropertyOf))
    return set()


def test_shape_files_exist():
    assert SHAPE_FILES, f"No shape files found in {SHAPES_DIR}"


@pytest.mark.parametrize("path", SHAPE_FILES, ids=lambda p: p.name)
def test_shape_file_parses(path: Path):
    Graph().parse(path, format="turtle")


def test_shapes_use_shapes_namespace(shapes: Graph):
    outside = [
        str(s) for s in shapes.subjects(RDF.type, SH.NodeShape) if not str(s).startswith(SHAPES_NS)
    ]
    assert not outside, f"Node shapes outside {SHAPES_NS}: {outside}"


def test_referenced_terms_exist(ontology: Graph, shapes: Graph):
    referenced = {
        term
        for predicate in (SH.path, SH.targetClass, SH["class"])
        for term in shapes.objects(None, predicate)
        if isinstance(term, URIRef) and str(term).startswith((TWS, IDO))
    }
    missing = sorted(str(t) for t in referenced if (t, RDF.type, None) not in ontology)
    assert not missing, f"Terms used in shapes but not declared in the ontology: {missing}"


def test_datatypes_match_ranges(ontology: Graph, shapes: Graph):
    mismatches = []
    for prop_shape in shapes.subjects(SH.datatype, None):
        path = shapes.value(prop_shape, SH.path)
        if not isinstance(path, URIRef) or not str(path).startswith(TWS):
            continue
        datatype = shapes.value(prop_shape, SH.datatype)
        ranges = _range_of(ontology, path)
        if datatype not in ranges:
            mismatches.append(f"{path}: sh:datatype {datatype}, rdfs:range {sorted(ranges)}")
    assert not mismatches, "sh:datatype differs from rdfs:range:\n" + "\n".join(mismatches)


def test_test_instances_conform(ontology: Graph, shapes: Graph):
    from pyshacl import validate

    data = Graph().parse(TEST_DATA_PATH, format="turtle")
    conforms, _, report = validate(
        data, shacl_graph=shapes, ont_graph=ontology, inference="rdfs", abort_on_first=False
    )
    assert conforms, report
