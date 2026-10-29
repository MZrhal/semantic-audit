"""Inspect only *explicitly declared* RDF/OWL vocabulary and individuals.

No OWL/RDFS inference, SHACL validation, or imports resolution is performed.
All counts of individuals refer to distinct named URI nodes (not blank nodes).
"""

from collections import defaultdict
from pathlib import Path

from rdflib import OWL, RDF, RDFS, BNode, Graph, Literal, URIRef

from semantic_audit.diagnostics import inspect_literals
from semantic_audit.loader import is_remote_url, load_graph
from semantic_audit.models import (
    ClassInfo,
    IndividualInfo,
    LocalizedText,
    OntologyReport,
    PropertyInfo,
    Statistics,
)

# Including characteristic declarations means e.g. an owl:TransitiveProperty
# is recognized as a property even if no owl:ObjectProperty triple is present.
PROPERTY_KINDS: dict[URIRef, str] = {
    RDF.Property: "rdf:Property",
    OWL.ObjectProperty: "owl:ObjectProperty",
    OWL.DatatypeProperty: "owl:DatatypeProperty",
    OWL.AnnotationProperty: "owl:AnnotationProperty",
    OWL.FunctionalProperty: "owl:FunctionalProperty",
    OWL.InverseFunctionalProperty: "owl:InverseFunctionalProperty",
    OWL.TransitiveProperty: "owl:TransitiveProperty",
    OWL.SymmetricProperty: "owl:SymmetricProperty",
    OWL.AsymmetricProperty: "owl:AsymmetricProperty",
    OWL.ReflexiveProperty: "owl:ReflexiveProperty",
    OWL.IrreflexiveProperty: "owl:IrreflexiveProperty",
}


def _named_subjects(graph: Graph, rdf_types: set[URIRef]) -> set[URIRef]:
    return {
        subject
        for rdf_type in rdf_types
        for subject in graph.subjects(RDF.type, rdf_type)
        if isinstance(subject, URIRef)
    }


def _uris(graph: Graph, subject: URIRef, predicate: URIRef) -> tuple[str, ...]:
    values = {str(node) for node in graph.objects(subject, predicate) if isinstance(node, URIRef)}
    return tuple(sorted(values))


def _texts(graph: Graph, subject: URIRef, predicate: URIRef) -> tuple[LocalizedText, ...]:
    entries = {
        LocalizedText(
            value=str(node),
            language=node.language,
            datatype=str(node.datatype) if node.datatype else None,
        )
        for node in graph.objects(subject, predicate)
        if isinstance(node, Literal)
    }
    return tuple(sorted(entries, key=lambda e: (e.language or "", e.value, e.datatype or "")))


def inspect_graph(graph: Graph, source: str = "<in-memory>") -> OntologyReport:
    """Inspect an already parsed RDFLib graph.

    A named individual is a URI resource explicitly typed as an enumerated
    class or owl:NamedIndividual, excluding known schema nodes. This is a
    deliberate operational definition, not complete OWL individual discovery.
    """
    declared_classes = _named_subjects(graph, {OWL.Class, RDFS.Class})
    declared_properties = _named_subjects(graph, set(PROPERTY_KINDS))
    ontology_nodes = _named_subjects(graph, {OWL.Ontology})
    schema_nodes = declared_classes | declared_properties | ontology_nodes

    direct_class_members: dict[URIRef, set[URIRef]] = defaultdict(set)
    individual_class_types: dict[URIRef, set[URIRef]] = defaultdict(set)
    for individual, rdf_type in graph.subject_objects(RDF.type):
        if (
            isinstance(individual, URIRef)
            and individual not in schema_nodes
            and rdf_type in declared_classes
        ):
            direct_class_members[rdf_type].add(individual)
            individual_class_types[individual].add(rdf_type)

    named_individuals = set(individual_class_types) | (
        _named_subjects(graph, {OWL.NamedIndividual}) - schema_nodes
    )

    classes = tuple(
        ClassInfo(
            iri=str(node),
            labels=_texts(graph, node, RDFS.label),
            comments=_texts(graph, node, RDFS.comment),
            direct_superclasses=_uris(graph, node, RDFS.subClassOf),
            direct_named_individual_count=len(direct_class_members[node]),
        )
        for node in sorted(declared_classes, key=str)
    )

    properties = tuple(
        PropertyInfo(
            iri=str(node),
            declared_types=tuple(
                sorted(
                    label
                    for rdf_type, label in PROPERTY_KINDS.items()
                    if (node, RDF.type, rdf_type) in graph
                )
            ),
            labels=_texts(graph, node, RDFS.label),
            comments=_texts(graph, node, RDFS.comment),
            domains=_uris(graph, node, RDFS.domain),
            ranges=_uris(graph, node, RDFS.range),
            direct_superproperties=_uris(graph, node, RDFS.subPropertyOf),
        )
        for node in sorted(declared_properties, key=str)
    )

    individuals = tuple(
        IndividualInfo(
            iri=str(node),
            labels=_texts(graph, node, RDFS.label),
            direct_classes=tuple(sorted(str(c) for c in individual_class_types[node])),
        )
        for node in sorted(named_individuals, key=str)
    )

    blank_nodes = {node for triple in graph for node in triple if isinstance(node, BNode)}

    return OntologyReport(
        source=source,
        statistics=Statistics(
            triples=len(graph),
            declared_classes=len(classes),
            declared_properties=len(properties),
            named_individuals=len(individuals),
            blank_nodes=len(blank_nodes),
        ),
        classes=classes,
        properties=properties,
        individuals=individuals,
        issues=inspect_literals(graph),
    )


def inspect_ontology(path: str | Path, rdf_format: str | None = None) -> OntologyReport:
    """Load and inspect a local RDF file; return a structured report."""
    graph = load_graph(path, rdf_format=rdf_format)
    source = str(path) if is_remote_url(path) else str(Path(path).expanduser())
    return inspect_graph(graph, source=source)
