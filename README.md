# MBOOST CV–DAO — automatisation 0.3

Service Python pour déposer un DAO et les pièces d'une personne, extraire les documents, analyser les exigences et produire un dossier de travail. Une file SQLite et un worker indépendant permettent de fermer le navigateur pendant le traitement sur le VPS.

## Parcours

1. Renseigner l'entreprise soumissionnaire et la personne ; déposer le DAO et ses pièces.
2. L'interface enregistre le travail dans la file persistante.
3. Le worker lit les DOC/DOCX/PDF/TXT, applique l'OCR aux pages peu textuelles et appelle le modèle configuré.
4. Le service vérifie les citations et distingue les faits documentés, déclarations et données à compléter.
5. Télécharger le ZIP contenant rapport JSON et brouillon PER-2. Obtenir les confirmations, signatures et pièces restantes avant dépôt.

Pour une équipe, le registre JSON affecte explicitement les fichiers à chaque personne. Les scans collectifs doivent être séparés par personne avant affectation. Le PER-1 regroupe les personnes confirmées.

## Démarrage local

Installer Python 3.12+, antiword, poppler-utils, tesseract-ocr, les langues fra et eng.

```bash
python -m venv .venv
.venv/bin/pip install -r requirements.txt
cp .env.example .env
```

Compléter `.env` côté serveur avec un fournisseur (`openai` ou `anthropic`), son modèle et sa clé API. Dans deux terminaux :

```bash
.venv/bin/uvicorn app:app --host 127.0.0.1 --port 8012
.venv/bin/python worker.py
```

Ouvrir `http://localhost:8012`. Les coûts API relèvent du fournisseur configuré. Aucune clé n'est incluse dans le code ou l'interface.

## VPS Hostinger

Voir [deploy/README.md](deploy/README.md). L'installation démarre deux services système isolés et liés à localhost. Le script conserve la configuration existante. Le worker n'exécute aucune commande issue d'un document.

Le mode PUBLIC_MODE=1 refuse les requêtes de données tant qu'un compte n'est pas configuré. Tout accès externe doit passer par HTTPS. Le mode privé par tunnel SSH est disponible sans publication publique.

## API

- `POST /api/jobs` : dépôt multipart, réponse 202 et job_id.
- `GET /api/jobs/{id}` : état queued/running/done/blocked/failed/interrupted.
- `POST /api/jobs/{id}/retry` : relance explicite d'un travail bloqué, échoué ou interrompu.
- `GET /api/cases` : dossiers ; `GET /api/cases/{id}/report` : rapport JSON.
- `GET /api/cases/{id}/bundle` : ZIP de travail, disponible après analyse.
- `POST /api/team/analyze` : DAO commun, documents individuels et registre JSON.
- `POST /api/team/per1` : JSON avec company et case_ids ; confirmations individuelles requises.
- `/api/analyze` reste disponible pour compatibilité en traitement synchrone.

Registre équipe :
```json
[{"name":"NOM Prénoms","company":"ENTREPRISE","roles":["Chef de chantier"],"documents":["diplome_personne.pdf","cv_personne.pdf"]}]
```

## Contrôles et limites

19 tests couvrent notamment la file, l'export ZIP, le blocage sans fournisseur, l'accès privé, les citations, les périodes et l'affectation documentaire. Le test de pipeline remplace l'appel modèle par une réponse simulée ; il ne valide pas les performances du modèle réel.

Le lecteur DOC/DOCX indique une pagination logique, différente des pages imprimées. L'OCR nécessite une relecture visuelle pour les noms, dates et cachets. Les signatures ne sont pas générées. Les formulaires exportés sont génériques et doivent être confrontés au DAO officiel.

Les emplois, projets et périodes ne sont pas déduits d'une date de diplôme. Un dossier incomplet génère des questions et un brouillon marqué. Le module compliance contient des fonctions de contrôle de périodes ; il n'est pas un verdict réglementaire automatisé.

Les appels interrompus ne sont pas relancés silencieusement : un appel peut déjà avoir été facturé. Le service est prévu pour un propriétaire unique. Le chiffrement applicatif des fichiers au repos, les rôles multiclients, WhatsApp, les webhooks sortants et la soumission d'offres ne sont pas implémentés.

Tests : `python -m unittest -v`.

## Mode local sans API

MODEL_PROVIDER=local active un inventaire documentaire sans appel facturé. Le ZIP comprend aussi les textes extraits. Les passages sont proposés à la revue ; aucun verdict de conformité ou affectation automatique ne provient de ce mode. La configuration IA reste nécessaire pour une analyse sémantique.
