"""Read an RDF document from disk without fetching OWL imports."""

from pathlib import Path

from rdflib import Graph
from rdflib.util import guess_format

from semantic_audit.errors import OntologyLoadError, OntologyParseError


def load_graph(path: str | Path, rdf_format: str | None = None) -> Graph:
    """Load an RDF file into an in-memory graph.

    Args:
        path: Local RDF document.
        rdf_format: Explicit RDFLib parser name (e.g. ``turtle``, ``xml``,
            ``json-ld``), useful when the extension is unknown.

    The parser does not follow ``owl:imports`` automatically. RDF document
    formats using external references (e.g. JSON-LD contexts) may still
    contact outside resources; only use trusted documents.
    """
    source = Path(path).expanduser()
    if not source.is_file():
        raise OntologyLoadError(f"Fichier introuvable : {source}")

    syntax = rdf_format or guess_format(source.name)
    if syntax is None:
        raise OntologyLoadError(
            f"Format RDF inconnu pour '{source.name}'. "
            "Indique --rdf-format turtle, xml ou json-ld."
        )

    graph = Graph()
    try:
        graph.parse(source=source.resolve().as_uri(), format=syntax)
    except Exception as exc:
        # RDFLib parsers raise several unrelated exception classes depending
        # on the format. Translate only at this I/O boundary.
        raise OntologyParseError(
            f"Impossible de lire '{source}' avec le format '{syntax}' : {exc}"
        ) from exc
    return graph
