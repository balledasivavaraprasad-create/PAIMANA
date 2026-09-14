import random
import hashlib
from datetime import datetime, timezone, timedelta
from typing import Optional, List, Union
from fastapi import APIRouter, Depends, HTTPException, Request, status, Body
from fastapi.security import OAuth2PasswordRequestForm

from app.db.mongodb import get_database
from app.models.user import (
    UserCreate, Token, UserRole, UserRegisterRequest, VerifyOtpRequest,
    ResendOtpRequest, LoginJsonRequest, MinistryItem
)
from app.security.hashing import get_password_hash, verify_password
from app.security.jwt import create_access_token
from app.api.dependencies import get_current_user
from app.services.email_service import (
    send_otp_email, send_account_created_email, send_login_alert_email
)
from app.config.settings import settings
from app.config.logging import logger

router = APIRouter(tags=["Authentication"])

MINISTRIES = [
    {"id": 1, "name": "Road Transport & Highways", "sector": "Transport & Logistics"},
    {"id": 2, "name": "Railways", "sector": "Railways & Freight"},
    {"id": 3, "name": "Housing & Urban Affairs", "sector": "Urban Transit & Metro"},
    {"id": 4, "name": "Power", "sector": "Energy & Power"},
    {"id": 5, "name": "Jal Shakti", "sector": "Water Resources & Sanitation"},
    {"id": 6, "name": "Coal", "sector": "Coal & Mining"},
    {"id": 7, "name": "Steel", "sector": "Steel & Metallurgical"},
    {"id": 8, "name": "Petroleum & Natural Gas", "sector": "Petrochemical & Gas"},
    {"id": 9, "name": "Ports, Shipping & Waterways", "sector": "Ports & Shipping"},
]

def generate_otp() -> str:
    return f"{random.randint(100000, 999999)}"

def hash_otp(code: str) -> str:
    return hashlib.sha256(code.encode("utf-8")).hexdigest()

# ============================================================
# GET /ministries & /auth/ministries
# ============================================================
@router.get("/ministries", response_model=List[MinistryItem])
@router.get("/auth/ministries", response_model=List[MinistryItem])
async def get_ministries():
    """Returns official infrastructure ministries and departments for signup."""
    return MINISTRIES

# ============================================================
# POST /auth/register
# ============================================================
@router.post("/auth/register")
async def register(req: UserRegisterRequest, request: Request):
    """
    Registers a new ministry official.
    Issues a 6-digit OTP to the provided email and prints to console.
    """
    if len(req.password) < 8:
        raise HTTPException(status_code=400, detail="Password must be at least 8 characters long.")
    if not req.termsAccepted or not req.aiAckAccepted:
        raise HTTPException(status_code=400, detail="You must accept the Terms and AI/ML processing acknowledgement.")

    db = get_database()
    email_clean = req.email.lower().strip()
    username = email_clean.split("@")[0]

    # Resolve ministry name
    ministry_name = req.ministry
    if req.ministryId:
        for m in MINISTRIES:
            if m["id"] == req.ministryId:
                ministry_name = m["name"]
                break

    if db is not None:
        existing = await db.users.find_one({"email": email_clean})
        if existing:
            if existing.get("is_verified", False):
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="An account with this official email already exists. Please sign in instead."
                )
            # Unverified account re-attempting signup: issue fresh OTP
            code = generate_otp()
            code_hash = hash_otp(code)
            expires_at = datetime.now(timezone.utc) + timedelta(minutes=settings.OTP_EXPIRE_MINUTES)
            await db.otp_codes.insert_one({
                "email": email_clean,
                "purpose": "signup",
                "code_hash": code_hash,
                "expires_at": expires_at,
                "attempts": 0,
                "consumed": False,
                "created_at": datetime.now(timezone.utc)
            })
            await send_otp_email(email_clean, code, "signup")
            return {"message": "This email is registered but not yet verified. A new verification code has been dispatched."}

    # Hash password & create user record
    hashed = get_password_hash(req.password)
    resolved_ministry = ministry_name or "Road Transport & Highways"

    # New users start with 0 projects until they ingest their first capital asset
    user_doc = {
        "username": username,
        "email": email_clean,
        "full_name": req.fullName,
        "ministry": resolved_ministry,
        "designation": req.designation or "Project Officer",
        "role": UserRole.PROJECT_OFFICER,
        "hashed_password": hashed,
        "is_active": True,
        "is_verified": False,
        "failed_logins": 0,
        "locked_until": None,
        "dphis_alert_threshold": 75.0,
        "alert_email": email_clean,
        "notify_via_email": True,
        "terms_accepted": True,
        "ai_ack_accepted": True,
        "assigned_projects": [],
        "created_at": datetime.now(timezone.utc)
    }

    if db is not None:
        await db.users.insert_one(user_doc)

        # Issue single-use 6-digit OTP
        code = generate_otp()
        code_hash = hash_otp(code)
        expires_at = datetime.now(timezone.utc) + timedelta(minutes=settings.OTP_EXPIRE_MINUTES)

        await db.otp_codes.insert_one({
            "email": email_clean,
            "purpose": "signup",
            "code_hash": code_hash,
            "expires_at": expires_at,
            "attempts": 0,
            "consumed": False,
            "created_at": datetime.now(timezone.utc)
        })

        # Send OTP email
        await send_otp_email(email_clean, code, "signup")

    return {"message": "Account created successfully. Check your email for the 6-digit verification code."}

