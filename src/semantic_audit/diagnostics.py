"""Identify invalid lexical forms in a conservative set of XSD datatypes.

This is a lightweight diagnostic pass, not XML Schema or SHACL validation.
"""

import re

from rdflib import XSD, BNode, Graph, Literal

from semantic_audit.models import Diagnostic

_CHECKED_DATATYPES = {
    XSD.boolean,
    XSD.integer,
    XSD.decimal,
    XSD.date,
    XSD.time,
    XSD.dateTime,
}

_INTEGER = re.compile(r"[+-]?[0-9]+\Z")
_DECIMAL = re.compile(r"[+-]?(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+)\Z")
_BOOLEAN = {"true", "false", "1", "0"}


def _has_invalid_lexical_form(literal: Literal) -> bool:
    """Check recognized datatypes without changing the RDF literal."""
    datatype = literal.datatype

    if datatype not in _CHECKED_DATATYPES:
        return False

    lexical = str(literal)

    if datatype == XSD.boolean and lexical not in _BOOLEAN:
        return True

    if datatype == XSD.integer and _INTEGER.fullmatch(lexical) is None:
        return True

    if datatype == XSD.decimal and _DECIMAL.fullmatch(lexical) is None:
        return True

    # RDFLib leaves value=None when conversion fails
    # for the supported datatypes.
    return literal.value is None


def inspect_literals(graph: Graph) -> tuple[Diagnostic, ...]:
    """Report invalid typed literals with their RDF context."""
    issues = []

    for subject, predicate, obj in graph:
        if not isinstance(obj, Literal):
            continue

        if not _has_invalid_lexical_form(obj):
            continue

        subject_id = f"_:{subject}" if isinstance(subject, BNode) else str(subject)

        issues.append(
            Diagnostic(
                code="INVALID_TYPED_LITERAL",
                severity="warning",
                subject=subject_id,
                predicate=str(predicate),
                datatype=str(obj.datatype),
                lexical_value=str(obj),
                message=("Invalid or unsupported lexical form for the declared XSD datatype."),
            )
        )

    return tuple(
        sorted(
            issues,
            key=lambda issue: (
                issue.subject,
                issue.predicate,
                issue.datatype,
                issue.lexical_value,
            ),
        )
    )
