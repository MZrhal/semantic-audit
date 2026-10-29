# Architecture — SemanticAudit 0.2.0

## Modules

- `loader.py` — lecture d'un document RDF local et traduction des erreurs RDFLib.
- `inspector.py` — logique métier **pure sur un `rdflib.Graph`** ; aucune écriture disque.
- `models.py` — résultats immuables et schéma de rapport versionné.
- `cli.py` — interface utilisateur, sérialisation et export JSON.
- `errors.py` — exceptions métiers.

```text
RDF/OWL file
   -> loader.load_graph()
   -> inspector.inspect_graph()
   -> models.OntologyReport
   -> cli.main() -> stdout / JSON file
```

## Règles de modélisation importantes

1. Une **classe déclarée** est un IRI avec `rdf:type owl:Class` ou `rdfs:Class`.
2. Une **propriété déclarée** est un IRI avec l'un des types listés dans
   `PROPERTY_KINDS` (`rdf:Property`, `owl:ObjectProperty`, etc.).
3. Un **individu nommé** est un IRI avec `rdf:type` d'une classe déclarée ou
   `rdf:type owl:NamedIndividual`, hors classes, propriétés et ressources
   `owl:Ontology`. Il est compté une seule fois, même avec plusieurs types.
4. Les classes d'un individu sont les `rdf:type` **explicitement présents**
   et correspondant à des classes déclarées.
5. `rdfs:subClassOf` est inspecté, **pas exécuté** : un `Employee` n'est pas
   automatiquement ajouté à `Person`.
6. Les nœuds anonymes ne sont pas des individus nommés. Leur nombre total
   dans le graphe est fourni séparément.
7. Les mentions `owl:imports` ne sont pas automatiquement résolues.

## Extensions prévues

- SHACL et rapport de validation `sh:ValidationReport`.
- Compétency questions SPARQL avec résultats attendus.
- Inférences RDFS / OWL RL : *enrichissement séparé* du graphe de données.
- Interface Streamlit et export audit.

Les règles ci-dessus sont volontairement conservatrices. L'inspecteur n'est
ni un reasoner, ni une preuve de cohérence logique.
