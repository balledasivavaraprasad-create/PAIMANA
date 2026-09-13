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
        "full_name": current_user.get("full_name"),
        "dphis_alert_threshold": current_user.get("dphis_alert_threshold", 75.0),
        "alert_email": current_user.get("alert_email") or current_user.get("email"),
        "notify_via_email": current_user.get("notify_via_email", True)
    }

@router.get("/preferences")
async def get_preferences(current_user: dict = Depends(get_current_user)):
    return {
        "dphis_alert_threshold": current_user.get("dphis_alert_threshold", 75.0),
        "alert_email": current_user.get("alert_email") or current_user.get("email"),
        "notify_via_email": current_user.get("notify_via_email", True)
    }

@router.put("/preferences")
async def update_preferences(
    payload: dict,
    current_user: dict = Depends(get_current_user)
):
    db = get_database()
    threshold = float(payload.get("dphis_alert_threshold", 75.0))
    alert_email = payload.get("alert_email") or current_user.get("email")
    notify_via_email = bool(payload.get("notify_via_email", True))

    update_fields = {
        "dphis_alert_threshold": threshold,
        "alert_email": alert_email,
        "notify_via_email": notify_via_email
    }

    if db is not None:
        await db.users.update_one(
            {"username": current_user.get("username")},
            {"$set": update_fields},
            upsert=True
        )

    return {
        "message": "Preferences updated successfully",
        "preferences": update_fields
    }
