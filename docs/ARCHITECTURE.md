
# SemanticAudit — Software Architecture

**Development branch:** `feature/v0.3.0`  
**Package version:** `0.3.0` 
**JSON report schema:** `1.2`  
**Language:** Python 3.13  
**Primary RDF library:** RDFLib

## 1. Overview

SemanticAudit is a modular Python command-line application for inspecting RDF/OWL ontologies and producing structured semantic quality reports.

The architecture separates document acquisition, RDF parsing, ontology inspection, diagnostics, namespace analysis, data modeling, and command-line interaction.

The design emphasizes:

- Explicit RDF/OWL inspection rules
- Separation of responsibilities
- Reproducible JSON reports
- Independent, testable analysis modules
- Compatibility with local and remote RDF sources
- Incremental extensibility toward semantic quality auditing

SemanticAudit is not currently a reasoner, SHACL validator, or ontology consistency checker.

## 2. High-Level Architecture

```text
                  +----------------------+
                  |       CLI            |
                  |       cli.py         |
                  +----------+-----------+
                             |
                             v
                  +----------------------+
                  |       Loader         |
                  |       loader.py      |
                  +----------+-----------+
                             |
                             v
                  +----------------------+
                  |     RDFLib Graph     |
                  +----------+-----------+
                             |
                             v
                  +----------------------+
                  |      Inspector       |
                  |     inspector.py     |
                  +----------+-----------+
                             |
               +-------------+-------------+
               |                           |
               v                           v
    +---------------------+     +---------------------+
    |   RDF Diagnostics   |     |  Namespace Analysis |
    |    diagnostics.py   |     |    namespaces.py    |
    +----------+----------+     +----------+----------+
               |                           |
               +-------------+-------------+
                             |
                             v
                  +----------------------+
                  |    Report Models     |
                  |      models.py       |
                  +----------+-----------+
                             |
                             v
                  +----------------------+
                  |    JSON Report       |
                  |  stdout / --output   |
                  +----------------------+
```

The inspector coordinates the analysis modules and produces an immutable report object.

The CLI serializes this report to JSON.

The analysis modules do not write reports directly to disk.

## 3. Module Responsibilities

| Module | Responsibility |
|---|---|
| `cli.py` | Parse CLI arguments, execute inspection, write JSON |
| `loader.py` | Load local or HTTP(S) RDF documents |
| `inspector.py` | Build the explicit ontology inventory and coordinate analysis |
| `diagnostics.py` | Detect invalid lexical forms of selected XSD literals |
| `namespaces.py` | Analyze namespace usage and configured internal vocabulary prefixes |
| `models.py` | Define immutable, typed report structures |
| `errors.py` | Define application-specific exceptions |
| `__main__.py` | Enable execution with `python -m semantic_audit` |
| `__init__.py` | Expose the public inspection API and package version |

The modular design allows additional analysis components to be introduced without replacing the entire inspection pipeline.

## 4. Input Handling

### 4.1 Supported Sources

SemanticAudit accepts:

1. Local RDF files
2. HTTP(S) URLs pointing to RDF documents
3. In-memory RDFLib graphs through the Python inspection API

The CLI accepts a local path or HTTP(S) URL as the positional input argument.

### 4.2 Local Files

Local files are loaded using RDFLib.

When possible, the RDF serialization format is identified through the file extension.

An explicit format override is available:

```bash
uv run python -m semantic_audit inspect ontology.data --rdf-format turtle
```

Missing files, unsupported input sources, and parsing errors are reported through application-specific exceptions.

### 4.3 Remote Documents

Remote ontology retrieval is implemented in `loader.py`.

The current implementation:

- Accepts HTTP(S) URLs
- Follows HTTP redirects
- Uses HTTP content types and file extensions for format detection
- Supports an explicit RDF format override
- Downloads into a temporary file
- Enforces a 100 MiB maximum download size
- Uses a 30-second network socket timeout
- Preserves the original input URL in the final report

The timeout is a socket-operation timeout, not a guaranteed maximum duration for the entire request and parsing process.

The temporary downloaded document is removed when the loading operation completes.

### 4.4 Security Considerations

Remote inspection is designed for local CLI use with trusted sources.

The current implementation is not a complete security boundary for arbitrary remote documents.

Important risks include:

