import pytest


class TestReservations:
    """Tests pour les endpoints de réservations."""

    @pytest.fixture
    def arcade_with_game(self, sample_arcade, sample_game, db):
        """Borne avec jeu associé pour les tests."""
        from app.models import ArcadeGame
        arcade_game = ArcadeGame(
            arcade_id=sample_arcade.id,
            game_id=sample_game.id,
            slot_number=1
        )
        db.add(arcade_game)
        db.commit()
        return sample_arcade

    @pytest.fixture
    def user_with_tickets(self, sample_user, db):
        """Utilisateur avec des tickets pour les tests."""
        sample_user.tickets_balance = 10
        db.commit()
        db.refresh(sample_user)
        return sample_user

    def test_create_reservation_success(self, client, auth_headers_user, user_with_tickets, arcade_with_game,
                                        sample_game):
        """Test de création de réservation réussie."""
        reservation_data = {
            "arcade_id": arcade_with_game.id,
            "game_id": sample_game.id
        }

        response = client.post("/api/v1/reservations/", json=reservation_data, headers=auth_headers_user)

        assert response.status_code == 200
        data = response.json()
        assert data["arcade_name"] == arcade_with_game.nom
        assert data["game_name"] == sample_game.nom
        assert data["player_pseudo"] == user_with_tickets.pseudo
        assert data["status"] == "waiting"
        assert data["tickets_used"] == sample_game.ticket_cost
        assert data["unlock_code"] in "12345678"
        assert data["position_in_queue"] == 1

    def test_create_reservation_with_player2(self, client, auth_headers_user, user_with_tickets, arcade_with_game,
                                             sample_game, db):
        """Test de création de réservation avec joueur 2."""
        # Créer un deuxième joueur
        from app.models import User
        player2 = User(
            firebase_uid="player2_uid",
            email="player2@example.com",
            nom="Player2",
            prenom="Test",
            pseudo="player2",
            date_naissance="1990-01-01",
            numero_telephone="0888888888",
            tickets_balance=0
        )
        db.add(player2)
        db.commit()
        db.refresh(player2)

        reservation_data = {
            "arcade_id": arcade_with_game.id,
            "game_id": sample_game.id,
            "player2_id": player2.id
        }

        response = client.post("/api/v1/reservations/", json=reservation_data, headers=auth_headers_user)

        assert response.status_code == 200
        data = response.json()
        assert data["player2_pseudo"] == player2.pseudo

    def test_create_reservation_arcade_not_found(self, client, auth_headers_user, sample_game):
        """Test de création avec borne inexistante."""
        reservation_data = {
            "arcade_id": 99999,
            "game_id": sample_game.id
        }

        response = client.post("/api/v1/reservations/", json=reservation_data, headers=auth_headers_user)

        assert response.status_code == 404
        assert "Borne d'arcade non trouvée" in response.json()["detail"]

    def test_create_reservation_game_not_on_arcade(self, client, auth_headers_user, sample_arcade, sample_game):
        """Test de création avec jeu non disponible sur la borne."""
        reservation_data = {
            "arcade_id": sample_arcade.id,
            "game_id": sample_game.id
        }

        response = client.post("/api/v1/reservations/", json=reservation_data, headers=auth_headers_user)

        assert response.status_code == 404
        assert "Jeu non disponible sur cette borne" in response.json()["detail"]

    def test_create_reservation_insufficient_tickets(self, client, auth_headers_user, sample_user, arcade_with_game,
                                                     sample_game, db):
        """Test de création avec tickets insuffisants."""
        # Vider le solde de tickets
        sample_user.tickets_balance = 0
        db.commit()

        reservation_data = {
            "arcade_id": arcade_with_game.id,
            "game_id": sample_game.id
        }

        response = client.post("/api/v1/reservations/", json=reservation_data, headers=auth_headers_user)

        assert response.status_code == 400
        assert "Tickets insuffisants" in response.json()["detail"]

    def test_create_reservation_player2_same_as_player1(self, client, auth_headers_user, user_with_tickets,
                                                        arcade_with_game, sample_game):
        """Test de création avec player2 = player1."""
        reservation_data = {
            "arcade_id": arcade_with_game.id,
            "game_id": sample_game.id,
            "player2_id": user_with_tickets.id
        }

        response = client.post("/api/v1/reservations/", json=reservation_data, headers=auth_headers_user)

        assert response.status_code == 400
        assert "jouer contre vous-même" in response.json()["detail"]

    def test_create_reservation_player2_not_found(self, client, auth_headers_user, user_with_tickets, arcade_with_game,
                                                  sample_game):
        """Test de création avec player2 inexistant."""
        reservation_data = {
            "arcade_id": arcade_with_game.id,
            "game_id": sample_game.id,
            "player2_id": 99999
        }

        response = client.post("/api/v1/reservations/", json=reservation_data, headers=auth_headers_user)

        assert response.status_code == 404
        assert "Joueur 2 non trouvé" in response.json()["detail"]

    def test_get_my_reservations_empty(self, client, auth_headers_user):
        """Test de récupération des réservations vides."""
        response = client.get("/api/v1/reservations/", headers=auth_headers_user)

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 0

    def test_get_my_reservations_with_data(self, client, auth_headers_user, user_with_tickets, arcade_with_game,
                                           sample_game, db):
        """Test de récupération des réservations avec données."""
        # Créer une réservation
        from app.models import Reservation
        reservation = Reservation(
            player_id=user_with_tickets.id,
            arcade_id=arcade_with_game.id,
            game_id=sample_game.id,
            unlock_code="1",
            tickets_used=sample_game.ticket_cost
        )
        db.add(reservation)
        db.commit()
        db.refresh(reservation)

        response = client.get("/api/v1/reservations/", headers=auth_headers_user)

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["id"] == reservation.id
        assert data[0]["unlock_code"] == "1"
        assert data[0]["status"] == "waiting"

    def test_get_reservation_by_id(self, client, auth_headers_user, user_with_tickets, arcade_with_game, sample_game,
                                   db):
        """Test de récupération d'une réservation par ID."""
        from app.models import Reservation
        reservation = Reservation(
            player_id=user_with_tickets.id,
            arcade_id=arcade_with_game.id,
            game_id=sample_game.id,
            unlock_code="2",
            tickets_used=sample_game.ticket_cost
        )
        db.add(reservation)
        db.commit()
        db.refresh(reservation)

        response = client.get(f"/api/v1/reservations/{reservation.id}", headers=auth_headers_user)

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == reservation.id
        assert data["unlock_code"] == "2"

    def test_get_reservation_not_found(self, client, auth_headers_user):
        """Test de récupération d'une réservation inexistante."""
        response = client.get("/api/v1/reservations/99999", headers=auth_headers_user)

        assert response.status_code == 404
        assert "Réservation non trouvée" in response.json()["detail"]

    def test_cancel_reservation_success(self, client, auth_headers_user, user_with_tickets, arcade_with_game,
                                        sample_game, db):
        """Test d'annulation de réservation réussie."""
        from app.models import Reservation
        initial_balance = user_with_tickets.tickets_balance

        reservation = Reservation(
            player_id=user_with_tickets.id,
            arcade_id=arcade_with_game.id,
            game_id=sample_game.id,
            unlock_code="3",
            tickets_used=sample_game.ticket_cost
        )
        db.add(reservation)

        # Déduire les tickets comme lors d'une vraie réservation
        user_with_tickets.tickets_balance -= sample_game.ticket_cost
        db.commit()
        db.refresh(reservation)

        response = client.delete(f"/api/v1/reservations/{reservation.id}", headers=auth_headers_user)

        assert response.status_code == 200
        assert "annulée" in response.json()["message"]

        # Vérifier que les tickets ont été remboursés
        db.refresh(user_with_tickets)
        assert user_with_tickets.tickets_balance == initial_balance

    def test_cancel_reservation_not_waiting(self, client, auth_headers_user, user_with_tickets, arcade_with_game,
                                            sample_game, db):
        """Test d'annulation d'une réservation qui n'est pas en attente."""
        from app.models import Reservation, ReservationStatus
        reservation = Reservation(
            player_id=user_with_tickets.id,
            arcade_id=arcade_with_game.id,
            game_id=sample_game.id,
            unlock_code="4",
            tickets_used=sample_game.ticket_cost,
            status=ReservationStatus.PLAYING
        )
        db.add(reservation)
        db.commit()
        db.refresh(reservation)

        response = client.delete(f"/api/v1/reservations/{reservation.id}", headers=auth_headers_user)

        assert response.status_code == 400
        assert "en attente peuvent être annulées" in response.json()["detail"]

    def test_cancel_reservation_not_found(self, client, auth_headers_user):
        """Test d'annulation d'une réservation inexistante."""
        response = client.delete("/api/v1/reservations/99999", headers=auth_headers_user)

        assert response.status_code == 404
        assert "Réservation non trouvée" in response.json()["detail"]

    def test_tickets_deducted_on_reservation(self, client, auth_headers_user, user_with_tickets, arcade_with_game,
                                             sample_game, db):
        """Test que les tickets sont bien déduits lors de la réservation."""
        initial_balance = user_with_tickets.tickets_balance

        reservation_data = {
            "arcade_id": arcade_with_game.id,
            "game_id": sample_game.id
        }

        response = client.post("/api/v1/reservations/", json=reservation_data, headers=auth_headers_user)

        assert response.status_code == 200

        # Vérifier que les tickets ont été déduits
        db.refresh(user_with_tickets)
        assert user_with_tickets.tickets_balance == initial_balance - sample_game.ticket_cost

    def test_queue_position_calculation(self, client, auth_headers_user, arcade_with_game, sample_game, db):
        """Test du calcul de la position dans la file d'attente."""
        # Créer plusieurs utilisateurs avec des tickets
        from app.models import User, Reservation
        users = []
        for i in range(3):
            user = User(
                firebase_uid=f"queue_user_{i}",
                email=f"queue{i}@example.com",
                nom=f"Queue{i}",
                prenom="User",
                pseudo=f"queueuser{i}",
                date_naissance="1990-01-01",
                numero_telephone=f"066666666{i}",
                tickets_balance=10
            )
            db.add(user)
            users.append(user)
        db.commit()

        # Créer plusieurs réservations
        reservations = []
        for i, user in enumerate(users):
            reservation = Reservation(
                player_id=user.id,
                arcade_id=arcade_with_game.id,
                game_id=sample_game.id,
                unlock_code=str(i + 5),
                tickets_used=sample_game.ticket_cost
            )
            db.add(reservation)
            reservations.append(reservation)
        db.commit()

        # Créer une nouvelle réservation et vérifier sa position
        with patch('app.core.security.verify_firebase_token') as mock_verify:
            mock_verify.return_value = {
                "uid": "new_queue_user",
                "email": "newqueue@example.com",
                "email_verified": True
            }

            new_user = User(
                firebase_uid="new_queue_user",
                email="newqueue@example.com",
                nom="NewQueue",
                prenom="User",
                pseudo="newqueueuser",
                date_naissance="1990-01-01",
                numero_telephone="0555555555",
                tickets_balance=10
            )
            db.add(new_user)
            db.commit()

            headers = {"Authorization": "Bearer fake_new_user_token"}
            reservation_data = {
                "arcade_id": arcade_with_game.id,
                "game_id": sample_game.id
            }

            response = client.post("/api/v1/reservations/", json=reservation_data, headers=headers)

            assert response.status_code == 200
            data = response.json()
            assert data["position_in_queue"] == 4  # 4ème position

    def test_reservations_endpoints_unauthorized(self, client, arcade_with_game, sample_game):
        """Test d'accès non autorisé aux endpoints de réservations."""
        protected_endpoints = [
            ("POST", "/api/v1/reservations/", {"arcade_id": arcade_with_game.id, "game_id": sample_game.id}),
            ("GET", "/api/v1/reservations/", None),
            ("GET", "/api/v1/reservations/1", None),
            ("DELETE", "/api/v1/reservations/1", None)
        ]

        for method, endpoint, json_data in protected_endpoints:
            if method == "POST":
                response = client.post(endpoint, json=json_data)
            elif method == "GET":
                response = client.get(endpoint)
            elif method == "DELETE":
                response = client.delete(endpoint)

            assert response.status_code == 403

    def test_reservation_as_player2_can_view(self, client, user_with_tickets, arcade_with_game, sample_game, db):
        """Test qu'un joueur 2 peut voir la réservation."""
        from app.models import User, Reservation
        from unittest.mock import patch

        # Créer un deuxième joueur
        player2 = User(
            firebase_uid="player2_view_uid",
            email="player2view@example.com",
            nom="Player2",
            prenom="View",
            pseudo="player2view",
            date_naissance="1990-01-01",
            numero_telephone="0444444444",
            tickets_balance=0
        )
        db.add(player2)
        db.commit()
        db.refresh(player2)

        # Créer une réservation avec ce joueur 2
        reservation = Reservation(
            player_id=user_with_tickets.id,
            player2_id=player2.id,
            arcade_id=arcade_with_game.id,
            game_id=sample_game.id,
            unlock_code="7",
            tickets_used=sample_game.ticket_cost
        )
        db.add(reservation)
        db.commit()
        db.refresh(reservation)

        # Tester l'accès depuis le compte du joueur 2
        with patch('app.core.security.verify_firebase_token') as mock_verify:
            mock_verify.return_value = {
                "uid": player2.firebase_uid,
                "email": player2.email,
                "email_verified": True
            }

            headers = {"Authorization": "Bearer fake_player2_token"}
            response = client.get(f"/api/v1/reservations/{reservation.id}", headers=headers)

            assert response.status_code == 200
            data = response.json()
            assert data["id"] == reservation.id