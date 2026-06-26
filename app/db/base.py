from app.db.base_class import Base
from app.models.asset import Asset, AssetRelationship  # noqa: E402,F401
from app.models.organization import Organization  # noqa: E402,F401
from app.models.refresh_token import RefreshToken  # noqa: E402,F401
from app.models.user import User  # noqa: E402,F401

metadata = Base.metadata

