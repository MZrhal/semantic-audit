"""Offline tests for HTTP(S) RDF sources (no live network needed)."""

import io
import json
from unittest.mock import patch
from urllib.error import HTTPError, URLError

import pytest
from rdflib import OWL, RDF, Graph, Namespace

from semantic_audit.cli import main
from semantic_audit.errors import OntologyLoadError
from semantic_audit.inspector import inspect_ontology
from semantic_audit.loader import load_graph

EX = Namespace("https://example.org/")
TTL = b"@prefix ex: <https://example.org/> . ex:Person a <http://www.w3.org/2002/07/owl#Class> ."


class FakeHTTPResponse:
    def __init__(
        self,
        data=TTL,
        url="https://example.org/ontology",
        content_type="text/turtle",
        headers=None,
    ):
        self.stream = io.BytesIO(data)
        self.url = url
        self.headers = {"Content-Type": content_type, **(headers or {})}

    def geturl(self):
        return self.url

    def read(self, n):
        return self.stream.read(n)

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.stream.close()


def test_remote_rdf_url_with_content_type():
    with patch("semantic_audit.loader.urlopen", return_value=FakeHTTPResponse()):
        graph = load_graph("https://example.org/ontology")
    assert (EX.Person, RDF.type, OWL.Class) in graph


def test_remote_source_is_not_mangled():
    url = "https://example.org/ontology?version=1"
    with patch("semantic_audit.loader.urlopen", return_value=FakeHTTPResponse()):
        report = inspect_ontology(url)
    assert report.source == url
    assert report.statistics.declared_classes == 1


def test_remote_url_uses_format_override():
    with patch(
        "semantic_audit.loader.urlopen",
        return_value=FakeHTTPResponse(content_type="application/octet-stream"),
    ):
        graph = load_graph("https://example.org/no-extension", rdf_format="turtle")
    assert len(graph) == 1


def test_remote_url_uses_owl_extension():
    graph = Graph()
    graph.add((EX.Person, RDF.type, OWL.Class))
    rdf_xml = graph.serialize(format="xml", encoding="utf-8")
    with patch(
        "semantic_audit.loader.urlopen",
        return_value=FakeHTTPResponse(
            data=rdf_xml,
            url="https://example.org/model.owl",
            content_type="application/octet-stream",
        ),
    ):
        loaded = load_graph("https://example.org/model.owl")
    assert (EX.Person, RDF.type, OWL.Class) in loaded


def test_remote_rejects_html_github_page():
    with (
        patch(
            "semantic_audit.loader.urlopen",
            return_value=FakeHTTPResponse(content_type="text/html"),
        ),
        pytest.raises(OntologyLoadError, match="HTML"),
    ):
        load_graph("https://github.com/org/repo/blob/main/model.ttl")


def test_remote_reports_http_failure():
    with (
        patch(
            "semantic_audit.loader.urlopen",
            side_effect=HTTPError("https://example.org/missing.owl", 404, "Not Found", None, None),
        ),
        pytest.raises(OntologyLoadError, match="404"),
    ):
        load_graph("https://example.org/missing.owl")


def test_remote_reports_network_failure():
    with (
        patch("semantic_audit.loader.urlopen", side_effect=URLError("offline")),
        pytest.raises(OntologyLoadError, match="télécharger"),
    ):
        load_graph("https://example.org/ontology.ttl")


def test_remote_rejects_oversized_document(monkeypatch):
    monkeypatch.setattr("semantic_audit.loader.MAX_DOWNLOAD_BYTES", 20)
    with (
        patch("semantic_audit.loader.urlopen", return_value=FakeHTTPResponse()),
        pytest.raises(OntologyLoadError, match="limite"),
    ):
        load_graph("https://example.org/ontology.ttl")


def test_remote_rejects_non_http_urls():
    with pytest.raises(OntologyLoadError, match="HTTP"):
        load_graph("ftp://example.org/ontology.ttl")


def test_cli_accepts_remote_url(tmp_path):
    output = tmp_path / "remote.json"
    url = "https://example.org/ontology.ttl"
    with patch("semantic_audit.loader.urlopen", return_value=FakeHTTPResponse()):
        exit_code = main(["inspect", url, "--output", str(output)])
    assert exit_code == 0
    report = json.loads(output.read_text(encoding="utf-8"))
    assert report["source"] == url
    assert report["statistics"]["declared_classes"] == 1
