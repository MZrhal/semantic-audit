"""Semantics-focused tests: only explicit declarations are counted."""

import json

from rdflib import OWL, RDF, RDFS, BNode, Graph, Literal, Namespace

from semantic_audit.inspector import inspect_graph, inspect_ontology

EX = Namespace("https://example.org/test/")


def test_example_inventory(example_path):
    report = inspect_ontology(example_path)
    assert report.source.endswith("organization.ttl")
    assert report.statistics.declared_classes == 5
    assert report.statistics.declared_properties == 5
    assert report.statistics.named_individuals == 5
    assert report.statistics.blank_nodes == 0
    assert len(report.classes) == 5
    assert len(report.properties) == 5
    assert len(report.individuals) == 5


def test_subclass_does_not_trigger_inference(example_path):
    report = inspect_ontology(example_path)
    classes = {cls.iri: cls for cls in report.classes}
    person = classes[str(Namespace("https://example.org/organization/").Person)]
    employee = classes[str(Namespace("https://example.org/organization/").Employee)]
    assert person.direct_named_individual_count == 0
    assert employee.direct_named_individual_count == 2
    assert person.iri in employee.direct_superclasses


def test_labels_preserve_language_and_sort_order():
    graph = Graph()
    graph.add((EX.Person, RDF.type, OWL.Class))
    graph.add((EX.Person, RDFS.label, Literal("Personne", lang="fr")))
    graph.add((EX.Person, RDFS.label, Literal("Person", lang="en")))
    labels = inspect_graph(graph).classes[0].labels
    assert [(item.value, item.language) for item in labels] == [
        ("Person", "en"), ("Personne", "fr")
    ]


def test_declared_class_deduplicated_across_owl_and_rdfs():
    graph = Graph()
    graph.add((EX.Person, RDF.type, OWL.Class))
    graph.add((EX.Person, RDF.type, RDFS.Class))
    report = inspect_graph(graph)
    assert report.statistics.declared_classes == 1


def test_property_declarations_and_multiple_characteristics():
    graph = Graph()
    graph.add((EX.knows, RDF.type, OWL.ObjectProperty))
    graph.add((EX.knows, RDF.type, OWL.SymmetricProperty))
    graph.add((EX.knows, RDFS.domain, EX.Person))
    graph.add((EX.knows, RDFS.range, EX.Person))
    graph.add((EX.knows, RDFS.subPropertyOf, EX.relatedTo))
    prop = inspect_graph(graph).properties[0]
    assert prop.iri == str(EX.knows)
    assert prop.declared_types == ("owl:ObjectProperty", "owl:SymmetricProperty")
    assert prop.domains == (str(EX.Person),)
    assert prop.ranges == (str(EX.Person),)
    assert prop.direct_superproperties == (str(EX.relatedTo),)


def test_named_individuals_are_unique_and_schema_nodes_excluded():
    graph = Graph()
    for cls in (EX.Person, EX.Employee):
        graph.add((cls, RDF.type, OWL.Class))
    graph.add((EX.alice, RDF.type, EX.Person))
    graph.add((EX.alice, RDF.type, EX.Employee))
    graph.add((EX.alice, RDF.type, OWL.NamedIndividual))
    # A schema class is not an individual for this inspector, even if typed as another class.
    graph.add((EX.Employee, RDF.type, EX.Person))
    report = inspect_graph(graph)
    assert report.statistics.named_individuals == 1
    assert report.individuals[0].direct_classes == (str(EX.Employee), str(EX.Person))
    assert {c.iri: c.direct_named_individual_count for c in report.classes} == {
        str(EX.Person): 1,
        str(EX.Employee): 1,
    }


def test_named_individual_without_class_is_included():
    graph = Graph()
    graph.add((EX.orphan, RDF.type, OWL.NamedIndividual))
    report = inspect_graph(graph)
    assert report.statistics.named_individuals == 1
    assert report.individuals[0].direct_classes == ()


def test_blank_node_is_counted_but_not_named_individual():
    graph = Graph()
    node = BNode()
    graph.add((EX.Person, RDF.type, OWL.Class))
    graph.add((node, RDF.type, EX.Person))
    report = inspect_graph(graph)
    assert report.statistics.blank_nodes == 1
    assert report.statistics.named_individuals == 0
    assert report.classes[0].direct_named_individual_count == 0


def test_untyped_use_of_property_does_not_make_property_declared():
    graph = Graph()
    graph.add((EX.alice, EX.hasSkill, EX.python))
    report = inspect_graph(graph)
    assert report.statistics.declared_properties == 0


def test_undeclared_type_does_not_count_as_named_individual():
    graph = Graph()
    graph.add((EX.alice, RDF.type, EX.Person))
    report = inspect_graph(graph)
    assert report.statistics.named_individuals == 0


def test_no_triples_produces_zero_statistics():
    report = inspect_graph(Graph())
    assert report.statistics.triples == 0
    assert report.classes == ()
    assert report.properties == ()
    assert report.individuals == ()


def test_report_is_json_serializable_and_versioned(example_path):
    report = inspect_ontology(example_path)
    payload = json.loads(json.dumps(report.to_dict(), ensure_ascii=False))
    assert payload["schema_version"] == "1.0"
    assert payload["statistics"]["declared_classes"] == 5
    assert any(
        label["language"] == "fr"
        for item in payload["classes"]
        for label in item["labels"]
    )


def test_report_order_is_stable():
    graph = Graph()
    graph.add((EX.Z, RDF.type, OWL.Class))
    graph.add((EX.A, RDF.type, OWL.Class))
    assert [row.iri for row in inspect_graph(graph).classes] == [str(EX.A), str(EX.Z)]
