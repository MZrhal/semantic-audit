# SemanticAudit

**SemanticAudit** est un outil Python open source pour inspecter des vocabulaires
RDF/OWL et préparer leur audit sémantique. Ce dépôt contient le **premier jalon
fonctionnel** : *Ontology Inspector*.

> Le projet évoluera vers SHACL, SPARQL competency testing, reasoning et une UI.
> **Ces fonctionnalités ne sont pas encore implémentées.**

## Prérequis

- Windows 10/11 (ou Linux/macOS)
- [`uv`](https://docs.astral.sh/uv/)
- Python **3.13** (uv utilisera `.python-version`; installation via `uv python install 3.13`)

## Démarrage (PowerShell dans VS Code)

Place-toi dans le dossier contenant `pyproject.toml` :

```powershell
uv sync
uv run semantic-audit --version
uv run semantic-audit inspect examples/organization.ttl
```

L'ancienne syntaxe fonctionne également :

```powershell
uv run semantic-audit examples/organization.ttl
```

Exporter le rapport :

```powershell
uv run semantic-audit inspect examples/organization.ttl --output reports/organization.json
```

Pour un fichier dont l'extension n'est pas reconnue :

```powershell
uv run semantic-audit inspect mon_ontologie.data --rdf-format turtle
```

Aide : `uv run semantic-audit --help`.

## Que contient le rapport ?

```json
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
```

> Les statistiques sont celles du fichier de démonstration. Les tableaux
> `"..."` sont abrégés pour la lisibilité ; la commande affiche des objets
> détaillés pour chaque classe, propriété et individu.

- Liste des classes déclarées, leurs labels, commentaires, superclasses directes
  et nombre d'individus nommés directement typés.
- Liste des propriétés déclarées, leur type OWL/RDF, leurs domaines, portées,
  superpropriétés et annotations.
- Liste des individus nommés, de leurs étiquettes et types directs.
- Nombre de triplets RDF et de blank nodes distincts.

Toutes les collections sont triées afin de rendre le JSON stable et comparable.

## Tests et qualité

```powershell
uv run pytest -v
uv run ruff check .
uv run ruff format --check .
```

## Structure du code

```text
src/semantic_audit/
    loader.py       # parsing RDF
    inspector.py    # inspection et comptages
    models.py       # rapports typés
    cli.py          # ligne de commande
    errors.py       # erreurs métiers
examples/           # ontologie de démonstration + fichier invalide
tests/              # tests unitaires et CLI
docs/ARCHITECTURE.md
```

## Limites intentionnelles

- **Pas de raisonnement** RDF(S)/OWL. Une sous-classe ne propage pas encore
  automatiquement ses instances vers la classe parente.
- **Pas de validation SHACL**, ni de vérification de cohérence.
- Seules les **déclarations explicites et nommées** sont listées.
- Les blank nodes sont comptés, mais ne sont pas listés comme individus nommés.
- Les imports OWL ne sont pas résolus ; traiter uniquement des sources de
  confiance (certains formats RDF peuvent inclure des références externes).

Voir [l'architecture](docs/ARCHITECTURE.md) pour les conventions exactes.

## Licence

MIT — voir [LICENSE](LICENSE).
