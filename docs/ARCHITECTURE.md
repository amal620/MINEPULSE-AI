# Architecture technique

## Couches
1. **Presentation** — HTML/CSS/JavaScript, navigation par modules, formulaires de télémétrie et de revue d'incident.
2. **API** — FastAPI expose les opérations de simulation, incidents, approbations, maintenance et monitoring.
3. **Orchestration** — LangGraph enchaîne les sept nœuds métier.
4. **Agents** — modules Python indépendants avec schémas Pydantic.
5. **Persistence** — SQLAlchemy synchronisé vers SQLite pour les managers métier et le monitoring.

## Flux d'exécution
`Input → Sensor Intelligence → Predictive Diagnosis → Risk Assessment → Digital Twin → Decision Optimizer → Resource Coordinator → Incident Management → END`

Le wrapper `monitored_node` encadre chaque nœud : écrit STARTED, exécute l'opération, puis écrit SUCCESS ou FAILED avec durée. Tous les événements partagent le même Correlation ID.

## Human approval
Un incident HIGH/CRITICAL est créé en `AWAITING_APPROVAL`. Le responsable peut approuver ou rejeter. La fonction de démarrage de maintenance refuse les incidents non approuvés. La clôture n'est autorisée qu'après résolution.

## Persistance
- `incidents`
- `approvals`
- `maintenance_records`
- `monitoring_events`

La base est locale SQLite. Pour un environnement multi-utilisateur de production, migrer vers PostgreSQL et ajouter une gestion d'identité/permissions.
