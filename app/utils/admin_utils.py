# app/utils/admin_utils.py (ajouts pour les jeux)

from datetime import datetime
from typing import Optional, Dict, Any, List
from .exceptions import AdminException


def validate_game_players(min_players: int, max_players: int):
    """Valide la cohérence du nombre de joueurs d'un jeu."""
    if min_players < 1 or min_players > 8:
        raise AdminException("Le nombre minimum de joueurs doit être entre 1 et 8", 400)

    if max_players < 1 or max_players > 8:
        raise AdminException("Le nombre maximum de joueurs doit être entre 1 et 8", 400)

    if max_players < min_players:
        raise AdminException("Le nombre maximum de joueurs doit être >= au minimum", 400)


def validate_ticket_cost(cost: int):
    """Valide le coût en tickets d'un jeu."""
    if cost < 0:
        raise AdminException("Le coût en tickets ne peut pas être négatif", 400)

    if cost > 100:
        raise AdminException("Le coût en tickets ne peut pas dépasser 100", 400)


def calculate_game_difficulty_score(min_players: int, max_players: int, avg_score: float) -> str:
    """Calcule un score de difficulté basé sur les statistiques."""
    # Logique simple de calcul de difficulté
    if avg_score < 50:
        return "Très difficile"
    elif avg_score < 100:
        return "Difficile"
    elif avg_score < 200:
        return "Moyen"
    elif avg_score < 500:
        return "Facile"
    else:
        return "Très facile"


def calculate_game_popularity_rank(reservations_count: int, total_games: int) -> Dict[str, Any]:
    """Calcule le rang de popularité d'un jeu."""
    # Logique simplifiée de calcul de popularité
    if reservations_count == 0:
        return {
            "rank": "Non classé",
            "percentile": 0,
            "category": "Nouveau/Inutilisé"
        }

    # Simulation d'un calcul de percentile
    percentile = min(100, (reservations_count / max(total_games, 1)) * 100)

    if percentile >= 80:
        category = "Très populaire"
    elif percentile >= 60:
        category = "Populaire"
    elif percentile >= 40:
        category = "Modérément populaire"
    elif percentile >= 20:
        category = "Peu populaire"
    else:
        category = "Impopulaire"

    return {
        "rank": f"Top {int(100 - percentile)}%",
        "percentile": round(percentile, 1),
        "category": category
    }


def format_game_revenue_report(revenue_data: Dict[str, Any]) -> Dict[str, Any]:
    """Formate un rapport de revenus pour un jeu."""
    return {
        "total_tickets_consumed": revenue_data.get("total_tickets_spent", 0),
        "estimated_revenue_euros": revenue_data.get("estimated_revenue_euros", 0),
        "revenue_per_game": revenue_data.get("tickets_per_game", 0),
        "total_sessions": revenue_data.get("total_reservations", 0),
        "average_revenue_per_session": round(
            revenue_data.get("estimated_revenue_euros", 0) / max(revenue_data.get("total_reservations", 1), 1),
            2
        )
    }


def generate_game_recommendations(game_stats: Dict[str, Any]) -> List[str]:
    """Génère des recommandations d'amélioration pour un jeu."""
    recommendations = []

    # Analyse du taux de complétion
    completion_rate = game_stats.get("reservation_stats", {}).get("completion_rate", 0)
    if completion_rate < 50:
        recommendations.append(
            "⚠️ Taux de complétion faible - Vérifiez si le jeu présente des problèmes techniques"
        )
    elif completion_rate < 70:
        recommendations.append(
            "💡 Taux de complétion moyen - Considérez l'amélioration de l'expérience utilisateur"
        )

    # Analyse de la popularité
    total_reservations = game_stats.get("reservation_stats", {}).get("total_reservations", 0)
    if total_reservations == 0:
        recommendations.append(
            "📢 Aucune réservation - Envisagez une campagne de promotion ou réduisez le coût"
        )
    elif total_reservations < 10:
        recommendations.append(
            "📈 Faible utilisation - Vérifiez le positionnement et la visibilité du jeu"
        )

    # Analyse des revenus
    revenue = game_stats.get("revenue_stats", {}).get("estimated_revenue_euros", 0)
    if revenue == 0:
        recommendations.append(
            "💰 Aucun revenu généré - Reconsidérez la stratégie de tarification"
        )

    # Recommandations générales
    if not recommendations:
        recommendations.append("✅ Performance satisfaisante - Continuez le monitoring régulier")

    return recommendations


