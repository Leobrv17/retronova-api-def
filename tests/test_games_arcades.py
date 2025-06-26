# import pytest
#
#
# class TestGames:
#     """Tests pour les endpoints de jeux."""
#
#     def test_get_games(self, client, sample_game):
#         """Test de récupération de la liste des jeux."""
#         response = client.get("/api/v1/games/")
#
#         assert response.status_code == 200
#         data = response.json()
#         assert len(data) >= 1
#
#         # Vérifier que notre jeu de test est présent
#         game_found = False
#         for game in data:
#             if game["id"] == sample_game.id:
#                 assert game["nom"] == sample_game.nom
#                 assert game["description"] == sample_game.description
#                 assert game["min_players"] == sample_game.min_players
#                 assert game["max_players"] == sample_game.max_players
#                 assert game["ticket_cost"] == sample_game.ticket_cost
#                 game_found = True
#                 break
#
#         assert game_found, "Le jeu de test n'a pas été trouvé"
#
#     def test_get_game_by_id(self, client, sample_game):
#         """Test de récupération d'un jeu par ID."""
#         response = client.get(f"/api/v1/games/{sample_game.id}")
#
#         assert response.status_code == 200
#         data = response.json()
#         assert data["id"] == sample_game.id
#         assert data["nom"] == sample_game.nom
#         assert data["description"] == sample_game.description
#         assert data["min_players"] == sample_game.min_players
#         assert data["max_players"] == sample_game.max_players
#         assert data["ticket_cost"] == sample_game.ticket_cost
#
#     def test_get_game_not_found(self, client):
#         """Test de récupération d'un jeu inexistant."""
#         response = client.get("/api/v1/games/99999")
#
#         assert response.status_code == 404
#         assert "Jeu non trouvé" in response.json()["detail"]
#
#
# class TestArcades:
#     """Tests pour les endpoints de bornes d'arcade."""
#
#     def test_get_arcades(self, client, sample_arcade):
#         """Test de récupération de la liste des bornes."""
#         response = client.get("/api/v1/arcades/")
#
#         assert response.status_code == 200
#         data = response.json()
#         assert len(data) >= 1
#
#         # Vérifier que notre borne de test est présente
#         arcade_found = False
#         for arcade in data:
#             if arcade["id"] == sample_arcade.id:
#                 assert arcade["nom"] == sample_arcade.nom
#                 assert arcade["description"] == sample_arcade.description
#                 assert arcade["localisation"] == sample_arcade.localisation
#                 assert arcade["latitude"] == sample_arcade.latitude
#                 assert arcade["longitude"] == sample_arcade.longitude
#                 arcade_found = True
#                 break
#
#         assert arcade_found, "La borne de test n'a pas été trouvée"
#
#     def test_get_arcade_by_id(self, client, sample_arcade):
#         """Test de récupération d'une borne par ID."""
#         response = client.get(f"/api/v1/arcades/{sample_arcade.id}")
#
#         assert response.status_code == 200
#         data = response.json()
#         assert data["id"] == sample_arcade.id
#         assert data["nom"] == sample_arcade.nom
#         assert data["description"] == sample_arcade.description
#         assert data["localisation"] == sample_arcade.localisation
#         assert data["latitude"] == sample_arcade.latitude
#         assert data["longitude"] == sample_arcade.longitude
#
#     def test_get_arcade_not_found(self, client):
#         """Test de récupération d'une borne inexistante."""
#         response = client.get("/api/v1/arcades/99999")
#
#         assert response.status_code == 404
#         assert "Borne d'arcade non trouvée" in response.json()["detail"]
#
#     def test_get_arcade_with_games(self, client, sample_arcade, sample_game, db):
#         """Test de récupération d'une borne avec ses jeux."""
#         # Associer le jeu à la borne
#         from app.models import ArcadeGame
#         arcade_game = ArcadeGame(
#             arcade_id=sample_arcade.id,
#             game_id=sample_game.id,
#             slot_number=1
#         )
#         db.add(arcade_game)
#         db.commit()
#
#         response = client.get(f"/api/v1/arcades/{sample_arcade.id}")
#
#         assert response.status_code == 200
#         data = response.json()
#         assert "games" in data
#         assert len(data["games"]) == 1
#         assert data["games"][0]["id"] == sample_game.id
#         assert data["games"][0]["slot_number"] == 1
#
#     def test_get_arcade_queue_unauthorized(self, client, sample_arcade):
#         """Test d'accès à la file sans clé API."""
#         response = client.get(f"/api/v1/arcades/{sample_arcade.id}/queue")
#
#         assert response.status_code == 401
#         assert "Clé API borne invalide" in response.json()["detail"]
#
#     def test_get_arcade_queue_with_api_key(self, client, sample_arcade, arcade_api_headers):
#         """Test d'accès à la file avec clé API valide."""
#         response = client.get(f"/api/v1/arcades/{sample_arcade.id}/queue", headers=arcade_api_headers)
#
#         assert response.status_code == 200
#         data = response.json()
#         assert isinstance(data, list)
#         # File vide au début
#         assert len(data) == 0
#
#     def test_get_arcade_queue_not_found(self, client, arcade_api_headers):
#         """Test d'accès à la file d'une borne inexistante."""
#         response = client.get("/api/v1/arcades/99999/queue", headers=arcade_api_headers)
#
#         assert response.status_code == 404
#         assert "Borne d'arcade non trouvée" in response.json()["detail"]
#
#     def test_get_arcade_config_unauthorized(self, client, sample_arcade):
#         """Test d'accès à la config sans clé API."""
#         response = client.get(f"/api/v1/arcades/{sample_arcade.id}/config")
#
#         assert response.status_code == 401
#
#     def test_get_arcade_config_with_api_key(self, client, sample_arcade, sample_game, arcade_api_headers, db):
#         """Test d'accès à la config avec clé API valide."""
#         # Associer le jeu à la borne
#         from app.models import ArcadeGame
#         arcade_game = ArcadeGame(
#             arcade_id=sample_arcade.id,
#             game_id=sample_game.id,
#             slot_number=1
#         )
#         db.add(arcade_game)
#         db.commit()
#
#         response = client.get(f"/api/v1/arcades/{sample_arcade.id}/config", headers=arcade_api_headers)
#
#         assert response.status_code == 200
#         data = response.json()
#         assert data["arcade_id"] == sample_arcade.id
#         assert data["arcade_name"] == sample_arcade.nom
#         assert "games" in data
#         assert len(data["games"]) == 1
#         assert data["games"][0]["slot"] == 1
#         assert data["games"][0]["game_id"] == sample_game.id
#         assert data["games"][0]["game_name"] == sample_game.nom
#
#     def test_get_arcade_config_not_found(self, client, arcade_api_headers):
#         """Test d'accès à la config d'une borne inexistante."""
#         response = client.get("/api/v1/arcades/99999/config", headers=arcade_api_headers)
#
#         assert response.status_code == 404
#         assert "Borne d'arcade non trouvée" in response.json()["detail"]
#
#     def test_arcade_games_multiple_slots(self, client, sample_arcade, db):
#         """Test d'une borne avec plusieurs jeux sur différents slots."""
#         from app.models import Game, ArcadeGame
#
#         # Créer un deuxième jeu
#         game2 = Game(
#             nom="Test Game 2",
#             description="Un autre jeu de test",
#             min_players=1,
#             max_players=1,
#             ticket_cost=2
#         )
#         db.add(game2)
#         db.commit()
#         db.refresh(game2)
#
#         # Associer les deux jeux à la borne
#         arcade_games = [
#             ArcadeGame(arcade_id=sample_arcade.id, game_id=sample_game.id, slot_number=1),
#             ArcadeGame(arcade_id=sample_arcade.id, game_id=game2.id, slot_number=2)
#         ]
#
#         for ag in arcade_games:
#             db.add(ag)
#         db.commit()
#
#         response = client.get(f"/api/v1/arcades/{sample_arcade.id}")
#
#         assert response.status_code == 200
#         data = response.json()
#         assert len(data["games"]) == 2
#
#         # Vérifier les slots
#         slots = {game["slot_number"]: game for game in data["games"]}
#         assert 1 in slots
#         assert 2 in slots
#         assert slots[1]["id"] == sample_game.id
#         assert slots[2]["id"] == game2.id
#
#     @pytest.fixture
#     def sample_game(self, db):
#         """Jeu de test pour cette classe."""
#         from app.models import Game
#         game = Game(
#             nom="Test Game",
#             description="Un jeu de test",
#             min_players=1,
#             max_players=2,
#             ticket_cost=1
#         )
#         db.add(game)
#         db.commit()
#         db.refresh(game)
#         return game