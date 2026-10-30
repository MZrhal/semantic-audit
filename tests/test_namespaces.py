"""Tests for RDF namespace analysis."""

import json

import pytest
from rdflib import OWL, RDF, RDFS, XSD, Graph, Literal, Namespace

from semantic_audit.cli import create_parser, main
from semantic_audit.inspector import inspect_graph

EX = Namespace("https://example.org/vocab#")
OTHER = Namespace("https://other.example/vocab#")
OBO = Namespace("http://purl.obolibrary.org/obo/")


def namespace_row(report, namespace):
    return next(row for row in report.namespaces if row.namespace == str(namespace))


def test_empty_graph_has_no_namespaces():
    report = inspect_graph(Graph())

    assert report.namespaces == ()


def test_without_prefixes_classification_is_unknown():
    graph = Graph()
    graph.add((EX.Person, RDF.type, OWL.Class))

    report = inspect_graph(graph)
    row = namespace_row(report, EX)

    assert row.classification == "unknown"
    assert row.declared_classes == 1
    assert row.internal_iri_count is None
    assert row.internal_declared_classes is None


def test_namespace_counts_declared_terms_and_unique_iris():
    graph = Graph()

    graph.add((EX.Person, RDF.type, OWL.Class))
    graph.add((EX.Person, RDFS.label, Literal("Person")))
    graph.add((EX.knows, RDF.type, OWL.ObjectProperty))
    graph.add((EX.alice, RDF.type, EX.Person))
    graph.add((EX.alice, EX.knows, EX.bob))

    report = inspect_graph(
        graph,
        internal_prefixes=(str(EX),),
    )

    row = namespace_row(report, EX)

    assert row.classification == "internal"
    assert row.iri_count == 4
    assert row.internal_iri_count == 4
    assert row.declared_classes == 1
    assert row.internal_declared_classes == 1
    assert row.declared_properties == 1
    assert row.internal_declared_properties == 1
    assert row.named_individuals == 1
    assert row.internal_named_individuals == 1


def test_used_property_is_not_automatically_declared():
    graph = Graph()
    graph.add((EX.alice, EX.hasSkill, EX.python))

    report = inspect_graph(
        graph,
        internal_prefixes=(str(EX),),
    )
    row = namespace_row(report, EX)

    assert row.iri_count == 3
    assert row.declared_properties == 0


def test_shared_obo_namespace_can_be_mixed():
    graph = Graph()

    graph.add((OBO.FOODON_000001, RDF.type, OWL.Class))
    graph.add((OBO.ENVO_000001, RDF.type, OWL.Class))
    graph.add((OBO.FOODON_000002, RDF.type, OWL.ObjectProperty))

    report = inspect_graph(
        graph,
        internal_prefixes=(str(OBO) + "FOODON_",),
    )

    row = namespace_row(report, OBO)

    assert row.classification == "mixed"
    assert row.iri_count == 3
    assert row.internal_iri_count == 2
    assert row.declared_classes == 2
    assert row.internal_declared_classes == 1
    assert row.declared_properties == 1
    assert row.internal_declared_properties == 1


def test_multiple_internal_prefixes():
    graph = Graph()

    graph.add((EX.Person, RDF.type, OWL.Class))
    graph.add((OTHER.Organization, RDF.type, OWL.Class))

    report = inspect_graph(
        graph,
        internal_prefixes=(str(EX), str(OTHER)),
    )

    assert namespace_row(report, EX).classification == "internal"
    assert namespace_row(report, OTHER).classification == "internal"

    assert namespace_row(report, OWL).classification == "external"


def test_literal_datatype_namespace_is_included():
    graph = Graph()

    graph.add(
        (
            EX.record,
            EX.createdAt,
            Literal(
                "2026-10-30T08:00:00",
                datatype=XSD.dateTime,
            ),
        )
    )

    report = inspect_graph(graph)

    row = namespace_row(report, XSD)

    assert row.iri_count == 1
    assert row.classification == "unknown"


def test_namespace_order_is_stable():
    graph = Graph()

    graph.add((OTHER.Organization, RDF.type, OWL.Class))
    graph.add((EX.Person, RDF.type, OWL.Class))

    report = inspect_graph(graph)

    namespaces = [row.namespace for row in report.namespaces]

    assert namespaces == sorted(namespaces)


def test_cli_serializes_namespace_analysis(tmp_path):
    source = tmp_path / "ontology.ttl"
    output = tmp_path / "namespace-report.json"

    source.write_text(
        "@prefix ex: <https://example.org/vocab#> . "
        "@prefix owl: <http://www.w3.org/2002/07/owl#> . "
        "ex:Person a owl:Class .",
        encoding="utf-8",
    )

    status = main(
        [
            "inspect",
            str(source),
            "--internal-prefix",
            str(EX),
            "--output",
            str(output),
        ]
    )

    assert status == 0

    payload = json.loads(output.read_text(encoding="utf-8"))

    assert payload["schema_version"] == "1.2"
    assert payload["internal_prefixes"] == [str(EX)]

    row = next(item for item in payload["namespaces"] if item["namespace"] == str(EX))

    assert row["classification"] == "internal"
    assert row["declared_classes"] == 1


def test_cli_rejects_empty_internal_prefix():
    parser = create_parser()

    with pytest.raises(SystemExit) as exc:
        parser.parse_args(["inspect", "ontology.ttl", "--internal-prefix", ""])

    assert exc.value.code == 2
