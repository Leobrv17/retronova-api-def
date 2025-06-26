import pytest
from unittest.mock import patch


class TestIntegration:
    """Tests d'intégration pour les workflows complets."""

    def test_complete_user_workflow(self, client, db, mock_firebase):
        """Test du workflow complet d'un utilisateur."""

        # 1. Enregistrement utilisateur
        mock_firebase.return_value = {
            "uid": "integration_user_123",
            "email": "integration@example.com",
            "email_verified": True
        }

        user_data = {
            "firebase_uid": "integration_user_123",
            "email": "integration@example.com",
            "nom": "Integration",
            "prenom": "User",
            "pseudo": "integrationuser",
            "date_naissance": "1990-01-01",
            "numero_telephone": "0123456789"
        }

        register_response = client.post("/api/v1/auth/register", json=user_data)
        assert register_response.status_code == 200
        user_id = register_response.json()["id"]

        auth_headers = {"Authorization": "Bearer fake_integration_token"}

        # 2. Achat de tickets
        # D'abord récupérer une offre
        offers_response = client.get("/api/v1/tickets/offers")
        assert offers_response.status_code == 200
        offers = offers_response.json()
        assert len(offers) > 0

        # Acheter des tickets
        purchase_data = {"offer_id": offers[0]["id"]}
        purchase_response = client.post("/api/v1/tickets/purchase", json=purchase_data, headers=auth_headers)
        assert purchase_response.status_code == 200

        # 3. Utiliser un code promo
        from app.models import PromoCode
        promo = PromoCode(
            code="INTEGRATION",
            tickets_reward=10,
            is_single_use_per_user=True
        )
        db.add(promo)
        db.commit()

        promo_data = {"code": "INTEGRATION"}
        promo_response = client.post("/api/v1/promos/use", json=promo_data, headers=auth_headers)
        assert promo_response.status_code == 200

        # 4. Vérifier le solde
        balance_response = client.get("/api/v1/tickets/balance", headers=auth_headers)
        assert balance_response.status_code == 200
        balance = balance_response.json()["balance"]
        expected_balance = offers[0]["tickets_amount"] + 10
        assert balance == expected_balance

        # 5. Créer une réservation
        # D'abord créer une borne et un jeu
        from app.models import Arcade, Game, ArcadeGame
        arcade = Arcade(
            nom="Integration Arcade",
            description="Borne pour tests d'intégration",
            api_key="integration_key",
            localisation="Test Location",
            latitude=43.6,
            longitude=1.4
        )
        game = Game(
            nom="Integration Game",
            description="Jeu pour tests d'intégration",
            min_players=1,
            max_players=2,
            ticket_cost=1
        )
        db.add(arcade)
        db.add(game)
        db.commit()
        db.refresh(arcade)
        db.refresh(game)

        # Associer le jeu à la borne
        arcade_game = ArcadeGame(
            arcade_id=arcade.id,
            game_id=game.id,
            slot_number=1
        )
        db.add(arcade_game)
        db.commit()

        # Faire la réservation
        reservation_data = {
            "arcade_id": arcade.id,
            "game_id": game.id
        }
        reservation_response = client.post("/api/v1/reservations/", json=reservation_data, headers=auth_headers)
        assert reservation_response.status_code == 200
        reservation_id = reservation_response.json()["id"]

        # 6. Vérifier que les tickets ont été déduits
        balance_after_response = client.get("/api/v1/tickets/balance", headers=auth_headers)
        new_balance = balance_after_response.json()["balance"]
        assert new_balance == expected_balance - game.ticket_cost

        # 7. Vérifier la file d'attente (avec clé API borne)
        arcade_headers = {"X-API-Key": "arcade-super-secret-api-key-change-this-in-production"}
        queue_response = client.get(f"/api/v1/arcades/{arcade.id}/queue", headers=arcade_headers)
        assert queue_response.status_code == 200
        queue = queue_response.json()
        assert len(queue) == 1
        assert queue[0]["id"] == reservation_id

    def test_friendship_workflow(self, client, db, mock_firebase):
        """Test du workflow complet d'amitié."""

        # Créer deux utilisateurs
        from app.models import User

        user1 = User(
            firebase_uid="friend1_uid",
            email="friend1@example.com",
            nom="Friend1",
            prenom="User",
            pseudo="friend1",
            date_naissance="1990-01-01",
            numero_telephone="0111111111",
            tickets_balance=0
        )

        user2 = User(
            firebase_uid="friend2_uid",
            email="friend2@example.com",
            nom="Friend2",
            prenom="User",
            pseudo="friend2",
            date_naissance="1990-01-01",
            numero_telephone="0222222222",
            tickets_balance=0
        )

        db.add(user1)
        db.add(user2)
        db.commit()
        db.refresh(user1)
        db.refresh(user2)

        # 1. User1 envoie une demande d'ami à User2
        mock_firebase.return_value = {
            "uid": user1.firebase_uid,
            "email": user1.email,
            "email_verified": True
        }

        user1_headers = {"Authorization": "Bearer fake_user1_token"}
        friend_request_data = {"user_id": user2.id}

        request_response = client.post("/api/v1/friends/request", json=friend_request_data, headers=user1_headers)
        assert request_response.status_code == 200

        # 2. User2 voit la demande dans ses demandes reçues
        mock_firebase.return_value = {
            "uid": user2.firebase_uid,
            "email": user2.email,
            "email_verified": True
        }

        user2_headers = {"Authorization": "Bearer fake_user2_token"}
        requests_response = client.get("/api/v1/friends/requests", headers=user2_headers)
        assert requests_response.status_code == 200

        requests = requests_response.json()
        assert len(requests) == 1
        friendship_id = requests[0]["id"]

        # 3. User2 accepte la demande
        accept_response = client.put(f"/api/v1/friends/request/{friendship_id}/accept", headers=user2_headers)
        assert accept_response.status_code == 200

        # 4. Les deux utilisateurs se voient maintenant dans leurs listes d'amis
        friends1_response = client.get("/api/v1/friends/", headers=user1_headers)
        assert friends1_response.status_code == 200
        friends1 = friends1_response.json()
        assert len(friends1) == 1
        assert friends1[0]["id"] == user2.id

        friends2_response = client.get("/api/v1/friends/", headers=user2_headers)
        assert friends2_response.status_code == 200
        friends2 = friends2_response.json()
        assert len(friends2) == 1
        assert friends2[0]["id"] == user1.id

    def test_gaming_session_workflow(self, client, db, mock_firebase):
        """Test du workflow complet d'une session de jeu."""

        # Préparer les données
        from app.models import User, Arcade, Game, ArcadeGame

        # Créer les utilisateurs
        player1 = User(
            firebase_uid="player1_session",
            email="player1@session.com",
            nom="Player1",
            prenom="Session",
            pseudo="player1session",
            date_naissance="1990-01-01",
            numero_telephone="0111111111",
            tickets_balance=10
        )

        player2 = User(
            firebase_uid="player2_session",
            email="player2@session.com",
            nom="Player2",
            prenom="Session",
            pseudo="player2session",
            date_naissance="1990-01-01",
            numero_telephone="0222222222",
            tickets_balance=10
        )

        # Créer la borne et le jeu
        arcade = Arcade(
            nom="Session Arcade",
            description="Borne pour session de jeu",
            api_key="session_key",
            localisation="Session Location",
            latitude=43.6,
            longitude=1.4
        )

        game = Game(
            nom="Session Game",
            description="Jeu pour session",
            min_players=2,
            max_players=2,
            ticket_cost=2
        )

        db.add_all([player1, player2, arcade, game])
        db.commit()
        db.refresh(player1)
        db.refresh(player2)
        db.refresh(arcade)
        db.refresh(game)

        # Associer le jeu à la borne
        arcade_game = ArcadeGame(
            arcade_id=arcade.id,
            game_id=game.id,
            slot_number=1
        )
        db.add(arcade_game)
        db.commit()

        # 1. Player1 fait une réservation avec Player2
        mock_firebase.return_value = {
            "uid": player1.firebase_uid,
            "email": player1.email,
            "email_verified": True
        }

        player1_headers = {"Authorization": "Bearer fake_player1_token"}
        reservation_data = {
            "arcade_id": arcade.id,
            "game_id": game.id,
            "player2_id": player2.id
        }

        reservation_response = client.post("/api/v1/reservations/", json=reservation_data, headers=player1_headers)
        assert reservation_response.status_code == 200
        reservation = reservation_response.json()

        # 2. Vérifier que les tickets de Player1 ont été déduits
        db.refresh(player1)
        assert player1.tickets_balance == 8  # 10 - 2

        # 3. La borne voit la réservation dans sa file
        arcade_headers = {"X-API-Key": "arcade-super-secret-api-key-change-this-in-production"}
        queue_response = client.get(f"/api/v1/arcades/{arcade.id}/queue", headers=arcade_headers)
        assert queue_response.status_code == 200
        queue = queue_response.json()
        assert len(queue) == 1
        assert queue[0]["player_pseudo"] == player1.pseudo
        assert queue[0]["player2_pseudo"] == player2.pseudo

        # 4. Après la partie, la borne enregistre le score
        score_data = {
            "player1_id": player1.id,
            "player2_id": player2.id,
            "game_id": game.id,
            "arcade_id": arcade.id,
            "score_j1": 150,
            "score_j2": 120
        }

        score_response = client.post("/api/v1/scores/", json=score_data, headers=arcade_headers)
        assert score_response.status_code == 200
        score = score_response.json()
        assert score["winner_pseudo"] == player1.pseudo

        # 5. Les joueurs peuvent voir leurs statistiques
        stats_response = client.get("/api/v1/scores/my-stats", headers=player1_headers)
        assert stats_response.status_code == 200
        stats = stats_response.json()
        assert stats["total_games"] == 1
        assert stats["wins"] == 1
        assert stats["win_rate"] == 100.0

    def test_admin_management_workflow(self, client, db, mock_firebase):
        """Test du workflow complet de gestion admin."""

        # 1. Admin crée une nouvelle borne
        mock_firebase.return_value = {
            "uid": "admin_workflow",
            "email": "admin@workflow.com",
            "email_verified": True
        }

        admin_headers = {"Authorization": "Bearer fake_admin_token"}

        arcade_data = {
            "nom": "Admin Arcade",
            "description": "Borne créée par admin",
            "localisation": "Admin Location",
            "latitude": 45.0,
            "longitude": 2.0
        }

        arcade_response = client.post("/api/v1/admin/arcades/", json=arcade_data, headers=admin_headers)
        assert arcade_response.status_code == 200
        arcade_id = arcade_response.json()["arcade_id"]

        # 2. Admin crée un nouveau jeu
        game_data = {
            "nom": "Admin Game",
            "description": "Jeu créé par admin",
            "min_players": 1,
            "max_players": 2,
            "ticket_cost": 3
        }

        game_response = client.post("/api/v1/admin/games/", json=game_data, headers=admin_headers)
        assert game_response.status_code == 200
        game_id = game_response.json()["game_id"]

        # 3. Admin assigne le jeu à la borne
        assignment_data = {
            "arcade_id": arcade_id,
            "game_id": game_id,
            "slot_number": 1
        }

        assignment_response = client.put(f"/api/v1/admin/arcades/{arcade_id}/games",
                                         json=assignment_data, headers=admin_headers)
        assert assignment_response.status_code == 200

        # 4. Admin crée un code promo
        promo_data = {
            "code": "ADMINPROMO",
            "tickets_reward": 15,
            "is_single_use_per_user": True,
            "usage_limit": 50
        }

        promo_response = client.post("/api/v1/admin/promo-codes/", json=promo_data, headers=admin_headers)
        assert promo_response.status_code == 200

        # 5. Vérifier les statistiques
        stats_response = client.get("/api/v1/admin/stats", headers=admin_headers)
        assert stats_response.status_code == 200
        stats = stats_response.json()
        assert stats["total_arcades"] >= 1
        assert stats["total_games"] >= 1
        assert stats["active_promo_codes"] >= 1

        # 6. Utilisateur normal peut utiliser la nouvelle infrastructure
        from app.models import User
        user = User(
            firebase_uid="workflow_user",
            email="workflow@user.com",
            nom="Workflow",
            prenom="User",
            pseudo="workflowuser",
            date_naissance="1990-01-01",
            numero_telephone="0333333333",
            tickets_balance=0
        )
        db.add(user)
        db.commit()

        mock_firebase.return_value = {
            "uid": user.firebase_uid,
            "email": user.email,
            "email_verified": True
        }

        user_headers = {"Authorization": "Bearer fake_workflow_user_token"}

        # Utiliser le code promo
        promo_use_response = client.post("/api/v1/promos/use", json={"code": "ADMINPROMO"}, headers=user_headers)
        assert promo_use_response.status_code == 200

        # Faire une réservation sur la nouvelle borne/jeu
        reservation_data = {
            "arcade_id": arcade_id,
            "game_id": game_id
        }

        reservation_response = client.post("/api/v1/reservations/", json=reservation_data, headers=user_headers)
        assert reservation_response.status_code == 200

    def test_error_handling_workflow(self, client, db, mock_firebase):
        """Test de gestion d'erreurs dans un workflow complet."""

        # Créer un utilisateur avec peu de tickets
        from app.models import User, Arcade, Game, ArcadeGame

        user = User(
            firebase_uid="error_user",
            email="error@user.com",
            nom="Error",
            prenom="User",
            pseudo="erroruser",
            date_naissance="1990-01-01",
            numero_telephone="0444444444",
            tickets_balance=1  # Seulement 1 ticket
        )

        arcade = Arcade(
            nom="Error Arcade",
            description="Borne pour test d'erreurs",
            api_key="error_key",
            localisation="Error Location",
            latitude=43.6,
            longitude=1.4
        )

        expensive_game = Game(
            nom="Expensive Game",
            description="Jeu cher",
            min_players=1,
            max_players=2,
            ticket_cost=5  # Plus cher que le solde de l'utilisateur
        )

        db.add_all([user, arcade, expensive_game])
        db.commit()
        db.refresh(user)
        db.refresh(arcade)
        db.refresh(expensive_game)

        # Associer le jeu à la borne
        arcade_game = ArcadeGame(
            arcade_id=arcade.id,
            game_id=expensive_game.id,
            slot_number=1
        )
        db.add(arcade_game)
        db.commit()

        mock_firebase.return_value = {
            "uid": user.firebase_uid,
            "email": user.email,
            "email_verified": True
        }

        user_headers = {"Authorization": "Bearer fake_error_user_token"}

        # 1. Tentative de réservation avec tickets insuffisants
        reservation_data = {
            "arcade_id": arcade.id,
            "game_id": expensive_game.id
        }

        reservation_response = client.post("/api/v1/reservations/", json=reservation_data, headers=user_headers)
        assert reservation_response.status_code == 400
        assert "Tickets insuffisants" in reservation_response.json()["detail"]

        # 2. Vérifier que le solde n'a pas changé
        balance_response = client.get("/api/v1/tickets/balance", headers=user_headers)
        assert balance_response.status_code == 200
        assert balance_response.json()["balance"] == 1

        # 3. Essayer d'utiliser un code promo inexistant
        promo_response = client.post("/api/v1/promos/use", json={"code": "INEXISTANT"}, headers=user_headers)
        assert promo_response.status_code == 404
        assert "Code promo invalide" in promo_response.json()["detail"]

        # 4. Essayer de faire une demande d'ami à soi-même
        friend_request_response = client.post("/api/v1/friends/request",
                                              json={"user_id": user.id}, headers=user_headers)
        assert friend_request_response.status_code == 400
        assert "vous ajouter vous-même" in friend_request_response.json()["detail"]

    def test_concurrent_reservations_workflow(self, client, db, mock_firebase):
        """Test de réservations concurrentes sur la même borne."""

        from app.models import User, Arcade, Game, ArcadeGame

        # Créer plusieurs utilisateurs
        users = []
        for i in range(3):
            user = User(
                firebase_uid=f"concurrent_user_{i}",
                email=f"concurrent{i}@example.com",
                nom=f"Concurrent{i}",
                prenom="User",
                pseudo=f"concurrent{i}",
                date_naissance="1990-01-01",
                numero_telephone=f"055555555{i}",
                tickets_balance=10
            )
            users.append(user)
            db.add(user)

        # Créer une borne et un jeu
        arcade = Arcade(
            nom="Concurrent Arcade",
            description="Borne pour tests concurrents",
            api_key="concurrent_key",
            localisation="Concurrent Location",
            latitude=43.6,
            longitude=1.4
        )

        game = Game(
            nom="Concurrent Game",
            description="Jeu pour tests concurrents",
            min_players=1,
            max_players=1,
            ticket_cost=1
        )

        db.add(arcade)
        db.add(game)
        db.commit()

        for user in users:
            db.refresh(user)
        db.refresh(arcade)
        db.refresh(game)

        # Associer le jeu à la borne
        arcade_game = ArcadeGame(
            arcade_id=arcade.id,
            game_id=game.id,
            slot_number=1
        )
        db.add(arcade_game)
        db.commit()

        # Chaque utilisateur fait une réservation
        reservations = []
        for i, user in enumerate(users):
            mock_firebase.return_value = {
                "uid": user.firebase_uid,
                "email": user.email,
                "email_verified": True
            }

            headers = {"Authorization": f"Bearer fake_concurrent_token_{i}"}
            reservation_data = {
                "arcade_id": arcade.id,
                "game_id": game.id
            }

            reservation_response = client.post("/api/v1/reservations/",
                                               json=reservation_data, headers=headers)
            assert reservation_response.status_code == 200
            reservations.append(reservation_response.json())

        # Vérifier la file d'attente (ordre FIFO)
        arcade_headers = {"X-API-Key": "arcade-super-secret-api-key-change-this-in-production"}
        queue_response = client.get(f"/api/v1/arcades/{arcade.id}/queue", headers=arcade_headers)
        assert queue_response.status_code == 200

        queue = queue_response.json()
        assert len(queue) == 3

        # Vérifier les positions dans la file
        for i, queue_item in enumerate(queue):
            assert queue_item["position"] == i + 1
            assert queue_item["player_pseudo"] == f"concurrent{i}"

    def test_data_consistency_workflow(self, client, db, mock_firebase):
        """Test de cohérence des données à travers les opérations."""

        from app.models import User, TicketOffer, PromoCode

        # Créer un utilisateur
        user = User(
            firebase_uid="consistency_user",
            email="consistency@example.com",
            nom="Consistency",
            prenom="User",
            pseudo="consistencyuser",
            date_naissance="1990-01-01",
            numero_telephone="0666666666",
            tickets_balance=0
        )

        # Créer une offre de tickets
        offer = TicketOffer(
            tickets_amount=20,
            price_euros=25.0,
            name="Consistency Offer"
        )

        # Créer un code promo
        promo = PromoCode(
            code="CONSISTENCY",
            tickets_reward=15,
            is_single_use_per_user=True
        )

        db.add_all([user, offer, promo])
        db.commit()
        db.refresh(user)
        db.refresh(offer)
        db.refresh(promo)

        mock_firebase.return_value = {
            "uid": user.firebase_uid,
            "email": user.email,
            "email_verified": True
        }

        headers = {"Authorization": "Bearer fake_consistency_token"}

        # 1. État initial - 0 tickets
        balance_response = client.get("/api/v1/tickets/balance", headers=headers)
        assert balance_response.json()["balance"] == 0

        # 2. Acheter des tickets - devrait avoir 20 tickets
        purchase_response = client.post("/api/v1/tickets/purchase",
                                        json={"offer_id": offer.id}, headers=headers)
        assert purchase_response.status_code == 200
        assert purchase_response.json()["new_balance"] == 20

        # Vérifier la cohérence
        balance_response = client.get("/api/v1/tickets/balance", headers=headers)
        assert balance_response.json()["balance"] == 20

        # 3. Utiliser le code promo - devrait avoir 35 tickets
        promo_response = client.post("/api/v1/promos/use",
                                     json={"code": "CONSISTENCY"}, headers=headers)
        assert promo_response.status_code == 200
        assert promo_response.json()["new_balance"] == 35

        # Vérifier la cohérence
        balance_response = client.get("/api/v1/tickets/balance", headers=headers)
        assert balance_response.json()["balance"] == 35

        # 4. Vérifier l'historique d'achats
        history_response = client.get("/api/v1/tickets/history", headers=headers)
        assert history_response.status_code == 200
        history = history_response.json()
        assert len(history) == 1
        assert history[0]["tickets_received"] == 20

        # 5. Vérifier l'historique des codes promo
        promo_history_response = client.get("/api/v1/promos/history", headers=headers)
        assert promo_history_response.status_code == 200
        promo_history = promo_history_response.json()
        assert len(promo_history) == 1
        assert promo_history[0]["tickets_received"] == 15

        # 6. Vérifier que les totaux correspondent
        total_from_history = (history[0]["tickets_received"] +
                              promo_history[0]["tickets_received"])
        current_balance = balance_response.json()["balance"]
        assert total_from_history == current_balance

    def test_api_endpoints_discovery(self, client):
        """Test de découverte des endpoints de l'API."""

        # Test du endpoint racine
        root_response = client.get("/")
        assert root_response.status_code == 200
        data = root_response.json()
        assert "Arcade API" in data["message"]
        assert "version" in data

        # Test du health check
        health_response = client.get("/health")
        assert health_response.status_code == 200
        health_data = health_response.json()
        assert health_data["status"] == "healthy"

        # Test des endpoints publics (sans auth)
        public_endpoints = [
            "/api/v1/games/",
            "/api/v1/arcades/",
            "/api/v1/tickets/offers"
        ]

        for endpoint in public_endpoints:
            response = client.get(endpoint)
            assert response.status_code == 200

    def test_performance_workflow(self, client, db, mock_firebase):
        """Test de performance avec de multiples opérations."""

        from app.models import User, Arcade, Game, ArcadeGame
        import time

        # Créer plusieurs utilisateurs, bornes et jeux
        start_time = time.time()

        users = []
        for i in range(10):
            user = User(
                firebase_uid=f"perf_user_{i}",
                email=f"perf{i}@example.com",
                nom=f"Perf{i}",
                prenom="User",
                pseudo=f"perf{i}",
                date_naissance="1990-01-01",
                numero_telephone=f"077777777{i}",
                tickets_balance=5
            )
            users.append(user)
            db.add(user)

        arcade = Arcade(
            nom="Performance Arcade",
            description="Borne pour tests de performance",
            api_key="perf_key",
            localisation="Perf Location",
            latitude=43.6,
            longitude=1.4
        )

        game = Game(
            nom="Performance Game",
            description="Jeu pour tests de performance",
            min_players=1,
            max_players=1,
            ticket_cost=1
        )

        db.add(arcade)
        db.add(game)
        db.commit()

        for user in users:
            db.refresh(user)
        db.refresh(arcade)
        db.refresh(game)

        # Associer le jeu à la borne
        arcade_game = ArcadeGame(
            arcade_id=arcade.id,
            game_id=game.id,
            slot_number=1
        )
        db.add(arcade_game)
        db.commit()

        setup_time = time.time() - start_time
        print(f"Setup time: {setup_time:.2f}s")

        # Faire de multiples réservations
        operation_start = time.time()

        for i, user in enumerate(users):
            mock_firebase.return_value = {
                "uid": user.firebase_uid,
                "email": user.email,
                "email_verified": True
            }

            headers = {"Authorization": f"Bearer fake_perf_token_{i}"}
            reservation_data = {
                "arcade_id": arcade.id,
                "game_id": game.id
            }

            reservation_response = client.post("/api/v1/reservations/",
                                               json=reservation_data, headers=headers)
            assert reservation_response.status_code == 200

        operations_time = time.time() - operation_start
        print(f"10 reservations time: {operations_time:.2f}s")

        # Vérifier que toutes les réservations sont dans la file
        arcade_headers = {"X-API-Key": "arcade-super-secret-api-key-change-this-in-production"}
        queue_response = client.get(f"/api/v1/arcades/{arcade.id}/queue", headers=arcade_headers)
        assert queue_response.status_code == 200

        queue = queue_response.json()
        assert len(queue) == 10

        # Le test ne devrait pas prendre plus de quelques secondes
        total_time = time.time() - start_time
        assert total_time < 10, f"Test took too long: {total_time:.2f}s"