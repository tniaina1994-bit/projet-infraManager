# AGENTS.md – projet-infraManager

## Repo state
- `InfraManager.md` = spec produit (français, tronquée en section 24 — queue inachevée, pas un choix délibéré). C'est la source de vérité pour périmètre et stack ; code et identifiants restent en anglais.
- Scaffolding en place : `backend/` (FastAPI) + `frontend/` (React/Vite) + `docker-compose.yml` (Postgres). Pas de CI.
- Ports imposés par cette machine (d'autres projets occupent 8000/8001/8002 et 5173-5175) : **backend = 8010, frontend dev = 5180**.

## Commandes (vérifiées)
```bash
# setup (une fois)
/usr/bin/python3 -m venv .venv          # PAS python3 : /usr/local/bin/python3 (3.14.7) n'a pas de module _sqlite3 → pytest échoue
.venv/bin/pip install -r backend/requirements.txt
cp .env.example .env                    # remplir PROXMOX_TOKEN_SECRET, SECRET_KEY, ENCRYPTION_KEY
cd frontend && npm install

# base de données — deux options
# A) la config actuelle (.env) : cluster Postgres en espace utilisateur, aucun root/docker requis
/usr/lib/postgresql/18/bin/pg_ctl -D ~/.local/share/pg-inframanager -l /tmp/pg-inframanager.log start   # port 5433, user/db inframanager
# B) alternative Docker (nécessite le groupe docker : `sudo usermod -aG docker $USER`)
docker compose up -d db   # alors mettre DATABASE_URL=...@localhost:5432/inframanager dans .env

cd backend && ../.venv/bin/alembic upgrade head   # après `alembic revision --autogenerate -m initial`
cd backend && ../.venv/bin/python -m app.seed     # idempotent : roles/permissions/admin/proxmox
# alembic doit être lancé depuis backend/ (script_location est relatif au CWD)

# exécution
cd backend && ../.venv/bin/uvicorn app.main:app --port 8010 --reload
cd frontend && npm run dev              # http://localhost:5180 (proxy /api -> 8010)

# vérification
cd backend && ../.venv/bin/python -m pytest -q    # 5 tests, SQLite in-memory, pas de Postgres requis
cd frontend && npm run build             # tsc --noEmit + vite build
cd frontend && npm run typecheck
```
- `.vscode/launch.json` : configs F5 (uvicorn debug/reload, pytest, alembic, vite) + compounds « ▶ Full stack ». En cas d'`Address already in use`, ce sont des processus orphelins : `ss -ltnp | grep ':8010\|:5180'` puis `kill <pid>`.
- Pas d'ordre lint/typecheck imposé : `npm run build` inclut déjà le typecheck ; le backend n'a pas de linter configuré.
- `alembic upgrade head` n'est pas obligatoire au premier démarrage : si la table `users` manque, le bootstrap crée le schéma + seed automatiquement (env `AUTO_CREATE_TABLES=false` pour désactiver). Alembic reste la vérité pour l'évolution du schéma.

## Architecture
- **Seul le backend parle à Proxmox/Veeam** — jamais le frontend. Secrets chiffrés en base (Fernet, clé = `ENCRYPTION_KEY` ou dérivée de `SECRET_KEY`).
- Toutes les routes REST sous `/api/v1/...` (`app/api/v1/router.py`), schémas Pydantic dans `app/schemas/__init__.py`.
- RBAC : rôles et permissions exacts de la spec dans `app/core/permissions.py` (`require_permission("proxmox.write")` etc.) — ne pas inventer de permissions.
- Syncs périodiques via APScheduler (`app/services/scheduler.py`) : Proxmox toutes les `PROXMOX_SYNC_SECONDS` (30 s), Veeam `VEEAM_SYNC_SECONDS` (300 s) ; push WebSocket sur `/api/v1/ws?token=<access JWT>`.
- Seuils d'alerte storage (80/90/95) lisibles en DB (`settings`) avec fallback env — pas de valeurs hardcodées.
- Enums fermés de la spec : statuts backup, sévérités, environments — réutiliser les valeurs littérales existantes.

## Proxmox (environnement de test)
- Serveur : `https://192.168.10.90:8006`, token `root@pam!inframanager` créé pour le projet, seedé depuis `.env` (`PROXMOX_*`).
- Recréation/rotation d'un token : `PVE_PASSWORD=... ./scripts/create-proxmox-token.sh [url] [userid] [tokenid]` (script testé ; gère les pièges d'API listés ci-dessous).
- Cert auto-signé → `PROXMOX_TLS_VERIFY=false` dans `.env` **et** colonne `proxmox_servers.tls_verify` (le seed ne met pas à jour une ligne existante).
- Piège API Proxmox 9.1 : la création de token n'est **pas** sur `/access/token` mais sur
  `POST /api2/json/access/users/{userid}/token/{tokenid}` ; header d'auth écrit **`CSRFPreventionToken`** (pas `CSRFProtection`). Vérifier avec `GET /api2/json/version`.
- Pièges de `/cluster/resources` (utilisé par `app/services/sync.py`) : les entrées `node` n'ont **pas** de champ `name` (hostname = clé `node`), le storage expose `disk`/`maxdisk` (pas `used`/`total`) et le hostname = clé `storage`. Les items ne sont pas ordonnés : traiter les nodes avant qemu/lxc.
- Les IP des VM ne sont pas dans `/cluster/resources` : colonne `ip` des VM/LXC restera vide tant que l'agent QEMU n'est pas interrogé.
- `ctid` est un nom de colonne système PostgreSQL : la colonne DB s'appelle `ctid_value`, l'attribut/le champ API reste `ctid`.

## Pièges locaux
- Ports : ne pas reprendre 8000/5173 (ProjetATS, projet-tool-network…), utiliser 8010/5180.
- `.env` lu depuis la racine du repo quel que soit le CWD (config.py) — pas besoin de copier le fichier dans `backend/`.
- Tests : `SCHEDULER_ENABLED=false` forcé, `get_db` overridé sur SQLite — un test qui touche au réseau réel échouera.
- Symptôme « app lente, requêtes qui n'aboutissent jamais » = backend mort mais socket TCP encore ouverte (combo debugpy + uvicorn `--reload` : l'enfant meurt, le parent garde le LISTEN). Vérifier `ss -ltn` → `recv-q` non nul sur :8010 → relancer la session F5 (ne pas utiliser `pkill -f 'port 8010'`).
- `docker compose` (profil par défaut) ne monte que `db` ; `--profile full` ajoute backend+frontend conteneurisés.
