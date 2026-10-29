"""Public errors for loading RDF files."""


class OntologyError(Exception):
    """Base exception for expected SemanticAudit failures."""


class OntologyLoadError(OntologyError):
    """The input file is absent, inaccessible or its format cannot be inferred."""


class OntologyParseError(OntologyError):
    """The RDF syntax is invalid or the RDF parser could not read the input."""
