"""Server-side authorization. UI hiding is not authorization."""

from typing import Iterable, Set
from fastapi import Depends, HTTPException, status
from app.api.dependencies import get_current_user
from app.domain.enums import ProductRole
from app.models.user import UserRole

ROLE_MAP = {
    UserRole.VIEWER.value: {ProductRole.VIEWER},
    UserRole.PROJECT_OFFICER.value: {ProductRole.VIEWER, ProductRole.ANALYST},
    UserRole.MO_SPI_ANALYST.value: {ProductRole.VIEWER, ProductRole.ANALYST, ProductRole.INVESTIGATOR},
    UserRole.MINISTRY_OFFICIAL.value: {
        ProductRole.VIEWER,
        ProductRole.ANALYST,
        ProductRole.INVESTIGATOR,
        ProductRole.APPROVER,
    },
    UserRole.ADMIN.value: {
        ProductRole.VIEWER,
        ProductRole.ANALYST,
        ProductRole.INVESTIGATOR,
        ProductRole.APPROVER,
        ProductRole.ADMINISTRATOR,
    },
}

PERMISSIONS = {
    "projects:read": {
        ProductRole.VIEWER,
        ProductRole.ANALYST,
        ProductRole.INVESTIGATOR,
        ProductRole.APPROVER,
        ProductRole.ADMINISTRATOR,
    },
    "projects:write": {ProductRole.ANALYST, ProductRole.ADMINISTRATOR},
    "projects:reassess": {ProductRole.INVESTIGATOR, ProductRole.ADMINISTRATOR},
    "analytics:read": {
        ProductRole.VIEWER,
        ProductRole.ANALYST,
        ProductRole.INVESTIGATOR,
        ProductRole.APPROVER,
        ProductRole.ADMINISTRATOR,
    },
    "analytics:export": {ProductRole.ANALYST, ProductRole.INVESTIGATOR, ProductRole.ADMINISTRATOR},
    "investigations:read": {
        ProductRole.ANALYST,
        ProductRole.INVESTIGATOR,
        ProductRole.APPROVER,
        ProductRole.ADMINISTRATOR,
    },
    "investigations:create": {ProductRole.INVESTIGATOR, ProductRole.ADMINISTRATOR},
    "investigations:approve": {ProductRole.APPROVER, ProductRole.ADMINISTRATOR},
    "alerts:acknowledge": {
        ProductRole.ANALYST,
        ProductRole.INVESTIGATOR,
        ProductRole.APPROVER,
        ProductRole.ADMINISTRATOR,
    },
    "thresholds:write": {ProductRole.ADMINISTRATOR},
    "integrations:write": {ProductRole.ADMINISTRATOR},
    "users:manage": {ProductRole.ADMINISTRATOR},
    "system:admin": {ProductRole.ADMINISTRATOR},
}


def normalize_legacy_role(role: object) -> str:
    if role is None:
        return UserRole.VIEWER.value
    if hasattr(role, "value"):
        return str(role.value)
    text = str(role)
    if text.startswith("UserRole."):
        text = text.split(".", 1)[1]
    return text.upper()


def product_roles_for(user: dict) -> Set[ProductRole]:
    legacy = normalize_legacy_role(user.get("role"))
    mapped = set(ROLE_MAP.get(legacy, {ProductRole.VIEWER}))
    extra = user.get("product_roles") or []
    for item in extra:
        try:
            mapped.add(ProductRole(str(item)))
        except ValueError:
            continue
    return mapped


def has_permission(user: dict, permission: str) -> bool:
    allowed = PERMISSIONS.get(permission, set())
    return bool(product_roles_for(user) & allowed)


def require_permission(permission: str):
    def checker(current_user: dict = Depends(get_current_user)):
        if not has_permission(current_user, permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "error": {
                        "code": "FORBIDDEN",
                        "message": f"Permission '{permission}' is required",
                    }
                },
            )
        return current_user

    return checker


def assigned_project_filter(user: dict) -> dict | None:
    roles = product_roles_for(user)
    if ProductRole.ADMINISTRATOR in roles or ProductRole.ANALYST in roles:
        return None
    assigned = user.get("assigned_projects") or []
    if not assigned:
        return {"project_id": {"$in": []}}
    return {"project_id": {"$in": assigned}}
