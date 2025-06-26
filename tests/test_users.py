# import pytest
#
#
# class TestUsers:
#     """Tests pour les endpoints utilisateurs."""
#
#     def test_get_my_profile(self, client, auth_headers_user, sample_user):
#         """Test de récupération du profil utilisateur."""
#         response = client.get("/api/v1/users/me", headers=auth_headers_user)
#
#         assert response.status_code == 200
#         data = response.json()
#         assert data["id"] == sample_user.id
#         assert data["email"] == sample_user.email
#         assert data["pseudo"] == sample_user.pseudo
#         assert data["nom"] == sample_user.nom
#         assert data["prenom"] == sample_user.prenom
#         assert data["tickets_balance"] == sample_user.tickets_balance
#
#     def test_update_my_profile_success(self, client, auth_headers_user, sample_user):
#         """Test de mise à jour du profil."""
#         update_data = {
#             "nom": "NouveauNom",
#             "prenom": "NouveauPrenom"
#         }
#
#         response = client.put("/api/v1/users/me", json=update_data, headers=auth_headers_user)
#
#         assert response.status_code == 200
#         data = response.json()
#         assert data["nom"] == "NouveauNom"
#         assert data["prenom"] == "NouveauPrenom"
#         assert data["email"] == sample_user.email  # Inchangé
#
#     def test_update_my_profile_duplicate_pseudo(self, client, auth_headers_user, sample_user, db):
#         """Test de mise à jour avec pseudo déjà utilisé."""
#         # Créer un autre utilisateur
#         from app.models import User
#         other_user = User(
#             firebase_uid="other_uid",
#             email="other@example.com",
#             nom="Other",
#             prenom="User",
#             pseudo="otheruser",
#             date_naissance="1990-01-01",
#             numero_telephone="0111111111",
#             tickets_balance=0
#         )
#         db.add(other_user)
#         db.commit()
#
#         update_data = {
#             "pseudo": "otheruser"  # Pseudo déjà pris
#         }
#
#         response = client.put("/api/v1/users/me", json=update_data, headers=auth_headers_user)
#
#         assert response.status_code == 400
#         assert "pseudo est déjà utilisé" in response.json()["detail"]
#
#     def test_update_my_profile_duplicate_phone(self, client, auth_headers_user, sample_user, db):
#         """Test de mise à jour avec téléphone déjà utilisé."""
#         # Créer un autre utilisateur
#         from app.models import User
#         other_user = User(
#             firebase_uid="other_uid2",
#             email="other2@example.com",
#             nom="Other2",
#             prenom="User2",
#             pseudo="otheruser2",
#             date_naissance="1990-01-01",
#             numero_telephone="0222222222",
#             tickets_balance=0
#         )
#         db.add(other_user)
#         db.commit()
#
#         update_data = {
#             "numero_telephone": "0222222222"  # Téléphone déjà pris
#         }
#
#         response = client.put("/api/v1/users/me", json=update_data, headers=auth_headers_user)
#
#         assert response.status_code == 400
#         assert "numéro de téléphone est déjà utilisé" in response.json()["detail"]
#
#     def test_search_users_success(self, client, auth_headers_user, sample_user, db):
#         """Test de recherche d'utilisateurs."""
#         # Créer des utilisateurs pour la recherche
#         from app.models import User
#         users_to_create = [
#             User(
#                 firebase_uid="search1",
#                 email="search1@example.com",
#                 nom="Dupont",
#                 prenom="Jean",
#                 pseudo="jeandupont",
#                 date_naissance="1990-01-01",
#                 numero_telephone="0111111111"
#             ),
#             User(
#                 firebase_uid="search2",
#                 email="search2@example.com",
#                 nom="Martin",
#                 prenom="Marie",
#                 pseudo="mariemartin",
#                 date_naissance="1990-01-01",
#                 numero_telephone="0222222222"
#             )
#         ]
#
#         for user in users_to_create:
#             db.add(user)
#         db.commit()
#
#         # Recherche par nom
#         response = client.get("/api/v1/users/search?q=Dupont", headers=auth_headers_user)
#
#         assert response.status_code == 200
#         data = response.json()
#         assert len(data) == 1
#         assert data[0]["nom"] == "Dupont"
#         assert data[0]["pseudo"] == "jeandupont"
#
#     def test_search_users_by_pseudo(self, client, auth_headers_user, sample_user, db):
#         """Test de recherche par pseudo."""
#         from app.models import User
#         search_user = User(
#             firebase_uid="search3",
#             email="searchpseudo@example.com",
#             nom="Recherche",
#             prenom="Pseudo",
#             pseudo="pseudotest",
#             date_naissance="1990-01-01",
#             numero_telephone="0333333333"
#         )
#         db.add(search_user)
#         db.commit()
#
#         response = client.get("/api/v1/users/search?q=pseudo", headers=auth_headers_user)
#
#         assert response.status_code == 200
#         data = response.json()
#         assert len(data) == 1
#         assert data[0]["pseudo"] == "pseudotest"
#
#     def test_search_users_empty_query(self, client, auth_headers_user):
#         """Test de recherche avec query trop courte."""
#         response = client.get("/api/v1/users/search?q=a", headers=auth_headers_user)
#
#         assert response.status_code == 422  # Validation error
#
#     def test_search_users_no_results(self, client, auth_headers_user):
#         """Test de recherche sans résultats."""
#         response = client.get("/api/v1/users/search?q=inexistant", headers=auth_headers_user)
#
#         assert response.status_code == 200
#         data = response.json()
#         assert len(data) == 0
#
#     def test_search_users_excludes_self(self, client, auth_headers_user, sample_user):
#         """Test que la recherche exclut l'utilisateur actuel."""
#         response = client.get(f"/api/v1/users/search?q={sample_user.pseudo}", headers=auth_headers_user)
#
#         assert response.status_code == 200
#         data = response.json()
#         # L'utilisateur ne doit pas être dans les résultats de sa propre recherche
#         user_ids = [user["id"] for user in data]
#         assert sample_user.id not in user_ids
#
#     def test_unauthorized_access(self, client):
#         """Test d'accès non autorisé aux endpoints utilisateurs."""
#         endpoints = [
#             "/api/v1/users/me",
#             "/api/v1/users/search?q=test"
#         ]
#
#         for endpoint in endpoints:
#             response = client.get(endpoint)
#             assert response.status_code == 403