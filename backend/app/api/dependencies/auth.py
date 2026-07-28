from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from app.core.security import decode_access_token
from app.core.config import settings
from pydantic import BaseModel
import structlog

logger = structlog.get_logger(__name__)
# Setting auto_error=False allows optional auth for local development
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login", auto_error=False)

class UserContext(BaseModel):
    user_id: str
    tenant_id: str
    role: str

async def get_current_user(token: str = Depends(oauth2_scheme)) -> UserContext:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    # In development mode, if no token is provided, fall back to a default dev user
    if token is None:
        if settings.ENV == "development":
            logger.debug("No token provided, using dev fallback user")
            return UserContext(user_id="dev_user", tenant_id="dev_tenant", role="user")
        else:
            logger.warning("No token provided in production environment")
            raise credentials_exception
            
    payload = decode_access_token(token)
    if payload is None:
        if settings.ENV == "development":
            logger.debug("Failed to decode token, using dev fallback user")
            return UserContext(user_id="dev_user", tenant_id="dev_tenant", role="user")
        logger.warning("Failed to decode JWT token")
        raise credentials_exception
        
    user_id: str = payload.get("sub")
    tenant_id: str = payload.get("tenant_id")
    role: str = payload.get("role", "user")
    
    if user_id is None or tenant_id is None:
        if settings.ENV == "development":
            return UserContext(user_id="dev_user", tenant_id="dev_tenant", role="user")
        logger.warning("Token missing required fields", user_id=user_id, tenant_id=tenant_id)
        raise credentials_exception
        
    # In a real app, you would query the DB here to ensure the user still exists and is active.
    # For now, we trust the JWT token.
    return UserContext(user_id=user_id, tenant_id=tenant_id, role=role)

async def get_current_tenant(current_user: UserContext = Depends(get_current_user)) -> str:
    """Dependency to quickly extract just the tenant_id for data isolation."""
    return current_user.tenant_id
