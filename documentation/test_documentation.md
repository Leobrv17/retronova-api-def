# Tests Arcade API

Cette suite de tests couvre l'ensemble des fonctionnalités de l'API Arcade avec une approche de code propre et une couverture complète.

## 🗂️ Structure des tests

```
tests/
├── conftest.py              # Configuration et fixtures communes
├── test_auth.py            # Tests d'authentification Firebase
├── test_users.py           # Tests de gestion des utilisateurs
├── test_tickets.py         # Tests du système de tickets
├── test_games_arcades.py   # Tests des jeux et bornes d'arcade
├── test_friends.py         # Tests du système d'amis
├── test_reservations.py    # Tests des réservations de parties
├── test_scores.py          # Tests des scores et statistiques
├── test_promos.py          # Tests des codes promo
├── test_admin.py           # Tests des fonctionnalités admin
└── test_integration.py     # Tests d'intégration complets
```

## 🚀 Lancement des tests

### Tous les tests
```bash
pytest
```

### Tests avec couverture
```bash
pytest --cov=app --cov-report=html
```

### Tests spécifiques
```bash
# Tests d'un module spécifique
pytest tests/test_auth.py

# Tests d'une classe spécifique
pytest tests/test_users.py::TestUsers

# Tests d'une fonction spécifique
pytest tests/test_auth.py::TestAuth::test_register_user_success

# Tests avec marqueurs
pytest -m "not slow"              # Exclure les tests lents
pytest -m "integration"           # Seulement les tests d'intégration
pytest -m "unit"                  # Seulement les tests unitaires
```

### Tests en mode verbose
```bash
pytest -v --tb=long
```

## 🧪 Types de tests

### Tests unitaires
- Testent des fonctionnalités isolées
- Utilisent des mocks pour Firebase
- Base de données SQLite en mémoire
- Rapides à exécuter

### Tests d'intégration
- Testent des workflows complets
- Vérifient l'interaction entre composants
- Simulent des scénarios utilisateur réels

### Tests d'administration
- Vérifient les fonctionnalités admin
- Testent les autorisations et permissions
- Couvrent la gestion des données

## 🛠️ Configuration des tests

### Fixtures principales

- **`client`** : Client FastAPI TestClient
- **`db`** : Session de base de données de test
- **`mock_firebase`** : Mock des fonctions Firebase
- **`sample_user`** : Utilisateur de test avec données valides
- **`sample_admin_user`** : Administrateur de test
- **`sample_game`** : Jeu de test
- **`sample_arcade`** : Borne d'arcade de test
- **`sample_ticket_offer`** : Offre de tickets de test
- **`sample_promo_code`** : Code promo de test
- **`auth_headers_user`** : Headers d'authentification utilisateur
- **`auth_headers_admin`** : Headers d'authentification admin
- **`arcade_api_headers`** : Headers API pour les bornes

### Base de données de test

- SQLite en mémoire pour la rapidité
- Isolation complète entre les tests
- Rollback automatique après chaque test
- Création/destruction automatique des tables

### Mocking Firebase

```python
# Authentification automatiquement mockée
mock_firebase.return_value = {
    "uid": "test_uid",
    "email": "test@example.com", 
    "email_verified": True
}
```

## 📊 Couverture des tests

### Endpoints couverts

#### Authentification (`/api/v1/auth/`)
- ✅ Enregistrement utilisateur
- ✅ Récupération profil connecté
- ✅ Gestion erreurs Firebase

#### Utilisateurs (`/api/v1/users/`)
- ✅ Récupération profil
- ✅ Mise à jour profil
- ✅ Recherche utilisateurs
- ✅ Validation unicité

#### Tickets (`/api/v1/tickets/`)
- ✅ Liste des offres
- ✅ Achat de tickets (mock Stripe)
- ✅ Consultation solde
- ✅ Historique des achats

#### Jeux (`/api/v1/games/`)
- ✅ Liste des jeux
- ✅ Détails d'un jeu
- ✅ Gestion des erreurs

#### Bornes (`/api/v1/arcades/`)
- ✅ Liste des bornes
- ✅ Détails d'une borne
- ✅ File d'attente (avec clé API)
- ✅ Configuration borne

