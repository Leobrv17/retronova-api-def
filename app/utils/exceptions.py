from fastapi import HTTPException


class AdminException(HTTPException):
    """Exception personnalisée pour les erreurs admin."""

    def __init__(self, detail: str, status_code: int = 400):
        super().__init__(status_code=status_code, detail=detail)


class ValidationException(AdminException):
    """Exception pour les erreurs de validation."""

    def __init__(self, detail: str):
        super().__init__(detail, 422)


class NotFoundAdminException(AdminException):
    """Exception pour les ressources non trouvées."""

    def __init__(self, resource: str):
        super().__init__(f"{resource} non trouvé(e)", 404)


class ConflictAdminException(AdminException):
    """Exception pour les conflits de données."""

    def __init__(self, detail: str):
        super().__init__(detail, 409)