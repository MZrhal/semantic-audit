"""User-facing command line interface."""

import argparse
import json
import sys
from collections.abc import Sequence
from pathlib import Path

from semantic_audit import __version__
from semantic_audit.errors import OntologyError
from semantic_audit.inspector import inspect_ontology


def create_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="semantic-audit", description="Inspection RDF/OWL sans inférence (milestone 1)."
    )
    parser.add_argument("--version", action="version", version=f"SemanticAudit {__version__}")
    subcommands = parser.add_subparsers(dest="command", required=True)
    inspect = subcommands.add_parser("inspect", help="Inspecter un document RDF local")
    inspect.add_argument("path", type=Path, help="Chemin vers le document RDF/OWL")
    inspect.add_argument(
        "--rdf-format", help="Format d'entrée RDFLib (ex. turtle, xml, json-ld)"
    )
    inspect.add_argument(
        "--output", type=Path, help="Écrire le JSON dans ce fichier au lieu de stdout"
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    arguments = list(argv if argv is not None else sys.argv[1:])
    # Backward compatibility with the original v0.1 CLI:
    #   semantic-audit examples/organization.ttl
    if (
        arguments
        and arguments[0] not in {"inspect", "-h", "--help", "--version"}
        and not arguments[0].startswith("-")
    ):
        arguments.insert(0, "inspect")

    args = create_parser().parse_args(arguments)
    try:
        report = inspect_ontology(args.path, rdf_format=args.rdf_format)
        serialized = json.dumps(report.to_dict(), ensure_ascii=False, indent=2) + "\n"
        if args.output is not None:
            if args.output.resolve() == args.path.resolve():
                print(
                    "Erreur : le rapport ne doit pas écraser le fichier RDF source.",
                    file=sys.stderr,
                )
                return 1
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(serialized, encoding="utf-8")
            print(f"Rapport enregistré : {args.output}", file=sys.stderr)
        else:
            sys.stdout.write(serialized)
    except (OntologyError, OSError) as exc:
        print(f"Erreur : {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
