from enum import StrEnum

from app.core.errors import AuthorizationError


class Permission(StrEnum):
    READ_ASSETS = "read_assets"
    READ_RELATIONSHIPS = "read_relationships"
    READ_GRAPH = "read_graph"
    CREATE_ASSET = "create_asset"
    UPDATE_ASSET = "update_asset"
    BULK_IMPORT = "bulk_import"
    MARK_STALE = "mark_stale"
    CREATE_RELATIONSHIP = "create_relationship"
    DELETE_OR_ARCHIVE = "delete_or_archive"


ROLE_PERMISSIONS: dict[str, set[Permission]] = {
    "viewer": {
        Permission.READ_ASSETS,
        Permission.READ_RELATIONSHIPS,
        Permission.READ_GRAPH,
    },
    "analyst": {
        Permission.READ_ASSETS,
        Permission.READ_RELATIONSHIPS,
        Permission.READ_GRAPH,
        Permission.CREATE_ASSET,
        Permission.UPDATE_ASSET,
        Permission.BULK_IMPORT,
        Permission.MARK_STALE,
        Permission.CREATE_RELATIONSHIP,
    },
    "admin": set(Permission),
}


def can(role: str, permission: Permission) -> bool:
    return permission in ROLE_PERMISSIONS.get(role, set())


def require_permission(role: str, permission: Permission) -> None:
    if not can(role, permission):
        raise AuthorizationError(permission.value)
