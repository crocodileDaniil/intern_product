from enum import StrEnum

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.utils.config import settings


class Role(StrEnum):
    admin = "admin"
    specialist = "specialist"
    user = "user"


security = HTTPBearer()


def get_current_role(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> Role:
    token_to_role = {
        settings.admin_token: Role.admin,
        settings.specialist_token: Role.specialist,
        settings.user_token: Role.user,
    }
    role = token_to_role.get(credentials.credentials)
    if role is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token",
        )
    return role


def require_roles(*allowed_roles: Role):
    def dependency(role: Role = Depends(get_current_role)) -> Role:
        if role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions",
            )
        return role

    return dependency
