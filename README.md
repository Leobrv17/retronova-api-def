# Arcade API

API FastAPI professionnelle pour la gestion de bornes d'arcade connectées.

## 🚀 Fonctionnalités

- **Authentification Firebase** : Double authentification (utilisateurs finaux + administrateurs)
- **Gestion des utilisateurs** : Profils complets avec système d'amis
- **Système de tickets** : Achat simulé (mock Stripe) avec 3 offres
- **Réservations de parties** : File d'attente FIFO avec codes de déverrouillage
- **Scoreboards** : Enregistrement et consultation des scores avec filtres
- **Codes promo** : Système flexible avec différents types d'utilisation
- **Interface admin** : Gestion complète des bornes, jeux et utilisateurs

## 🏗️ Architecture

```
arcade_api/
├── app/
│   ├── core/          # Configuration, DB, sécurité
│   ├── models/        # Modèles SQLAlchemy
│   ├── schemas/       # Schémas Pydantic
│   ├── api/           # Routes et dépendances
│   ├── services/      # Logique métier
│   └── utils/         # Utilitaires
├── tests/             # Tests unitaires
├── alembic/           # Migrations DB
└── docker/            # Fichiers Docker
```

## 🛠️ Installation

### Prérequis

- Python 3.11+
- Docker & Docker Compose
- Comptes Firebase (2 projets : utilisateurs + admin)

### Configuration

1. **Cloner le projet**
```bash
git clone <repo>
cd arcade_api
```

2. **Configurer l'environnement**
```bash
cp .env.example .env
```

3. **Remplir le fichier .env** avec vos credentials Firebase et autres paramètres

4. **Lancer avec Docker**
```bash
docker-compose up --build
```

L'API sera disponible sur `http://localhost:8000`

## 📚 Documentation API

Une fois l'API lancée, accédez à :
- Swagger UI : `http://localhost:8000/docs`
- ReDoc : `http://localhost:8000/redoc`

## 🔐 Authentification

### Utilisateurs finaux
```http
Authorization: Bearer <firebase_user_token>
```

### Administrateurs
```http
Authorization: Bearer <firebase_admin_token>
```

### Bornes d'arcade
```http
X-API-Key: <arcade_api_key>
```

## 📋 Endpoints principaux

### Authentification
- `POST /api/v1/auth/register` - Enregistrement utilisateur
- `GET /api/v1/auth/me` - Profil utilisateur

### Utilisateurs
- `GET /api/v1/users/me` - Mon profil
- `PUT /api/v1/users/me` - Modifier mon profil
- `GET /api/v1/users/search` - Rechercher des utilisateurs

### Amis
- `GET /api/v1/friends/` - Liste des amis
- `POST /api/v1/friends/request` - Envoyer une demande d'ami
- `PUT /api/v1/friends/request/{id}/accept` - Accepter une demande

### Tickets
- `GET /api/v1/tickets/offers` - Offres de tickets
- `POST /api/v1/tickets/purchase` - Acheter des tickets
- `GET /api/v1/tickets/balance` - Solde actuel

### Bornes & Jeux
- `GET /api/v1/arcades/` - Liste des bornes
- `GET /api/v1/arcades/{id}/queue` - File d'attente (borne)
- `GET /api/v1/games/` - Liste des jeux

### Réservations
- `POST /api/v1/reservations/` - Créer une réservation
- `GET /api/v1/reservations/` - Mes réservations
- `DELETE /api/v1/reservations/{id}` - Annuler une réservation

### Scores
- `POST /api/v1/scores/` - Enregistrer un score (borne)
- `GET /api/v1/scores/` - Consulter les scores (avec filtres)
- `GET /api/v1/scores/my-stats` - Mes statistiques

### Codes promo
- `POST /api/v1/promos/use` - Utiliser un code promo
- `GET /api/v1/promos/history` - Historique des codes utilisés

### Administration
- `POST /api/v1/admin/arcades/` - Créer une borne
- `POST /api/v1/admin/games/` - Créer un jeu
- `POST /api/v1/admin/promo-codes/` - Créer un code promo
- `PUT /api/v1/admin/users/tickets` - Modifier les tickets d'un utilisateur
- `GET /api/v1/admin/stats` - Statistiques globales

## 🗄️ Base de données

La base de données PostgreSQL est automatiquement configurée avec Docker Compose.

### Migrations

```bash
# Créer une migration
alembic revision --autogenerate -m "Description"

# Appliquer les migrations
alembic upgrade head
```

### Données d'exemple

Le fichier `docker/init-db.sql` contient des données d'exemple :
- 3 offres de tickets (1€→2€, 10€→15€, 20€→20€)
- 4 jeux d'arcade
- 2 bornes avec jeux assignés

## 🔧 Développement

### Structure des modèles

Tous les modèles héritent de `BaseModel` qui fournit :
- `id` : Clé primaire auto-incrémentée
- `created_at`, `updated_at` : Timestamps automatiques
- `deleted_at`, `is_deleted` : Soft delete

### Bonnes pratiques respectées

- **Séparation des responsabilités** : Routes, services, modèles séparés
- **Validation Pydantic** : Schémas stricts pour les entrées/sorties
- **Gestion d'erreurs** : HTTP exceptions appropriées
- **Code propre** : Fonctions courtes, noms explicites
- **Documentation** : Docstrings et commentaires

## 🐳 Docker

### Services

- **api** : Application FastAPI
- **db** : PostgreSQL 15

### Volumes persistants

- `postgres_data` : Données PostgreSQL

## 🚦 Tests

```bash
# Lancer les tests
pytest

# Avec couverture
pytest --cov=app tests/
```

## 📈 Monitoring

L'API expose des endpoints de santé :
- `GET /health` - Vérification de l'état de l'API

## 🔒 Sécurité

- Authentification Firebase Admin SDK
- Validation des tokens sur chaque requête protégée
- Clés API pour les bornes d'arcade
- Soft delete pour la conformité RGPD
- Validation stricte des entrées

## 🌟 Fonctionnalités avancées

### Système de file d'attente FIFO
Les réservations sont traitées dans l'ordre chronologique de création.

### Codes promo flexibles
- Usage unique global
- Usage unique par utilisateur
- Limite d'utilisation globale configurable

### Gestion des amis avec double consentement
Système d'invitation + acceptation obligatoire.

### Scores et statistiques
Système complet de scores avec filtres par jeu, borne et amis.

## 📞 Support

Pour toute question ou problème, consultez la documentation Swagger intégrée ou créez une issue.

## 📄 Licence

Ce projet est sous licence MIT.