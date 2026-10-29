Architecture — SemanticAudit v0.2.0
Overview
SemanticAudit v0.2.0 is a Python command-line tool that inspects explicitly declared RDF/OWL vocabulary elements and directly typed named individuals. It produces a structured, versioned JSON report. The current implementation does not perform SHACL validation, OWL/RDFS reasoning, or automatic ontology import resolution.
Module responsibilities
Module	Responsibility
loader.py	Loads a local RDF document into an rdflib.Graph; handles input and RDF parsing errors.
inspector.py	Analyzes an existing rdflib.Graph and computes an inventory without writing to disk.
models.py	Defines immutable, typed report objects and the JSON report schema.
cli.py	Parses command-line arguments, invokes the inspection workflow, and prints or writes JSON output.
errors.py	Defines application-specific exceptions.
__main__.py	Enables execution with python -m semantic_audit.


Execution flow
Local RDF/OWL file
        |
        v
loader.load_graph()
        |
        v
    rdflib.Graph
        |
        v
inspector.inspect_graph()
        |
        v
 models.OntologyReport
        |
        v
      cli.main()
        |
        +----> Standard output (JSON)
        |
        +----> JSON report file
The inspector can also be called directly with an in-memory rdflib.Graph, which keeps the analysis logic independent of file I/O and makes it easier to test.
Inventory semantics
The following rules define what SemanticAudit v0.2.0 reports. They are operational conventions, not a complete implementation of OWL semantics.
1. Declared class: an IRI explicitly associated with rdf:type owl:Class or rdf:type rdfs:Class. A class declared in both ways is counted only once.
2. Declared property: an IRI explicitly typed with any property category or characteristic listed in PROPERTY_KINDS (for example, rdf:Property, owl:ObjectProperty, or owl:TransitiveProperty). Merely using an IRI as a predicate does not make it a declared property in this inventory.
3. Named individual: an IRI explicitly typed as an already declared class or as owl:NamedIndividual, excluding identified classes, properties, and owl:Ontology resources. Each IRI is counted once even if it has multiple types. This is an intentional inventory rule, not exhaustive OWL individual discovery.
4. Direct class membership: only explicit rdf:type assertions to declared classes are counted. The inspector does not infer membership in superclasses.
5. Hierarchy: rdfs:subClassOf and rdfs:subPropertyOf references are recorded when their objects are named IRIs. These relations are not evaluated by a reasoner.
6. Annotations: literal rdfs:label and rdfs:comment values retain their language tags and datatypes. Report collections are sorted to ensure deterministic output.
7. Blank nodes: distinct blank nodes occurring anywhere in the graph are counted separately. They are not included in the named-individual inventory.
8. Imports: owl:imports statements are not automatically followed; the report covers only the graph loaded from the supplied file.
Reports and interoperability
Reports use the versioned schema field schema_version: "1.0" and include source information, statistics, classes, properties, and named individuals. Stable ordering makes report diffs and regression checks easier to interpret.

Supported input serialization formats include Turtle, RDF/XML, and JSON-LD. For file extensions that cannot be inferred, the CLI supports an explicit --rdf-format option.
Testing and quality
Automated tests cover file loading, error handling, inventory rules, JSON serialization, and command-line behavior. The tests intentionally distinguish explicit assertions from inferred statements.
uv run python -m pytest -v
uv run python -m ruff check .
uv run python -m ruff format --check .
On Windows systems that block the generated semantic-audit.exe launcher, the application can be run without bypassing system security controls:
uv run python -m semantic_audit inspect examples/organization.ttl
Planned extensions
- SHACL constraint validation and sh:ValidationReport output.
- SPARQL competency questions with expected-result and regression checks.
- Optional RDFS/OWL 2 RL reasoning as a separate graph-enrichment step.
- Quality indicators and a Streamlit dashboard.
Current limitations
SemanticAudit v0.2.0 is not an OWL reasoner, a consistency checker, or a SHACL validator. Its counts reflect explicit declarations under the conventions above; they should not be interpreted as a complete semantic classification of an ontology.