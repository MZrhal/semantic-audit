
# SemanticAudit

**RDF/OWL Ontology Inspection and Semantic Quality Diagnostics**

*Inspection d'ontologies RDF/OWL et diagnostics de qualité sémantique*

An open-source Python CLI for RDF/OWL ontology inspection, structured diagnostics, and namespace analysis.

**Development status:** v0.3.0 in progress  
**Current package version:** 0.3.0  
**JSON report schema:** 1.2  
**License:** MIT

[English](#english) | [Français](#français)

---

# English

## Overview

SemanticAudit is an open-source Python command-line tool designed to inspect RDF/OWL ontologies and provide structured information about their vocabulary, organization, and data quality.

The project aims to make ontology analysis more accessible, reproducible, and transparent through automated inspection and JSON reporting.

SemanticAudit is being developed incrementally toward a broader semantic quality auditing toolkit.

The current development branch (`feature/v0.3.0`) provides three main capabilities:

1. **Ontology Inspector** — inventory of explicitly declared RDF/OWL vocabulary elements.
2. **RDF Diagnostics** — detection of invalid lexical representations for selected XSD datatypes.
3. **Namespace Analysis** — identification and classification of RDF namespaces and internal vocabulary terms.

SemanticAudit does not currently perform OWL reasoning, SHACL validation, or logical consistency checking.

## Features

### 1. Ontology Inspector

SemanticAudit extracts information about explicitly declared ontology elements.

**Classes**
- Declared `owl:Class` and `rdfs:Class` resources
- Labels and comments
- Direct named superclasses
- Counts of directly typed named individuals

**Properties**
- Declared RDF/OWL properties
- Property types and characteristics
- Named domains and ranges
- Direct named superproperties
- Labels and comments

**Individuals**
- Named individuals identified by the project's explicit inventory rules
- Directly asserted classes
- Labels

**Graph statistics**
- Total RDF triples
- Declared classes
- Declared properties
- Named individuals
- Distinct blank nodes

SemanticAudit analyzes explicit statements only. It does not infer additional class memberships or property relationships.

### 2. Remote Ontology Inspection

SemanticAudit can inspect ontologies stored locally or available through HTTP(S) URLs.

Supported capabilities include:
- Local RDF file loading
- Direct HTTP(S) ontology retrieval
- RDF serialization format detection
- Explicit format override
- Bounded remote downloads
- Structured loading and parsing errors
- Temporary storage for remote documents

Example:

```powershell
uv run python -m semantic_audit inspect `
  "https://raw.githubusercontent.com/w3c-lbd-cg/bot/master/bot.ttl" `
  --output reports/bot-remote.json
```

Remote files are downloaded temporarily and parsed using the same inspection pipeline as local files.

**Important:** Remote retrieval is intended for trusted sources and local CLI use. It is not yet hardened for arbitrary URLs submitted to a public web service.

For details, see [Remote Ontology Inspection](docs/REMOTE_URL.md).

### 3. RDF Diagnostics

SemanticAudit detects invalid lexical representations for selected XML Schema datatypes.

Currently supported datatypes:

- `xsd:boolean`
- `xsd:integer`
- `xsd:decimal`
- `xsd:date`
- `xsd:time`
- `xsd:dateTime`

Detected anomalies are recorded in the JSON report under `issues`.

Each diagnostic includes:

- Diagnostic code
- Severity level
- RDF subject
- RDF predicate
- Declared datatype
- Original lexical value
- Diagnostic message

Example:

```json
{
  "code": "INVALID_TYPED_LITERAL",
  "severity": "warning",
  "subject": "https://example.org/record",
  "predicate": "https://example.org/createdAt",
  "datatype": "http://www.w3.org/2001/XMLSchema#dateTime",
  "lexical_value": "2026-04-10 9:06:01",
  "message": "Invalid or unsupported lexical form for the declared XSD datatype."
}
```

The loader preserves the lexical forms of RDF literals during parsing, allowing diagnostics to identify values that might otherwise be normalized by RDFLib.

This is a lightweight diagnostic mechanism, not comprehensive XML Schema, SHACL, or OWL validation.

### 4. Namespace Analysis

SemanticAudit identifies RDF namespaces and computes vocabulary statistics for each namespace.

The analysis includes:

- Distinct IRIs observed in the graph
- Declared classes per namespace
- Declared properties per namespace
- Named individuals per namespace
- Internal vocabulary counts
- Namespace classification

The `--internal-prefix` option identifies which IRIs should be treated as belonging to the ontology's internal vocabulary.

Example:

```powershell
uv run python -m semantic_audit inspect `
  examples/bot.ttl `
  --internal-prefix "https://w3id.org/bot#" `
  --output reports/bot-namespaces.json
```

Multiple internal prefixes can be provided by repeating the option.

Namespaces are assigned one of four classifications:

| Classification | Meaning |
|---|---|
| `internal` | All observed IRIs match a configured internal prefix |
| `external` | No observed IRIs match an internal prefix |
| `mixed` | Both internal and external IRIs are present |
| `unknown` | No internal prefixes were configured |

Classification is based on user-configured IRI prefixes, not semantic inference.

This distinction is especially important for ontologies sharing a namespace.

For example, FoodOn and other OBO ontologies can use the namespace:

```text
http://purl.obolibrary.org/obo/
```

FoodOn-specific identifiers can be distinguished using:

```text
http://purl.obolibrary.org/obo/FOODON_
```

Example:

```powershell
uv run python -m semantic_audit inspect `
  examples/foodon-base.owl `
  --internal-prefix "http://purl.obolibrary.org/obo/FOODON_" `
  --output reports/foodon-namespaces.json
```

The BOT and FoodOn files in these examples must be downloaded separately; they are not part of the bundled demonstration fixtures.

Namespace Analysis does not verify whether an IRI resolves successfully over HTTP.

## Requirements

- Windows 10/11, Linux, or macOS
- Python 3.13
- [uv](https://docs.astral.sh/uv/)

The project requires Python 3.13 or later according to its package metadata and is currently developed and tested with Python 3.13.

## Installation

Clone the repository:

```bash
git clone https://github.com/MZrhal/semantic-audit.git
cd semantic-audit
```

Install the project and development dependencies:

```bash
uv sync
```

Check the installed package version:

```bash
uv run python -m semantic_audit --version
```

The package still reports version `0.2.0` while the v0.3.0 development branch is being finalized.

On Windows systems where the generated executable launcher is restricted, using `python -m semantic_audit` avoids relying on that launcher.

Use an approved Python installation rather than bypassing operating-system security controls.

## Usage

### Inspect a local ontology

```bash
uv run python -m semantic_audit inspect examples/organization.ttl
```

The original syntax without the `inspect` subcommand remains supported:

```bash
uv run python -m semantic_audit examples/organization.ttl
```

### Generate a JSON report

```bash
uv run python -m semantic_audit inspect examples/organization.ttl --output reports/organization.json
```

### Specify the RDF format

```bash
uv run python -m semantic_audit inspect ontology.data --rdf-format turtle
```

### Inspect an ontology from a URL

```bash
uv run python -m semantic_audit inspect https://example.org/ontology.ttl
```

### Analyze internal vocabulary terms

```bash
uv run python -m semantic_audit inspect examples/organization.ttl --internal-prefix "https://example.org/organization/"
```

### Inspect multiple internal prefixes

```powershell
uv run python -m semantic_audit inspect `
  examples/organization.ttl `
  --internal-prefix "https://example.org/organization/" `
  --internal-prefix "https://example.org/other/"
```

### View the available options

```bash
uv run python -m semantic_audit --help
uv run python -m semantic_audit inspect --help
```

## JSON Reports

SemanticAudit generates structured, JSON-serializable reports.

The v0.3.0 development schema is version `1.2`.

The following example illustrates the general report structure. Array contents are abbreviated for readability.

```json
{
  "schema_version": "1.2",
  "source": "examples/organization.ttl",
  "statistics": {
    "triples": 48,
    "declared_classes": 5,
    "declared_properties": 5,
    "named_individuals": 5,
    "blank_nodes": 0
  },
  "classes": ["..."],
  "properties": ["..."],
  "individuals": ["..."],
  "issues": [],
  "internal_prefixes": [],
  "namespaces": ["..."]
}
```

In actual reports, `classes`, `properties`, `individuals`, and `namespaces` contain structured objects rather than placeholder strings.

The report schema has evolved as follows:

| Schema | Main additions |
|---|---|
| `1.0` | Ontology inventory and graph statistics |
| `1.1` | Structured RDF literal diagnostics |
| `1.2` | Namespace analysis and internal prefix configuration |

JSON output is designed for downstream processing, integration, and comparison.

## Project Structure

```text
semantic-audit/
├── src/
│   └── semantic_audit/
│       ├── __init__.py
│       ├── __main__.py
│       ├── cli.py
│       ├── loader.py
│       ├── inspector.py
│       ├── diagnostics.py
│       ├── namespaces.py
│       ├── models.py
│       └── errors.py
├── examples/
│   └── organization.ttl
├── tests/
│   ├── test_cli.py
│   ├── test_loader.py
│   ├── test_inspector.py
│   ├── test_remote_url.py
│   ├── test_diagnostics.py
│   └── test_namespaces.py
├── docs/
│   ├── ARCHITECTURE.md
│   └── REMOTE_URL.md
├── .github/
│   └── workflows/
│       └── ci.yml
├── pyproject.toml
└── README.md
```

Additional test fixtures and configuration files are omitted from this simplified tree.

## Testing and Code Quality

The project uses pytest for automated testing and Ruff for linting and formatting.

Run the test suite:

```bash
uv run python -m pytest -v
```

Check code quality:

```bash
uv run python -m ruff check .
```

Verify formatting:

```bash
uv run python -m ruff format --check .
```

The v0.3.0 development test suite currently contains 57 tests covering ontology loading, inspection, diagnostics, namespace analysis, and CLI behavior.

GitHub Actions runs automated checks on pushes and pull requests.

## Current Limitations

SemanticAudit currently does not provide:

- OWL/RDFS reasoning or automatic inference
- SHACL constraint validation
- Ontological consistency checking
- Automatic resolution of `owl:imports`
- Complete interpretation of anonymous OWL expressions
- Comprehensive XML Schema datatype validation
- HTTP accessibility or dereferenceability checks for individual IRIs
- A graphical user interface

Remote RDF parsing may access external resources through format-specific mechanisms. Remote loading is not yet suitable for accepting arbitrary untrusted URLs in a hosted service.

The reported vocabulary inventory represents explicit declarations according to documented operational rules, not a complete semantic classification.

## Roadmap

Potential future development areas include:

- Deprecated ontology term detection
- IRI dereferenceability and broken-link diagnostics
- Additional ontology quality indicators
- SHACL validation
- SPARQL competency question testing
- Optional RDFS/OWL reasoning
- Visualization and reporting interfaces

The roadmap is indicative and does not imply that these features are already implemented.

For technical details, see [Architecture](docs/ARCHITECTURE.md).

## License

SemanticAudit is distributed under the MIT License. See [LICENSE](LICENSE).

---

# Français

## Présentation

SemanticAudit est un outil Python open source en ligne de commande destiné à l'inspection des ontologies RDF/OWL et à l'analyse de leur qualité sémantique.

L'objectif est de rendre l'analyse des ontologies plus accessible, reproductible et transparente grâce à des inspections automatisées et à la génération de rapports JSON structurés.

Le projet évolue progressivement vers un outil d'audit de qualité sémantique plus complet.

La branche de développement `feature/v0.3.0` comprend trois grandes fonctionnalités :

1. **Ontology Inspector** — inventaire des éléments RDF/OWL explicitement déclarés.
2. **RDF Diagnostics** — détection de représentations lexicales invalides pour certains datatypes XSD.
3. **Namespace Analysis** — identification et classification des namespaces RDF et des termes internes.

SemanticAudit ne réalise pas encore de raisonnement OWL, de validation SHACL ou de vérification de cohérence logique.

## Fonctionnalités

### 1. Inspection des ontologies

SemanticAudit extrait les informations relatives aux éléments explicitement déclarés dans une ontologie.

**Classes**
- Classes `owl:Class` et `rdfs:Class`
- Libellés et commentaires
- Superclasses directes nommées
- Nombre d'individus nommés directement typés

**Propriétés**
- Propriétés RDF/OWL déclarées
- Types et caractéristiques des propriétés
- Domaines et portées nommés
- Superpropriétés directes nommées
- Libellés et commentaires

**Individus**
- Individus nommés identifiés selon les règles explicites de l'outil
- Classes directement déclarées
- Libellés

**Statistiques**
- Nombre total de triplets RDF
- Classes déclarées
- Propriétés déclarées
- Individus nommés
- Nœuds anonymes distincts

L'inspection porte uniquement sur les déclarations explicites. Aucun raisonnement n'est appliqué pour déduire de nouvelles relations.

### 2. Inspection d'ontologies distantes

SemanticAudit permet d'inspecter des ontologies stockées localement ou accessibles par une URL HTTP(S).

Les fonctionnalités comprennent :
- Chargement de fichiers RDF locaux
- Téléchargement temporaire de documents RDF distants
- Identification du format RDF
- Possibilité de préciser explicitement le format
- Limitation de la taille des téléchargements
- Gestion des erreurs réseau et de parsing

Exemple :

```powershell
uv run python -m semantic_audit inspect `
  "https://raw.githubusercontent.com/w3c-lbd-cg/bot/master/bot.ttl" `
  --output reports/bot-remote.json
```

Les documents distants sont temporairement téléchargés puis analysés par le même pipeline que les fichiers locaux.

Cette fonctionnalité est conçue pour une utilisation CLI avec des sources de confiance. Elle n'est pas encore sécurisée pour exposer librement le téléchargement d'URL dans une application web publique.

Documentation : [Remote Ontology Inspection](docs/REMOTE_URL.md).

### 3. Diagnostics des littéraux RDF

SemanticAudit détecte les représentations lexicales invalides de certains datatypes XML Schema.

Types pris en charge :

- `xsd:boolean`
- `xsd:integer`
- `xsd:decimal`
- `xsd:date`
- `xsd:time`
- `xsd:dateTime`

Les anomalies sont enregistrées dans le champ `issues` du rapport JSON.

Chaque diagnostic contient :
- Un code
- Un niveau de sévérité
- Le sujet RDF concerné
- Le prédicat RDF concerné
- Le datatype déclaré
- La valeur lexicale originale
- Un message explicatif

Le chargement préserve les représentations lexicales des littéraux, y compris lorsque leurs valeurs sont invalides.

Cette fonctionnalité constitue une première couche de diagnostic, et non une validation complète XML Schema, SHACL ou OWL.

### 4. Analyse des namespaces

SemanticAudit identifie les namespaces RDF et calcule des statistiques sur les vocabulaires présents dans l'ontologie.

L'analyse comprend :
- Les IRI distinctes observées
- Les classes déclarées par namespace
- Les propriétés déclarées par namespace
- Les individus nommés par namespace
- Le nombre de termes considérés comme internes
- La classification des namespaces

L'option `--internal-prefix` permet de définir les préfixes d'IRI correspondant au vocabulaire interne.

Exemple avec BOT :

```powershell
uv run python -m semantic_audit inspect `
  examples/bot.ttl `
  --internal-prefix "https://w3id.org/bot#" `
  --output reports/bot-namespaces.json
```

Les namespaces sont classés selon quatre catégories :

| Classification | Signification |
|---|---|
| `internal` | Toutes les IRI correspondent à un préfixe interne |
| `external` | Aucune IRI ne correspond à un préfixe interne |
| `mixed` | Le namespace contient des IRI internes et externes |
| `unknown` | Aucun préfixe interne n'a été configuré |

Cette classification repose sur les préfixes IRI définis par l'utilisateur. Elle ne résulte pas d'un raisonnement sémantique.

Pour FoodOn, le préfixe suivant permet d'identifier les termes spécifiques à ce vocabulaire :

```text
http://purl.obolibrary.org/obo/FOODON_
```

Exemple :

```powershell
uv run python -m semantic_audit inspect `
  examples/foodon-base.owl `
  --internal-prefix "http://purl.obolibrary.org/obo/FOODON_" `
  --output reports/foodon-namespaces.json
```

Les fichiers BOT et FoodOn doivent être téléchargés séparément : ils ne sont pas fournis avec les exemples de base du dépôt.

L'analyse des namespaces ne vérifie pas encore l'accessibilité HTTP des IRI.

## Prérequis

- Windows 10/11, Linux ou macOS
- Python 3.13
- [uv](https://docs.astral.sh/uv/)

Le projet requiert Python 3.13 ou une version ultérieure selon ses métadonnées. Le développement et les tests actuels utilisent Python 3.13.

## Installation

Cloner le dépôt :

```bash
git clone https://github.com/MZrhal/semantic-audit.git
cd semantic-audit
```

Installer les dépendances :

```bash
uv sync
```

Afficher la version du package :

```bash
uv run python -m semantic_audit --version
```

Le package indique encore la version `0.2.0` pendant la finalisation de la branche v0.3.0.

Sous Windows, l'utilisation de `python -m semantic_audit` permet d'éviter les problèmes liés aux restrictions d'exécution de certains lanceurs.

Il est recommandé d'utiliser une installation Python autorisée plutôt que de contourner les restrictions de sécurité du système.

## Utilisation

### Inspecter une ontologie locale

```bash
uv run python -m semantic_audit inspect examples/organization.ttl
```

L'ancienne syntaxe reste compatible :

```bash
uv run python -m semantic_audit examples/organization.ttl
```

### Enregistrer un rapport JSON

```bash
uv run python -m semantic_audit inspect examples/organization.ttl --output reports/organization.json
```

### Préciser le format RDF

```bash
uv run python -m semantic_audit inspect ontologie.data --rdf-format turtle
```

### Inspecter une ontologie distante

```bash
uv run python -m semantic_audit inspect https://example.org/ontology.ttl
```

### Analyser le vocabulaire interne

```bash
uv run python -m semantic_audit inspect examples/organization.ttl --internal-prefix "https://example.org/organization/"
```

### Utiliser plusieurs préfixes internes

L'option `--internal-prefix` peut être répétée autant de fois que nécessaire.

```powershell
uv run python -m semantic_audit inspect `
  examples/organization.ttl `
  --internal-prefix "https://example.org/organization/" `
  --internal-prefix "https://example.org/other/"
```

### Afficher l'aide

```bash
uv run python -m semantic_audit --help
uv run python -m semantic_audit inspect --help
```

## Rapports JSON

SemanticAudit produit des rapports JSON structurés.

Le schéma utilisé dans la branche v0.3.0 est la version `1.2`.

Exemple simplifié :

```json
{
  "schema_version": "1.2",
  "source": "examples/organization.ttl",
  "statistics": {
    "triples": 48,
    "declared_classes": 5,
    "declared_properties": 5,
    "named_individuals": 5,
    "blank_nodes": 0
  },
  "classes": ["..."],
  "properties": ["..."],
  "individuals": ["..."],
  "issues": [],
  "internal_prefixes": [],
  "namespaces": ["..."]
}
```

Dans les rapports réels, les tableaux contiennent des objets structurés. Les chaînes `"..."` servent uniquement à abréger cet exemple.

Évolution du schéma :

| Version | Fonctionnalités principales |
|---|---|
| `1.0` | Inventaire ontologique et statistiques |
| `1.1` | Diagnostics RDF structurés |
| `1.2` | Analyse des namespaces et préfixes internes |

Les rapports peuvent être exploités par d'autres outils, scripts ou applications.

## Structure du projet

```text
semantic-audit/
├── src/
│   └── semantic_audit/
│       ├── __init__.py
│       ├── __main__.py
│       ├── cli.py
│       ├── loader.py
│       ├── inspector.py
│       ├── diagnostics.py
│       ├── namespaces.py
│       ├── models.py
│       └── errors.py
├── examples/
│   └── organization.ttl
├── tests/
│   ├── test_cli.py
│   ├── test_loader.py
│   ├── test_inspector.py
│   ├── test_remote_url.py
│   ├── test_diagnostics.py
│   └── test_namespaces.py
├── docs/
│   ├── ARCHITECTURE.md
│   └── REMOTE_URL.md
├── .github/
│   └── workflows/
│       └── ci.yml
├── pyproject.toml
└── README.md
```

Cette représentation simplifiée ne contient pas tous les fichiers de configuration et de test du projet.

## Tests et qualité du code

SemanticAudit utilise pytest pour les tests automatisés et Ruff pour l'analyse statique et le formatage Python.

Lancer les tests :

```bash
uv run python -m pytest -v
```

Vérifier la qualité du code :

```bash
uv run python -m ruff check .
```

Vérifier le formatage :

```bash
uv run python -m ruff format --check .
```

La branche de développement v0.3.0 comprend actuellement 57 tests couvrant le chargement RDF, l'inspection, les diagnostics, l'analyse des namespaces et la CLI.

GitHub Actions exécute automatiquement les vérifications à chaque push et pull request.

## Limites actuelles

SemanticAudit ne propose pas encore :

- De raisonnement RDF(S)/OWL
- De validation SHACL
- De vérification de cohérence logique
- De résolution automatique des `owl:imports`
- D'interprétation complète des expressions OWL anonymes
- De validation exhaustive des datatypes XML Schema
- De vérification HTTP de l'accessibilité des IRI
- D'interface graphique

Le chargement de documents RDF peut impliquer des références externes selon le format utilisé. L'inspection de sources distantes doit rester limitée à des documents de confiance.

Les statistiques reflètent les déclarations explicites conformément aux conventions documentées.

## Feuille de route

Les prochains axes de développement envisagés comprennent :

- Détection des termes ontologiques obsolètes
- Validation des IRI et détection des liens cassés
- Indicateurs supplémentaires de qualité ontologique
- Validation SHACL
- Tests de compétences SPARQL
- Raisonnement RDF(S)/OWL optionnel
- Visualisation et interfaces de reporting

Ces fonctionnalités sont prévues ou envisagées, mais ne sont pas encore implémentées.

Pour les détails techniques, consulter [l'architecture du projet](docs/ARCHITECTURE.md).

## Licence

SemanticAudit est distribué sous licence MIT. Voir [LICENSE](LICENSE).
