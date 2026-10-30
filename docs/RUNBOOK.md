# Runbook — MINEPULSE AI

## Démarrage
1. Activer `.venv`.
2. Installer `requirements.txt`.
3. Exécuter `uvicorn backend.main:app --reload`.
4. Vérifier `/api/health`.
5. Ouvrir `/` et exécuter le scénario de démonstration.

## Vérification d'un incident
1. Analyser un scénario critique.
2. Vérifier le `Correlation ID` dans Observability.
3. Vérifier l'incident dans Incident Center.
4. Approuver ou rejeter en tant que superviseur.
5. Après approbation, démarrer la maintenance simulée.
6. Compléter et vérifier (simulation), puis clôturer.

## Diagnostic rapide
- **ModuleNotFoundError** : vérifier que le venv est activé puis `pip install -r requirements.txt`.
- **Port 8000 occupé** : `uvicorn backend.main:app --reload --port 8010`.
- **DB verrouillée** : arrêter les instances Uvicorn/pytest qui utilisent `minepulse.db`, puis relancer.
- **Aucun incident** : seules les catégories HIGH/CRITICAL créent un incident ; tester le preset Critical.
- **Aucune trace** : vérifier que la requête `/api/analyze` a terminé et consulter le Correlation ID renvoyé.

## Limites opérationnelles
Prototype simulation uniquement. Ne pas connecter à une machine réelle ni utiliser les valeurs de démonstration comme consignes de sécurité.