- Server-side request forgery (SSRF) in hosted deployments
- HTTP redirects to unexpected destinations
- Access to local or private networks
- Large or resource-intensive RDF inputs
- External JSON-LD contexts
- External resources accessed by format-specific parsers

Before exposing remote retrieval in a hosted API, additional safeguards are required, including network egress restrictions, DNS/IP validation, redirect validation, and resource limits.

## 5. Literal Normalization

RDFLib can normalize certain typed literals during parsing.

For example, a lexical representation that does not conform to the declared XML Schema datatype may be converted into another representation.

Such normalization is undesirable for a diagnostic tool because it can hide the original problematic value.

SemanticAudit therefore temporarily disables RDFLib's global `NORMALIZE_LITERALS` setting while parsing.

The previous setting is restored afterward, including when parsing fails.

A reentrant lock coordinates this operation among SemanticAudit's own loading calls.

### Limitation

`NORMALIZE_LITERALS` is process-global.

The current locking mechanism does not guarantee isolation from unrelated threads that use RDFLib directly.

This design is acceptable for the current local CLI workflow but should be revisited before introducing a concurrent server environment.

## 6. Ontology Inspector

The central inspection implementation is located in `inspector.py`.

The inspector operates on an `rdflib.Graph` and extracts an explicit inventory of ontology elements.

It does not modify the input graph or perform semantic inference.

### 6.1 Declared Classes

A named class is an IRI explicitly associated with either:

```turtle
?class rdf:type owl:Class .
```

or:

```turtle
?class rdf:type rdfs:Class .
```

A class declared using both forms is counted once.

Classes used only as objects of `rdf:type` without an explicit class declaration are not automatically included in the declared-class inventory.

### 6.2 Declared Properties

A declared property is an IRI explicitly typed using one of the property kinds recognized by the inspector.

Recognized types include:

- `rdf:Property`
- `owl:ObjectProperty`
- `owl:DatatypeProperty`
- `owl:AnnotationProperty`
- `owl:FunctionalProperty`
- `owl:InverseFunctionalProperty`
- `owl:TransitiveProperty`
- `owl:SymmetricProperty`
- `owl:AsymmetricProperty`
- `owl:ReflexiveProperty`
- `owl:IrreflexiveProperty`

A property can have multiple recognized types or characteristics.

It is counted once in the global declared-property total.

Merely using an IRI as a predicate does not make it a declared property.

### 6.3 Named Individuals

SemanticAudit uses an operational definition of named individuals.

An individual is included when it:

- Is a named IRI explicitly typed as a declared class; or
- Is explicitly typed as `owl:NamedIndividual`

Known schema resources are excluded, including identified classes, properties, and ontology resources.

The inspector does not attempt complete OWL individual discovery.

### 6.4 Class Membership

Only direct and explicit class membership is considered.

Example:

```turtle
ex:Employee rdfs:subClassOf ex:Person .
ex:alice rdf:type ex:Employee .
```

Without reasoning, Alice is counted as a direct instance of `ex:Employee`, not as a direct instance of `ex:Person`.

No inferred superclass membership is added.

### 6.5 Hierarchical Relationships

The inspector extracts named direct relationships using:

- `rdfs:subClassOf`
- `rdfs:subPropertyOf`

The inspector records these relationships without computing their transitive closure.

Anonymous OWL class expressions are not fully interpreted.

### 6.6 Annotations

The inspector extracts literal annotations for:

- `rdfs:label`
- `rdfs:comment`

Literal values retain:

- Lexical value
- Language tag, when available
- Datatype IRI, when available

Annotations are represented using immutable `LocalizedText` objects.

### 6.7 Blank Nodes

Blank nodes are counted as distinct RDF nodes occurring anywhere in the graph.

They are not included in the named-individual inventory.

The count does not imply that anonymous OWL expressions have been semantically interpreted.

## 7. RDF Diagnostics

The `diagnostics.py` module provides lightweight analysis of typed RDF literals.

Its main public analysis function is:

```python
inspect_literals(graph)
```

The function returns an immutable tuple of `Diagnostic` objects.

### 7.1 Supported Datatypes

The current implementation checks selected XML Schema datatypes:

- `xsd:boolean`
- `xsd:integer`
- `xsd:decimal`
- `xsd:date`
- `xsd:time`
- `xsd:dateTime`

### 7.2 Validation Approach

For supported datatypes, the module examines the literal's lexical representation.

