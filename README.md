SemanticAudit
RDF/OWL ontology inspection from the command line · Inspection d'ontologies RDF/OWL en ligne de commande

English | Français
English
SemanticAudit is an open-source Python tool for inspecting RDF/OWL vocabularies and laying the groundwork for semantic quality audits. Version 0.2.0 provides the first working component: the Ontology Inspector.
Project status: SHACL validation, SPARQL competency tests, reasoning, and a user interface are planned, not yet implemented.

Requirements
- Windows 10/11, Linux, or macOS
- uv
- Python 3.13 (the project's .python-version specifies 3.13)
Quick start
Open a terminal in the directory containing pyproject.toml:
uv sync
uv run python -m semantic_audit --version
uv run python -m semantic_audit inspect examples/organization.ttl
The legacy invocation without inspect is also supported:
uv run python -m semantic_audit examples/organization.ttl
Save a JSON report:
uv run python -m semantic_audit inspect examples/organization.ttl --output reports/organization.json
Specify the serialization when the file extension does not identify its RDF format:
uv run python -m semantic_audit inspect my_ontology.data --rdf-format turtle
View available options:
uv run python -m semantic_audit --help
The installed semantic-audit command is also available on systems that permit its launcher to run. Using python -m semantic_audit avoids relying on that launcher, which may be blocked by Windows application-control policies. If your machine blocks an unsigned uv-managed Python installation, use an approved, signed system Python 3.13 interpreter rather than changing security controls.
JSON report
For the bundled demonstration ontology, the report has this general shape:
{
  "schema_version": "1.0",
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
  "individuals": ["..."]
}
The counts refer to the bundled sample ontology. The "..." entries abbreviate arrays for readability; actual reports contain detailed objects.

The report includes:
- Declared classes, labels, comments, direct named superclasses, and counts of directly typed named individuals.
- Declared properties, RDF/OWL property types, named domains and ranges, named superproperties, and annotations.
- Named individuals, labels, and explicitly asserted types.
- RDF triple counts and distinct blank-node counts.
Collections are sorted to produce stable, comparable JSON output.
Tests and code quality
uv run python -m pytest -v
uv run python -m ruff check .
uv run python -m ruff format --check .
Project structure
src/semantic_audit/
    loader.py       # RDF file parsing
    inspector.py    # Vocabulary inspection and counts
    models.py       # Typed report models
    cli.py          # Command-line interface
    errors.py       # Application-specific errors
examples/           # Bundled demo ontology and invalid input fixture
tests/              # Unit and CLI tests
docs/ARCHITECTURE.md
Current limitations
- No RDF(S)/OWL reasoning. For example, subclass membership is not inferred from an individual's declared type.
- No SHACL validation or logical consistency checking.
- The inventory focuses on explicit declarations and named resources; anonymous OWL expressions are not fully interpreted.
- Blank nodes are counted but are not treated as named individuals.
- OWL imports are not automatically resolved. Only load RDF documents from trusted sources; some RDF formats may contain external references.
See [the architecture notes](docs/ARCHITECTURE.md) for the exact inspection conventions and report semantics.
License
MIT — see LICENSE.
Français
SemanticAudit est un outil Python open source pour inspecter des vocabulaires RDF/OWL et préparer leur audit de qualité sémantique. La version 0.2.0 fournit le premier composant fonctionnel : Ontology Inspector.
État du projet : la validation SHACL, les tests de compétences SPARQL, le raisonnement et une interface utilisateur sont prévus, mais pas encore implémentés.

Prérequis
- Windows 10/11, Linux ou macOS
- uv
- Python 3.13 (le fichier .python-version indique 3.13)
Démarrage rapide
Ouvre un terminal dans le dossier contenant pyproject.toml :
uv sync
uv run python -m semantic_audit --version
uv run python -m semantic_audit inspect examples/organization.ttl
L'ancienne syntaxe sans inspect reste prise en charge :
uv run python -m semantic_audit examples/organization.ttl
Enregistrer un rapport JSON :
uv run python -m semantic_audit inspect examples/organization.ttl --output reports/organization.json
Préciser la sérialisation si l'extension ne permet pas d'identifier le format RDF :
uv run python -m semantic_audit inspect mon_ontologie.data --rdf-format turtle
Afficher les options disponibles :
uv run python -m semantic_audit --help
La commande installée semantic-audit est également disponible lorsque le système autorise l'exécution de son lanceur. L'appel python -m semantic_audit évite de dépendre de ce lanceur, parfois bloqué par les stratégies de contrôle des applications Windows. Si une distribution Python gérée par uv est bloquée, utilise un interpréteur Python 3.13 système signé et autorisé plutôt que de modifier les paramètres de sécurité.
Rapport JSON
Pour l'ontologie de démonstration incluse, le rapport a la structure générale suivante :
{
  "schema_version": "1.0",
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
  "individuals": ["..."]
}
Ces statistiques concernent l'ontologie de démonstration. Les valeurs "..." abrègent les tableaux pour faciliter la lecture ; les vrais rapports contiennent des objets détaillés.

Le rapport présente :
- Les classes déclarées, leurs libellés, commentaires, superclasses directes nommées et le nombre d'individus nommés directement typés.
- Les propriétés déclarées, leurs types RDF/OWL, domaines et portées nommés, superpropriétés nommées et annotations.
- Les individus nommés, leurs libellés et leurs types explicitement déclarés.
- Le nombre de triplets RDF et de nœuds anonymes distincts.
Les collections sont triées pour produire un JSON stable et comparable.
Tests et qualité du code
uv run python -m pytest -v
uv run python -m ruff check .
uv run python -m ruff format --check .
Structure du projet
src/semantic_audit/
    loader.py       # Analyse des fichiers RDF
    inspector.py    # Inspection et comptages
    models.py       # Modèles de rapport typés
    cli.py          # Interface en ligne de commande
    errors.py       # Erreurs applicatives
examples/           # Ontologie de démonstration et fichier d'entrée invalide
tests/              # Tests unitaires et tests CLI
docs/ARCHITECTURE.md
Limites actuelles
- Pas de raisonnement RDF(S)/OWL. Par exemple, l'appartenance à une classe parente n'est pas inférée à partir du type d'un individu.
- Pas de validation SHACL ni de vérification de cohérence logique.
- L'inventaire porte sur les déclarations explicites et les ressources nommées ; les expressions OWL anonymes ne sont pas entièrement interprétées.
- Les nœuds anonymes sont comptés, mais ne sont pas considérés comme des individus nommés.
- Les imports OWL ne sont pas résolus automatiquement. Ne charge que des documents RDF de confiance : certains formats peuvent contenir des références externes.
Consulte [les notes d'architecture](docs/ARCHITECTURE.md) pour les conventions d'inspection et la sémantique exacte du rapport.
Licence
MIT — voir LICENSE.