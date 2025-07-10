import pytest
from datetime import datetime, timedelta, timezone
from app.models import PromoCode


class TestPromoExpiry:
    """Tests pour les dates de péremption des codes promo."""

    def test_create_promo_with_expiry_date(self, client, auth_headers_admin):
        """Test de création de code promo avec date d'expiration."""
        future_date = datetime.now(timezone.utc) + timedelta(days=30)

        promo_data = {
            "code": "EXPIRE30",
            "tickets_reward": 10,
            "valid_until": future_date.isoformat(),
            "is_single_use_per_user": True
        }

        response = client.post("/api/v1/admin/promo-codes/", json=promo_data, headers=auth_headers_admin)

        assert response.status_code == 200
        data = response.json()
        assert "Code promo créé" in data["message"]
        assert data["is_valid_now"] == True
        assert data["days_until_expiry"] == 30

    def test_create_promo_with_start_date(self, client, auth_headers_admin):
        """Test de création de code promo avec date de début."""
        start_date = datetime.now(timezone.utc) + timedelta(days=1)
        end_date = datetime.now(timezone.utc) + timedelta(days=10)

        promo_data = {
            "code": "FUTURE",
            "tickets_reward": 5,
            "valid_from": start_date.isoformat(),
            "valid_until": end_date.isoformat(),
            "is_single_use_per_user": True
        }

        response = client.post("/api/v1/admin/promo-codes/", json=promo_data, headers=auth_headers_admin)

        assert response.status_code == 200
        data = response.json()
        assert data["is_valid_now"] == False  # Pas encore valide

    def test_create_promo_invalid_date_range(self, client, auth_headers_admin):
        """Test de création avec dates invalides (fin avant début)."""
        start_date = datetime.now(timezone.utc) + timedelta(days=10)
        end_date = datetime.now(timezone.utc) + timedelta(days=5)  # Avant le début !

        promo_data = {
            "code": "INVALID",
            "tickets_reward": 5,
            "valid_from": start_date.isoformat(),
            "valid_until": end_date.isoformat()
        }

        response = client.post("/api/v1/admin/promo-codes/", json=promo_data, headers=auth_headers_admin)

        assert response.status_code == 400
        assert "après la date de début" in response.json()["detail"]

    def test_use_expired_promo_code(self, client, auth_headers_user, db):
        """Test d'utilisation d'un code promo expiré."""
        # Créer un code expiré
        expired_date = datetime.now(timezone.utc) - timedelta(days=1)
        expired_promo = PromoCode(
            code="EXPIRED",
            tickets_reward=10,
            valid_until=expired_date,
            is_single_use_per_user=True
        )
        db.add(expired_promo)
        db.commit()

        promo_data = {"code": "EXPIRED"}

        response = client.post("/api/v1/promos/use", json=promo_data, headers=auth_headers_user)

        assert response.status_code == 400
        assert "code promo a expiré" in response.json()["detail"]

    def test_use_future_promo_code(self, client, auth_headers_user, db):
        """Test d'utilisation d'un code promo pas encore valide."""
        # Créer un code qui commence demain
        future_date = datetime.now(timezone.utc) + timedelta(days=1)
        future_promo = PromoCode(
            code="FUTURE",
            tickets_reward=15,
            valid_from=future_date,
            is_single_use_per_user=True
        )
        db.add(future_promo)
        db.commit()

        promo_data = {"code": "FUTURE"}

        response = client.post("/api/v1/promos/use", json=promo_data, headers=auth_headers_user)

        assert response.status_code == 400
        assert "pas encore valide" in response.json()["detail"]

    def test_use_inactive_promo_code(self, client, auth_headers_user, db):
        """Test d'utilisation d'un code promo désactivé."""
        inactive_promo = PromoCode(
            code="INACTIVE",
            tickets_reward=20,
            is_active=False,
            is_single_use_per_user=True
        )
        db.add(inactive_promo)
        db.commit()

        promo_data = {"code": "INACTIVE"}

        response = client.post("/api/v1/promos/use", json=promo_data, headers=auth_headers_user)

        assert response.status_code == 400
        assert "n'est plus actif" in response.json()["detail"]

    def test_use_valid_promo_with_dates(self, client, auth_headers_user, sample_user, db):
        """Test d'utilisation d'un code promo valide avec dates."""
        # Créer un code valide (commencé hier, expire dans 30 jours)
        start_date = datetime.now(timezone.utc) - timedelta(days=1)
        end_date = datetime.now(timezone.utc) + timedelta(days=30)

        valid_promo = PromoCode(
            code="VALIDNOW",
            tickets_reward=25,
            valid_from=start_date,
            valid_until=end_date,
            is_single_use_per_user=True
        )
        db.add(valid_promo)
        db.commit()

        initial_balance = sample_user.tickets_balance
        promo_data = {"code": "VALIDNOW"}

        response = client.post("/api/v1/promos/use", json=promo_data, headers=auth_headers_user)

        assert response.status_code == 200
        data = response.json()
        assert data["tickets_received"] == 25
        assert data["new_balance"] == initial_balance + 25

    def test_promo_model_is_valid_now_method(self, db):
        """Test des méthodes de validation du modèle PromoCode."""
        now = datetime.now(timezone.utc)

        # Code valide (pas de dates)
        valid_promo = PromoCode(code="VALID", tickets_reward=10, is_active=True)
        assert valid_promo.is_valid_now() == True

        # Code inactif
        inactive_promo = PromoCode(code="INACTIVE", tickets_reward=10, is_active=False)
        assert inactive_promo.is_valid_now() == False

        # Code expiré
        expired_promo = PromoCode(
            code="EXPIRED",
            tickets_reward=10,
            valid_until=now - timedelta(days=1),
            is_active=True
        )
        assert expired_promo.is_valid_now() == False
        assert expired_promo.is_expired() == True

        # Code futur
        future_promo = PromoCode(
            code="FUTURE",
            tickets_reward=10,
            valid_from=now + timedelta(days=1),
            is_active=True
        )
        assert future_promo.is_valid_now() == False

        # Code dans la période valide
        current_promo = PromoCode(
            code="CURRENT",
            tickets_reward=10,
            valid_from=now - timedelta(days=1),
            valid_until=now + timedelta(days=1),
            is_active=True
        )
        assert current_promo.is_valid_now() == True

    def test_promo_days_until_expiry_method(self, db):
        """Test de la méthode days_until_expiry."""
        now = datetime.now(timezone.utc)

        # Code sans expiration
        no_expiry = PromoCode(code="NOEXPIRY", tickets_reward=10)
        assert no_expiry.days_until_expiry() == -1

        # Code expirant dans 5 jours
        expires_in_5 = PromoCode(
            code="EXPIRES5",
            tickets_reward=10,
            valid_until=now + timedelta(days=5)
        )
        assert expires_in_5.days_until_expiry() == 5

        # Code déjà expiré
        already_expired = PromoCode(
            code="PASTEXPIRY",
            tickets_reward=10,
            valid_until=now - timedelta(days=1)
        )
        assert already_expired.days_until_expiry() == 0

    def test_admin_list_promo_codes_with_expiry_info(self, client, auth_headers_admin, db):
        """Test de listage admin avec informations d'expiration."""
        now = datetime.now(timezone.utc)

        # Créer différents types de codes
        promos = [
            PromoCode(
                code="ACTIVE",
                tickets_reward=10,
                valid_until=now + timedelta(days=10),
                is_active=True
            ),
            PromoCode(
                code="EXPIRED",
                tickets_reward=5,
                valid_until=now - timedelta(days=1),
                is_active=True
            ),
            PromoCode(
                code="INACTIVE",
                tickets_reward=15,
                is_active=False
            )
        ]

        for promo in promos:
            db.add(promo)
        db.commit()

        # Test sans filtrage (inclut les expirés)
        response = client.get("/api/v1/admin/promo-codes/?include_expired=true", headers=auth_headers_admin)

        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 3

        # Vérifier les informations d'expiration
        for promo_info in data:
            assert "is_valid_now" in promo_info
            assert "is_expired" in promo_info
            assert "days_until_expiry" in promo_info

    def test_admin_expiring_soon_endpoint(self, client, auth_headers_admin, db):
        """Test de l'endpoint pour codes expirant bientôt."""
        now = datetime.now(timezone.utc)

        # Créer des codes qui expirent à différents moments
        promos = [
            PromoCode(
                code="EXPIRES_TOMORROW",
                tickets_reward=10,
                valid_until=now + timedelta(days=1),
                is_active=True
            ),
            PromoCode(
                code="EXPIRES_WEEK",
                tickets_reward=15,
                valid_until=now + timedelta(days=5),
                is_active=True
            ),
            PromoCode(
                code="EXPIRES_MONTH",
                tickets_reward=20,
                valid_until=now + timedelta(days=30),
                is_active=True
            )
        ]

        for promo in promos:
            db.add(promo)
        db.commit()

        # Test avec 7 jours (par défaut)
        response = client.get("/api/v1/admin/promo-codes/expiring-soon", headers=auth_headers_admin)

        assert response.status_code == 200
        data = response.json()
        assert data["days_ahead"] == 7
        assert data["total_count"] == 2  # Seulement les 2 premiers

        # Vérifier l'ordre (le plus proche en premier)
        expiring_codes = data["expiring_codes"]
        assert expiring_codes[0]["code"] == "EXPIRES_TOMORROW"
        assert expiring_codes[1]["code"] == "EXPIRES_WEEK"

    def test_admin_toggle_promo_active(self, client, auth_headers_admin, db):
        """Test d'activation/désactivation d'un code promo."""
        promo = PromoCode(
            code="TOGGLE",
            tickets_reward=10,
            is_active=True
        )
        db.add(promo)
        db.commit()
        db.refresh(promo)

        # Désactiver
        response = client.post(f"/api/v1/admin/promo-codes/{promo.id}/toggle-active", headers=auth_headers_admin)

        assert response.status_code == 200
        data = response.json()
        assert "désactivé" in data["message"]
        assert data["is_active"] == False
        assert data["is_valid_now"] == False

        # Réactiver
        response = client.post(f"/api/v1/admin/promo-codes/{promo.id}/toggle-active", headers=auth_headers_admin)

        assert response.status_code == 200
        data = response.json()
        assert "activé" in data["message"]
        assert data["is_active"] == True
        assert data["is_valid_now"] == True

    def test_update_promo_code_dates(self, client, auth_headers_admin, db):
        """Test de mise à jour des dates d'un code promo."""
        now = datetime.now(timezone.utc)
        promo = PromoCode(
            code="UPDATE",
            tickets_reward=10,
            valid_until=now + timedelta(days=5)
        )
        db.add(promo)
        db.commit()
        db.refresh(promo)

        # Étendre la date d'expiration
        new_expiry = now + timedelta(days=30)
        update_data = {
            "valid_until": new_expiry.isoformat()
        }

        response = client.put(f"/api/v1/admin/promo-codes/{promo.id}", json=update_data, headers=auth_headers_admin)

        assert response.status_code == 200
        data = response.json()
        assert data["days_until_expiry"] == 30

    def test_get_available_promo_codes_user(self, client, auth_headers_user, db):
        """Test de récupération des codes disponibles pour un utilisateur."""
        now = datetime.now(timezone.utc)

        # Créer différents codes
        promos = [
            PromoCode(
                code="AVAILABLE",
                tickets_reward=10,
                valid_until=now + timedelta(days=10),
                is_active=True
            ),
            PromoCode(
                code="EXPIRED_USER",
                tickets_reward=5,
                valid_until=now - timedelta(days=1),
                is_active=True
            ),
            PromoCode(
                code="INACTIVE_USER",
                tickets_reward=15,
                is_active=False
            )
        ]

        for promo in promos:
            db.add(promo)
        db.commit()

        response = client.get("/api/v1/promos/available", headers=auth_headers_user)

        assert response.status_code == 200
        data = response.json()

        # Seul le code "AVAILABLE" devrait être retourné
        assert len(data) == 1
        assert data[0]["tickets_reward"] == 10
        assert data[0]["days_until_expiry"] == 10
        # Le code exact ne doit pas être révélé
        assert "code" not in data[0]