Boolean, integer, and decimal values receive explicit lexical checks.

For supported date/time datatypes, RDFLib's conversion result is used as a lightweight validity signal.

The implementation does not provide exhaustive XML Schema validation.

### 7.3 Diagnostic Model

Each detected issue contains:

| Field | Description |
|---|---|
| `code` | Machine-readable diagnostic identifier |
| `severity` | Diagnostic severity |
| `subject` | Subject of the RDF triple |
| `predicate` | Predicate of the RDF triple |
| `datatype` | Declared datatype IRI |
| `lexical_value` | Original lexical representation |
| `message` | Human-readable diagnostic message |

The current diagnostic code is:

```text
INVALID_TYPED_LITERAL
```

The current severity is:

```text
warning
```

### 7.4 Diagnostic Semantics

Diagnostics are produced after RDF parsing.

A graph can therefore be successfully loaded and inspected even when some literals have invalid lexical representations.

Diagnostics describe observed issues without modifying RDF triples.

The initial implementation does not distinguish all possible XSD validation failures.

Custom datatypes are not validated.

### 7.5 Determinism

Diagnostics are sorted using their context and lexical information.

Blank-node identifiers may differ between independent graph parses, so stable ordering does not guarantee identical identifiers across all executions.

## 8. Namespace Analysis

Namespace analysis is implemented in `namespaces.py`.

Its main analysis function is:

```python
analyze_namespaces(
    graph,
    declared_classes,
    declared_properties,
    named_individuals,
    internal_prefixes=(),
)
```

The module summarizes the namespaces observed in a graph and separates internal vocabulary terms using configurable IRI prefixes.

### 8.1 Namespace Extraction

The module collects IRIs appearing as:

- RDF subjects
- RDF predicates
- RDF objects
- Literal datatypes

Duplicate IRIs are counted once.

Namespace extraction uses RDFLib's `split_uri()` function.

IRI values without a separable local name may be excluded from the namespace summary.

### 8.2 Internal Vocabulary Configuration

SemanticAudit does not assume that the ontology's source URL, ontology IRI, or most frequent namespace necessarily identifies its internal vocabulary.

Instead, the user provides one or more internal IRI prefixes.

CLI example:

```powershell
uv run python -m semantic_audit inspect `
  examples/bot.ttl `
  --internal-prefix "https://w3id.org/bot#"
```

Multiple internal prefixes are supported.

### 8.3 Namespace Classification

Each namespace receives one classification:

| Classification | Condition |
|---|---|
| `internal` | All observed IRIs match at least one internal prefix |
| `external` | No observed IRIs match an internal prefix |
| `mixed` | Both internal and non-internal IRIs are present |
| `unknown` | No internal prefixes have been configured |

Classification is a configured IRI-prefix convention.

It does not establish formal ownership, provenance, or semantic dependency.

### 8.4 Namespace Statistics

Each namespace report contains:

| Field | Description |
|---|---|
| `namespace` | Namespace IRI |
| `classification` | Namespace classification |
| `iri_count` | Number of distinct observed IRIs |
| `internal_iri_count` | Number matching internal prefixes |
| `declared_classes` | Declared classes in the namespace |
| `internal_declared_classes` | Declared classes matching internal prefixes |
| `declared_properties` | Declared properties in the namespace |
| `internal_declared_properties` | Declared properties matching internal prefixes |
| `named_individuals` | Named individuals in the namespace |
| `internal_named_individuals` | Named individuals matching internal prefixes |

When no internal prefixes are configured, the internal counts are `null`.

This differentiates unknown classification from a count of zero.

### 8.5 Shared Namespace Considerations

Some ontologies share a common namespace while using distinct identifier prefixes.

For example:

```text
http://purl.obolibrary.org/obo/FOODON_00000001
http://purl.obolibrary.org/obo/ENVO_00000001
```

Both terms belong to the namespace:

```text
http://purl.obolibrary.org/obo/
```

However, the first identifier begins with `FOODON_`, while the second begins with `ENVO_`.

Using:

```text
http://purl.obolibrary.org/obo/FOODON_
```

as the internal prefix enables SemanticAudit to distinguish the configured FoodOn identifier family within the shared OBO namespace.

A shared namespace can therefore be classified as `mixed`.

### 8.6 Global Counts vs Namespace Counts

