"""Immutable, JSON-serializable public report models."""

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class LocalizedText:
    value: str
    language: str | None = None
    datatype: str | None = None


@dataclass(frozen=True, slots=True)
class ClassInfo:
    iri: str
    labels: tuple[LocalizedText, ...]
    comments: tuple[LocalizedText, ...]
    direct_superclasses: tuple[str, ...]
    direct_named_individual_count: int


@dataclass(frozen=True, slots=True)
class PropertyInfo:
    iri: str
    declared_types: tuple[str, ...]
    labels: tuple[LocalizedText, ...]
    comments: tuple[LocalizedText, ...]
    domains: tuple[str, ...]
    ranges: tuple[str, ...]
    direct_superproperties: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class IndividualInfo:
    iri: str
    labels: tuple[LocalizedText, ...]
    direct_classes: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class Statistics:
    triples: int
    declared_classes: int
    declared_properties: int
    named_individuals: int
    blank_nodes: int


@dataclass(frozen=True, slots=True)
class Diagnostic:
    code: str
    severity: str
    subject: str
    predicate: str
    datatype: str
    lexical_value: str
    message: str


@dataclass(frozen=True, slots=True)
class OntologyReport:
    source: str
    statistics: Statistics
    classes: tuple[ClassInfo, ...]
    properties: tuple[PropertyInfo, ...]
    individuals: tuple[IndividualInfo, ...]
    issues: tuple[Diagnostic, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        """Convert the report to a deterministic JSON-friendly object."""
        return {"schema_version": "1.1", **asdict(self)}
