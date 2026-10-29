from pathlib import Path

import pytest
from rdflib import OWL, RDF, Graph, Namespace

from semantic_audit.errors import OntologyLoadError, OntologyParseError
from semantic_audit.loader import load_graph

EX = Namespace("https://example.org/")


def test_nonexistent_file(tmp_path):
    with pytest.raises(OntologyLoadError, match="introuvable"):
        load_graph(tmp_path / "missing.ttl")


def test_unsupported_extension_requires_explicit_format(tmp_path):
    path = tmp_path / "my-ontology.data"
    path.write_text(
        "@prefix ex: <https://example.org/> . ex:Person a <http://www.w3.org/2002/07/owl#Class> .",
        encoding="utf-8",
    )
    with pytest.raises(OntologyLoadError, match="rdf-format"):
        load_graph(path)
    graph = load_graph(path, rdf_format="turtle")
    assert (EX.Person, RDF.type, OWL.Class) in graph


def test_malformed_turtle_is_reported(tmp_path):
    path = tmp_path / "invalid.ttl"
    path.write_text("@prefix : <https://example.org/> . :x :p", encoding="utf-8")
    with pytest.raises(OntologyParseError, match="Impossible de lire"):
        load_graph(path)


@pytest.mark.parametrize("rdf_format,suffix", [("xml", ".rdf"), ("json-ld", ".jsonld")])
def test_other_rdf_formats_are_supported(tmp_path, rdf_format, suffix):
    graph = Graph()
    graph.add((EX.Person, RDF.type, OWL.Class))
    path = tmp_path / f"model{suffix}"
    graph.serialize(destination=path, format=rdf_format)
    loaded = load_graph(path)
    assert (EX.Person, RDF.type, OWL.Class) in loaded


def test_directory_is_not_a_source(tmp_path):
    with pytest.raises(OntologyLoadError):
        load_graph(Path(tmp_path))