# ============================================================
# POST /auth/verify-otp
# ============================================================
@router.post("/auth/verify-otp")
async def verify_otp(req: VerifyOtpRequest):
    """Verifies the 6-digit OTP code and activates the account."""
    email_clean = req.email.lower().strip()
    otp_code = req.otp.strip()

    if len(otp_code) != 6 or not otp_code.isdigit():
        raise HTTPException(status_code=400, detail="Please enter all 6 numeric digits.")

    db = get_database()
    if db is None:
        # Fallback for mock/in-memory mode
        return {"message": "Account verified successfully. You can now sign in."}

    user = await db.users.find_one({"email": email_clean})
    if not user:
        raise HTTPException(status_code=404, detail="No registration record found for this email.")

    # Find latest unconsumed OTP for this email
    otp_record = await db.otp_codes.find_one(
        {"email": email_clean, "purpose": "signup", "consumed": False},
        sort=[("created_at", -1)]
    )

    if not otp_record:
        raise HTTPException(status_code=400, detail="No pending verification code found. Please request a new one.")

    if datetime.now(timezone.utc) > otp_record["expires_at"].replace(tzinfo=timezone.utc):
        raise HTTPException(status_code=400, detail="Verification code has expired. Please request a new one.")

    if otp_record.get("attempts", 0) >= 5:
        raise HTTPException(status_code=400, detail="Too many invalid attempts. Please request a new code.")

    # Compare SHA-256 hash
    if hash_otp(otp_code) != otp_record["code_hash"]:
        await db.otp_codes.update_one({"_id": otp_record["_id"]}, {"$inc": {"attempts": 1}})
        raise HTTPException(status_code=400, detail="Incorrect verification code.")

    # Mark OTP consumed and user verified
    await db.otp_codes.update_one({"_id": otp_record["_id"]}, {"$set": {"consumed": True}})
    await db.users.update_one({"_id": user["_id"]}, {"$set": {"is_verified": True}})

    # Dispatch welcome email asynchronously
    await send_account_created_email(email_clean, user.get("full_name", "Officer"))

    return {"message": "Account verified successfully. You can now sign in."}

# ============================================================
# POST /auth/resend-otp
# ============================================================
@router.post("/auth/resend-otp")
async def resend_otp(req: ResendOtpRequest):
    """Resends a fresh 6-digit OTP code to unverified user."""
    email_clean = req.email.lower().strip()
    db = get_database()

    if db is not None:
        user = await db.users.find_one({"email": email_clean})
        if not user:
            raise HTTPException(status_code=404, detail="No account found for that email.")
        if user.get("is_verified", False):
            raise HTTPException(status_code=400, detail="This account is already verified.")

        code = generate_otp()
        code_hash = hash_otp(code)
        expires_at = datetime.now(timezone.utc) + timedelta(minutes=settings.OTP_EXPIRE_MINUTES)

        await db.otp_codes.insert_one({
            "email": email_clean,
            "purpose": req.purpose,
            "code_hash": code_hash,
            "expires_at": expires_at,
            "attempts": 0,
            "consumed": False,
            "created_at": datetime.now(timezone.utc)
        })

        await send_otp_email(email_clean, code, req.purpose)

    return {"message": "A new verification code has been dispatched."}

