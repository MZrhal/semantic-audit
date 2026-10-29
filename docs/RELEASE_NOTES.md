Release Notes — SemanticAudit v0.2.0
Overview
Version 0.2.0 replaces the initial proof of concept with a modular, testable Ontology Inspector. The release focuses on reliable RDF loading, explicit RDF/OWL inventory, and reproducible JSON reports.
Improvements over v0.1
Architecture
- Separated RDF loading, ontology inspection, report models, command-line handling, and application errors into dedicated modules.
- Introduced typed, immutable Python report models.
- Added a versioned JSON report format (schema_version: "1.0").
Ontology inspection
- Added inventories of explicitly declared classes, properties, and named individuals.
- Preserved multilingual labels, comments, direct superclass relationships, property domains, ranges, and direct superproperties.
- Recognized multiple property declarations or characteristics on the same IRI and avoided duplicate entity counts.
- Counted distinct blank nodes separately from named individuals.
- Documented and tested direct, explicit class membership counts without implicit reasoning.
File loading and CLI
- Supported RDF/XML and JSON-LD in addition to Turtle.
- Added --rdf-format for input files with unrecognized extensions.
- Added an explicit inspect subcommand while preserving the original command syntax.
- Added JSON export to a file with protection against overwriting the input document.
- Improved error messages for missing files, malformed RDF, and other invalid input.
- Added the python -m semantic_audit entry point.
Testing and project maintenance
- Added automated tests covering RDF loading, ontology inventory rules, blank nodes, serialization, and CLI behavior.
- Added GitHub Actions continuous integration configuration.
- Added project documentation and an MIT license.
Usage
uv sync
uv run python -m pytest -v
uv run python -m semantic_audit --version
uv run python -m semantic_audit inspect examples/organization.ttl
uv run python -m semantic_audit inspect examples/organization.ttl --output reports/organization.json
Scope and known limitations
This release does not yet implement SHACL constraint validation, OWL/RDFS reasoning, ontology consistency checking, or automatic owl:imports resolution. The inspector reports explicitly declared information according to its documented inventory rules.

See [ARCHITECTURE.md](ARCHITECTURE.md) for implementation details and precise counting rules.
