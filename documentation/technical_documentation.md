# 🎮 Documentation Technique - Retronova API

## Table des matières
1. [Architecture générale](#architecture-générale)
2. [Choix des technologies](#choix-des-technologies)
3. [Services et microservices](#services-et-microservices)
4. [Configuration Docker](#configuration-docker)
5. [Endpoints API](#endpoints-api)
6. [Sécurité et authentification](#sécurité-et-authentification)
7. [Base de données](#base-de-données)

---

## Architecture générale

Retronova API est une architecture microservices conçue pour gérer un réseau de bornes d'arcade. Le système est containerisé avec Docker et utilise une approche API-first pour assurer la scalabilité et la maintenabilité.

### Composants principaux
- **API Gateway** : Point d'entrée unique pour toutes les requêtes
- **Service d'authentification** : Gestion des utilisateurs via Firebase
- **Service de réservation** : Gestion des files d'attente et réservations
- **Service de scoring** : Enregistrement et récupération des scores
- **Service de paiement** : Gestion des tickets et codes promotionnels
- **Base de données PostgreSQL** : Stockage persistant
- **Cache Redis** : Amélioration des performances

---

## Choix des technologies

### Backend Framework : FastAPI
**Justification du choix :**
- **Performance exceptionnelle** : Basé sur Starlette et Pydantic, offre des performances comparables à Node.js
- **Typage fort** : Support natif de Python 3.6+ avec type hints
- **Documentation automatique** : Génération automatique de documentation OpenAPI/Swagger
- **Validation automatique** : Validation des données d'entrée et de sortie
- **Asynchrone natif** : Support complet de async/await pour une meilleure concurrence

### Base de données : PostgreSQL
**Justification du choix :**
- **Robustesse** : Base de données relationnelle mature et fiable
- **ACID compliance** : Garantit la cohérence des transactions critiques (paiements, réservations)
- **Extensibilité** : Support des extensions (PostGIS pour la géolocalisation future)
- **Performance** : Optimisations avancées pour les requêtes complexes
- **JSON natif** : Support du stockage et requêtage JSON pour la flexibilité

### ORM : SQLAlchemy
**Justification du choix :**
- **Maturité** : ORM Python le plus mature et stable
- **Flexibilité** : Permet du SQL brut quand nécessaire
- **Migrations** : Avec Alembic pour la gestion des schémas
- **Performance** : Lazy loading et optimisations de requêtes
- **Type safety** : Excellent support avec les type hints Python

### Authentification : Firebase Authentication
**Justification du choix :**
- **Sécurité enterprise** : Infrastructure Google avec sécurité de niveau bancaire
- **Multi-plateformes** : Support mobile (iOS/Android) et web
- **Providers multiples** : Email, Google, Facebook, Apple, etc.
- **Scalabilité automatique** : Pas de gestion d'infrastructure
- **Conformité** : GDPR et autres réglementations gérées par Google

### Cache : Redis
**Justification du choix :**
- **Performance** : Stockage en mémoire ultra-rapide
- **Structures de données** : Listes, sets, hashes pour différents cas d'usage
- **Persistence** : Options de sauvegarde sur disque
- **Pub/Sub** : Communication temps réel entre services
- **Clustering** : Scalabilité horizontale native

### Containerisation : Docker
**Justification du choix :**
- **Consistency** : Même environnement en dev, test et production
- **Isolation** : Chaque service dans son propre container
- **Scalabilité** : Facilite le déploiement et la montée en charge
- **CI/CD** : Intégration naturelle avec les pipelines de déploiement
- **Portabilité** : Déploiement sur any cloud provider

---

## Services et microservices

### Service Principal : API Gateway
**Responsabilités :**
- Routage des requêtes vers les services appropriés
- Authentification et autorisation centralisées
- Rate limiting et throttling
- Logging et monitoring centralisés
- Transformation des réponses et gestion des erreurs

### Service d'authentification
**Responsabilités :**
- Vérification des tokens Firebase
- Gestion des sessions utilisateurs
- Middleware d'autorisation
- Gestion des rôles (utilisateur, admin)

**Communication :**
- Synchrone via HTTP pour la vérification des tokens
- Cache Redis pour les sessions actives

### Service de gestion des utilisateurs
**Responsabilités :**
- CRUD des profils utilisateurs
- Gestion des amitiés et relations sociales
- Recherche d'utilisateurs
- Historique des activités

**Données gérées :**
- Profils utilisateurs (nom, email, pseudo, etc.)
- Relations d'amitié avec statuts
- Préférences et paramètres

### Service de réservation
**Responsabilités :**
- Gestion des files d'attente par borne
- Système de réservation avec codes de déverrouillage
- Calcul des positions en file
- Gestion des statuts de réservation

**Logique métier :**
- Déduction automatique des tickets lors de la réservation
- Gestion des réservations à 2 joueurs
- Système de timeout pour les réservations expirées
- Notification temps réel des changements de file

### Service de scoring
**Responsabilités :**
- Enregistrement des scores de parties
- Calcul des statistiques personnelles
- Classements et leaderboards
- Historique des performances

**Fonctionnalités :**
- Scores individuels et comparatifs
- Filtrage par jeu, borne, période
- Statistiques d'amis uniquement
- Détection des égalités et gagnants

### Service de gestion des tickets
**Responsabilités :**
- Vente de packs de tickets
- Gestion des soldes utilisateurs
- Codes promotionnels
- Historique des achats

**Transactions :**
- Validation des paiements
- Mise à jour atomique des soldes
- Gestion des échecs de transaction
- Audit trail complet

### Service de gestion des bornes et jeux
**Responsabilités :**
- Inventaire des bornes d'arcade
- Catalogue des jeux disponibles
- Configuration borne-jeu (slots)
- APIs spécifiques aux bornes physiques

**APIs bornes :**
- Authentification par clé API
- Récupération de la configuration
- Mise à jour des statuts en temps réel
- Files d'attente par borne

### Service d'administration
**Responsabilités :**
- Interface admin pour la gestion
- Statistiques et analytics
- Gestion des utilisateurs supprimés
- Configuration système

**Fonctionnalités admin :**
- Création et modification des bornes/jeux
- Gestion des codes promotionnels
- Ajustement des soldes utilisateurs
- Restauration de comptes supprimés

---

## Configuration Docker

### Architecture des containers

**Container Principal : retronova-api**
- Image : Python 3.11 Alpine
- Port exposé : 8000
- Variables d'environnement pour configuration
- Volume pour logs et uploads

**Container Base de données : retronova-db**
- Image : PostgreSQL 15
- Port exposé : 5432
- Volume persistant pour les données
- Configuration optimisée pour l'application

**Container Cache : retronova-redis**
- Image : Redis 7 Alpine
- Port exposé : 6379
- Configuration en mémoire avec persistence
- Optimisé pour les sessions et cache de requêtes

### Orchestration Docker Compose

**Services définis :**
- **api** : Service principal FastAPI
- **db** : Base de données PostgreSQL
- **redis** : Cache et sessions
- **nginx** : Reverse proxy (production)

**Réseaux :**
- Réseau interne pour communication inter-services
- Exposition sélective des ports nécessaires

**Volumes :**
- Volume persistant pour PostgreSQL
- Volume pour les logs applicatifs
- Volume pour les fichiers statiques

### Environnements multiples

**Développement :**
- Hot reload activé
- Logs verbeux
- Base de données locale
- Variables d'environnement en fichier

**Test :**
- Base de données éphémère
- Mock des services externes
- Coverage et profiling activés

**Production :**
- Optimisations de performance
- Logs structurés
- Health checks configurés
- Secrets gérés par orchestrateur

### Scalabilité et monitoring

**Horizontal scaling :**
- Services stateless pour faciliter la réplication
- Load balancer avec session affinity si nécessaire
- Base de données avec read replicas

**Monitoring intégré :**
- Health checks pour chaque service
- Metrics Prometheus exposées
- Logs centralisés avec ELK stack
- Alerting sur les métriques critiques

---

## Endpoints API

### Authentification (`/api/v1/auth`)

**POST /register**
- Inscription d'un nouvel utilisateur
- Validation des données avec Firebase
- Création du profil complet

**GET /me**
- Récupération du profil utilisateur connecté
- Informations complètes avec solde de tickets

### Gestion des utilisateurs (`/api/v1/users`)

**GET /search**
- Recherche d'utilisateurs par nom/pseudo
- Pagination et filtres
- Exclusion de l'utilisateur connecté

**GET /profile**
- Profil utilisateur complet
- Statistiques publiques

**PUT /profile**
- Mise à jour du profil
- Validation unicité pseudo/téléphone

### Gestion des amitiés (`/api/v1/friends`)

**GET /**
- Liste des amis confirmés
- Informations de profil basiques

**POST /request**
- Envoi d'une demande d'amitié
- Validation existence du destinataire

**GET /requests**
- Demandes d'amitié reçues
- Statut pending uniquement

**POST /accept/{friend_id}**
- Acceptation d'une demande
- Création de la relation bidirectionnelle

**POST /reject/{friend_id}**
- Refus d'une demande
- Suppression de la demande

**DELETE /{friend_id}**
- Suppression d'une amitié
- Nettoyage bidirectionnel

### Gestion des jeux (`/api/v1/games`)

**GET /**
- Liste de tous les jeux actifs
- Informations complètes (coût, joueurs)

**GET /{game_id}**
- Détails d'un jeu spécifique
- Statistiques et disponibilité

### Gestion des bornes (`/api/v1/arcades`)

**GET /**
- Liste des bornes actives
- Localisation et jeux disponibles

**GET /{arcade_id}**
- Détails d'une borne spécifique
- Configuration et statut

**GET /{arcade_id}/queue** (API Key required)
- File d'attente actuelle
- Informations pour les bornes physiques

**GET /{arcade_id}/config** (API Key required)
- Configuration de la borne
- Jeux assignés et paramètres

### Système de réservation (`/api/v1/reservations`)

**POST /**
- Création d'une réservation
- Déduction automatique des tickets
- Support joueur unique ou duo

**GET /my**
- Réservations de l'utilisateur connecté
- Historique complet avec statuts

**GET /{reservation_id}**
- Détails d'une réservation spécifique
- Accessible par les participants

**DELETE /{reservation_id}**
- Annulation d'une réservation
- Remboursement des tickets si en attente

### Gestion des scores (`/api/v1/scores`)

**POST /**
- Enregistrement d'un nouveau score
- Validation des participants et du jeu

**GET /**
- Liste des scores avec filtres
- Tri par date, jeu, borne
- Option amis uniquement

**GET /my-stats**
- Statistiques personnelles
- Performances par jeu
- Comparaisons avec amis

### Système de tickets (`/api/v1/tickets`)

**GET /offers**
- Offres de tickets disponibles
- Prix et quantités

**POST /purchase**
- Achat de tickets
- Intégration paiement et mise à jour solde

**GET /balance**
- Solde actuel de tickets
- Historique récent

**GET /purchase-history**
- Historique complet des achats
- Détails des transactions

### Codes promotionnels (`/api/v1/promos`)

**POST /use**
- Utilisation d'un code promo
- Validation et ajout de tickets

**GET /history**
- Historique des codes utilisés
- Détails des promotions

### Administration (`/api/v1/admin`)

**POST /arcades**
- Création d'une nouvelle borne
- Configuration initiale

**POST /games**
- Ajout d'un nouveau jeu
- Paramètres et coût

**POST /arcades/{arcade_id}/games**
- Association jeu-borne
- Configuration du slot

**POST /promo-codes**
- Création de codes promotionnels
- Limites d'usage et montants

**GET /promo-codes**
- Liste des codes créés
- Statistiques d'utilisation

**PUT /users/{user_id}/tickets**
- Ajustement manuel du solde
- Ajout ou retrait de tickets

**GET /users/deleted**
- Utilisateurs supprimés
- Options de restauration

**POST /users/{user_id}/restore**
- Restauration d'un compte supprimé

**GET /stats**
- Statistiques globales de la plateforme
- Métriques d'usage et revenus

---

## Sécurité et authentification

### Authentification Firebase

**Token JWT validation :**
- Vérification de la signature Google
- Validation de l'expiration et des claims
- Cache des tokens valides pour performance

**Middleware de sécurité :**
- Injection automatique de l'utilisateur dans le contexte
- Gestion des erreurs d'authentification
- Rate limiting par utilisateur

### Autorisation basée sur les rôles

**Rôles définis :**
- **User** : Accès aux fonctionnalités standard
- **Admin** : Accès aux endpoints d'administration

**Contrôle d'accès :**
- Décorateurs de fonction pour protection des routes
- Validation des permissions en fonction du contexte
- Logs d'audit pour les actions sensibles

### Sécurité API des bornes

**Authentification par clé API :**
- Clés uniques par borne
- Rotation régulière recommandée
- Validation stricte pour les endpoints critiques

**Endpoints protégés :**
- Configuration des bornes
- Files d'attente en temps réel
- Mise à jour des statuts

### Protection des données

**Validation des entrées :**
- Schemas Pydantic pour tous les endpoints
- Sanitization automatique des données
- Protection contre les injections

**Données sensibles :**
- Hachage sécurisé des informations critiques
- Pas de stockage des données de paiement
- Logs sans informations personnelles

---

## Base de données

### Architecture de données

**Soft delete pattern :**
- Champ deleted_at sur les entités principales
- Préservation de l'historique et des relations
- Possibilité de restauration

**Audit trail :**
- Champs created_at et updated_at automatiques
- Traçabilité complète des modifications
- Intégrité référentielle maintenue

### Optimisations de performance

**Index stratégiques :**
- Index sur les clés étrangères
- Index composites pour les requêtes fréquentes
- Index partiels pour les données actives

**Requêtes optimisées :**
- Eager loading pour éviter N+1
- Pagination systématique
- Cache des requêtes lourdes

### Migrations et versioning

**Gestion des schémas :**
- Migrations Alembic pour tous les changements
- Scripts de rollback pour chaque migration
- Tests de migration sur données de production

**Stratégie de déploiement :**
- Migrations backward compatible
- Déploiement blue-green pour zero downtime
- Validation automatique post-migration

Cette architecture garantit la scalabilité, la sécurité et la maintenabilité du système Retronova API tout en offrant une expérience utilisateur optimale.