def validate_bulk_game_action(action: str, parameters: Optional[Dict[str, Any]] = None):
    """Valide les paramètres d'une action en masse sur les jeux."""
    allowed_actions = ["delete", "restore", "update_cost", "toggle_active"]

    if action not in allowed_actions:
        raise AdminException(f"Action '{action}' non autorisée", 400)

    if action == "update_cost":
        if not parameters or "new_cost" not in parameters:
            raise AdminException("Le paramètre 'new_cost' est requis pour l'action update_cost", 400)

        new_cost = parameters["new_cost"]
        if not isinstance(new_cost, int) or new_cost < 0 or new_cost > 100:
            raise AdminException("Le nouveau coût doit être un entier entre 0 et 100", 400)


def calculate_game_performance_metrics(game_stats: Dict[str, Any]) -> Dict[str, Any]:
    """Calcule des métriques de performance avancées pour un jeu."""
    reservation_stats = game_stats.get("reservation_stats", {})
    score_stats = game_stats.get("score_stats", {})
    revenue_stats = game_stats.get("revenue_stats", {})

    total_reservations = reservation_stats.get("total_reservations", 0)
    completed_reservations = reservation_stats.get("completed_reservations", 0)
    total_games_played = score_stats.get("total_games_played", 0)
    total_revenue = revenue_stats.get("estimated_revenue_euros", 0)

    # Calculs des métriques
    completion_rate = (completed_reservations / max(total_reservations, 1)) * 100
    revenue_per_game = total_revenue / max(total_games_played, 1)
    games_per_reservation = total_games_played / max(completed_reservations, 1)

    # Score de performance global (0-100)
    performance_score = min(100, (
            (completion_rate * 0.4) +  # 40% basé sur le taux de complétion
            (min(revenue_per_game * 10, 50) * 0.3) +  # 30% basé sur le revenu par partie
            (min(games_per_reservation * 20, 30) * 0.3)  # 30% basé sur l'engagement
    ))

    return {
        "completion_rate": round(completion_rate, 2),
        "revenue_per_game": round(revenue_per_game, 2),
        "games_per_reservation": round(games_per_reservation, 2),
        "performance_score": round(performance_score, 2),
        "performance_grade": _get_performance_grade(performance_score),
        "trend_indicator": _calculate_trend_indicator(game_stats)
    }


def _get_performance_grade(score: float) -> str:
    """Convertit un score de performance en grade."""
    if score >= 90:
        return "A+"
    elif score >= 80:
        return "A"
    elif score >= 70:
        return "B+"
    elif score >= 60:
        return "B"
    elif score >= 50:
        return "C+"
    elif score >= 40:
        return "C"
    elif score >= 30:
        return "D"
    else:
        return "F"


def _calculate_trend_indicator(game_stats: Dict[str, Any]) -> str:
    """Calcule un indicateur de tendance simple."""
    # Pour une vraie implémentation, on comparerait avec les périodes précédentes
    # Ici, c'est une simulation basée sur les données actuelles

    completion_rate = game_stats.get("reservation_stats", {}).get("completion_rate", 0)
    total_reservations = game_stats.get("reservation_stats", {}).get("total_reservations", 0)

    if total_reservations > 50 and completion_rate > 80:
        return "📈 En hausse"
    elif total_reservations > 20 and completion_rate > 60:
        return "➡️ Stable"
    elif total_reservations < 10 or completion_rate < 40:
        return "📉 En baisse"
    else:
        return "🔄 Variable"


def format_game_analytics_timeframe(start_date: datetime, end_date: datetime, group_by: str) -> Dict[str, Any]:
    """Formate les informations de période pour les analytics."""
    duration = end_date - start_date

    if group_by == "hour":
        expected_points = int(duration.total_seconds() / 3600)
        granularity = "Horaire"
    elif group_by == "day":
        expected_points = duration.days
        granularity = "Quotidienne"
    elif group_by == "week":
        expected_points = int(duration.days / 7)
        granularity = "Hebdomadaire"
    elif group_by == "month":
        expected_points = int(duration.days / 30)
        granularity = "Mensuelle"
    else:
        expected_points = 0
        granularity = "Inconnue"

    return {
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "duration_days": duration.days,
        "granularity": granularity,
        "expected_data_points": expected_points
    }


def validate_game_analytics_request(start_date: Optional[datetime], end_date: Optional[datetime], group_by: str):
    """Valide une demande d'analytics de jeu."""
    if start_date and end_date:
        if end_date <= start_date:
            raise AdminException("La date de fin doit être après la date de début", 400)

        duration = end_date - start_date
        if duration.days > 365:
            raise AdminException("La période d'analyse ne peut pas dépasser 365 jours", 400)

        if duration.days < 1 and group_by in ["week", "month"]:
            raise AdminException(
                f"Période trop courte pour un groupement {group_by}",
                400
            )

    allowed_group_by = ["hour", "day", "week", "month"]
    if group_by not in allowed_group_by:
        raise AdminException(
            f"group_by doit être l'un de : {', '.join(allowed_group_by)}",
            400
        )