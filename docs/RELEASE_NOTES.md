# Version 0.2.0 — Refonte du premier jalon

## Différences par rapport au prototype v0.1

- Séparation nette : chargement RDF, inspection, modèles de rapport, CLI, erreurs.
- Modèles Python typés et immuables ; JSON versionné (`schema_version: 1.0`).
- Inventaire des classes, propriétés et individus **nommés** déclarés.
- Labels et commentaires multilingues ; hiérarchies directes et domaines/portées.
- Détection de déclarations multiples et élimination des doublons.
- Comptages directs sans inférence, documentés et vérifiés par les tests.
- Chargement RDF/XML et JSON-LD en plus de Turtle ; option `--rdf-format`.
- Export JSON ; protection contre l'écrasement du fichier source.
- CLI explicite `inspect` et compatibilité avec l'ancienne commande.
- Tests couvrant erreurs, formats RDF, OWL, blank nodes et CLI.
- GitHub Actions, licence MIT et documentation.

## Périmètre réel

Ce n'est **pas encore** un outil de validation SHACL ou de reasoning OWL :
le projet ne fait à ce stade que de l'inspection d'informations explicites.
