from fastapi import APIRouter, Depends, HTTPException, status

from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_session
from app.core.db_client import DBClient
from app.core import security
from app.schemas.user import UserCreate, UserRead, Token, TokenInfo

from datetime import datetime, timezone
import traceback
import jwt

from app.core.config import settings

router = APIRouter(tags=["Auth"])

@router.post("/login", response_model=Token)
async def login(
    creds: UserCreate,
    session: AsyncSession = Depends(get_session),
):
    db = DBClient(session)
    user = await db.query_table_data(
        "users", filters={"email": creds.email}, single_row=True
    )
    if not user or not security.verify_password(creds.password, user["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = security.create_access_token({"sub": str(user.get("id"))})
    return {"access_token": token, "token_type": "bearer"}

@router.post("/signup", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def create_user(
    data: UserCreate,
    session: AsyncSession = Depends(get_session),
):  
    db = DBClient(session)
    # Hash the password before saving
    hashed_password = security.hash_password(data.password)
    payload = {
        "email": data.email,
        "hashed_password": hashed_password,
        "is_active": True
    }

    try:
        new_user = await db.create_table_entry(
            "users",
            payload
        )
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=400, detail="Internal error while creating user")

    if not new_user:
        raise HTTPException(
            status_code=400,
            detail="Could not create user (email may already be registered)"
        )
    new_user.pop("hashed_password", None)  # Remove hashed password from response
    return new_user
    

# Other auth-related endpoints
@router.get("/token/validate", response_model=TokenInfo)
async def validate_token(token: str = Depends(security.oauth2_scheme)):
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET,
            algorithms=[settings.JWT_ALGORITHM]
        )
    except jwt.ExpiredSignatureError:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Token has expired")
    except jwt.PyJWTError:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid token")

    exp_timestamp = payload.get("exp")
    if exp_timestamp is None:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "No expiration in token")

    exp_dt = datetime.fromtimestamp(exp_timestamp, tz=timezone.utc)
    now = datetime.now(timezone.utc)
    remaining = int((exp_dt - now).total_seconds())

    return {
        "exp": exp_dt,
        "sub": payload.get("sub"),
        "expires_in": remaining,
    }