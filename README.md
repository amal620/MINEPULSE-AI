# MINEPULSE AI
**Plateforme intelligente multi-agents pour la supervision et l'aide à la décision minière**

MINEPULSE AI est un prototype de décision-support pour opérations minières. Il illustre un pipeline multi-agents qui analyse des télémétries simulées, identifie des anomalies, propose des causes possibles, classe le risque, met à jour un état virtuel, compare des options, coordonne des ressources simulées et crée un incident si le risque est élevé ou critique.

> **Limite de sécurité :** ce dépôt est un prototype académique. Les valeurs capteurs et seuils sont simulés/illustratifs. Il n'est pas connecté à des équipements réels, ne fournit pas de seuils de sécurité certifiés et ne commande aucun équipement industriel. Toute intervention doit être évaluée et approuvée par un responsable qualifié.

## Fonctionnalités
- Orchestration LangGraph de 7 nœuds métier.
- Monitoring transversal des nœuds : `STARTED`, `SUCCESS`, `FAILED`, durée et Correlation ID.
- Persistance SQLite des incidents, approbations, maintenances et événements de monitoring.
- Human-in-the-loop : un incident critique attend une approbation avant le démarrage d'une maintenance simulée.
- Cycle incident : `AWAITING_APPROVAL → APPROVED/REJECTED → IN_PROGRESS → RESOLVED → CLOSED`.
- Interface web : overview, Live Operations, Digital Twin schématique, Incident Center, Observability et Agent Governance.
- Scénarios What-if qualitatifs et explications.
- Agent Cards, tests Pytest, Docker et GitHub Actions.

## Architecture
```text
Frontend (HTML/CSS/JS)
        |
     FastAPI
        |
    LangGraph
        |
        +--> Sensor Intelligence
        +--> Predictive Diagnosis
        +--> Risk Assessment
        +--> Digital Twin Simulator
        +--> Decision Optimizer
        +--> Resource Coordinator
        +--> Incident Management
        |
 Monitoring wrapper around every node
        |
 SQLAlchemy / SQLite
   + incidents
   + approvals
   + maintenance_records
   + monitoring_events
```

Monitoring is cross-cutting; it is not a sequential business node. The 7 LangGraph nodes each emit a `STARTED` and a terminal `SUCCESS` or `FAILED` event. The Monitoring Agent creates the correlation ID for each graph run.

## Requirements
- Python 3.11 or 3.12 recommended
- Git
- Docker Desktop (optional)
- No API key required for the current deterministic simulation prototype.

## Run locally (Windows PowerShell)
```powershell
# 1) Open the extracted project folder
cd MINEPULSE-AI

# 2) Create and activate a virtual environment
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1

# 3) Install dependencies
python -m pip install --upgrade pip
pip install -r requirements.txt

# 4) Optional: create local environment file
Copy-Item .env.example .env

# 5) Start the API and web application
uvicorn backend.main:app --reload
```
Open:
- Web interface: http://127.0.0.1:8000
- API documentation: http://127.0.0.1:8000/docs
- Health: http://127.0.0.1:8000/api/health

The SQLite database `minepulse.db` is created in the project root if it does not exist. Do not commit secrets or production database files.

## Demo scenario (2–3 minutes)
1. Open **Live Operations**.
2. Keep equipment `C-02`, temperature `92`, vibration `12`, speed `1.8`.
3. Click **Run multi-agent analysis**.
4. Explain the detected anomalies, risk, virtual twin status, recommended option and generated incident.
5. Open **Incident Center**, select the new incident and approve it as `Mine Supervisor`.
6. Start simulated maintenance.
7. Complete the maintenance. The prototype then verifies the result using an explicit simulated boolean and closes the incident.
8. Open **Observability** and show the Correlation ID and the persisted STARTED/SUCCESS events.
9. Open **Agent Governance** to show Agent Cards and control boundaries.

Use the Normal preset to demonstrate a no-incident path.

## API overview
- `GET /api/health`
- `GET /api/dashboard`
- `POST /api/analyze`
- `GET /api/incidents`
- `GET /api/incidents/{incident_id}`
- `POST /api/incidents/{incident_id}/approval`
- `POST /api/incidents/{incident_id}/maintenance`
- `GET /api/incidents/{incident_id}/maintenance/latest`
- `POST /api/maintenance/{maintenance_id}/complete`
- `POST /api/maintenance/{maintenance_id}/verify`
- `POST /api/incidents/{incident_id}/close`
- `GET /api/monitoring/recent`
- `GET /api/monitoring/{correlation_id}`
- `GET /api/governance/agent-cards`

## Automated tests
```powershell
pytest -q
```

## Docker
```powershell
docker compose up --build
```
Open http://localhost:8000.

## GitHub
```powershell
git init
git add .
git commit -m "Initial MINEPULSE AI prototype"
git branch -M main
git remote add origin https://github.com/<YOUR-USERNAME>/MINEPULSE-AI.git
git push -u origin main
```
Create the empty GitHub repository first and replace the placeholder URL. Never commit `.env`, `.venv`, or secrets.

## Project criteria mapping
| Criterion | Implementation |
|---|---|
| Multi-Agent Architecture | LangGraph graph with 7 business nodes |
| Monitoring Agent | `backend/monitoring/monitoring_agent.py`, monitored node wrapper |
| Correlation ID | UUID generated for every graph execution |
| Observability | Persistent trace events and report endpoint/UI |
| Automated Tests | `tests/` with Pytest |
| GitHub Actions | `.github/workflows/ci.yml` |
| Governance / Agent Cards | `agent_cards/agent_cards.json` and Governance UI |
| Docker | `Dockerfile`, `docker-compose.yml` |
| Database | SQLite + SQLAlchemy |
| Incident / Runbook | Incident Center and `docs/RUNBOOK.md` |
| Technical Documentation | README and docs |
| Demo | Reproducible scenario documented above |
| Added value | Digital Twin schematic, What-if scenarios, Explainable output, Human Approval, Audit Trail |

## Known prototype limitations
- No real mine, PLC, SCADA, IoT broker or sensor integration.
- No real-time WebSocket stream; the UI refreshes through API calls.
- Digital Twin is a schematic representation, not a 3D physics model.
- Decision alternatives use qualitative estimates, not a validated optimization solver.
- Resource availability is a hard-coded simulation, not a live inventory.
- Diagnosis is rule-based/heuristic, not a trained predictive model.
- No cloud deployment has been performed by this repository. Docker is locally runnable; cloud deployment is a next operational step.
