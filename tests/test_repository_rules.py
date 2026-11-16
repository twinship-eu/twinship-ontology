"""Repository rules from CLAUDE.md: no rdfs:domain in source modules, and one version everywhere."""

import re
from pathlib import Path

import pytest
from rdflib import Graph, Namespace
from rdflib.namespace import OWL, RDF, RDFS

ROOT = Path(__file__).parent.parent
SOURCE_MODULES = sorted((ROOT / "model").glob("*.ttl")) + sorted(
    (ROOT / "model" / "modules").glob("*.ttl")
)
PAV = Namespace("http://purl.org/pav/")


def _version() -> str:
    text = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    return re.search(r'(?m)^version = "([^"]+)"', text).group(1)


VERSION = _version()


@pytest.mark.parametrize("path", SOURCE_MODULES, ids=lambda p: p.name)
def test_no_rdfs_domain_in_source(path: Path) -> None:
    """Source modules use class restrictions; rdfs:domain is only allowed in build/."""
    graph = Graph().parse(path, format="turtle")
    domains = sorted(str(s) for s in graph.subjects(RDFS.domain, None))
    assert not domains, f"rdfs:domain in {path.name}: {domains}"


@pytest.mark.parametrize("path", SOURCE_MODULES, ids=lambda p: p.name)
def test_ontology_header_version(path: Path) -> None:
    """Each module's versionIRI and version literals match the version in pyproject.toml."""
    graph = Graph().parse(path, format="turtle")
    ontologies = list(graph.subjects(RDF.type, OWL.Ontology))
    assert len(ontologies) == 1, f"{path.name}: expected one owl:Ontology header"
    ontology = ontologies[0]
    version_iris = [str(o) for o in graph.objects(ontology, OWL.versionIRI)]
    assert version_iris == [
        f"{ontology}/{VERSION}"
    ], f"{path.name}: versionIRI {version_iris}, expected {ontology}/{VERSION}"
    for prop in (PAV.version, OWL.versionInfo):
        for literal in graph.objects(ontology, prop):
            assert str(literal) == VERSION, f"{path.name}: {prop} is {literal}"


# File, and a pattern whose group(1) must equal the version (every match is checked)
VERSION_PATTERNS = [
    ("CITATION.cff", r"(?m)^version:\s*(\S+)"),
    ("CHANGELOG.md", r"(?m)^## \[(\d+\.\d+\.\d+)\]"),
    ("STATISTICS.md", r"\*\*Version:\*\*\s*(\S+)"),
    ("model/README.md", r"\*\*Version\*\*:\s*(\S+)"),
    ("model/catalog-v001.xml", r'name="https://twin-ship\.eu/twinship/[\w-]+/(\d+\.\d+\.\d+)"'),
    ("shapes/twinship-shapes.ttl", r'pav:version "([^"]+)"'),
    ("shapes/twinship-shapes.ttl", r"twinship/shapes/(\d+\.\d+\.\d+)>"),
    ("scripts/generate_website.sh", r"TwinShip Ontology \| Version (\d+\.\d+\.\d+)"),
]


@pytest.mark.parametrize("file, pattern", VERSION_PATTERNS, ids=lambda v: str(v))
def test_version_in_sync(file: str, pattern: str) -> None:
    """Version numbers listed in CLAUDE.md (Common Pitfalls 10) match pyproject.toml."""
    text = (ROOT / file).read_text(encoding="utf-8")
    found = re.findall(pattern, text)
    assert found, f"{file}: no version found with {pattern!r}"
    if file == "CHANGELOG.md":
        found = found[:1]  # only the latest release heading
    assert set(found) == {VERSION}, f"{file}: {sorted(set(found))}, expected {VERSION}"
