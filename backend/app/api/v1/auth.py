from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import get_db
from app.core.security import verify_password, get_password_hash, create_access_token
from app.models.user import User, UserRole
from app.models.channel import Channel
from app.schemas.user import UserCreate, UserRead
from app.schemas.auth import Token, LoginRequest
from app.api.deps import get_current_user

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/register", response_model=Token, status_code=status.HTTP_201_CREATED)
async def register(user_in: UserCreate, db: AsyncSession = Depends(get_db)):
    # Check if email exists
    existing_email = await db.execute(select(User).where(User.email == user_in.email))
    if existing_email.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with this email already exists"
        )

    # Check if username exists
    existing_user = await db.execute(select(User).where(User.username == user_in.username))
    if existing_user.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with this username already exists"
        )

    # Create user
    user = User(
        email=user_in.email,
        username=user_in.username,
        full_name=user_in.full_name or user_in.username,
        avatar_url=user_in.avatar_url or f"https://api.dicebear.com/7.x/bottts/svg?seed={user_in.username}",
        hashed_password=get_password_hash(user_in.password),
        role=UserRole.USER
    )
    db.add(user)
    await db.flush()

    # Automatically create personal Channel
    channel = Channel(
        user_id=user.id,
        handle=f"@{user.username}",
        name=user.full_name or user.username,
        description=f"Welcome to {user.username}'s official channel!",
        avatar_url=user.avatar_url
    )
    db.add(channel)
    await db.commit()
    await db.refresh(user)

    token = create_access_token(user.id)
    return Token(access_token=token, token_type="bearer", user=UserRead.model_validate(user))

@router.post("/login", response_model=Token)
async def login(
    login_data: LoginRequest,
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(User).where((User.email == login_data.email) | (User.username == login_data.email))
    )
    user = result.scalar_one_or_none()

    if not user or not verify_password(login_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User account is deactivated"
        )

    token = create_access_token(user.id)
    return Token(access_token=token, token_type="bearer", user=UserRead.model_validate(user))

@router.get("/me", response_model=UserRead)
async def get_me(current_user: User = Depends(get_current_user)):
    return UserRead.model_validate(current_user)
