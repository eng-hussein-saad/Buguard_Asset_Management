import pytest
from app.core.errors import AuthorizationError
from app.services.rbac import Permission, can, require_permission


@pytest.mark.parametrize(
    ("role", "allowed", "denied"),
    [
        ("viewer", {Permission.READ_ASSETS}, {Permission.CREATE_ASSET}),
        ("analyst", {Permission.CREATE_ASSET}, {Permission.DELETE_OR_ARCHIVE}),
        ("admin", {Permission.DELETE_OR_ARCHIVE}, set()),
    ],
)
def test_role_matrix(role, allowed, denied) -> None:
    for permission in allowed:
        assert can(role, permission)
        require_permission(role, permission)

    for permission in denied:
        assert not can(role, permission)
        with pytest.raises(AuthorizationError):
            require_permission(role, permission)
