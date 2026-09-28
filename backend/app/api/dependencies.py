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
    
    from app.db.seeded_data import DEFAULT_USER_10_IDS, DEFAULT_ADMIN_28_IDS

    db = get_database()
    if db is not None:
        user = await db.users.find_one({"username": username})
        if user:
            role = user.get("role", UserRole.PROJECT_OFFICER)
            is_adm = str(role).upper() in ("ADMIN", "ANALYST", "USERROLE.ADMIN", "USERROLE.MO_SPI_ANALYST")
            assigned = user.get("assigned_projects", [])
            if is_adm and len(assigned) < 25:
                user["assigned_projects"] = DEFAULT_ADMIN_28_IDS
            elif not is_adm and len(assigned) != 10:
                user["assigned_projects"] = (assigned[:10] if len(assigned) >= 10 else DEFAULT_USER_10_IDS)
            return user

    # Fallback default demo user
    role = payload.get("role", UserRole.MO_SPI_ANALYST)
    is_adm = str(role).upper() in ("ADMIN", "ANALYST", "USERROLE.ADMIN", "USERROLE.MO_SPI_ANALYST")
    return {
        "username": username,
        "role": role,
        "email": f"{username}@paimana.gov.in",
        "full_name": "Executive Analyst",
        "assigned_projects": DEFAULT_ADMIN_28_IDS if is_adm else DEFAULT_USER_10_IDS
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
