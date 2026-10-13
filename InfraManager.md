# Projet : InfraManager

## 1. Objectif du projet

Créer une plateforme web professionnelle appelée **InfraManager**, destinée à centraliser la gestion, la supervision et l'administration d'une infrastructure informatique.

La plateforme doit permettre à un administrateur système/réseau de gérer depuis une interface unique :

* les infrastructures Proxmox ;
* les Datacenters ;
* les Nodes ;
* les Virtual Machines (VM) ;
* les Containers (LXC) ;
* les ressources CPU/RAM/Storage ;
* les sauvegardes ;
* les tâches de backup ;
* les repositories de sauvegarde ;
* les jobs Veeam ;
* les événements et erreurs ;
* les alertes ;
* les logs d'administration ;
* les utilisateurs et leurs permissions.

L'application doit être conçue comme une **plateforme modulaire et extensible**, afin de pouvoir ajouter plus tard d'autres systèmes de virtualisation, de backup ou de monitoring.

---

# 2. Stack technique

## Backend

* Python 3.12+
* FastAPI
* Pydantic
* SQLAlchemy
* Alembic
* PostgreSQL
* JWT Authentication
* WebSocket pour les informations temps réel
* HTTPX pour les appels API externes
* APScheduler ou Celery pour les tâches planifiées

## Frontend

* React
* TypeScript
* Vite
* React Router
* TanStack Query
* Axios
* Tailwind CSS
* shadcn/ui ou équivalent
* Recharts pour les graphiques
* Lucide Icons

## Infrastructure

* PostgreSQL
* Redis optionnel
* Docker / Docker Compose
* Nginx comme reverse proxy

## Intégrations

* Proxmox VE API
* Veeam API
* API REST génériques pour de futures intégrations

---

# 3. Architecture générale

Utiliser une architecture :

```text
                    ┌──────────────────────┐
                    │      React UI        │
                    │      Frontend        │
                    └──────────┬───────────┘
                               │
                               │ REST / WebSocket
                               ▼
                    ┌──────────────────────┐
                    │       FastAPI        │
                    │       Backend        │
                    └──────────┬───────────┘
                               │
              ┌────────────────┼────────────────┐
              │                │                │
              ▼                ▼                ▼
        PostgreSQL          Proxmox API       Veeam API
              │
              ▼
        Redis / Scheduler
```

Le backend doit servir de couche centrale entre l'interface utilisateur et les infrastructures externes.

Ne jamais exposer directement les credentials Proxmox ou Veeam au frontend.

---

# 4. Modules de l'application

Créer les modules suivants.

## Module 1 — Authentication

Créer un système d'authentification sécurisé.

Fonctionnalités :

* Login
* Logout
* JWT
* Refresh token
* Password hashing
* Gestion des sessions
* Protection des routes
* RBAC

Rôles :

```text
ADMIN
OPERATOR
VIEWER
```

Permissions possibles :

```text
infrastructure.read
infrastructure.write

proxmox.read
proxmox.write

backup.read
backup.write

veeam.read
veeam.write

users.read
users.write

audit.read
```

---

# 5. Dashboard principal

Créer un dashboard permettant d'avoir une vue globale de l'infrastructure.

Afficher :

### Infrastructure

* nombre de datacenters
* nombre de Proxmox nodes
* nombre de VMs
* nombre de containers
* nombre de Veeam servers
* nombre de repositories

### Santé

* Nodes online
* Nodes offline
* VMs running
* VMs stopped
* Storage warnings
* Backup failures
* Backup warnings

### Ressources

Afficher des graphiques :

```text
CPU Usage
RAM Usage
Disk Usage
Storage Usage
Network Traffic
```

### Backup

Afficher :

```text
Last successful backup
Failed backups
Running backups
Backup success rate
Backup storage usage
```

### Activité récente

Afficher les dernières activités :

```text
VM started
VM stopped
Backup completed
Backup failed
Node disconnected
User login
Configuration changed
```

---

# 6. Module Infrastructure

Créer une section :

```text
Infrastructure
```

Elle doit permettre de gérer plusieurs infrastructures.

Structure :

```text
Infrastructure
 ├── Datacenter
 │    ├── Cluster
 │    │    ├── Node
 │    │    │    ├── VM
 │    │    │    └── LXC
 │    │    └── Storage
 │    └── Network
```

Chaque infrastructure doit avoir :

* Name
* Description
* Location
* Environment
* Status
* Provider
* API endpoint
* Created date
* Updated date

Environments :

```text
Production
Staging
Development
Lab
```

---

# 7. Module Proxmox

Créer une intégration avec l'API Proxmox VE.

L'administrateur doit pouvoir ajouter un serveur Proxmox :

```text
Name
Hostname / IP
API URL
Port
Authentication method
API Token
Token Secret
TLS verification
```

Les credentials doivent être stockés de manière sécurisée.

---

# 8. Proxmox Dashboard

Créer une interface dédiée Proxmox.

Afficher :

```text
Datacenters
Clusters
Nodes
VMs
Containers
Storage
Networks
Tasks
```

Pour chaque Node :

```text
Hostname
Status
CPU
RAM
Disk
Uptime
Kernel
Version
Load
Network
```

Afficher des graphiques historiques :

```text
CPU usage
RAM usage
Disk usage
Network RX
Network TX
```

---

# 9. Gestion des VMs

Créer une page permettant de visualiser toutes les VMs.

Colonnes :

```text
VMID
Name
Node
Status
CPU
RAM
Disk
IP
Uptime
```

Actions :

```text
Start
Stop
Shutdown
Reboot
Console
Refresh
```

Les actions critiques doivent demander une confirmation.

Exemple :

