import pytest


class TestFriends:
    """Tests pour les endpoints d'amis."""

    @pytest.fixture
    def friend_user(self, db):
        """Utilisateur ami pour les tests."""
        from app.models import User
        friend = User(
            firebase_uid="friend_uid_123",
            email="friend@example.com",
            nom="Friend",
            prenom="User",
            pseudo="frienduser",
            date_naissance="1990-01-01",
            numero_telephone="0999999999",
            tickets_balance=5
        )
        db.add(friend)
        db.commit()
        db.refresh(friend)
        return friend

    def test_get_my_friends_empty(self, client, auth_headers_user):
        """Test de récupération d'une liste d'amis vide."""
        response = client.get("/api/v1/friends/", headers=auth_headers_user)

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 0

    def test_send_friend_request_success(self, client, auth_headers_user, friend_user):
        """Test d'envoi de demande d'ami réussi."""
        request_data = {
            "user_id": friend_user.id
        }

        response = client.post("/api/v1/friends/request", json=request_data, headers=auth_headers_user)

        assert response.status_code == 200
        assert "Demande d'ami envoyée" in response.json()["message"]

    def test_send_friend_request_to_self(self, client, auth_headers_user, sample_user):
        """Test d'envoi de demande d'ami à soi-même."""
        request_data = {
            "user_id": sample_user.id
        }

        response = client.post("/api/v1/friends/request", json=request_data, headers=auth_headers_user)

        assert response.status_code == 400
        assert "vous ajouter vous-même" in response.json()["detail"]

    def test_send_friend_request_user_not_found(self, client, auth_headers_user):
        """Test d'envoi de demande à un utilisateur inexistant."""
        request_data = {
            "user_id": 99999
        }

        response = client.post("/api/v1/friends/request", json=request_data, headers=auth_headers_user)

        assert response.status_code == 404
        assert "Utilisateur non trouvé" in response.json()["detail"]

    def test_send_duplicate_friend_request(self, client, auth_headers_user, friend_user, db):
        """Test d'envoi de demande d'ami en double."""
        # Créer une première demande
        from app.models import Friendship
        friendship = Friendship(
            requester_id=friend_user.id,
            requested_id=friend_user.id
        )
        db.add(friendship)
        db.commit()

        request_data = {
            "user_id": friend_user.id
        }

        # Première demande
        response1 = client.post("/api/v1/friends/request", json=request_data, headers=auth_headers_user)
        assert response1.status_code == 200

        # Deuxième demande (doit échouer)
        response2 = client.post("/api/v1/friends/request", json=request_data, headers=auth_headers_user)
        assert response2.status_code == 400
        assert "déjà en cours" in response2.json()["detail"]

    def test_get_friend_requests_empty(self, client, auth_headers_user):
        """Test de récupération des demandes reçues vides."""
        response = client.get("/api/v1/friends/requests", headers=auth_headers_user)

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 0

    def test_get_friend_requests_with_pending_request(self, client, auth_headers_user, sample_user, friend_user, db):
        """Test de récupération des demandes avec une demande en attente."""
        from app.models import Friendship
        friendship = Friendship(
            requester_id=friend_user.id,
            requested_id=sample_user.id
        )
        db.add(friendship)
        db.commit()

        response = client.get("/api/v1/friends/requests", headers=auth_headers_user)

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["requester"]["id"] == friend_user.id
        assert data[0]["requested"]["id"] == sample_user.id
        assert data[0]["status"] == "pending"

    def test_accept_friend_request_success(self, client, auth_headers_user, sample_user, friend_user, db):
        """Test d'acceptation d'une demande d'ami."""
        from app.models import Friendship
        friendship = Friendship(
            requester_id=friend_user.id,
            requested_id=sample_user.id
        )
        db.add(friendship)
        db.commit()
        db.refresh(friendship)

        response = client.put(f"/api/v1/friends/request/{friendship.id}/accept", headers=auth_headers_user)

        assert response.status_code == 200
        assert "acceptée" in response.json()["message"]

        # Vérifier que le statut a changé
        db.refresh(friendship)
        assert friendship.status.value == "accepted"

    def test_accept_friend_request_not_found(self, client, auth_headers_user):
        """Test d'acceptation d'une demande inexistante."""
        response = client.put("/api/v1/friends/request/99999/accept", headers=auth_headers_user)

        assert response.status_code == 404
        assert "Demande d'ami non trouvée" in response.json()["detail"]

    def test_reject_friend_request_success(self, client, auth_headers_user, sample_user, friend_user, db):
        """Test de rejet d'une demande d'ami."""
        from app.models import Friendship
        friendship = Friendship(
            requester_id=friend_user.id,
            requested_id=sample_user.id
        )
        db.add(friendship)
        db.commit()
        db.refresh(friendship)

        response = client.put(f"/api/v1/friends/request/{friendship.id}/reject", headers=auth_headers_user)

        assert response.status_code == 200
        assert "rejetée" in response.json()["message"]

        # Vérifier que le statut a changé
        db.refresh(friendship)
        assert friendship.status.value == "rejected"

    def test_get_friends_after_acceptance(self, client, auth_headers_user, sample_user, friend_user, db):
        """Test de récupération des amis après acceptation."""
        from app.models import Friendship, FriendshipStatus
        friendship = Friendship(
            requester_id=friend_user.id,
            requested_id=sample_user.id,
            status=FriendshipStatus.ACCEPTED
        )
        db.add(friendship)
        db.commit()

        response = client.get("/api/v1/friends/", headers=auth_headers_user)

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["id"] == friend_user.id
        assert data[0]["pseudo"] == friend_user.pseudo

    def test_remove_friend_success(self, client, auth_headers_user, sample_user, friend_user, db):
        """Test de suppression d'un ami."""
        from app.models import Friendship, FriendshipStatus
        friendship = Friendship(
            requester_id=friend_user.id,
            requested_id=sample_user.id,
            status=FriendshipStatus.ACCEPTED
        )
        db.add(friendship)
        db.commit()
        db.refresh(friendship)

        response = client.delete(f"/api/v1/friends/{friend_user.id}", headers=auth_headers_user)

        assert response.status_code == 200
        assert "retiré" in response.json()["message"]

        # Vérifier que l'amitié est marquée comme supprimée
        db.refresh(friendship)
        assert friendship.is_deleted == True

    def test_remove_friend_not_found(self, client, auth_headers_user):
        """Test de suppression d'un ami inexistant."""
        response = client.delete("/api/v1/friends/99999", headers=auth_headers_user)

        assert response.status_code == 404
        assert "Amitié non trouvée" in response.json()["detail"]

    def test_friendship_bidirectional(self, client, sample_user, friend_user, db):
        """Test que l'amitié fonctionne dans les deux sens."""
        from app.models import Friendship, FriendshipStatus
        from app.core.security import verify_firebase_token

        # Créer une amitié acceptée
        friendship = Friendship(
            requester_id=sample_user.id,
            requested_id=friend_user.id,
            status=FriendshipStatus.ACCEPTED
        )
        db.add(friendship)
        db.commit()

        # Tester depuis le compte de l'ami
        with patch('app.core.security.verify_firebase_token') as mock_verify:
            mock_verify.return_value = {
                "uid": friend_user.firebase_uid,
                "email": friend_user.email,
                "email_verified": True
            }
            friend_headers = {"Authorization": "Bearer fake_friend_token"}

            response = client.get("/api/v1/friends/", headers=friend_headers)

            assert response.status_code == 200
            data = response.json()
            assert len(data) == 1
            assert data[0]["id"] == sample_user.id

    def test_friends_endpoints_unauthorized(self, client, friend_user):
        """Test d'accès non autorisé aux endpoints d'amis."""
        protected_endpoints = [
            ("GET", "/api/v1/friends/", None),
            ("GET", "/api/v1/friends/requests", None),
            ("POST", "/api/v1/friends/request", {"user_id": friend_user.id}),
            ("PUT", "/api/v1/friends/request/1/accept", None),
            ("PUT", "/api/v1/friends/request/1/reject", None),
            ("DELETE", f"/api/v1/friends/{friend_user.id}", None)
        ]

        for method, endpoint, json_data in protected_endpoints:
            if method == "GET":
                response = client.get(endpoint)
            elif method == "POST":
                response = client.post(endpoint, json=json_data)
            elif method == "PUT":
                response = client.put(endpoint)
            elif method == "DELETE":
                response = client.delete(endpoint)

            assert response.status_code == 403