# ============================================================
# POST /auth/login (supports JSON and form-data)
# ============================================================
@router.post("/auth/login", response_model=Token)
async def login(
    request: Request,
    json_body: Optional[LoginJsonRequest] = Body(None),
    form_data: Optional[OAuth2PasswordRequestForm] = Depends(lambda: None)
):
    """
    Authenticates user and issues access token.
    Supports both JSON body ({ email, password }) and OAuth2 form data.
    """
    db = get_database()

    # Extract credentials
    user_identifier = ""
    password = ""
    if json_body:
        user_identifier = json_body.email.strip()
        password = json_body.password
    elif form_data:
        user_identifier = form_data.username.strip()
        password = form_data.password
    else:
        try:
            raw_json = await request.json()
            user_identifier = (raw_json.get("email") or raw_json.get("username") or "").strip()
            password = raw_json.get("password") or ""
        except Exception:
            pass

    if not user_identifier or not password:
        raise HTTPException(status_code=400, detail="Email/username and password are required.")

    # 1. Backdoor / Demo accounts
    if user_identifier.lower() in ("admin", "admin@paimana.gov.in") and password in ("admin123", "paimana2026"):
        admin_doc = await db.users.find_one({"username": "admin"}) if db is not None else None
        token = create_access_token({"sub": "admin", "role": UserRole.ADMIN})
        return Token(
            access_token=token,
            token_type="bearer",
            role=UserRole.ADMIN,
            username="admin",
            email="admin@paimana.gov.in",
            full_name="National Director (MoSPI)",
            ministry="Ministry of Statistics and Programme Implementation",
            assigned_projects=admin_doc.get("assigned_projects", []) if admin_doc else []
        )
    if user_identifier.lower() in ("analyst", "analyst@paimana.gov.in") and password in ("analyst123", "paimana2026"):
        analyst_doc = await db.users.find_one({"username": "analyst"}) if db is not None else None
        token = create_access_token({"sub": "analyst", "role": UserRole.MO_SPI_ANALYST})
        return Token(
            access_token=token,
            token_type="bearer",
            role=UserRole.MO_SPI_ANALYST,
            username="analyst",
            email="analyst@paimana.gov.in",
            full_name="Lead Infrastructure Risk Analyst",
            ministry="Central Project Intelligence Unit",
            assigned_projects=analyst_doc.get("assigned_projects", []) if analyst_doc else []
        )

    # 2. Database verification
    if db is not None:
        user = await db.users.find_one({
            "$or": [
                {"email": user_identifier.lower()},
                {"username": user_identifier}
            ]
        })

        if user:
            if not user.get("is_active", True):
                raise HTTPException(status_code=403, detail="This account has been suspended.")
            if not user.get("is_verified", True):
                raise HTTPException(status_code=403, detail="Please verify your account via the signup OTP first.")

            if verify_password(password, user.get("hashed_password", "")):
                token = create_access_token({
                    "sub": user["username"],
                    "role": user.get("role", UserRole.PROJECT_OFFICER)
                })

                # Dispatch asynchronous login alert email
                now_str = datetime.now().strftime("%d %b %Y, %I:%M %p")
                client_ip = request.client.host if request.client else "127.0.0.1"
                await send_login_alert_email(user["email"], now_str, client_ip)

                return Token(
                    access_token=token,
                    token_type="bearer",
                    role=user.get("role", UserRole.PROJECT_OFFICER),
                    username=user["username"],
                    email=user["email"],
                    full_name=user.get("full_name", user["username"]),
                    ministry=user.get("ministry", "Central Infrastructure"),
                    assigned_projects=user.get("assigned_projects", [])
                )

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid official email or password."
    )

# ============================================================
# User Profile & Preferences
# ============================================================
@router.get("/auth/me")
async def get_me(current_user: dict = Depends(get_current_user)):
    return {
        "username": current_user.get("username"),
        "role": current_user.get("role"),
        "email": current_user.get("email"),
        "full_name": current_user.get("full_name"),
        "ministry": current_user.get("ministry"),
        "designation": current_user.get("designation"),
        "dphis_alert_threshold": current_user.get("dphis_alert_threshold", 75.0),
        "alert_email": current_user.get("alert_email") or current_user.get("email"),
        "notify_via_email": current_user.get("notify_via_email", True),
        "assigned_projects": current_user.get("assigned_projects", [])
    }

@router.get("/auth/preferences")
async def get_preferences(current_user: dict = Depends(get_current_user)):
    return {
        "dphis_alert_threshold": current_user.get("dphis_alert_threshold", 75.0),
        "alert_email": current_user.get("alert_email") or current_user.get("email"),
        "notify_via_email": current_user.get("notify_via_email", True)
    }

@router.put("/auth/preferences")
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
