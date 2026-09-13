from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from app.db.mongodb import get_database
from app.security.jwt import decode_token
from app.models.user import UserRole, UserInDB
from typing import List

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

async def get_current_user(token: str = Depends(oauth2_scheme)) -> dict:
    payload = decode_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    username: str = payload.get("sub")
    if not username:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token subject")
    
    db = get_database()
    if db is not None:
        user = await db.users.find_one({"username": username})
        if user:
            return user

    # Fallback default demo user
    return {
        "username": username,
        "role": payload.get("role", UserRole.MO_SPI_ANALYST),
        "email": f"{username}@paimana.gov.in",
        "full_name": "Executive Analyst"
    }

def require_roles(allowed_roles: List[UserRole]):
    def role_checker(current_user: dict = Depends(get_current_user)):
        role = current_user.get("role")
        if role not in [r.value if hasattr(r, 'value') else str(r) for r in allowed_roles]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Operation not permitted for current user role"
            )
        return current_user
    return role_checker