Namespace statistics complement the existing global inventory.

They do not replace or modify the global class, property, or individual counts.

For example, a graph may contain explicitly declared terms from vocabularies other than its main vocabulary.

Global inventory counts include all terms satisfying the inspector's declaration rules.

Internal namespace counts include only terms matching configured internal prefixes.

This distinction is essential for interpreting ontology size and vocabulary composition.

### 8.7 Namespace Limitations

The current module:

- Does not prove formal ownership of ontology terms
- Does not resolve imported ontologies
- Does not infer namespace ownership
- Does not verify HTTP accessibility
- Does not validate namespace documentation
- Does not test whether a namespace base URI returns HTTP 200

HTTP dereferenceability is a separate planned development area.

## 9. Data Models and Reporting

Report models are defined in `models.py`.

They use immutable Python dataclasses.

Main models include:

- `LocalizedText`
- `ClassInfo`
- `PropertyInfo`
- `IndividualInfo`
- `Statistics`
- `Diagnostic`
- `NamespaceInfo`
- `OntologyReport`

### 9.1 Report Construction

The inspector constructs an `OntologyReport` containing the inventory and all enabled analysis results.

The report is converted into a JSON-compatible dictionary through:

```python
report.to_dict()
```

The CLI serializes this dictionary using Python's JSON library.

### 9.2 JSON Schema Evolution

The report structure is explicitly versioned.

| Version | Scope |
|---|---|
| `1.0` | Explicit RDF/OWL inventory |
| `1.1` | Structured typed-literal diagnostics |
| `1.2` | Namespace analysis and internal prefix configuration |

Schema version `1.2` includes:

```text
schema_version
source
statistics
classes
properties
individuals
issues
internal_prefixes
namespaces
```

The `schema_version` field describes the JSON report format.

It is independent of the Python package version.

### 9.3 Ordering and Reproducibility

Inventory and diagnostic collections are sorted where defined by the inspection implementation.

The namespace collection is sorted by namespace IRI.

This supports reproducible reports and easier regression comparisons.

However, RDF blank-node identifiers are not guaranteed to remain identical across independent parses.

## 10. CLI Architecture

The CLI is implemented with Python's `argparse`.

The principal command is:

```text
semantic-audit inspect <source>
```

Main options include:

| Option | Purpose |
|---|---|
| `--rdf-format` | Override RDF serialization format |
| `--output` | Save JSON to a specified path |
| `--internal-prefix` | Configure an internal IRI prefix |
| `--help` | Display CLI help |
| `--version` | Display package version (global option) |

`--internal-prefix` can be repeated.

The CLI supports the legacy form without the `inspect` subcommand.

Execution failures are returned through nonzero exit codes and error messages written to standard error.

Successful JSON output is written to standard output unless an output path is specified.

The CLI prevents overwriting the input RDF file with the output report when a local input path is used.

## 11. Testing Strategy

Automated testing is implemented with pytest.

The test suite covers:

- Local RDF loading
- Remote HTTP(S) loading
- Format identification and override
- Loading and parsing errors
- Ontology inventory semantics
- Named-individual counting
- Class and property declarations
- JSON report serialization
- RDF literal diagnostics
- Lexical-form preservation
- Namespace extraction
- Namespace classification
- Internal prefix handling
- CLI behavior

Remote retrieval unit tests use simulated HTTP responses and do not require live network access.

The current v0.3.0 development suite includes 57 tests.

### 11.1 Run Tests

```bash
uv run python -m pytest -v
```

### 11.2 Linting

```bash
uv run python -m ruff check .
```

### 11.3 Formatting

```bash
uv run python -m ruff format --check .
```

### 11.4 Continuous Integration

GitHub Actions runs automated checks on pushes and pull requests.

The CI workflow includes:

- Python 3.13 environment setup
- Dependency installation with uv
- pytest execution
- Ruff linting
- Ruff formatting verification

## 12. Validation with Real Ontologies

SemanticAudit has been exercised on several real-world ontologies.

These integration checks complement the automated unit tests.

### 12.1 BOT

The Building Topology Ontology (BOT) was inspected through both a local file and a remote raw GitHub URL.

Observed inventory:

| Metric | Value |
|---|---:|
| RDF triples | 957 |
| Declared classes | 8 |
| Declared properties | 31 |
| Named individuals | 0 |
| Blank nodes | 4 |

