"""Tests for RDF typed-literal diagnostics."""

import json
import warnings

import pytest
from rdflib import XSD, BNode, Graph, Literal, Namespace

from semantic_audit.cli import main
from semantic_audit.inspector import inspect_graph, inspect_ontology

EX = Namespace("https://example.org/test/")


@pytest.mark.parametrize(
    ("lexical_value", "datatype"),
    [
        ("2026-04-10 9:06:01", XSD.dateTime),
        ("https://orcid.org/0000-0002-8844-9165", XSD.dateTime),
        ("12x", XSD.integer),
        ("2e3", XSD.decimal),
        ("sometimes", XSD.boolean),
    ],
)
def test_invalid_typed_literals_reported(lexical_value, datatype):
    graph = Graph()

    with warnings.catch_warnings():
        warnings.filterwarnings(
            "ignore",
            message="Parsing weird boolean.*",
        )
        graph.add(
            (
                EX.record,
                EX.hasValue,
                Literal(lexical_value, datatype=datatype, normalize=False),
            )
        )

    issues = inspect_graph(graph).issues

    assert len(issues) == 1

    issue = issues[0]
    assert issue.code == "INVALID_TYPED_LITERAL"
    assert issue.severity == "warning"
    assert issue.subject == str(EX.record)
    assert issue.predicate == str(EX.hasValue)
    assert issue.datatype == str(datatype)
    assert issue.lexical_value == lexical_value


def test_valid_typed_literals_not_reported():
    graph = Graph()

    graph.add(
        (
            EX.record,
            EX.timestamp,
            Literal("2026-04-10T09:06:01", datatype=XSD.dateTime),
        )
    )
    graph.add((EX.record, EX["count"], Literal("42", datatype=XSD.integer)))
    graph.add((EX.record, EX.active, Literal("true", datatype=XSD.boolean)))
    graph.add((EX.record, EX.price, Literal("1.5", datatype=XSD.decimal)))

    assert inspect_graph(graph).issues == ()


def test_custom_datatypes_not_misclassified():
    graph = Graph()
    graph.add(
        (
            EX.record,
            EX.hasValue,
            Literal("custom", datatype=EX.customDatatype),
        )
    )

    assert inspect_graph(graph).issues == ()


def test_issues_are_sorted_by_subject():
    graph = Graph()
    graph.add((EX.z, EX.hasValue, Literal("bad", datatype=XSD.integer)))
    graph.add((EX.a, EX.hasValue, Literal("worse", datatype=XSD.integer)))

    issues = inspect_graph(graph).issues

    assert [issue.subject for issue in issues] == [
        str(EX.a),
        str(EX.z),
    ]


def test_blank_node_subjects_are_identifiable():
    graph = Graph()
    blank = BNode()

    graph.add((blank, EX.hasValue, Literal("bad", datatype=XSD.integer)))

    issue = inspect_graph(graph).issues[0]
    assert issue.subject.startswith("_:")


def test_cli_serializes_diagnostics(tmp_path):
    source = tmp_path / "invalid.ttl"
    output = tmp_path / "audit.json"

    source.write_text(
        "@prefix xsd: <http://www.w3.org/2001/XMLSchema#> . "
        "<https://example.org/record> "
        "<https://example.org/createdAt> "
        '"2026-04-10 9:06:01"^^xsd:dateTime .',
        encoding="utf-8",
    )

    assert main(["inspect", str(source), "--output", str(output)]) == 0

    payload = json.loads(output.read_text(encoding="utf-8"))

    assert payload["schema_version"] == "1.2"
    assert len(payload["issues"]) == 1
    assert payload["issues"][0]["code"] == "INVALID_TYPED_LITERAL"
    assert payload["issues"][0]["lexical_value"] == "2026-04-10 9:06:01"


def test_file_parsing_preserves_invalid_lexical_forms(tmp_path):
    source = tmp_path / "invalid-literals.ttl"

    source.write_text(
        "@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .\n"
        "<https://example.org/record> "
        "<https://example.org/value> "
        '"2e3"^^xsd:decimal, '
        '"sometimes"^^xsd:boolean .',
        encoding="utf-8",
    )

    with warnings.catch_warnings():
        warnings.filterwarnings(
            "ignore",
            message="Parsing weird boolean.*",
        )
        report = inspect_ontology(source)

    values = sorted(issue.lexical_value for issue in report.issues)

    assert values == ["2e3", "sometimes"]