#### Amis (`/api/v1/friends/`)
- ✅ Liste des amis
- ✅ Demandes d'amitié
- ✅ Acceptation/rejet
- ✅ Suppression d'amis

#### Réservations (`/api/v1/reservations/`)
- ✅ Création réservations
- ✅ Liste des réservations
- ✅ Annulation
- ✅ File d'attente FIFO

#### Scores (`/api/v1/scores/`)
- ✅ Enregistrement scores (borne)
- ✅ Consultation scores
- ✅ Filtres (jeu, borne, amis)
- ✅ Statistiques personnelles

#### Codes promo (`/api/v1/promos/`)
- ✅ Utilisation codes
- ✅ Historique
- ✅ Limitations d'usage

#### Administration (`/api/v1/admin/`)
- ✅ Création bornes/jeux
- ✅ Gestion codes promo
- ✅ Modification tickets utilisateurs
- ✅ Statistiques globales

### Scénarios d'erreur couverts

- 🔒 Authentification manquante/invalide
- 📋 Validation des données d'entrée
- 🚫 Ressources non trouvées
- 💰 Soldes insuffisants
- 🔄 Contraintes d'unicité
- ⚠️ États invalides (ex: annulation réservation en cours)

## 🔧 Bonnes pratiques appliquées

### Structure des tests
- **AAA Pattern** : Arrange, Act, Assert
- **Tests isolés** : Chaque test est indépendant
- **Noms explicites** : Description claire de ce qui est testé
- **Fixtures réutilisables** : Éviter la duplication

### Gestion des données
- **Transactions isolées** : Rollback automatique
- **Données prévisibles** : Fixtures avec valeurs fixes
- **État propre** : Réinitialisation entre les tests

### Mocking intelligent
- **Firebase mocké** : Pas de dépendance externe
- **Clé API configurée** : Tests des bornes fonctionnels
- **Base de données locale** : Tests rapides

### Assertions détaillées
```python
# ✅ Assertion détaillée
assert response.status_code == 200
data = response.json()
assert data["tickets_received"] == 5
assert data["new_balance"] == 15

# ❌ Assertion trop générale
assert response.status_code == 200
```

## 🐛 Debugging des tests

### Affichage des données
```python
# Dans un test, pour débugger
import json
print(json.dumps(response.json(), indent=2))
```

### Tests en isolation
```python
# Lancer un seul test en mode debug
pytest -s tests/test_auth.py::TestAuth::test_register_user_success
```

### Logs de l'application
```python
# Activer les logs durant les tests
import logging
logging.basicConfig(level=logging.DEBUG)
```

## 📈 Métriques et performance

### Temps d'exécution
- Tests unitaires : < 1ms par test
- Tests d'intégration : < 100ms par test
- Suite complète : < 30 secondes

### Couverture attendue
- **Lignes de code** : > 90%
- **Branches** : > 85%
- **Fonctions** : > 95%

## 🔄 CI/CD Integration

Ces tests sont conçus pour s'intégrer facilement dans une pipeline CI/CD :

```yaml
# Exemple GitHub Actions
- name: Run Tests
  run: |
    pip install -r requirements-test.txt
    pytest --cov=app --cov-report=xml
    
- name: Upload Coverage
  uses: codecov/codecov-action@v3
```

## 🎯 Ajout de nouveaux tests

### Pour un nouvel endpoint :

1. **Ajouter les tests de base**
   ```python
   def test_endpoint_success(self, client, auth_headers):
       response = client.get("/api/v1/new-endpoint", headers=auth_headers)
       assert response.status_code == 200
   
   def test_endpoint_unauthorized(self, client):
       response = client.get("/api/v1/new-endpoint")
       assert response.status_code == 403
   ```

2. **Tester les cas d'erreur**
   ```python
   def test_endpoint_not_found(self, client, auth_headers):
       response = client.get("/api/v1/new-endpoint/99999", headers=auth_headers)
       assert response.status_code == 404
   ```

3. **Ajouter aux tests d'intégration**
   ```python
   def test_new_feature_workflow(self, client, db):
       # Test du workflow complet
       pass
   ```

Cette suite de tests garantit la fiabilité et la maintenabilité de l'API Arcade avec une approche professionnelle et des pratiques de développement propres.