Using the internal prefix:

```text
https://w3id.org/bot#
```

the analysis identified:

- 7 internal declared classes
- 17 internal declared properties
- 1 declared class outside the internal prefix
- 14 declared properties outside the internal prefix

These results demonstrate the distinction between global ontology inventory counts and internal vocabulary counts.

### 12.2 FoodOn

The locally inspected FoodOn base ontology contained:

| Metric | Value |
|---|---:|
| RDF triples | 313,170 |
| Global declared classes | 31,607 |
| Global declared properties | 60 |
| Detected typed-literal issues | 2 |

For the namespace:

```text
http://purl.obolibrary.org/obo/
```

the analysis identified:

| Metric | Value |
|---|---:|
| Distinct observed IRIs | 31,759 |
| Internal FOODON_ IRIs | 29,278 |
| Declared classes in OBO namespace | 31,606 |
| Internal FOODON_ declared classes | 29,255 |
| Declared properties in OBO namespace | 41 |
| Internal FOODON_ declared properties | 4 |

The OBO namespace was classified as `mixed`.

These values describe the tested file and configured prefix; they are not universal statistics for all FoodOn distributions or versions.

The two previously observed invalid `xsd:dateTime` literals were preserved in the JSON diagnostics.

## 13. Error Handling

Application-specific errors are defined in `errors.py`.

The loader distinguishes input acquisition failures from RDF parsing failures.

The CLI catches supported application and operating-system errors and returns an error status.

The current diagnostic subsystem reports supported invalid literals without treating every diagnostic as a fatal inspection error.

Future versions may introduce configurable severity policies or inspection exit-code thresholds.

These policies are not implemented yet.

## 14. Known Limitations

SemanticAudit currently does not implement:

1. OWL/RDFS inference
2. OWL logical consistency checking
3. SHACL validation
4. Automatic import resolution
5. Complete anonymous OWL expression interpretation
6. Exhaustive datatype and XML Schema validation
7. Formal ontology provenance or ownership detection
8. HTTP dereferenceability testing for ontology IRIs
9. SPARQL competency testing
10. A graphical user interface

Namespace classifications depend on the configured internal prefixes.

Vocabulary declarations and individual counts follow operational inventory conventions rather than complete OWL semantics.

Network acquisition and parser behavior require additional security controls before deployment as a public service.

## 15. Planned Extensions

Potential development areas include:

### 15.1 Deprecated Term Detection

Identify ontology elements annotated with `owl:deprecated`.

Possible checks include deprecated classes, properties, and references to deprecated vocabulary elements.

### 15.2 IRI Dereferenceability and Link Validation

Introduce optional HTTP checks for selected IRIs.

Possible capabilities include:

- HTTP response inspection
- Redirect resolution
- Timeout and retry policies
- Broken-link diagnostics
- Distinguishing namespace bases from individual resource IRIs
- Structured reporting of dereferenceability results

An HTTP 404 response for a namespace base does not necessarily mean that every IRI within that namespace is invalid.

A URI is not required to be dereferenceable for an RDF statement to be syntactically valid.

### 15.3 SHACL Validation

Introduce SHACL constraint validation as a separate component.

### 15.4 SPARQL Competency Questions

Support expected-result assertions for ontology competency questions and regression testing.

### 15.5 Optional Reasoning

Investigate controlled RDFS or OWL 2 RL reasoning as an optional analysis step.

Inferred facts should remain distinguishable from explicit statements.

### 15.6 Quality Metrics and Reporting

Introduce additional indicators, reporting formats, and visualization capabilities.

## 16. Architecture Principles

The long-term development of SemanticAudit follows several principles:

**Modularity**

Each analysis component should have a clearly defined responsibility.

**Explicit semantics**

The tool must document precisely what it counts or validates.

**Traceability**

Diagnostics should reference the RDF elements responsible for an observed issue.

**Reproducibility**

Reports should be structured, versioned, and consistently ordered where possible.

**Backward compatibility**

Existing public interfaces and report fields should be preserved when feasible. Schema changes should be documented.

**Progressive validation**

New functionality should be covered by automated tests and validated against representative real-world ontologies.

**Security awareness**

Remote data retrieval and RDF parsing must be treated as potentially risky operations.

---

SemanticAudit is developed as an extensible foundation for RDF/OWL ontology inspection and semantic quality auditing.
