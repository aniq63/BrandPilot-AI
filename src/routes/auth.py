from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from database.crud import create_user, get_user_by_email
from src.routes.deps import get_current_user, get_db
from src.routes.schemas import LoginRequest, SignupRequest, TokenResponse, UserResponse
from src.security import create_access_token, hash_password, verify_password
from src.utilis.logging import log_calls
from database.models import User

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/signup", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
@log_calls
def signup(payload: SignupRequest, db: Session = Depends(get_db)):
    email = payload.email.strip().lower()
    if get_user_by_email(db, email):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists",
        )

    user = create_user(
        db=db,
        username=payload.username.strip(),
        email=email,
        password_hash=hash_password(payload.password),
    )
    return TokenResponse(
        access_token=create_access_token(user.id),
        user=UserResponse.model_validate(user),
    )


@router.post("/login", response_model=TokenResponse)
@log_calls
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    user = get_user_by_email(db, payload.email.strip().lower())
    if user is None or not verify_password(payload.password, user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )

    return TokenResponse(
        access_token=create_access_token(user.id),
        user=UserResponse.model_validate(user),
    )


@router.get("/me", response_model=UserResponse)
@log_calls
def me(current_user: User = Depends(get_current_user)):
    return UserResponse.model_validate(current_user)
