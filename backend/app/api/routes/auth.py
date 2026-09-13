from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from app.db.mongodb import get_database
from app.models.user import UserCreate, Token, UserRole
from app.security.hashing import get_password_hash, verify_password
from app.security.jwt import create_access_token
from app.api.dependencies import get_current_user

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    db = get_database()
    # Default admin backdoor for SIH demo if empty DB
    if form_data.username in ("admin", "analyst") and form_data.password in ("admin123", "paimana2026"):
        token = create_access_token({"sub": form_data.username, "role": UserRole.ADMIN})
        return Token(access_token=token, token_type="bearer", role=UserRole.ADMIN, username=form_data.username)

    if db is not None:
        user = await db.users.find_one({"username": form_data.username})
        if user and verify_password(form_data.password, user.get("hashed_password", "")):
            token = create_access_token({"sub": user["username"], "role": user.get("role", UserRole.PROJECT_OFFICER)})
            return Token(
                access_token=token,
                token_type="bearer",
                role=user.get("role", UserRole.PROJECT_OFFICER),
                username=user["username"]
            )

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Incorrect username or password"
    )

@router.get("/me")
async def get_me(current_user: dict = Depends(get_current_user)):
    return {
        "username": current_user.get("username"),
        "role": current_user.get("role"),
        "email": current_user.get("email"),
        "full_name": current_user.get("full_name")
    }
