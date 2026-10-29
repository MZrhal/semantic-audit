"""Load local or HTTP(S) RDF documents without resolving ``owl:imports``."""

from pathlib import Path
from tempfile import NamedTemporaryFile
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import Request, urlopen

from rdflib import Graph
from rdflib.util import guess_format

from semantic_audit.errors import OntologyLoadError, OntologyParseError

# Avoid unbounded downloads, especially when analysing third-party URLs.
MAX_DOWNLOAD_BYTES = 100 * 1024 * 1024
DOWNLOAD_TIMEOUT_SECONDS = 30
CHUNK_SIZE = 64 * 1024
ACCEPT = (
    "text/turtle, application/rdf+xml;q=0.9, application/ld+json;q=0.8, "
    "application/n-triples;q=0.7, application/octet-stream;q=0.5"
)
CONTENT_TYPES = {
    "text/turtle": "turtle",
    "application/x-turtle": "turtle",
    "application/rdf+xml": "xml",
    "application/xml": "xml",
    "text/xml": "xml",
    "application/ld+json": "json-ld",
    "application/n-triples": "nt",
    "application/n-quads": "nquads",
    "application/trig": "trig",
    "text/n3": "n3",
}


def is_remote_url(source: str | Path) -> bool:
    """Return whether the input is an HTTP(S) URL (not a local path)."""
    return urlsplit(str(source)).scheme.lower() in {"http", "https"}


def _read_remote(url: str, rdf_format: str | None) -> Graph:
    """Download a bounded RDF response and parse it with the remote URL as base IRI."""
    parsed = urlsplit(url)
    if not parsed.hostname or parsed.username or parsed.password:
        raise OntologyLoadError("URL RDF invalide : nom d'hôte manquant ou identifiants interdits.")

    request = Request(
        url,
        headers={"Accept": ACCEPT, "Accept-Encoding": "identity", "User-Agent": "SemanticAudit"},
    )
    try:
        with urlopen(request, timeout=DOWNLOAD_TIMEOUT_SECONDS) as response:
            final_url = response.geturl()
            if not is_remote_url(final_url):
                raise OntologyLoadError("Redirection vers un protocole non HTTP(S) interdite.")
            content_type = response.headers.get("Content-Type", "").split(";", 1)[0].lower().strip()
            if content_type == "text/html" and rdf_format is None:
                raise OntologyLoadError(
                    "L'URL retourne du HTML, pas un document RDF. "
                    "Utilise l'URL du fichier brut (raw) ou un endpoint RDF."
                )
            syntax = (
                rdf_format
                or CONTENT_TYPES.get(content_type)
                or guess_format(urlsplit(final_url).path)
                or guess_format(parsed.path)
            )
            if syntax is None:
                raise OntologyLoadError(
                    "Format RDF distant inconnu. Indique --rdf-format turtle, xml ou json-ld."
                )
            length = response.headers.get("Content-Length")
            if length is not None and length.isdecimal() and int(length) > MAX_DOWNLOAD_BYTES:
                raise OntologyLoadError("Le document distant dépasse la limite de 100 Mo.")

            with NamedTemporaryFile(mode="w+b", suffix=".rdf") as download:
                total = 0
                while chunk := response.read(CHUNK_SIZE):
                    total += len(chunk)
                    if total > MAX_DOWNLOAD_BYTES:
                        raise OntologyLoadError("Le document distant dépasse la limite de 100 Mo.")
                    download.write(chunk)
                download.seek(0)
                graph = Graph()
                try:
                    # publicID preserves relative-IRI resolution against the remote URL.
                    graph.parse(file=download, format=syntax, publicID=final_url)
                except Exception as exc:
                    raise OntologyParseError(
                        f"Impossible d'analyser '{url}' avec le format '{syntax}' : {exc}"
                    ) from exc
                return graph
    except HTTPError as exc:
        raise OntologyLoadError(f"Échec HTTP {exc.code} pour '{url}'.") from exc
    except (URLError, TimeoutError) as exc:
        raise OntologyLoadError(f"Impossible de télécharger '{url}' : {exc}") from exc


def load_graph(path: str | Path, rdf_format: str | None = None) -> Graph:
    """Load an RDF document from a local file or an HTTP(S) URL.

    URLs are fetched temporarily; nothing is saved persistently. The parser
    does not resolve ``owl:imports`` automatically. JSON-LD contexts and XML
    parser features can independently access external resources: only inspect
    sources you trust. Do not expose arbitrary URL fetching in a server without
    additional SSRF protections.
    """
    source_text = str(path)
    if is_remote_url(source_text):
        return _read_remote(source_text, rdf_format)
    if "://" in source_text:
        raise OntologyLoadError("Seules les URL HTTP(S) sont prises en charge.")

    source = Path(path).expanduser()
    if not source.is_file():
        raise OntologyLoadError(f"Fichier introuvable : {source}")

    syntax = rdf_format or guess_format(source.name)
    if syntax is None:
        raise OntologyLoadError(
            f"Format RDF inconnu pour '{source.name}'. Indique --rdf-format turtle, xml ou json-ld."
        )

    graph = Graph()
    try:
        graph.parse(source=source.resolve().as_uri(), format=syntax)
    except Exception as exc:
        raise OntologyParseError(
            f"Impossible de lire '{source}' avec le format '{syntax}' : {exc}"
        ) from exc
    return graph