```text
Are you sure you want to stop VM 105?
```

---

# 10. Gestion des containers LXC

Créer une interface similaire aux VMs.

Afficher :

```text
CTID
Name
Node
Status
CPU
RAM
Disk
IP
Uptime
```

Actions :

```text
Start
Stop
Shutdown
Reboot
```

---

# 11. Gestion Storage Proxmox

Afficher tous les storages :

```text
Storage Name
Node
Type
Total
Used
Free
Usage %
Status
```

Créer des alertes lorsque :

```text
Usage > 80%
Usage > 90%
Usage > 95%
```

Les seuils doivent être configurables.

---

# 12. Module Backup Management

Créer un module complet :

```text
Backup Management
```

Objectif :

Centraliser la supervision des sauvegardes.

Afficher :

```text
Backup Jobs
Backup History
Backup Status
Backup Repositories
Backup Storage
Failed Backups
Running Backups
```

Statuts :

```text
SUCCESS
WARNING
FAILED
RUNNING
CANCELLED
UNKNOWN
```

---

# 13. Backup Jobs

Créer une page :

```text
Backup Jobs
```

Chaque job doit contenir :

```text
Name
Source
Target
Schedule
Retention
Last Run
Next Run
Duration
Size
Status
```

Permettre de rechercher et filtrer les jobs.

Filtres :

```text
Status
Server
Date
Environment
Backup type
```

---

# 14. Backup History

Créer un historique des sauvegardes.

Afficher :

```text
Date
Job
Server
VM
Start Time
End Time
Duration
Backup Size
Transferred Data
Status
Error
```

Créer des graphiques :

```text
Backup success rate
Backup failures
Backup volume
Backup duration
```

---

# 15. Module Veeam

Créer une intégration Veeam API.

Permettre d'ajouter un serveur Veeam :

```text
Name
Hostname
API URL
Port
Credentials
TLS configuration
```

Synchroniser :

```text
Jobs
Sessions
Repositories
Servers
Backup files
Restore points
Errors
Warnings
```

Afficher un dashboard Veeam :

```text
Total Jobs
Running Jobs
Successful Jobs
Failed Jobs
Warning Jobs
Repository Capacity
Repository Free Space
```

---

# 16. Veeam Jobs

Afficher :

```text
Job Name
Type
Status
Last Run
Next Run
Duration
Transferred
Backup Size
```

Permettre d'afficher les détails d'une exécution.

---

# 17. Backup Repository

Créer une page dédiée aux repositories.

Afficher :

```text
Repository
Type
Total Capacity
Used
Free
Usage %
Status
Last Backup
```

Afficher une barre de progression pour l'utilisation.

Créer automatiquement une alerte si :

```text
> 80%
> 90%
> 95%
```

---

# 18. Module Alerting

Créer un système centralisé d'alertes.

Types d'alertes :

```text
NODE_OFFLINE
VM_OFFLINE
HIGH_CPU
HIGH_RAM
HIGH_STORAGE
BACKUP_FAILED
BACKUP_WARNING
REPOSITORY_FULL
API_ERROR
AUTHENTICATION_ERROR
```

Chaque alerte doit contenir :

```text
Severity
Title
Description
Source
Resource
Timestamp
Status
```

Severities :

```text
INFO
WARNING
CRITICAL
```

---

# 19. Notifications

Préparer l'architecture pour :

```text
Email
Telegram
Discord
Webhook
```

Créer un système de notification configurable.

Exemple :

```text
Backup failed
     ↓
Alert Engine
     ↓
Email
Telegram
Webhook
```

---

# 20. Module Logs / Audit

Créer un système d'audit.

Enregistrer :

```text
User
Action
Resource
Resource ID
IP Address
Timestamp
Result
```

Exemples :

```text
User admin logged in
User admin started VM 105
User admin stopped VM 105
User admin added Proxmox server
User admin modified backup configuration
```

Les logs d'audit ne doivent pas être supprimables par les utilisateurs normaux.

---

# 21. API Backend

Créer une API REST structurée.

Exemple :

```text
/api/v1/auth
/api/v1/users

/api/v1/infrastructures
/api/v1/datacenters
/api/v1/nodes

/api/v1/proxmox
/api/v1/proxmox/nodes
/api/v1/proxmox/vms
/api/v1/proxmox/containers
/api/v1/proxmox/storage

/api/v1/backups
/api/v1/backups/jobs
/api/v1/backups/history
/api/v1/backups/repositories

/api/v1/veeam
/api/v1/veeam/jobs
/api/v1/veeam/repositories
/api/v1/veeam/sessions

/api/v1/alerts
/api/v1/notifications

/api/v1/audit
```

Utiliser des schemas Pydantic pour toutes les entrées et sorties.

---

# 22. Synchronisation

Mettre en place un système de synchronisation périodique.

Exemple :

```text
Every 30 seconds
        ↓
Proxmox API
        ↓
Collect metrics
        ↓
Store data
        ↓
Update dashboard
```

Pour Veeam :

```text
Every 1-5 minutes
        ↓
Veeam API
        ↓
Synchronize jobs
        ↓
Synchronize sessions
        ↓
Synchronize repositories
```

La fréquence doit être configurable.

---

# 23. WebSocket

Utiliser WebSocket pour les informations nécessitant une mise à jour temps réel.

Exemples :

```text
VM status
Node status
Backup status
Alerts
Tasks
```

Le dashboard doit pouvoir afficher :

```text
Backup running...
CPU 72%
RAM 64%
Node online
```

sans nécessiter un refresh manuel de la page.

---

# 24. Base de données

Créer un modèle PostgreSQL propre.

Tables principales :

```text
users
roles
permissions

infrastructures
datacenters
cl
```
