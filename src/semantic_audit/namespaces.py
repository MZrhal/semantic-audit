"""Summarize RDF namespaces and user-defined internal IRI ownership."""

from collections import defaultdict
from collections.abc import Iterable

from rdflib import Graph, Literal, URIRef
from rdflib.namespace import split_uri

from semantic_audit.models import NamespaceInfo


def analyze_namespaces(
    graph: Graph,
    declared_classes: set[URIRef],
    declared_properties: set[URIRef],
    named_individuals: set[URIRef],
    internal_prefixes: Iterable[str] = (),
) -> tuple[NamespaceInfo, ...]:
    """Summarize unique IRIs by namespace.

    Internal ownership is based on explicitly configured IRI prefixes.
    Without prefixes, namespace ownership remains unknown.
    """
    prefixes = tuple(internal_prefixes)

    if any(not prefix for prefix in prefixes):
        raise ValueError("Internal IRI prefixes must not be empty.")

    iris: set[URIRef] = set()

    # Collect IRIs used as subjects, predicates and objects.
    # Include datatypes of RDF literals.
    for subject, predicate, obj in graph:
        for node in (subject, predicate, obj):
            if isinstance(node, URIRef):
                iris.add(node)

        if isinstance(obj, Literal) and obj.datatype is not None:
            iris.add(obj.datatype)

    # Group by RDF namespace, independently of declared prefix labels.
    grouped: dict[str, set[URIRef]] = defaultdict(set)

    for iri in iris:
        try:
            namespace, _ = split_uri(iri)
        except ValueError:
            # Some IRIs have no separable local name.
            continue

        grouped[str(namespace)].add(iri)

    rows = []

    for namespace, members in sorted(grouped.items()):
        internal = {
            iri for iri in members if any(str(iri).startswith(prefix) for prefix in prefixes)
        }

        if not prefixes:
            classification = "unknown"
        elif len(internal) == len(members):
            classification = "internal"
        elif not internal:
            classification = "external"
        else:
            classification = "mixed"

        rows.append(
            NamespaceInfo(
                namespace=namespace,
                classification=classification,
                iri_count=len(members),
                internal_iri_count=(len(internal) if prefixes else None),
                declared_classes=len(members & declared_classes),
                internal_declared_classes=(len(internal & declared_classes) if prefixes else None),
                declared_properties=len(members & declared_properties),
                internal_declared_properties=(
                    len(internal & declared_properties) if prefixes else None
                ),
                named_individuals=len(members & named_individuals),
                internal_named_individuals=(
                    len(internal & named_individuals) if prefixes else None
                ),
            )
        )

    return tuple(rows)
